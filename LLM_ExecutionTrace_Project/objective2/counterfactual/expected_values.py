"""
Expected Value Inference Module.

Extracts expected variable values from failing test assertions or return expectations
without fabricating ungrounded evidence.
"""

import ast
import re
from typing import Any, Tuple

from objective2.models import CriticalVariable, Objective2InputRecord


class ExpectedValueInferencer:
    """
    Infers expected target variable values from test harness traces and assertions.
    """

    def infer(
        self, record: Objective2InputRecord, candidate_var: str, candidate_line: int
    ) -> CriticalVariable:
        """
        Derives a CriticalVariable object with expected_value and justification.
        """
        obs_val = None
        exp_val = None
        source = "UNRESOLVED"
        conf = 0.0
        explanation = "Insufficient evidence to infer exact expected value."

        # 1. Inspect stderr/traceback for assertion values
        # e.g., "AssertionError: assert [1, 3] == [2, 4]" or "assert candidate(2, 10) == [2, 4, 6, 8]"
        if record.traceback:
            for line in record.traceback.splitlines():
                line = line.strip()
                if line.startswith("assert "):
                    try:
                        tree = ast.parse(line)
                        if isinstance(tree.body[0], ast.Assert):
                            test = tree.body[0].test
                            if isinstance(test, ast.Compare) and len(test.comparators) == 1:
                                exp_val = ast.literal_eval(test.comparators[0])
                                source = "assertion_traceback"
                                conf = 0.9
                                explanation = "Inferred from failing assertion right-hand side in traceback"
                                break
                    except Exception:
                        pass

        # 2. Inspect record expected_output field if available
        if exp_val is None and record.expected_output is not None:
            exp_val = record.expected_output
            source = "test_expected_output"
            conf = 0.8
            explanation = "Extracted directly from test record expected_output field."

        # Safety constraint: Only apply function-level expected outputs if we are confident 
        # the variable/line represents the function's return value.
        is_return_context = False
        if record.generated_code:
            lines = record.generated_code.splitlines()
            if 1 <= candidate_line <= len(lines):
                if lines[candidate_line - 1].strip().startswith("return "):
                    is_return_context = True

        if exp_val is not None and not is_return_context:
            # We don't have enough semantic mapping to assign the function output to an intermediate variable
            exp_val = None
            source = "unknown"
            conf = 0.0
            explanation = "Function expected output cannot be safely mapped to intermediate variable."

        return CriticalVariable(
            variable_name=candidate_var,
            definition_line=candidate_line,
            observed_value=obs_val,
            expected_value=exp_val,
            expected_value_source=source,
            confidence=conf,
            inference_explanation=explanation,
        )
