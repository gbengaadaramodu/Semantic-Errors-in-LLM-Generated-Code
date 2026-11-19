"""Tests for AST Merge logic."""
import unittest

from objective3.ast_merge.merger import ASTMerger
from objective3.ast_merge.validator import MergeValidator

class TestASTMerge(unittest.TestCase):
    def setUp(self):
        self.merger = ASTMerger()
        self.validator = MergeValidator()

    def test_full_function_replacement(self):
        original = (
            "def add(a, b):\n"
            "    return a - b\n"
        )
        repair = (
            "def add(a, b):\n"
            "    return a + b\n"
        )
        res = self.merger.merge_full_replacement(original, repair, "add")
        self.assertTrue(res.success)
        self.assertIn("return a + b", res.merged_code)

    def test_signature_validation(self):
        original = (
            "def add(a, b):\n"
            "    return a - b\n"
        )
        repair = (
            "def add(a, b, c):\n"
            "    return a + b + c\n"
        )
        # Assuming the signature validation catches the mismatch
        res = self.merger.merge_full_replacement(original, repair, "add")
        self.assertFalse(res.success)
        self.assertIn("signature changed", res.error_message)

    def test_line_splice_fallback(self):
        original = (
            "def add(a, b):\n"
            "    x = a\n"
            "    y = b\n"
            "    return x - y\n"
        )
        repair = (
            "    return x + y\n"
        )
        res = self.merger.merge(original, repair, "add", 4, 4)
        self.assertTrue(res.success)
        self.assertIn("return x + y", res.merged_code)

if __name__ == "__main__":
    unittest.main()
