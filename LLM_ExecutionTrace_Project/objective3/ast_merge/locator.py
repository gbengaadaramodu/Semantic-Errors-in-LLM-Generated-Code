"""
Objective 3 — AST Node Locator.

Identifies the AST node(s) in the original source that correspond to
a diagnostic fault location (line range).
"""

from __future__ import annotations

import ast
import logging
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class FaultNodeLocator:
    """
    Locates AST nodes corresponding to a diagnostic line range.
    """

    def locate(
        self,
        tree: ast.Module,
        start_line: int,
        end_line: int,
    ) -> List[ast.stmt]:
        """
        Find top-level or function-body statements that overlap [start_line, end_line].

        Returns a list of matching AST statement nodes.
        """
        matches: List[ast.stmt] = []
        self._find_in_body(ast.iter_child_nodes(tree), start_line, end_line, matches)
        if not matches:
            # Widen search: look at all statements recursively
            matches = self._find_recursive(tree, start_line, end_line)
        return matches

    def locate_enclosing_function(
        self,
        tree: ast.Module,
        start_line: int,
    ) -> Optional[ast.FunctionDef]:
        """
        Find the function definition that contains the given line.
        Returns None if the line is at module level.
        """
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                    if node.lineno <= start_line <= (node.end_lineno or node.lineno):
                        return node  # type: ignore[return-value]
        return None

    def _find_in_body(
        self,
        nodes,
        start_line: int,
        end_line: int,
        results: List[ast.stmt],
    ) -> None:
        for node in nodes:
            if not isinstance(node, ast.stmt):
                continue
            node_start = getattr(node, "lineno", None)
            node_end = getattr(node, "end_lineno", node_start)
            if node_start is None:
                continue
            node_end = node_end or node_start
            # Overlapping check
            if node_start <= end_line and node_end >= start_line:
                results.append(node)
                # Recurse into compound statements
                for child_list in [
                    getattr(node, "body", []),
                    getattr(node, "orelse", []),
                    getattr(node, "handlers", []),
                    getattr(node, "finalbody", []),
                ]:
                    self._find_in_body(child_list, start_line, end_line, results)

    def _find_recursive(
        self,
        tree: ast.AST,
        start_line: int,
        end_line: int,
    ) -> List[ast.stmt]:
        """Broad recursive search across all nodes."""
        matches: List[ast.stmt] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.stmt):
                continue
            node_start = getattr(node, "lineno", None)
            node_end = getattr(node, "end_lineno", node_start)
            if node_start is None:
                continue
            node_end = node_end or node_start
            if node_start <= end_line and node_end >= start_line:
                matches.append(node)
        return matches

    def find_function_body_range(
        self,
        tree: ast.Module,
        function_name: str,
    ) -> Tuple[int, int]:
        """
        Return (start_line, end_line) for the body of a named function.
        Returns (0, 0) if not found.
        """
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == function_name:
                    start = node.lineno
                    end = getattr(node, "end_lineno", node.lineno) or node.lineno
                    return start, end
        return 0, 0
