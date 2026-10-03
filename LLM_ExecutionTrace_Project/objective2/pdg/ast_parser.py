"""
AST Parser Module.

Performs static Python AST analysis to extract statements, variable reads/writes,
control structures, and function definitions.
"""

import ast
import logging
from typing import Dict, List, Set, Tuple

from objective2.models import ASTStatement

logger = logging.getLogger(__name__)


class VariableVisitor(ast.NodeVisitor):
    """
    Extracts variable names read (used) and written (defined) in an AST subtree.
    """

    def __init__(self) -> None:
        self.reads: Set[str] = set()
        self.writes: Set[str] = set()

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Store):
            self.writes.add(node.id)
        elif isinstance(node.ctx, ast.Load):
            self.reads.add(node.id)
        elif isinstance(node.ctx, ast.Del):
            self.writes.add(node.id)
        self.generic_visit(node)

    def visit_arg(self, node: ast.arg) -> None:
        self.writes.add(node.arg)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.writes.add(node.name)
        # Visit arguments
        self.visit(node.args)
        # Do not recurse into body to avoid double counting nested function bodies
        pass


class ASTParser:
    """
    Parses Python source code into a sequence of ASTStatement objects.
    """

    def parse(self, source_code: str) -> List[ASTStatement]:
        if not source_code.strip():
            return []

        try:
            tree = ast.parse(source_code)
        except SyntaxError as exc:
            logger.warning("SyntaxError when parsing source code: %s", exc)
            return []

        source_lines = source_code.splitlines()
        statements: List[ASTStatement] = []
        node_id_counter = 1

        def get_source_line(start: int, end: int) -> str:
            if 1 <= start <= len(source_lines):
                if end and start <= end <= len(source_lines):
                    return "\n".join(source_lines[start - 1 : end]).strip()
                return source_lines[start - 1].strip()
            return ""

        def extract_reads_writes(node: ast.AST) -> Tuple[List[str], List[str]]:
            visitor = VariableVisitor()
            visitor.visit(node)
            return sorted(list(visitor.reads)), sorted(list(visitor.writes))

        class StatementExtractor(ast.NodeVisitor):
            def __init__(self) -> None:
                self.current_function = "<module>"
                self.parent_id_stack: List[int] = []

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                nonlocal node_id_counter
                stmt_id = node_id_counter
                node_id_counter += 1

                line = getattr(node, "lineno", 1)
                end_line = getattr(node, "end_lineno", line)
                src = get_source_line(line, line) # header line

                reads, writes = extract_reads_writes(node.args)
                writes.append(node.name)

                parent = self.parent_id_stack[-1] if self.parent_id_stack else None

                statements.append(
                    ASTStatement(
                        node_id=stmt_id,
                        line_number=line,
                        end_line_number=end_line,
                        source_code=src or f"def {node.name}(...):",
                        ast_type="FunctionDef",
                        reads=reads,
                        writes=writes,
                        parent_id=parent,
                        function_name=self.current_function,
                    )
                )

                old_func = self.current_function
                self.current_function = node.name
                self.parent_id_stack.append(stmt_id)

                for stmt in node.body:
                    self.visit(stmt)

                self.parent_id_stack.pop()
                self.current_function = old_func

            def visit_If(self, node: ast.If) -> None:
                nonlocal node_id_counter
                stmt_id = node_id_counter
                node_id_counter += 1

                line = getattr(node, "lineno", 1)
                end_line = getattr(node, "end_lineno", line)
                src = get_source_line(line, line)

                reads, writes = extract_reads_writes(node.test)
                parent = self.parent_id_stack[-1] if self.parent_id_stack else None

                statements.append(
                    ASTStatement(
                        node_id=stmt_id,
                        line_number=line,
                        end_line_number=end_line,
                        source_code=src or "if ...:",
                        ast_type="If",
                        reads=reads,
                        writes=writes,
                        parent_id=parent,
                        function_name=self.current_function,
                    )
                )

                self.parent_id_stack.append(stmt_id)
                for stmt in node.body:
                    self.visit(stmt)
                for stmt in node.orelse:
                    self.visit(stmt)
                self.parent_id_stack.pop()

            def visit_For(self, node: ast.For) -> None:
                nonlocal node_id_counter
                stmt_id = node_id_counter
                node_id_counter += 1

                line = getattr(node, "lineno", 1)
                end_line = getattr(node, "end_lineno", line)
                src = get_source_line(line, line)

                t_reads, t_writes = extract_reads_writes(node.target)
                i_reads, i_writes = extract_reads_writes(node.iter)

                parent = self.parent_id_stack[-1] if self.parent_id_stack else None

                statements.append(
                    ASTStatement(
                        node_id=stmt_id,
                        line_number=line,
                        end_line_number=end_line,
                        source_code=src or "for ...:",
                        ast_type="For",
                        reads=sorted(list(set(i_reads + t_reads))),
                        writes=sorted(list(set(t_writes))),
                        parent_id=parent,
                        function_name=self.current_function,
                    )
                )

                self.parent_id_stack.append(stmt_id)
                for stmt in node.body:
                    self.visit(stmt)
                for stmt in node.orelse:
                    self.visit(stmt)
                self.parent_id_stack.pop()

            def visit_While(self, node: ast.While) -> None:
                nonlocal node_id_counter
                stmt_id = node_id_counter
                node_id_counter += 1

                line = getattr(node, "lineno", 1)
                end_line = getattr(node, "end_lineno", line)
                src = get_source_line(line, line)

                reads, writes = extract_reads_writes(node.test)
                parent = self.parent_id_stack[-1] if self.parent_id_stack else None

                statements.append(
                    ASTStatement(
                        node_id=stmt_id,
                        line_number=line,
                        end_line_number=end_line,
                        source_code=src or "while ...:",
                        ast_type="While",
                        reads=reads,
                        writes=writes,
                        parent_id=parent,
                        function_name=self.current_function,
                    )
                )

                self.parent_id_stack.append(stmt_id)
                for stmt in node.body:
                    self.visit(stmt)
                for stmt in node.orelse:
                    self.visit(stmt)
                self.parent_id_stack.pop()

            def generic_visit(self, node: ast.AST) -> None:
                nonlocal node_id_counter
                if isinstance(node, ast.stmt) and not isinstance(
                    node, (ast.FunctionDef, ast.If, ast.For, ast.While)
                ):
                    stmt_id = node_id_counter
                    node_id_counter += 1

                    line = getattr(node, "lineno", 1)
                    end_line = getattr(node, "end_lineno", line)
                    src = get_source_line(line, end_line)

                    reads, writes = extract_reads_writes(node)
                    parent = self.parent_id_stack[-1] if self.parent_id_stack else None

                    statements.append(
                        ASTStatement(
                            node_id=stmt_id,
                            line_number=line,
                            end_line_number=end_line,
                            source_code=src or type(node).__name__,
                            ast_type=type(node).__name__,
                            reads=reads,
                            writes=writes,
                            parent_id=parent,
                            function_name=self.current_function,
                        )
                    )
                else:
                    super().generic_visit(node)

        extractor = StatementExtractor()
        extractor.visit(tree)
        return statements
