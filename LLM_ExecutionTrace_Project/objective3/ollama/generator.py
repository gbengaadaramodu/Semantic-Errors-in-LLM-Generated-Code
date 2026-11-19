"""
High-level code-generation helpers for Objective 3.

:class:`OllamaCodeGenerator` wraps an :class:`~objective3.ollama.client.OllamaClient`
and provides domain-specific generation methods that return ``(raw_text, model_used)``
tuples for uniform downstream handling.
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple

from objective3.ollama.client import OllamaClient, OllamaConnectionError, OllamaGenerationError

logger = logging.getLogger(__name__)


class OllamaCodeGenerator:
    """High-level code generator backed by an :class:`OllamaClient`.

    This class provides named generation methods that keep domain logic
    (repair vs. initial generation) separate from the raw HTTP layer while
    sharing the same underlying client and its retry / config machinery.

    Parameters
    ----------
    client:
        A fully configured :class:`~objective3.ollama.client.OllamaClient`
        instance.
    """

    def __init__(self, client: OllamaClient) -> None:
        self.client = client
        logger.debug(
            "OllamaCodeGenerator initialised – default model=%s",
            client.config.model,
        )

    # ------------------------------------------------------------------
    # Internal helper
    # ------------------------------------------------------------------

    def _run_generation(
        self,
        prompt: str,
        model: Optional[str],
        temperature: Optional[float],
        task_label: str,
    ) -> Tuple[str, str]:
        """Call :meth:`OllamaClient.generate` and extract ``(raw_text, model)``.

        Parameters
        ----------
        prompt:
            The full prompt string to send to the model.
        model:
            Optional model override; ``None`` uses the client's default.
        temperature:
            Optional temperature override; ``None`` uses the client's default.
        task_label:
            A short string used only for log messages (e.g. ``"repair"``).

        Returns
        -------
        Tuple[str, str]
            ``(raw_response_text, model_actually_used)``

        Raises
        ------
        OllamaConnectionError
            Propagated from the client when the server is unreachable.
        OllamaGenerationError
            Propagated from the client on HTTP errors.
        """
        logger.info("Starting %s generation – model=%s", task_label, model or "(default)")
        try:
            response_dict: dict = self.client.generate(
                prompt=prompt, model=model, temperature=temperature
            )
        except OllamaConnectionError:
            logger.error(
                "%s generation aborted – could not connect to Ollama server.", task_label
            )
            raise
        except OllamaGenerationError:
            logger.error("%s generation failed – server returned an error.", task_label)
            raise

        raw_text: str = response_dict.get("response", "")
        model_used: str = response_dict.get("_actual_model", self.client.config.model)
        logger.info(
            "%s generation complete – model_used=%s chars=%d",
            task_label,
            model_used,
            len(raw_text),
        )
        return raw_text, model_used

    # ------------------------------------------------------------------
    # Public generation methods
    # ------------------------------------------------------------------

    def generate_repair(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> Tuple[str, str]:
        """Generate a code-repair response from the LLM.

        Sends *prompt* (which should contain the broken code and any
        diagnostic context) to the configured Ollama model and returns the
        raw generated text together with the name of the model that was
        actually used.

        Parameters
        ----------
        prompt:
            The repair prompt including the faulty code snippet, error
            messages, and any relevant execution-trace context.
        model:
            Override the model for this call; ``None`` uses the client's
            configured default.
        temperature:
            Override the sampling temperature; ``None`` uses the client's
            configured default.

        Returns
        -------
        Tuple[str, str]
            ``(raw_response, model_actually_used)``

            * ``raw_response`` – the full text returned by the LLM (may
              contain markdown fences, explanations, etc.; callers are
              responsible for post-processing).
            * ``model_actually_used`` – the exact model identifier as
              recorded by the client, useful for logging and provenance
              tracking.

        Raises
        ------
        OllamaConnectionError
            If the Ollama server cannot be reached after all retries.
        OllamaGenerationError
            If the server returns a non-2xx HTTP status.
        """
        return self._run_generation(
            prompt=prompt,
            model=model,
            temperature=temperature,
            task_label="repair",
        )

    def generate_initial_code(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> Tuple[str, str]:
        """Generate an initial code implementation from a specification prompt.

        Sends *prompt* (which should describe the desired function / module)
        to the configured Ollama model and returns the raw generated text
        together with the name of the model that was actually used.

        Parameters
        ----------
        prompt:
            The specification prompt describing what code should be
            generated (e.g. a function signature, docstring, or natural-
            language description).
        model:
            Override the model for this call; ``None`` uses the client's
            configured default.
        temperature:
            Override the sampling temperature; ``None`` uses the client's
            configured default.

        Returns
        -------
        Tuple[str, str]
            ``(raw_response, model_actually_used)``

            * ``raw_response`` – the full text returned by the LLM.
            * ``model_actually_used`` – the exact model identifier as
              recorded by the client.

        Raises
        ------
        OllamaConnectionError
            If the Ollama server cannot be reached after all retries.
        OllamaGenerationError
            If the server returns a non-2xx HTTP status.
        """
        return self._run_generation(
            prompt=prompt,
            model=model,
            temperature=temperature,
            task_label="initial_code",
        )
