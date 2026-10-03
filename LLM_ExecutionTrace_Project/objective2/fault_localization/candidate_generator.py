"""
Fault Candidate Generator Module.

Generates candidate fault locations from PDG nodes and reverse traversal paths.
"""

from typing import List

from objective2.models import CandidateCause, ProgramDependencyGraph
from objective2.pdg.traversal import ReversePDGTraversal


class FaultCandidateGenerator:
    """
    Generates candidate cause statements and variables using reverse PDG traversal.
    """

    def __init__(self) -> None:
        self.traversal = ReversePDGTraversal()

    def generate_candidates(
        self, pdg: ProgramDependencyGraph, top_k: int = 5
    ) -> List[CandidateCause]:
        return self.traversal.traverse(pdg, top_k=top_k)
