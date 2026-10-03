"""
SCM Graph Module.

Graph representation for Structural Causal Models, supporting JSON export
and DOT graphviz format generation.
"""

from typing import Dict, List
from objective2.models import SCMEdge, SCMNode, StructuralCausalModel


class SCMGraph:
    """
    Manages structural causal model graphs and exports DOT representations.
    """

    @staticmethod
    def to_dot(scm: StructuralCausalModel) -> str:
        """
        Generate Graphviz DOT representation of the Structural Causal Model.
        """
        lines = [
            'digraph SCM {',
            '    rankdir=LR;',
            '    node [shape=ellipse, style=filled, color=lightskyblue, fontname="Helvetica"];',
            '    edge [fontname="Helvetica", fontsize=10];',
            '',
        ]

        for n in scm.nodes:
            label_text = f"{n.symbol}: {n.label}"
            lines.append(f'    "{n.node_id}" [label="{label_text}"];')

        lines.append('')
        for e in scm.edges:
            lines.append(
                f'    "{e.source}" -> "{e.target}" [label="{e.relationship}"];'
            )

        lines.append('}')
        return '\n'.join(lines)
