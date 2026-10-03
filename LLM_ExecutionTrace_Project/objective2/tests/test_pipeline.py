"""
Synthetic Causal Tests for Objective 2 Pipeline.

Verifies that the system can distinguish failure location from causal fault location on synthetic programs:
    - Test Case A: Parity filter condition bug in sum_even
    - Test Case B: Zero division exception
    - Test Case C: Accumulator initialization bug in count_items
"""

import unittest
from objective2.config import Objective2Config
from objective2.models import AnalysisStatus, Objective2InputRecord
from objective2.pipeline import Objective2Pipeline


class TestPipelineSynthetic(unittest.TestCase):
    def test_synthetic_case_a_parity_bug(self):
        """Test Case A: Filtering condition bug in sum_even."""
        record = Objective2InputRecord(
            trace_id="SYN_A",
            dataset="HumanEval",
            task_id="Synthetic/A",
            generated_code="""def sum_even(numbers):
    total = 0
    for n in numbers:
        if n % 2 != 0:
            total += n
    return total
""",
            entry_point="sum_even",
            test_code="def check(candidate):\n    assert candidate([1, 2, 3, 4]) == 6, 'Failed sum_even'\n",
            execution_status="Failed",
            traceback='File "SYN_A.py", line 7, in check\n    assert candidate([1, 2, 3, 4]) == 6\nAssertionError',
            parser_prediction="Wrong-Output Error",
        )

        pipeline = Objective2Pipeline(Objective2Config())
        res = pipeline.analyze_single_case(record)

        self.assertEqual(res.analysis_status, AnalysisStatus.ANALYZED)
        self.assertIsNotNone(res.fault_location)
        self.assertIn(res.fault_location.line_number, (3, 4, 5, 6))
        self.assertIsNotNone(res.root_cause)
        self.assertIn(res.root_cause.fault_line, (3, 4, 5, 6))

    def test_synthetic_case_b_zero_division(self):
        """Test Case B: Division by zero exception."""
        record = Objective2InputRecord(
            trace_id="SYN_B",
            dataset="HumanEval",
            task_id="Synthetic/B",
            generated_code="""def divide(a, b):
    return a / b
""",
            entry_point="divide",
            test_code="def check(candidate):\n    assert candidate(10, 0) == 0\n",
            execution_status="Failed",
            exception_type="ZeroDivisionError",
            exception_message="division by zero",
            traceback='File "SYN_B.py", line 2, in divide\n    return a / b\nZeroDivisionError: division by zero',
            parser_prediction="Runtime Exception",
            expected_output=0,
        )

        pipeline = Objective2Pipeline(Objective2Config())
        res = pipeline.analyze_single_case(record)

        self.assertEqual(res.analysis_status, AnalysisStatus.ANALYZED)
        self.assertIsNotNone(res.fault_location)
        self.assertEqual(res.fault_location.line_number, 2)

    def test_synthetic_case_c_accumulator_init(self):
        """Test Case C: Accumulator off-by-one initialization."""
        record = Objective2InputRecord(
            trace_id="SYN_C",
            dataset="MBPP",
            task_id="Synthetic/C",
            generated_code="""def count_items(items):
    count = 1
    for item in items:
        count += 1
    return count
""",
            entry_point="count_items",
            test_code="assert count_items([10, 20, 30]) == 3\n",
            execution_status="Failed",
            traceback='File "SYN_C.py", line 6, in <module>\n    assert count_items([10, 20, 30]) == 3\nAssertionError',
            parser_prediction="Wrong-Output Error",
        )

        pipeline = Objective2Pipeline(Objective2Config())
        res = pipeline.analyze_single_case(record)

        self.assertEqual(res.analysis_status, AnalysisStatus.ANALYZED)
        self.assertIsNotNone(res.fault_location)
        self.assertIn(res.fault_location.line_number, (2, 3, 4, 5))


if __name__ == "__main__":
    unittest.main()
