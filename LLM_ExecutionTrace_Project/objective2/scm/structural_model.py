"""
SCM Structural Model Builder.

Builds SCM instances representing causal relationships:
    S -> C
    C -> E
    T -> E
    E -> O
"""

from objective2.models import (
    Objective2InputRecord,
    SCMEdge,
    SCMNode,
    StructuralCausalModel,
)
from objective2.scm.variables import SCMVariables


class SCMBuilder:
    """
    Constructs Structural Causal Models for benchmark tasks.
    """

    @staticmethod
    def build(record: Objective2InputRecord) -> StructuralCausalModel:
        """
        Build an SCM populated with values and edges for a record.
        """
        vars_dict = SCMVariables.create_default_variables()

        vars_dict["S"].value = record.problem_summary or record.task_id
        vars_dict["C"].value = record.generated_code[:200] if record.generated_code else ""
        vars_dict["E"].value = (
            f"status={record.execution_status}, "
            f"exc={record.exception_type}, "
            f"msg={record.exception_message}"
        )
        vars_dict["T"].value = record.test_code[:100] if record.test_code else ""
        vars_dict["O"].value = record.execution_status

        nodes = [
            SCMNode("S", "Specification", "S", "Specification"),
            SCMNode("C", "GeneratedCode", "C", "Generated Code"),
            SCMNode("E", "ExecutionTrace", "E", "Execution Trace"),
            SCMNode("T", "TestSuite", "T", "Test Suite"),
            SCMNode("O", "Outcome", "O", "Outcome"),
        ]

        edges = [
            SCMEdge("S", "C", "generates"),
            SCMEdge("C", "E", "produces"),
            SCMEdge("T", "E", "evaluates"),
            SCMEdge("E", "O", "determines"),
        ]

        return StructuralCausalModel(
            task_id=record.task_id,
            nodes=nodes,
            edges=edges,
            variables=vars_dict,
        )
