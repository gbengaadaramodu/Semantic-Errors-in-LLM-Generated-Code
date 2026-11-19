"""
Initial code generator for Objective 3.

Supports two modes:
  - Mode A (default): Read pre-generated code from disk (output of Objective 1).
  - Mode B: Generate code on-the-fly via Ollama using the task specification.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from objective3.config import Objective3Config

logger = logging.getLogger(__name__)


class InitialCodeGenerator:
    """Retrieve or generate the initial Python code for a given trace ID.

    Parameters
    ----------
    config:
        Project-wide configuration object that exposes paths and model settings.
    ollama_client:
        An optional Ollama client instance (e.g. ``ollama.Client``).  Only
        required when using Mode B.  If *None* and Mode B is requested, a
        ``RuntimeError`` is raised at call time rather than at construction.
    """

    def __init__(
        self,
        config: Objective3Config,
        ollama_client: Optional[object] = None,
    ) -> None:
        self.config = config
        self.ollama_client = ollama_client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_initial_code(
        self,
        trace_id: str,
        mode: str = "A",
    ) -> Optional[str]:
        """Return the initial Python source code for *trace_id*.

        Parameters
        ----------
        trace_id:
            Identifier for the benchmark task, e.g. ``"HE001"``.
        mode:
            ``"A"`` (default) — read from ``generated_code/<trace_id>.py``.
            ``"B"`` — generate via Ollama using the task specification.

        Returns
        -------
        str or None
            The Python source code as a string, or *None* if the code could
            not be located / generated.

        Raises
        ------
        ValueError
            If an unknown *mode* is supplied.
        RuntimeError
            If Mode B is requested but no ``ollama_client`` was provided.
        """
        mode = mode.upper()
        if mode == "A":
            return self._read_from_disk(trace_id)
        elif mode == "B":
            return self._generate_via_ollama(trace_id)
        else:
            raise ValueError(
                f"Unknown mode '{mode}'. Valid values are 'A' (read from disk) "
                "or 'B' (generate via Ollama)."
            )

    def code_exists(self, trace_id: str) -> bool:
        """Check whether pre-generated code exists on disk for *trace_id*.

        Parameters
        ----------
        trace_id:
            Identifier for the benchmark task, e.g. ``"HE001"``.

        Returns
        -------
        bool
            ``True`` if the corresponding ``.py`` file is present and
            non-empty, ``False`` otherwise.
        """
        path = self._code_path(trace_id)
        return path.is_file() and path.stat().st_size > 0

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _code_path(self, trace_id: str) -> Path:
        """Return the expected on-disk path for *trace_id*'s generated code."""
        return Path(self.config.paths.generated_code_dir) / f"{trace_id}.py"

    def _read_from_disk(self, trace_id: str) -> Optional[str]:
        """Read and return the pre-generated source file for *trace_id*.

        Parameters
        ----------
        trace_id:
            Identifier for the benchmark task.

        Returns
        -------
        str or None
            File contents, or *None* if the file does not exist or is empty.
        """
        path = self._code_path(trace_id)
        if not path.is_file():
            logger.warning(
                "Mode A: generated code file not found: %s", path
            )
            return None

        code = path.read_text(encoding="utf-8").strip()
        if not code:
            logger.warning(
                "Mode A: generated code file is empty: %s", path
            )
            return None

        logger.debug("Mode A: loaded code for %s from %s", trace_id, path)
        return code

    def _generate_via_ollama(self, trace_id: str) -> Optional[str]:
        """Generate code for *trace_id* by querying the Ollama model.

        The task specification is read from
        ``config.task_specs_dir/<trace_id>.txt`` (or whichever path the
        config exposes).  The prompt is built with
        :class:`~objective3.generation.prompt_builder.GenerationPromptBuilder`.

        Parameters
        ----------
        trace_id:
            Identifier for the benchmark task.

        Returns
        -------
        str or None
            The generated Python source code, or *None* on failure.

        Raises
        ------
        RuntimeError
            If no ``ollama_client`` was supplied at construction time.
        """
        if self.ollama_client is None:
            raise RuntimeError(
                "Mode B requires an Ollama client.  Pass one via the "
                "'ollama_client' constructor argument."
            )

        # Import here to avoid circular dependencies at module level.
        from objective3.generation.prompt_builder import GenerationPromptBuilder
        from objective3.models import BenchmarkTask

        # Load the task specification so the prompt builder can use it.
        spec_path = Path(self.config.paths.prompts_dir) / f"{trace_id}.txt"
        if not spec_path.is_file():
            logger.error(
                "Mode B: task specification not found: %s", spec_path
            )
            return None

        specification = spec_path.read_text(encoding="utf-8").strip()
        task = BenchmarkTask(
            trace_id=trace_id,
            specification=specification,
        )

        prompt = GenerationPromptBuilder().build_initial_prompt(task)

        try:
            response = self.ollama_client.generate(  # type: ignore[attr-defined]
                model=self.config.ollama.model,
                prompt=prompt,
            )
            # The Ollama Python client returns a dict-like object; the
            # generated text lives in response["response"].
            code: str = (
                response["response"]
                if isinstance(response, dict)
                else response.response
            )
            logger.debug(
                "Mode B: generated %d chars for %s", len(code), trace_id
            )
            return code.strip() or None
        except Exception as exc:  # pragma: no cover
            logger.error(
                "Mode B: Ollama generation failed for %s: %s", trace_id, exc,
                exc_info=True,
            )
            return None
