"""
Causal Effect Evaluator Module.

Evaluates counterfactual re-execution outcomes against Pearl's causal criterion:
    Original Outcome = FAIL
    Counterfactual Outcome = PASS (Completed)
    => Causal Effect = TRUE
"""

import time
from typing import Optional

from objective2.models import (
    CandidateCause,
    CausalEffect,
    CounterfactualResult,
    Intervention,
    Objective2InputRecord,
)


class CausalEffectEvaluator:
    """
    Evaluates whether an intervention successfully flips a failure to pass.
    """

    def evaluate(
        self,
        candidate: CandidateCause,
        intervention: Optional[Intervention],
        original_status: str,
        cf_status: str,
        cf_stdout: str,
        cf_stderr: str,
        exec_time: float,
    ) -> CounterfactualResult:
        if intervention is None:
            return CounterfactualResult(
                candidate_rank=candidate.rank,
                intervention=Intervention(
                    target_variable=candidate.variable_name,
                    target_line=candidate.line_number,
                    observed_value=candidate.observed_value,
                    counterfactual_value=candidate.expected_value,
                    operation_type="failed_construction",
                    modified_code="",
                ),
                original_outcome=original_status,
                counterfactual_outcome="FAILED_CONSTRUCTION",
                causal_effect=CausalEffect.UNRESOLVED,
                execution_time=0.0,
                status="UNRESOLVED",
                explanation="Failed to construct valid AST counterfactual intervention.",
            )

        # Primary causal criterion
        # Original: Failed / Timeout
        # Counterfactual: Completed
        if cf_status == "Completed":
            effect = CausalEffect.TRUE
            explanation = "Intervention successfully flipped execution outcome from FAIL to PASS."
        elif cf_status == "Failed":
            effect = CausalEffect.FALSE
            explanation = "Intervention failed to resolve the program failure (FAIL -> FAIL)."
        else:
            effect = CausalEffect.UNRESOLVED
            explanation = "Counterfactual execution timed out or crashed in an invalid state."

        return CounterfactualResult(
            candidate_rank=candidate.rank,
            intervention=intervention,
            original_outcome=original_status,
            counterfactual_outcome=cf_status,
            original_actual_output=None,
            counterfactual_output=cf_stdout[:200] if cf_stdout else None,
            causal_effect=effect,
            execution_time=exec_time,
            status="EXECUTED",
            explanation=explanation,
        )
