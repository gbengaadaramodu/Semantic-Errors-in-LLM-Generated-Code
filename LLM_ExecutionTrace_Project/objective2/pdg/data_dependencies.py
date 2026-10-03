"""
Data Dependency Analysis Module.

Computes definition-use pairs and establishes data dependency edges between PDG nodes.
"""

from typing import Dict, List, Set
from objective2.models import DependencyType, PDGEdge, PDGNode


class DataDependencyAnalyzer:
    """
    Analyzes variable definitions and usages to construct data dependency edges.
    """

    def analyze(self, nodes: Dict[int, PDGNode]) -> List[PDGEdge]:
        edges: List[PDGEdge] = []
        sorted_nodes = sorted(nodes.values(), key=lambda n: (n.line_number, n.node_id))

        # Map variable -> list of node_ids that defined/wrote it
        def_map: Dict[str, List[int]] = {}

        for node in sorted_nodes:
            # Check data dependencies: if this node reads var V, depend on previous nodes writing V
            for var in node.reads:
                if var in def_map and def_map[var]:
                    # Connect to most recent reaching definition(s)
                    reaching_def = def_map[var][-1]
                    if reaching_def != node.node_id:
                        edges.append(
                            PDGEdge(
                                source_id=reaching_def,
                                target_id=node.node_id,
                                dependency_type=DependencyType.DATA,
                                variable=var,
                                label=f"DATA({var})",
                            )
                        )

            # Register writes from this node
            for var in node.writes:
                if var not in def_map:
                    def_map[var] = []
                def_map[var].append(node.node_id)

        return edges
