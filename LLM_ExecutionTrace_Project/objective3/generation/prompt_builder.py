"""
Prompt builder for initial code generation in Objective 3.

Constructs prompts in the ``[INST]...[/INST]`` format used throughout the
project's ``prompts/`` directory.
"""

from __future__ import annotations

from objective3.models import BenchmarkTask


class GenerationPromptBuilder:
    """Build prompts for initial Python code generation.

    All prompts follow the ``[INST]...[/INST]`` instruction-tagging
    convention used by the project's existing prompt files.
    """

    # ------------------------------------------------------------------
    # Template constants
    # ------------------------------------------------------------------

    _INITIAL_TEMPLATE: str = (
        "[INST] Complete the following Python function. "
        "Return ONLY the function implementation, no explanations.\n\n"
        "{specification}\n\n"
        "[/INST]"
    )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_initial_prompt(self, task: BenchmarkTask) -> str:
        """Build a code-generation prompt for *task*.

        The resulting string uses the ``[INST]...[/INST]`` format and
        instructs the model to return only the function implementation
        without any prose explanation.

        Parameters
        ----------
        task:
            A :class:`~objective3.models.BenchmarkTask` whose
            ``specification`` attribute contains the function stub /
            docstring / description that the model should complete.

        Returns
        -------
        str
            A fully formatted prompt string ready to be sent to the LLM.

        Raises
        ------
        ValueError
            If *task.specification* is empty or consists only of whitespace.

        Examples
        --------
        >>> from objective3.models import BenchmarkTask
        >>> task = BenchmarkTask(trace_id="HE001", specification="def add(a, b):\\n    ...")
        >>> prompt = GenerationPromptBuilder().build_initial_prompt(task)
        >>> prompt.startswith("[INST]")
        True
        """
        specification = task.specification.strip()
        if not specification:
            raise ValueError(
                f"BenchmarkTask '{task.trace_id}' has an empty specification. "
                "Cannot build a generation prompt without a specification."
            )

        return self._INITIAL_TEMPLATE.format(specification=specification)
