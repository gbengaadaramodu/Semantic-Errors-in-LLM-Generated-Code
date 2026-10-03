"""Unit tests for Counterfactual Intervention Engine and Executor."""
import unittest
from objective2.config import ExecutionConfig
from objective2.counterfactual.executor import SafeCounterfactualExecutor
from objective2.counterfactual.intervention import CounterfactualInterventionEngine
from objective2.models import Objective2InputRecord

class TestCounterfactual(unittest.TestCase):
    def test_counterfactual_intervention(self):
        code = """def sum_even(numbers):
    total = 0
    for n in numbers:
        if n % 2 != 0:
            total += n
    return total
"""
        engine = CounterfactualInterventionEngine()
        intervention = engine.create_intervention(
            source_code=code,
            target_line=4,
            var_name="n",
            observed_value=None,
            expected_value=None,
        )
        self.assertIsNotNone(intervention)
        self.assertNotEqual(intervention.modified_code, "")

    def test_counterfactual_execution(self):
        record = Objective2InputRecord(
            trace_id="TEST_01",
            dataset="MBPP",
            task_id="TEST_01",
            generated_code="def foo(x):\n    return x + 1\n",
            test_code="assert foo(2) == 3\n",
        )
        executor = SafeCounterfactualExecutor(ExecutionConfig())
        status, stdout, stderr = executor.execute_intervened(record, record.generated_code)
        self.assertEqual(status, "Completed")

if __name__ == "__main__":
    unittest.main()
