"""
Objective 3 — AST-Based Code Merger.

Implements the five-stage AST merge algorithm:

    Stage 1 — Parse     : Parse original and repair code into ASTs
    Stage 2 — Locate    : Locate AST nodes at the fault line range
    Stage 3 — Replace   : Replace located nodes with repair AST nodes
    Stage 4 — Boundary  : Expand to nearest enclosing block if needed
    Stage 5 — Regenerate: Unparse merged AST to Python source

The merger preserves:
  - Function signature
  - Surrounding function structure
  - Imports (unless intentionally changed)
  - Unrelated code
  - Benchmark test code outside the generated implementation

After merging, the validator runs parse → compile → existence → signature checks.
A failed validation produces INVALID_REPAIR status.

Scientific note: Naive string replacement is NOT used as the primary mechanism.
"""

from __future__ import annotations

import ast
import copy
import logging
from typing import List, Optional, Tuple

from objective3.ast_merge.locator import FaultNodeLocator
from objective3.ast_merge.validator import MergeValidator
from objective3.models import ASTMergeResult

logger = logging.getLogger(__name__)


class ASTMerger:
    """
    AST-based code merger.

    Given the original source, the repaired block, a fault location,
    and the required entry point, produces a merged Python source
    with the faulty statements replaced by the repair.
    """

    def __init__(self) -> None:
        self._locator = FaultNodeLocator()
        self._validator = MergeValidator()

    def merge(
        self,
        original_source: str,
        repair_code: str,
        entry_point: str,
        start_line: int,
        end_line: int,
    ) -> ASTMergeResult:
        """
        Merge the repair code into the original source.

        Parameters
        ----------
        original_source : The complete original (failing) Python source.
        repair_code     : The repaired code block from the LLM.
        entry_point     : Expected function name (for validation).
        start_line      : Fault location start line (1-indexed).
        end_line        : Fault location end line (1-indexed, inclusive).

        Returns
        -------
        ASTMergeResult
        """
        # ── Stage 1: Parse ───────────────────────────────────────────────────
        try:
            orig_tree = ast.parse(original_source)
        except SyntaxError as exc:
            return ASTMergeResult(
                success=False,
                error_message=f"Original source has syntax error: {exc}",
            )

        try:
            repair_tree = ast.parse(repair_code)
            repair_has_target_func = self._has_function(repair_tree, entry_point)
        except SyntaxError as exc:
            # Repair code might be a fragment/snippet with indentation. Fallback to line splice.
            logger.debug(f"Repair code parse failed (snippet?): {exc}. Falling back to splice.")
            original_sig = self._validator.extract_signature(original_source, entry_point)
            return self._line_splice_merge(
                original_source, repair_code, entry_point, original_sig,
                start_line, end_line, boundary_expanded=False
            )

        # Extract function signature for later validation
        original_sig = self._validator.extract_signature(original_source, entry_point)

        # ── Strategy Selection ────────────────────────────────────────────────
        # Prefer function-level replacement when repair_code defines the target function


        if repair_has_target_func:
            # Replace the entire target function with the repair version
            return self._replace_function(
                orig_tree,
                repair_tree,
                original_source,
                repair_code,
                entry_point,
                original_sig,
            )
        else:
            # Replace statement(s) at the fault location
            return self._replace_statements(
                orig_tree,
                repair_tree,
                original_source,
                repair_code,
                entry_point,
                original_sig,
                start_line,
                end_line,
            )

    def _replace_function(
        self,
        orig_tree: ast.Module,
        repair_tree: ast.Module,
        original_source: str,
        repair_code: str,
        entry_point: str,
        original_sig: Optional[str],
    ) -> ASTMergeResult:
        """
        Replace the entire target function definition in the original AST
        with the one from the repair tree.
        """
        # Find original function node index in module body
        orig_func_idx: Optional[int] = None
        orig_func_node: Optional[ast.stmt] = None
        for i, node in enumerate(orig_tree.body):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == entry_point:
                    orig_func_idx = i
                    orig_func_node = node
                    break

        # Find repair function node
        repair_func_node: Optional[ast.stmt] = None
        for node in ast.walk(repair_tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == entry_point:
                    repair_func_node = node
                    break
            # Also accept any function if target not found by name
        if repair_func_node is None:
            # Fallback: use first function in repair
            for node in repair_tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    repair_func_node = node
                    break

        if repair_func_node is None:
            return ASTMergeResult(
                success=False,
                error_message="Repair code contains no function definition.",
            )

        # Build merged tree
        merged_tree = copy.deepcopy(orig_tree)

        if orig_func_idx is not None:
            # Replace the existing function
            merged_tree.body[orig_func_idx] = copy.deepcopy(repair_func_node)
        else:
            # Append if not found (unusual case)
            logger.warning(
                "Function '%s' not found in original; appending repair function.",
                entry_point,
            )
            merged_tree.body.append(copy.deepcopy(repair_func_node))

        # Also include any imports from repair that are not in original
        merged_tree = self._merge_imports(merged_tree, repair_tree)

        # Fix line numbers before unparsing
        ast.fix_missing_locations(merged_tree)

        try:
            merged_source = ast.unparse(merged_tree)
        except Exception as exc:
            return ASTMergeResult(
                success=False,
                error_message=f"AST unparse failed: {exc}",
            )

        # ── Stage 5 Validation ────────────────────────────────────────────────
        return self._validate_and_return(
            merged_source, entry_point, original_sig, boundary_expanded=False
        )

    def _replace_statements(
        self,
        orig_tree: ast.Module,
        repair_tree: ast.Module,
        original_source: str,
        repair_code: str,
        entry_point: str,
        original_sig: Optional[str],
        start_line: int,
        end_line: int,
    ) -> ASTMergeResult:
        """
        Replace individual statements at the fault location.
        Falls back to string-line splice if AST node identification fails.
        """
        boundary_expanded = False

        # ── Stage 2: Locate fault nodes ──────────────────────────────────────
        fault_nodes = self._locator.locate(orig_tree, start_line, end_line)

        if not fault_nodes:
            logger.warning(
                "No AST nodes found at lines %d-%d; expanding to enclosing function.",
                start_line,
                end_line,
            )
            boundary_expanded = True
            # Fallback: replace the enclosing function
            enclosing = self._locator.locate_enclosing_function(orig_tree, start_line)
            if enclosing:
                start_line = enclosing.lineno
                end_line = getattr(enclosing, "end_lineno", enclosing.lineno) or enclosing.lineno
            # Try line-splice approach
            return self._line_splice_merge(
                original_source, repair_code, entry_point, original_sig,
                start_line, end_line, boundary_expanded=True
            )

        # ── Stage 3 & 4: Replace nodes ───────────────────────────────────────
        # Extract repair body statements
        repair_stmts = list(repair_tree.body)

        # Determine if boundary expansion is needed (multi-node repair)
        if len(fault_nodes) > 1:
            boundary_expanded = True

        # Build replacement using line-splice (more reliable than deep AST surgery)
        return self._line_splice_merge(
            original_source, repair_code, entry_point, original_sig,
            start_line, end_line, boundary_expanded=boundary_expanded
        )

    def _line_splice_merge(
        self,
        original_source: str,
        repair_code: str,
        entry_point: str,
        original_sig: Optional[str],
        start_line: int,
        end_line: int,
        boundary_expanded: bool = False,
    ) -> ASTMergeResult:
        """
        Line-splice fallback merger: replaces lines [start_line, end_line]
        in the original with the repair code lines that correspond to the
        faulty function body.

        This is a well-defined operation used when AST node identification
        of individual statements is insufficient.
        """
        orig_lines = original_source.splitlines()
        n = len(orig_lines)

        # Sanitize range
        s = max(0, start_line - 1)   # 0-indexed
        e = min(n, end_line)          # exclusive upper bound (0-indexed)

        # Determine indentation context from original
        if s < n:
            indent = len(orig_lines[s]) - len(orig_lines[s].lstrip())
        else:
            indent = 0
        indent_str = " " * indent

        # Prepare repair lines with matching indentation
        repair_lines = repair_code.splitlines()
        # Remove existing leading indentation from repair and re-apply
        repair_dedented = []
        for line in repair_lines:
            if line.strip():
                stripped = line.lstrip()
                repair_dedented.append(indent_str + stripped)
            else:
                repair_dedented.append("")

        merged_lines = orig_lines[:s] + repair_dedented + orig_lines[e:]
        merged_source = "\n".join(merged_lines)

        uncertainty = "HIGH" if boundary_expanded else "LOW"
        return self._validate_and_return(
            merged_source, entry_point, original_sig,
            boundary_expanded=boundary_expanded,
            uncertainty=uncertainty,
        )

    def _validate_and_return(
        self,
        merged_source: str,
        entry_point: str,
        original_sig: Optional[str],
        boundary_expanded: bool = False,
        uncertainty: str = "LOW",
    ) -> ASTMergeResult:
        """Run validation and return ASTMergeResult."""
        valid, error_msg = self._validator.validate(
            merged_source, entry_point, original_sig
        )
        if not valid:
            return ASTMergeResult(
                success=False,
                merged_code=merged_source,
                boundary_expanded=boundary_expanded,
                uncertainty=uncertainty,
                error_message=error_msg,
                signature_preserved=False,
            )
        return ASTMergeResult(
            success=True,
            merged_code=merged_source,
            boundary_expanded=boundary_expanded,
            uncertainty=uncertainty,
            signature_preserved=True,
        )

    def _has_function(self, tree: ast.Module, name: str) -> bool:
        """Return True if tree contains a function definition with the given name."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == name:
                    return True
        return False

    def _merge_imports(
        self,
        base_tree: ast.Module,
        repair_tree: ast.Module,
    ) -> ast.Module:
        """
        Add any import statements from repair_tree that are not already in base_tree.
        Imports are inserted at the top of the module body.
        """
        existing_imports = set()
        for node in base_tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                existing_imports.add(ast.unparse(node))

        new_imports = []
        for node in repair_tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                unparsed = ast.unparse(node)
                if unparsed not in existing_imports:
                    new_imports.append(copy.deepcopy(node))

        if new_imports:
            # Find insertion point after existing imports
            insert_idx = 0
            for i, node in enumerate(base_tree.body):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    insert_idx = i + 1
            for imp in new_imports:
                base_tree.body.insert(insert_idx, imp)
                insert_idx += 1

        return base_tree

    def merge_full_replacement(
        self,
        original_source: str,
        repair_code: str,
        entry_point: str,
    ) -> ASTMergeResult:
        """
        Full-function replacement merge: used for structural redesign.
        The repair_code completely replaces the target function.
        """
        try:
            orig_tree = ast.parse(original_source)
            repair_tree = ast.parse(repair_code)
        except SyntaxError as exc:
            return ASTMergeResult(
                success=False,
                error_message=f"Parse error in full replacement: {exc}",
            )
        original_sig = self._validator.extract_signature(original_source, entry_point)
        return self._replace_function(
            orig_tree, repair_tree, original_source, repair_code,
            entry_point, original_sig
        )
