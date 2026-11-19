"""
Objective 3 — AST Merge Validator.

Post-merge validation pipeline:
    1. Parse the merged source
    2. Compile it
    3. Verify the target function still exists
    4. Verify the function signature is preserved
"""

from __future__ import annotations

import ast
import copy
import logging
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class MergeValidator:
    """
    Validates the merged source code after AST-based repair.
    """

    def validate(
        self,
        merged_source: str,
        entry_point: str,
        original_signature: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Run full validation on the merged source.

        Parameters
        ----------
        merged_source       : The merged Python source code string.
        entry_point         : Expected function name.
        original_signature  : Original function signature for comparison (optional).

        Returns
        -------
        (valid: bool, error_message: str)
        """
        # ── Step 1: Parse ────────────────────────────────────────────────────
        try:
            tree = ast.parse(merged_source)
        except SyntaxError as exc:
            msg = f"Merged code syntax error at line {exc.lineno}: {exc.msg}"
            logger.warning(msg)
            return False, msg

        # ── Step 2: Compile ──────────────────────────────────────────────────
        try:
            compile(merged_source, "<merged>", "exec")
        except SyntaxError as exc:
            msg = f"Merged code compile error: {exc}"
            logger.warning(msg)
            return False, msg

        # ── Step 3: Function existence check ─────────────────────────────────
        found_func = self._find_function(tree, entry_point)
        if found_func is None:
            msg = (
                f"Merged code does not contain the required function '{entry_point}'. "
                "The function may have been accidentally deleted by the repair."
            )
            logger.warning(msg)
            return False, msg

        # ── Step 4: Signature check ──────────────────────────────────────────
        if original_signature:
            sig_valid, sig_msg = self._check_signature(found_func, original_signature)
            if not sig_valid:
                logger.warning(sig_msg)
                return False, sig_msg

        return True, ""

    def _find_function(
        self,
        tree: ast.Module,
        name: str,
    ) -> Optional[ast.FunctionDef]:
        """Find a function definition by name anywhere in the AST."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == name:
                    return node  # type: ignore[return-value]
        return None

    def _check_signature(
        self,
        func_node: ast.FunctionDef,
        original_signature: str,
    ) -> Tuple[bool, str]:
        """
        Check that the function signature (name + argument names) matches the original.
        We check argument names, not types or defaults, to avoid false positives.
        """
        try:
            orig_tree = ast.parse(original_signature + ":\n    pass")
        except SyntaxError:
            # Can't parse reference signature — skip check
            return True, ""

        orig_func = None
        for node in ast.walk(orig_tree):
            if isinstance(node, ast.FunctionDef):
                orig_func = node
                break

        if orig_func is None:
            return True, ""

        # Compare argument names
        orig_args = [a.arg for a in orig_func.args.args]
        new_args = [a.arg for a in func_node.args.args]

        if orig_args != new_args:
            return False, (
                f"Function signature changed: original args {orig_args}, "
                f"merged args {new_args}."
            )
        return True, ""

    def extract_signature(self, source: str, entry_point: str) -> Optional[str]:
        """
        Extract the function signature line from source code.
        Returns 'def func_name(args)' or None.
        """
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == entry_point:
                    # Clear body so we only unparse the signature
                    dummy = copy.deepcopy(node)
                    dummy.body = [ast.Pass()]
                    dummy.decorator_list = []
                    return ast.unparse(dummy).split(":")[0].strip()
        return None
