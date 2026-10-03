"""
Runtime Annotator Module.

Maps dynamic runtime events back onto static PDG nodes, populating execution frequency,
observed variable states, and marking failure-related nodes.
"""

import logging
from typing import Dict, List, Optional

from objective2.models import EventType, PDGNode, RuntimeEvent

logger = logging.getLogger(__name__)


class RuntimeAnnotator:
    """
    Annotates static PDG graph nodes with runtime execution evidence.
    """

    def annotate(
        self,
        nodes: Dict[int, PDGNode],
        events: List[RuntimeEvent],
        failure_line: Optional[int] = None,
    ) -> List[int]:
        """
        Annotates nodes in place. Returns list of failure-related node IDs.
        """
        line_to_nodes: Dict[int, List[PDGNode]] = {}
        for n in nodes.values():
            if n.line_number not in line_to_nodes:
                line_to_nodes[n.line_number] = []
            line_to_nodes[n.line_number].append(n)

        failure_node_ids: List[int] = []

        for ev in events:
            line_nodes = line_to_nodes.get(ev.line_number, [])
            for node in line_nodes:
                node.executed = True
                node.execution_count += 1

                for k, v in ev.local_variables.items():
                    if k not in node.runtime_values:
                        node.runtime_values[k] = []
                    if len(node.runtime_values[k]) < 50: # cap history
                        node.runtime_values[k].append(v)

                if ev.event_type == EventType.EXCEPTION:
                    node.failure_related = True
                    if node.node_id not in failure_node_ids:
                        failure_node_ids.append(node.node_id)

        # Mark explicitly passed failure_line if not already captured
        if failure_line and failure_line in line_to_nodes:
            for node in line_to_nodes[failure_line]:
                node.failure_related = True
                if node.node_id not in failure_node_ids:
                    failure_node_ids.append(node.node_id)

        # Fallback: if no failure node marked yet, take the last executed node
        if not failure_node_ids and events:
            for ev in reversed(events):
                if ev.line_number in line_to_nodes:
                    for node in line_to_nodes[ev.line_number]:
                        node.failure_related = True
                        failure_node_ids.append(node.node_id)
                        break
                if failure_node_ids:
                    break

        return failure_node_ids
