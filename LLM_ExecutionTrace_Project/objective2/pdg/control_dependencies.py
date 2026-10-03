"""
Control Dependency Analysis Module.

Establishes control dependency edges based on AST nesting (parent control nodes:
If, For, While, FunctionDef).
"""

from typing import Dict, List
from objective2.models import ASTStatement, DependencyType, PDGEdge, PDGNode


class ControlDependencyAnalyzer:
    """
    Constructs control dependency edges linking enclosing control statements
    to body statements.
    """

    def analyze(
        self, nodes: Dict[int, PDGNode], ast_statements: List[ASTStatement]
    ) -> List[PDGEdge]:
        edges: List[PDGEdge] = []
        node_map = {n.node_id: n for n in nodes.values()}

        for stmt in ast_statements:
            if stmt.parent_id is not None and stmt.parent_id in node_map:
                parent_node = node_map[stmt.parent_id]
                child_node = node_map[stmt.node_id]

                # Create CONTROL edge from parent (e.g. If, For) to child
                edges.append(
                    PDGEdge(
                        source_id=parent_node.node_id,
                        target_id=child_node.node_id,
                        dependency_type=DependencyType.CONTROL,
                        variable=None,
                        label=f"CONTROL({parent_node.statement_type})",
                    )
                )

        return edges
