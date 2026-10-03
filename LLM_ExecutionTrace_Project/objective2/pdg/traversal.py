"""
Reverse PDG Traversal Module.

Performs backward traversal along data and control dependencies from failure-related
nodes to extract candidate cause statements and variables.
"""

from collections import deque
from typing import Dict, List, Set, Tuple

from objective2.models import CandidateCause, DependencyType, PDGEdge, PDGNode, ProgramDependencyGraph


class ReversePDGTraversal:
    """
    Traverses the Program Dependency Graph in reverse from failure locations.
    """

    def traverse(
        self, pdg: ProgramDependencyGraph, top_k: int = 5
    ) -> List[CandidateCause]:
        if not pdg.nodes:
            return []

        start_node_ids = pdg.failure_node_ids
        if not start_node_ids:
            # Fallback: take all executed nodes or highest line number node
            start_node_ids = [
                n.node_id for n in pdg.nodes.values() if n.executed
            ]
            if not start_node_ids:
                start_node_ids = list(pdg.nodes.keys())

        # Construct reverse adjacency list: target_id -> list of (source_id, edge)
        rev_adj: Dict[int, List[Tuple[int, PDGEdge]]] = {
            nid: [] for nid in pdg.nodes
        }
        for edge in pdg.edges:
            if edge.target_id in rev_adj:
                rev_adj[edge.target_id].append((edge.source_id, edge))

        visited: Set[int] = set()
        queue: deque = deque([(nid, 0, 1.0) for nid in start_node_ids])
        candidates: List[CandidateCause] = []
        rank_counter = 1

        while queue and len(candidates) < top_k:
            curr_id, distance, path_score = queue.popleft()

            if curr_id in visited:
                continue
            visited.add(curr_id)

            curr_node = pdg.nodes.get(curr_id)
            if not curr_node:
                continue

            # Identify candidate variable
            cand_var = ""
            if curr_node.writes:
                cand_var = curr_node.writes[0]
            elif curr_node.reads:
                cand_var = curr_node.reads[0]

            obs_val = None
            if cand_var and cand_var in curr_node.runtime_values:
                vals = curr_node.runtime_values[cand_var]
                if vals:
                    obs_val = vals[-1]

            # Prevent identifying function signature/parameters as the fault mechanism
            if curr_node.statement_type == "FunctionDef":
                # Expand predecessors but skip generating a candidate for the signature itself
                for parent_id, edge in rev_adj.get(curr_id, []):
                    if parent_id not in visited:
                        edge_weight = 0.9 if edge.dependency_type == DependencyType.DATA else 0.7
                        queue.append((parent_id, distance + 1, path_score * edge_weight))
                continue

            prox_score = max(0.0, 1.0 - (0.15 * distance))

            candidates.append(
                CandidateCause(
                    rank=rank_counter,
                    node_id=curr_node.node_id,
                    line_number=curr_node.line_number,
                    statement_code=curr_node.source_code,
                    variable_name=cand_var or "<statement>",
                    observed_value=obs_val,
                    expected_value=None,
                    proximity_score=round(prox_score, 3),
                    dependency_score=round(path_score, 3),
                    explanation=(
                        f"Reached via reverse traversal (distance={distance}, "
                        f"type={curr_node.statement_type})"
                    ),
                )
            )
            rank_counter += 1

            # Expand predecessors
            for parent_id, edge in rev_adj.get(curr_id, []):
                if parent_id not in visited:
                    edge_weight = 0.9 if edge.dependency_type == DependencyType.DATA else 0.7
                    queue.append((parent_id, distance + 1, path_score * edge_weight))

        return candidates
