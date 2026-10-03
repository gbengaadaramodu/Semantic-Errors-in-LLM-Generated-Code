"""
Fault Locator Module.

Determines the precise program statement, line number, function, and variable
identified as the causal fault location.
"""

from typing import List, Optional, Tuple

from objective2.models import (
    CandidateCause,
    CausalEffect,
    CounterfactualResult,
    FaultLocation,
    Objective2InputRecord,
)


class FaultLocator:
    """
    Locates the statement responsible for program failure based on ranked causal evidence.
    """

    def locate_fault(
        self,
        record: Objective2InputRecord,
        ranked_candidates: List[Tuple[CandidateCause, float]],
        cf_results: List[CounterfactualResult],
    ) -> Optional[FaultLocation]:
        if not ranked_candidates:
            return None

        # Look for top candidate validated by counterfactual intervention
        cf_map = {cf.candidate_rank: cf for cf in cf_results}

        top_cand, top_score = ranked_candidates[0]
        cf_res = cf_map.get(top_cand.rank)

        confidence = 0.5
        if cf_res and cf_res.causal_effect == CausalEffect.TRUE:
            confidence = 0.95
        elif cf_res and cf_res.causal_effect == CausalEffect.FALSE:
            confidence = 0.3

        func_name = record.entry_point or "<module>"

        return FaultLocation(
            file=f"{record.trace_id}.py",
            line_number=top_cand.line_number,
            statement_code=top_cand.statement_code,
            function_name=func_name,
            causal_variable=top_cand.variable_name,
            evidence_score=top_score,
            confidence=confidence,
        )
