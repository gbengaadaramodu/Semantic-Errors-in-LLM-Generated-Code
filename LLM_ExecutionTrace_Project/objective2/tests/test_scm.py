"""Unit tests for Structural Causal Model (SCM)."""
import unittest
from objective2.models import Objective2InputRecord
from objective2.scm.structural_model import SCMBuilder
from objective2.scm.graph import SCMGraph

class TestSCM(unittest.TestCase):
    def test_scm_builder(self):
        record = Objective2InputRecord(
            trace_id="HE001",
            dataset="HumanEval",
            task_id="HumanEval/163",
            generated_code="def foo(): return 1",
            execution_status="Failed",
        )
        scm = SCMBuilder.build(record)
        self.assertEqual(len(scm.nodes), 5)
        self.assertEqual(len(scm.edges), 4)
        dot_text = SCMGraph.to_dot(scm)
        self.assertIn("digraph SCM", dot_text)

if __name__ == "__main__":
    unittest.main()
