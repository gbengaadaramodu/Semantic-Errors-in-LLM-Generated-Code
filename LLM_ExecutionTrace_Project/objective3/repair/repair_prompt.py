"""
Objective 3 — Four-Component Repair Prompt Builder.

Implements the methodology-specified deterministic prompt template:

    Component 1 — Specification
    Component 2 — Fault Localization (localized code block)
    Component 3 — Error Classification (Objective 1)
    Component 4 — Repair Strategy (Objective 2)

The prompt is constructed mechanically from a fixed template.
No LLM is used to rewrite or summarize the diagnostic report.
"""

from __future__ import annotations

import logging
from typing import Optional

from objective3.models import (
    BenchmarkTask,
    ErrorCategory,
    RepairStrategy,
    StructuredDiagnosticReport,
)
from objective3.repair.repair_strategy import RepairStrategySelector

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fixed prompt template (methodologically required four-component structure)
# ---------------------------------------------------------------------------

_REPAIR_PROMPT_TEMPLATE = """\
You are repairing a Python program.

=== COMPONENT 1: SPECIFICATION ===
{specification}

=== COMPONENT 2: FAULT LOCALIZATION ===
Fault identified at lines {start_line}–{end_line}:

```python
{faulty_code}
```

=== COMPONENT 3: ERROR CLASSIFICATION ===
Error Category: {error_category}

=== COMPONENT 4: REPAIR STRATEGY ===
{repair_strategy}

=== CAUSAL EXPLANATION ===
{causal_explanation}

Diagnosis Confidence: {confidence_level} ({confidence_value:.2f})
Diagnosis Status: {diagnosis_status}

=== TASK ===
Repair the identified defect in the complete function below.

```python
{full_source}
```

=== CONSTRAINTS ===
1. Preserve the required function signature exactly.
2. Do not modify or remove test assertions.
3. Do not hard-code expected outputs.
4. Preserve all unrelated correct behaviour.
5. Make the smallest justified correction unless structural redesign is required.
6. Return ONLY the complete corrected Python function implementation.
7. Do not include explanatory text, only the corrected code.
"""


class RepairPromptBuilder:
    """
    Constructs deterministic four-component repair prompts.

    The prompt is built mechanically from the StructuredDiagnosticReport and
    the current source code. No LLM is involved in prompt construction.
    """

    def __init__(self) -> None:
        self._strategy_selector = RepairStrategySelector()

    def build(
        self,
        task: BenchmarkTask,
        diagnostic_report: StructuredDiagnosticReport,
        current_source: str,
        repair_strategy: RepairStrategy = RepairStrategy.LOCAL_MODIFICATION,
        iteration: int = 1,
    ) -> str:
        """
        Build the complete four-component repair prompt.

        Parameters
        ----------
        task               : Benchmark task specification (Component 1).
        diagnostic_report  : Objective 2 structured report (Components 2, 3, 4).
        current_source     : The current (failing) Python source code.
        repair_strategy    : Current repair strategy (affects Component 4 wording).
        iteration          : Current repair iteration number (informational).

        Returns
        -------
        str : Complete repair prompt ready for submission to the repair model.
        """
        # ── Component 2: Extract faulty code block ──────────────────────────
        start_line, end_line, faulty_code = self._extract_fault_block(
            current_source, diagnostic_report
        )

        # ── Component 3: Error classification ──────────────────────────────
        error_category_str = diagnostic_report.error_category.value

        # ── Component 4: Repair strategy ────────────────────────────────────
        # Combine Objective 2 repair_strategy with strategy escalation label
        base_strategy = diagnostic_report.repair_strategy or (
            "Repair the identified defect at the fault location."
        )
        escalation_label = self._strategy_selector.strategy_label(repair_strategy)

        if repair_strategy == RepairStrategy.STRUCTURAL_REDESIGN:
            combined_strategy = (
                f"{escalation_label}\n\n"
                f"Objective 2 guidance: {base_strategy}"
            )
        else:
            combined_strategy = (
                f"{base_strategy}\n\n"
                f"Strategy scope: {escalation_label}"
            )

        # ── Confidence ──────────────────────────────────────────────────────
        confidence_level = diagnostic_report.confidence.level
        confidence_value = diagnostic_report.confidence.value
        diagnosis_status = diagnostic_report.diagnosis_status.value

        # ── Specification ────────────────────────────────────────────────────
        specification = task.specification.strip()

        # ── Causal explanation ───────────────────────────────────────────────
        causal_explanation = diagnostic_report.causal_explanation or (
            "No causal explanation available (diagnosis status: "
            f"{diagnosis_status})."
        )

        prompt = _REPAIR_PROMPT_TEMPLATE.format(
            specification=specification,
            start_line=start_line,
            end_line=end_line,
            faulty_code=faulty_code.strip(),
            error_category=error_category_str,
            repair_strategy=combined_strategy,
            causal_explanation=causal_explanation,
            confidence_level=confidence_level,
            confidence_value=confidence_value,
            diagnosis_status=diagnosis_status,
            full_source=current_source.strip(),
        )

        logger.debug(
            "Built repair prompt for iteration %d "
            "(error=%s, strategy=%s, diagnosis=%s, lines=%d-%d).",
            iteration,
            error_category_str,
            repair_strategy.value,
            diagnosis_status,
            start_line,
            end_line,
        )
        return prompt

    def _extract_fault_block(
        self,
        source: str,
        report: StructuredDiagnosticReport,
    ) -> tuple[int, int, str]:
        """
        Extract the faulty code block corresponding to the fault location.

        Returns (start_line, end_line, extracted_code).
        Falls back to the full source if no fault location is available.
        """
        lines = source.splitlines()
        n = len(lines)

        if report.fault_location is None:
            logger.warning(
                "No fault location in diagnostic report; using full source as faulty block."
            )
            return 1, n, source

        start = max(1, report.fault_location.start_line)
        end = min(n, report.fault_location.end_line)

        # Expand by one line for context (both directions)
        ctx_start = max(1, start - 1)
        ctx_end = min(n, end + 1)

        extracted = "\n".join(lines[ctx_start - 1 : ctx_end])
        return start, end, extracted

    def build_structural_redesign_prompt(
        self,
        task: BenchmarkTask,
        current_source: str,
        error_history: str,
    ) -> str:
        """
        Build a structural redesign prompt when local modifications have failed.
        Used as an alternative when no valid diagnostic report is available.
        """
        return (
            f"You are repairing a Python program that has failed multiple times.\n\n"
            f"=== SPECIFICATION ===\n{task.specification.strip()}\n\n"
            f"=== CURRENT FAILING CODE ===\n```python\n{current_source.strip()}\n```\n\n"
            f"=== FAILURE HISTORY ===\n{error_history}\n\n"
            f"=== TASK ===\n"
            f"Previous local modifications failed to fix the program.\n"
            f"Redesign the complete function implementation using an alternative approach.\n\n"
            f"=== CONSTRAINTS ===\n"
            f"1. Preserve the required function signature exactly.\n"
            f"2. Do not modify or remove test assertions.\n"
            f"3. Do not hard-code expected outputs.\n"
            f"4. Return ONLY the complete corrected Python function implementation.\n"
            f"5. Do not include explanatory text, only the corrected code.\n"
        )
