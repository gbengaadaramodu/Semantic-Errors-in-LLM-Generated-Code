"""
Ollama HTTP client for Objective 3.

Provides :class:`OllamaClient`, a thin wrapper around the Ollama REST API,
with retry logic, structured error handling, and full logging.
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional

import requests

from objective3.config import Obj3OllamaConfig

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class OllamaConnectionError(RuntimeError):
    """Raised when the Ollama server cannot be reached after all retries."""


class OllamaGenerationError(RuntimeError):
    """Raised when the Ollama server returns an HTTP error during generation."""


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class OllamaClient:
    """HTTP client for the Ollama local inference server.

    Parameters
    ----------
    config:
        An :class:`~objective3.config.Obj3OllamaConfig` instance that carries
        the base URL, default model, temperature, token limits, and retry
        settings.
    """

    def __init__(self, config: Obj3OllamaConfig) -> None:
        self.config = config
        self._base_url = config.base_url.rstrip("/")
        self.session = requests.Session()
        logger.debug("OllamaClient initialised – base_url=%s", self._base_url)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _url(self, path: str) -> str:
        """Build a full endpoint URL from a relative *path*."""
        return f"{self._base_url}/{path.lstrip('/')}"

    def _get(self, path: str, timeout: int = 10) -> requests.Response:
        """Perform a GET request and return the :class:`requests.Response`.

        Parameters
        ----------
        path:
            API path relative to the base URL.
        timeout:
            Socket timeout in seconds.

        Returns
        -------
        requests.Response
            The raw response object (caller is responsible for status checks).
        """
        url = self._url(path)
        logger.debug("GET %s", url)
        return self.session.get(url, timeout=timeout)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Return ``True`` if the Ollama server is reachable and responding.

        Performs a GET request to ``/api/tags``.  Any network error or
        non-2xx response causes ``False`` to be returned rather than raising
        so callers can use this as a simple liveness probe.

        Returns
        -------
        bool
            ``True`` when the server is healthy, ``False`` otherwise.
        """
        try:
            response = self._get("/api/tags")
            healthy = response.ok
            logger.info("Ollama health check – status=%s healthy=%s", response.status_code, healthy)
            return healthy
        except (requests.ConnectionError, requests.Timeout) as exc:
            logger.warning("Ollama health check failed: %s", exc)
            return False

    def get_version(self) -> str:
        """Return the Ollama server version string.

        Performs a GET request to ``/api/version`` and extracts the
        ``version`` field from the JSON response.

        Returns
        -------
        str
            The version string reported by the server (e.g. ``"0.1.32"``).

        Raises
        ------
        OllamaConnectionError
            If the request cannot be completed due to a network error.
        OllamaGenerationError
            If the server returns a non-2xx HTTP status.
        """
        url = self._url("/api/version")
        logger.debug("GET %s", url)
        try:
            response = self.session.get(url, timeout=10)
        except (requests.ConnectionError, requests.Timeout) as exc:
            raise OllamaConnectionError(f"Cannot connect to Ollama at {url}: {exc}") from exc

        if not response.ok:
            raise OllamaGenerationError(
                f"GET /api/version returned HTTP {response.status_code}: {response.text}"
            )

        version: str = response.json().get("version", "unknown")
        logger.info("Ollama version: %s", version)
        return version

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> dict:
        """Send a generation request to the Ollama ``/api/generate`` endpoint.

        Implements exponential-backoff retry on connection/timeout errors up to
        ``config.max_retries`` attempts.  HTTP errors (4xx / 5xx) are **not**
        retried and raise :class:`OllamaGenerationError` immediately.

        Parameters
        ----------
        prompt:
            The full text prompt to send to the model.
        model:
            Override the model name; falls back to ``config.model`` when
            ``None``.
        temperature:
            Override the sampling temperature; falls back to
            ``config.temperature`` when ``None``.

        Returns
        -------
        dict
            The parsed JSON response from Ollama, augmented with two
            additional keys:

            * ``"_actual_model"`` – the model name that was actually used.
            * ``"_actual_temperature"`` – the temperature that was actually used.

        Raises
        ------
        OllamaConnectionError
            When all retry attempts are exhausted without a successful
            connection.
        OllamaGenerationError
            When the server returns a non-2xx HTTP status code.
        """
        actual_model: str = model if model is not None else self.config.model
        actual_temperature: float = (
            temperature if temperature is not None else self.config.temperature
        )

        payload: dict = {
            "model": actual_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": actual_temperature,
                "num_predict": self.config.max_tokens,
            },
        }

        url = self._url("/api/generate")
        max_retries: int = self.config.max_retries
        backoff: float = self.config.retry_backoff

        last_exc: Exception | None = None
        for attempt in range(1, max_retries + 2):  # attempt 1 … max_retries+1
            try:
                logger.debug(
                    "POST %s – model=%s temperature=%.2f attempt=%d/%d",
                    url,
                    actual_model,
                    actual_temperature,
                    attempt,
                    max_retries + 1,
                )
                response = self.session.post(url, json=payload, timeout=self.config.request_timeout)
            except (requests.ConnectionError, requests.Timeout) as exc:
                last_exc = exc
                if attempt <= max_retries:
                    wait = backoff * (2 ** (attempt - 1))
                    logger.warning(
                        "Ollama connection error on attempt %d/%d – retrying in %.1fs: %s",
                        attempt,
                        max_retries + 1,
                        wait,
                        exc,
                    )
                    time.sleep(wait)
                    continue
                # All retries exhausted
                break

            # We got an HTTP response – check status before returning.
            if not response.ok:
                raise OllamaGenerationError(
                    f"POST /api/generate returned HTTP {response.status_code}: {response.text}"
                )

            result: dict = response.json()
            result["_actual_model"] = actual_model
            result["_actual_temperature"] = actual_temperature
            logger.debug(
                "Generation successful – model=%s tokens=%s",
                actual_model,
                result.get("eval_count", "?"),
            )
            return result

        raise OllamaConnectionError(
            f"Failed to connect to Ollama at {url} after {max_retries + 1} attempt(s). "
            f"Last error: {last_exc}"
        )

    def list_models(self) -> List[str]:
        """Return a list of model names available on the Ollama server.

        Performs a GET request to ``/api/tags`` and extracts the ``name``
        field from each entry in the ``models`` list.

        Returns
        -------
        List[str]
            Model name strings (e.g. ``["llama3:latest", "mistral:7b"]``).

        Raises
        ------
        OllamaConnectionError
            If the request cannot be completed due to a network error.
        OllamaGenerationError
            If the server returns a non-2xx HTTP status.
        """
        url = self._url("/api/tags")
        logger.debug("GET %s", url)
        try:
            response = self.session.get(url, timeout=10)
        except (requests.ConnectionError, requests.Timeout) as exc:
            raise OllamaConnectionError(f"Cannot connect to Ollama at {url}: {exc}") from exc

        if not response.ok:
            raise OllamaGenerationError(
                f"GET /api/tags returned HTTP {response.status_code}: {response.text}"
            )

        data = response.json()
        models: List[str] = [entry["name"] for entry in data.get("models", [])]
        logger.info("Available Ollama models: %s", models)
        return models
