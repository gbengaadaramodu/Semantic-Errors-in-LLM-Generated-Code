"""
Counterfactual Diagnoser Module.

Orchestrates candidate intervention generation, re-execution, evaluation, and ranking.
"""

import time
from typing import List, Tuple

from objective2.config import ExecutionConfig
from objective2.counterfactual.evaluator import CausalEffectEvaluator
from objective2.counterfactual.executor import SafeCounterfactualExecutor
from objective2.counterfactual.expected_values import ExpectedValueInferencer
from objective2.counterfactual.intervention import CounterfactualInterventionEngine
from objective2.models import (
    CandidateCause,
    CausalEffect,
    CounterfactualResult,
    Objective2InputRecord,
)


class CounterfactualDiagnoser:
    """
    Executes counterfactual diagnosis over candidate cause variables.
    """

    def __init__(self, config: ExecutionConfig) -> None:
        self.config = config
        self.inferencer = ExpectedValueInferencer()
        self.intervention_engine = CounterfactualInterventionEngine()
        self.executor = SafeCounterfactualExecutor(config)
        self.evaluator = CausalEffectEvaluator()

    def diagnose_candidates(
        self, record: Objective2InputRecord, candidates: List[CandidateCause]
    ) -> List[CounterfactualResult]:
        results: List[CounterfactualResult] = []

        for candidate in candidates:
            # 1. Infer expected value for candidate
            crit_var = self.inferencer.infer(
                record, candidate.variable_name, candidate.line_number
            )
            candidate.expected_value = crit_var.expected_value

            # 2. Build intervention
            intervention = self.intervention_engine.create_intervention(
                source_code=record.generated_code,
                target_line=candidate.line_number,
                var_name=candidate.variable_name,
                observed_value=candidate.observed_value,
                expected_value=crit_var.expected_value,
            )

            # 3. Execute intervention if constructed
            t0 = time.perf_counter()
            if intervention and intervention.modified_code:
                cf_status, stdout, stderr = self.executor.execute_intervened(
                    record, intervention.modified_code
                )
            else:
                cf_status, stdout, stderr = "FAILED_CONSTRUCTION", "", ""
            exec_time = round(time.perf_counter() - t0, 4)

            # 4. Evaluate causal effect
            res = self.evaluator.evaluate(
                candidate=candidate,
                intervention=intervention,
                original_status=record.execution_status,
                cf_status=cf_status,
                cf_stdout=stdout,
                cf_stderr=stderr,
                exec_time=exec_time,
            )
            results.append(res)

        return results
