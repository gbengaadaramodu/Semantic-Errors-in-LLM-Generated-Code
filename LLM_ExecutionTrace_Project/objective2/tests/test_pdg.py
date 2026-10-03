"""Unit tests for Program Dependency Graph (PDG) construction and reverse traversal."""
import unittest
from objective2.pdg.graph_builder import PDGGraphBuilder
from objective2.pdg.traversal import ReversePDGTraversal

class TestPDG(unittest.TestCase):
    def test_pdg_builder_and_traversal(self):
        code = """def count_items(items):
    count = 1
    for item in items:
        count += 1
    return count
"""
        builder = PDGGraphBuilder()
        pdg = builder.build_pdg(code, failure_line=4)
        self.assertGreater(len(pdg.nodes), 0)
        self.assertGreater(len(pdg.edges), 0)
        traversal = ReversePDGTraversal()
        candidates = traversal.traverse(pdg, top_k=3)
        self.assertGreater(len(candidates), 0)

if __name__ == "__main__":
    unittest.main()
