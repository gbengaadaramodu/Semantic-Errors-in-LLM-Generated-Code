"""
Counterfactual Intervention Engine.

Operationalizes `do(X = x)` through precise AST transformations and code modifications.
"""

import ast
import logging
from typing import Any, Optional

from objective2.models import Intervention

logger = logging.getLogger(__name__)


class InterventionTransformer(ast.NodeTransformer):
    """
    AST Transformer to inject or modify variable assignments/conditions at target lines.
    """

    def __init__(self, target_line: int, var_name: str, exp_val: Any) -> None:
        self.target_line = target_line
        self.var_name = var_name
        self.exp_val = exp_val
        self.applied = False

    def visit_Assign(self, node: ast.Assign) -> Any:
        self.generic_visit(node)
        if node.lineno == self.target_line:
            # Check if var_name is in targets
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == self.var_name:
                    try:
                        new_value_node = ast.Constant(value=self.exp_val)
                        node.value = new_value_node
                        self.applied = True
                    except Exception:
                        pass
        return node

    def visit_Return(self, node: ast.Return) -> Any:
        self.generic_visit(node)
        if hasattr(node, 'lineno') and node.lineno == self.target_line:
            # Only intervene if the return value IS the target variable directly
            if isinstance(node.value, ast.Name) and node.value.id == self.var_name:
                try:
                    node.value = ast.Constant(value=self.exp_val)
                    self.applied = True
                except Exception:
                    pass
        return node

    def visit_Compare(self, node: ast.Compare) -> Any:
        self.generic_visit(node)
        if hasattr(node, 'lineno') and node.lineno == self.target_line:
            try:
                new_ops = []
                flipped = False
                for op in node.ops:
                    if isinstance(op, ast.NotEq):
                        new_ops.append(ast.Eq())
                        flipped = True
                    elif isinstance(op, ast.Eq):
                        new_ops.append(ast.NotEq())
                        flipped = True
                    elif isinstance(op, ast.Lt):
                        new_ops.append(ast.GtE())
                        flipped = True
                    elif isinstance(op, ast.Gt):
                        new_ops.append(ast.LtE())
                        flipped = True
                    elif isinstance(op, ast.LtE):
                        new_ops.append(ast.Gt())
                        flipped = True
                    elif isinstance(op, ast.GtE):
                        new_ops.append(ast.Lt())
                        flipped = True
                    else:
                        new_ops.append(op)
                
                if flipped:
                    node.ops = new_ops
                    self.applied = True
            except Exception:
                pass
        return node


class CounterfactualInterventionEngine:
    """
    Generates intervened program code for candidate causes.
    """

    def create_intervention(
        self,
        source_code: str,
        target_line: int,
        var_name: str,
        observed_value: Any,
        expected_value: Any,
    ) -> Optional[Intervention]:
        if not source_code.strip():
            return None

        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return None

        transformer = InterventionTransformer(target_line, var_name, expected_value)
        modified_tree = transformer.visit(tree)
        ast.fix_missing_locations(modified_tree)

        modified_code = ""
        if transformer.applied:
            try:
                modified_code = ast.unparse(modified_tree)
            except Exception:
                modified_code = ""

        # Fallback line-replacement if AST unparsing was not triggered or supported
        if not modified_code:
            lines = source_code.splitlines()
            if 1 <= target_line <= len(lines):
                target_src = lines[target_line - 1]
                if var_name in target_src and expected_value is not None:
                    indent = len(target_src) - len(target_src.lstrip())
                    # Insert an override assignment right before the usage
                    override = f"{' ' * indent}{var_name} = {repr(expected_value)}"
                    lines.insert(target_line - 1, override)
                    modified_code = "\n".join(lines)

        if not modified_code:
            return None

        return Intervention(
            target_variable=var_name,
            target_line=target_line,
            observed_value=observed_value,
            counterfactual_value=expected_value,
            operation_type="AST_transform",
            modified_code=modified_code,
        )
