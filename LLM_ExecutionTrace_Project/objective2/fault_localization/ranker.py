"""
Candidate Cause Ranker Module.

Ranks candidate statements and variables based on combined proximity, dependency,
and counterfactual evidence scores.
"""

from typing import List, Tuple

from objective2.models import CandidateCause, CausalEffect, CounterfactualResult


class CandidateRanker:
    """
    Ranks fault candidates based on structural and interventional evidence.
    """

    def rank(
        self,
        candidates: List[CandidateCause],
        cf_results: List[CounterfactualResult],
    ) -> List[Tuple[CandidateCause, float]]:
        # Map rank -> CounterfactualResult
        cf_map = {cf.candidate_rank: cf for cf in cf_results}

        scored_candidates: List[Tuple[CandidateCause, float]] = []

        for cand in candidates:
            cf_res = cf_map.get(cand.rank)
            score = 0.5 * cand.proximity_score + 0.5 * cand.dependency_score

            if cf_res and cf_res.causal_effect == CausalEffect.TRUE:
                # Strong causal evidence boost
                score += 2.0
            elif cf_res and cf_res.causal_effect == CausalEffect.FALSE:
                score *= 0.5

            scored_candidates.append((cand, round(score, 3)))

        # Sort descending by score
        scored_candidates.sort(key=lambda item: item[1], reverse=True)

        # Re-assign ranks 1..N based on final score
        for i, (cand, score) in enumerate(scored_candidates, 1):
            cand.rank = i

        return scored_candidates
