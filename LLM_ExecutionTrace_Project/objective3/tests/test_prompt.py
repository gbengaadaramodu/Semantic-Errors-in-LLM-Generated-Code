"""Tests for prompt building logic."""
import unittest

from objective3.models import BenchmarkTask, StructuredDiagnosticReport, ErrorCategory, FaultLocation
from objective3.repair.repair_prompt import RepairPromptBuilder
from objective3.repair.repair_strategy import RepairStrategy

class TestPromptBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = RepairPromptBuilder()
        self.task = BenchmarkTask(
            trace_id="T01",
            task_id="task/1",
            benchmark="Test",
            specification="Add two numbers",
            entry_point="add",
            test_code="assert add(1, 2) == 3"
        )
        self.source = "def add(a, b):\n    return a - b"
        self.diag = StructuredDiagnosticReport(
            error_category=ErrorCategory.WRONG_OUTPUT,
            fault_location=FaultLocation(start_line=2, end_line=2),
            causal_explanation="Subtracts instead of adds.",
            repair_strategy="Fix computation."
        )

    def test_build_prompt(self):
        prompt = self.builder.build(self.task, self.diag, self.source, RepairStrategy.LOCAL_MODIFICATION, 1)
        self.assertIn("COMPONENT 1: SPECIFICATION", prompt)
        self.assertIn("Add two numbers", prompt)
        self.assertIn("COMPONENT 2: FAULT LOCALIZATION", prompt)
        self.assertIn("return a - b", prompt)
        self.assertIn("COMPONENT 3: ERROR CLASSIFICATION", prompt)
        self.assertIn("Wrong-Output Error", prompt)
        self.assertIn("COMPONENT 4: REPAIR STRATEGY", prompt)
        self.assertIn("Fix computation.", prompt)
        self.assertIn("CAUSAL EXPLANATION", prompt)

if __name__ == "__main__":
    unittest.main()
