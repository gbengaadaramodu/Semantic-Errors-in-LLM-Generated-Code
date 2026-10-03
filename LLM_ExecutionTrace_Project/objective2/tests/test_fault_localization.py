"""Unit tests for Fault Localization and Root Cause Diagnosis."""
import unittest
from objective2.fault_localization.locator import FaultLocator
from objective2.fault_localization.ranker import CandidateRanker
from objective2.fault_localization.root_cause import RootCauseDiagnoser
from objective2.models import CandidateCause, Objective2InputRecord

class TestFaultLocalization(unittest.TestCase):
    def test_fault_localization_and_root_cause(self):
        cand = CandidateCause(
            rank=1,
            node_id=1,
            line_number=4,
            statement_code="if n % 2 != 0:",
            variable_name="n",
            proximity_score=1.0,
            dependency_score=1.0,
        )
        ranker = CandidateRanker()
        ranked = ranker.rank([cand], [])

        record = Objective2InputRecord(
            trace_id="TEST_02",
            dataset="HumanEval",
            task_id="TEST_02",
            generated_code="def sum_even(numbers):\n    total = 0\n    for n in numbers:\n        if n % 2 != 0:\n            total += n\n    return total",
            parser_prediction="Wrong-Output Error",
        )

        locator = FaultLocator()
        loc = locator.locate_fault(record, ranked, [])
        self.assertIsNotNone(loc)
        self.assertEqual(loc.line_number, 4)

        diagnoser = RootCauseDiagnoser()
        diag = diagnoser.diagnose(record, loc, None)
        self.assertIsNotNone(diag)
        self.assertEqual(diag.causal_variable, "n")
        self.assertTrue("filtering condition" in diag.candidate_explanation or "line 4" in diag.candidate_explanation)


if __name__ == "__main__":
    unittest.main()
