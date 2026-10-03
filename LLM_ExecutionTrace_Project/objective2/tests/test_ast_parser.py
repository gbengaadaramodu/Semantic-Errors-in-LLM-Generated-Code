"""Unit tests for AST Parser."""
import unittest
from objective2.pdg.ast_parser import ASTParser

class TestASTParser(unittest.TestCase):
    def test_ast_parser_basic(self):
        code = """def sum_even(numbers):
    total = 0
    for n in numbers:
        if n % 2 != 0:
            total += n
    return total
"""
        parser = ASTParser()
        stmts = parser.parse(code)
        self.assertGreaterEqual(len(stmts), 4)
        func_stmt = stmts[0]
        self.assertEqual(func_stmt.ast_type, "FunctionDef")
        self.assertIn("sum_even", func_stmt.writes)

if __name__ == "__main__":
    unittest.main()
