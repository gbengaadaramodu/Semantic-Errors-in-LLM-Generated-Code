"""
PDG Graph Builder Module.

Assembles static and dynamic AST node representations, data dependency edges,
control dependency edges, and runtime annotations into a unified Program Dependency Graph.
"""

from typing import Dict, List, Optional

from objective2.models import (
    PDGEdge,
    PDGNode,
    ProgramDependencyGraph,
    RuntimeEvent,
)
from objective2.pdg.ast_parser import ASTParser
from objective2.pdg.control_dependencies import ControlDependencyAnalyzer
from objective2.pdg.data_dependencies import DataDependencyAnalyzer
from objective2.pdg.nodes import PDGNodeBuilder
from objective2.pdg.runtime_annotator import RuntimeAnnotator


class PDGGraphBuilder:
    """
    Orchestrates AST parsing, dependency extraction, and runtime annotation
    to construct Program Dependency Graphs.
    """

    def __init__(self) -> None:
        self.ast_parser = ASTParser()
        self.data_analyzer = DataDependencyAnalyzer()
        self.control_analyzer = ControlDependencyAnalyzer()
        self.annotator = RuntimeAnnotator()

    def build_pdg(
        self,
        source_code: str,
        events: Optional[List[RuntimeEvent]] = None,
        failure_line: Optional[int] = None,
    ) -> ProgramDependencyGraph:
        ast_stmts = self.ast_parser.parse(source_code)
        nodes: Dict[int, PDGNode] = {}

        for stmt in ast_stmts:
            nodes[stmt.node_id] = PDGNodeBuilder.from_ast_statement(stmt)

        if not nodes:
            return ProgramDependencyGraph()

        entry_node_id = sorted(nodes.keys())[0]

        # Extract static dependencies
        data_edges = self.data_analyzer.analyze(nodes)
        control_edges = self.control_analyzer.analyze(nodes, ast_stmts)
        all_edges = data_edges + control_edges

        # Dynamic runtime annotation
        failure_node_ids = []
        if events:
            failure_node_ids = self.annotator.annotate(nodes, events, failure_line)

        return ProgramDependencyGraph(
            nodes=nodes,
            edges=all_edges,
            entry_node_id=entry_node_id,
            failure_node_ids=failure_node_ids,
        )

    @staticmethod
    def to_dot(pdg: ProgramDependencyGraph) -> str:
        """
        Export PDG to Graphviz DOT format.
        """
        lines = [
            'digraph PDG {',
            '    rankdir=TB;',
            '    node [shape=box, style=filled, fillcolor=white, fontname="Courier"];',
            '    edge [fontname="Helvetica", fontsize=9];',
            '',
        ]

        for node_id, n in pdg.nodes.items():
            color = "lightgrey"
            if n.failure_related:
                color = "salmon"
            elif n.executed:
                color = "lightgreen"

            clean_src = n.source_code.replace('"', '\\"').replace('\n', ' ')
            label = f"L{n.line_number}: {clean_src}"
            if n.writes:
                label += f" | W:{','.join(n.writes)}"
            if n.reads:
                label += f" | R:{','.join(n.reads)}"

            lines.append(f'    "{node_id}" [label="{label}", fillcolor="{color}"];')

        lines.append('')
        for e in pdg.edges:
            style = "solid"
            if e.dependency_type.value == "CONTROL":
                style = "dashed"
            lines.append(
                f'    "{e.source_id}" -> "{e.target_id}" '
                f'[label="{e.label}", style="{style}"];'
            )

        lines.append('}')
        return '\n'.join(lines)
