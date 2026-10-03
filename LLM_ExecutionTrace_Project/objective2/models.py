"""
Objective 2 Data Models.

Provides strongly typed dataclasses and enums representing SCM, PDG, AST nodes,
runtime events, candidate causes, counterfactual interventions, fault locations,
and final root-cause diagnosis outputs.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AnalysisStatus(str, Enum):
    ANALYZED = "ANALYZED"
    SKIPPED = "SKIPPED"
    UNSUPPORTED = "UNSUPPORTED"
    FAILED = "FAILED"
    UNRESOLVED = "UNRESOLVED"


class DependencyType(str, Enum):
    DATA = "DATA"
    CONTROL = "CONTROL"
    CALL = "CALL"
    RETURN = "RETURN"
    RUNTIME = "RUNTIME"


class EventType(str, Enum):
    CALL = "call"
    LINE = "line"
    RETURN = "return"
    EXCEPTION = "exception"


class CausalEffect(str, Enum):
    TRUE = "TRUE"        # FAIL -> PASS
    FALSE = "FALSE"      # FAIL -> FAIL
    UNRESOLVED = "UNRESOLVED" # Execution error / invalid state / timeout


# ---------------------------------------------------------------------------
# Input Record
# ---------------------------------------------------------------------------

@dataclass
class Objective2InputRecord:
    """Represents a single task record loaded from Objective 1 corpus/logs."""

    trace_id: str
    dataset: str
    task_id: str
    problem_summary: str = ""
    execution_status: str = ""
    stdout: str = ""
    stderr: str = ""
    traceback: str = ""
    exception_type: str = ""
    exception_message: str = ""
    execution_time: float = 0.0
    timed_out: bool = False
    exit_code: int = 0
    tests_passed: Optional[bool] = None
    tests_failed: int = 0
    expected_output: Optional[str] = None
    actual_output: Optional[str] = None
    assertion_source: Optional[str] = None
    assertion_failed: bool = False
    parser_prediction: str = ""

    # Associated code and test definitions
    generated_code: str = ""
    entry_point: str = ""
    test_code: str = ""
    test_imports: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "dataset": self.dataset,
            "task_id": self.task_id,
            "problem_summary": self.problem_summary,
            "execution_status": self.execution_status,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "traceback": self.traceback,
            "exception_type": self.exception_type,
            "exception_message": self.exception_message,
            "execution_time": self.execution_time,
            "timed_out": self.timed_out,
            "exit_code": self.exit_code,
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_failed,
            "expected_output": self.expected_output,
            "actual_output": self.actual_output,
            "assertion_source": self.assertion_source,
            "assertion_failed": self.assertion_failed,
            "parser_prediction": self.parser_prediction,
        }


# ---------------------------------------------------------------------------
# SCM Models
# ---------------------------------------------------------------------------

@dataclass
class SCMVariable:
    name: str
    symbol: str
    description: str
    value: Any = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "symbol": self.symbol,
            "description": self.description,
            "value": str(self.value) if self.value is not None else None,
        }


@dataclass
class SCMNode:
    node_id: str
    variable_name: str
    symbol: str
    label: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "variable_name": self.variable_name,
            "symbol": self.symbol,
            "label": self.label,
        }


@dataclass
class SCMEdge:
    source: str
    target: str
    relationship: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "relationship": self.relationship,
        }


@dataclass
class StructuralCausalModel:
    task_id: str
    nodes: List[SCMNode] = field(default_factory=list)
    edges: List[SCMEdge] = field(default_factory=list)
    variables: Dict[str, SCMVariable] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "variables": {k: v.to_dict() for k, v in self.variables.items()},
        }


# ---------------------------------------------------------------------------
# AST & Runtime Tracing Models
# ---------------------------------------------------------------------------

@dataclass
class ASTStatement:
    node_id: int
    line_number: int
    end_line_number: int
    source_code: str
    ast_type: str
    reads: List[str] = field(default_factory=list)
    writes: List[str] = field(default_factory=list)
    parent_id: Optional[int] = None
    function_name: str = "<module>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "line_number": self.line_number,
            "end_line_number": self.end_line_number,
            "source_code": self.source_code,
            "ast_type": self.ast_type,
            "reads": self.reads,
            "writes": self.writes,
            "parent_id": self.parent_id,
            "function_name": self.function_name,
        }


@dataclass
class RuntimeEvent:
    event_id: int
    timestamp: float
    event_type: EventType
    filename: str
    function_name: str
    line_number: int
    local_variables: Dict[str, Any] = field(default_factory=dict)
    return_value: Optional[Any] = None
    exception: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type.value,
            "filename": self.filename,
            "function_name": self.function_name,
            "line_number": self.line_number,
            "local_variables": {k: str(v) for k, v in self.local_variables.items()},
            "return_value": str(self.return_value) if self.return_value is not None else None,
            "exception": self.exception,
        }


@dataclass
class VariableState:
    variable_name: str
    line_number: int
    observed_value: Any
    timestamp: float
    event_type: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variable_name": self.variable_name,
            "line_number": self.line_number,
            "observed_value": str(self.observed_value),
            "timestamp": self.timestamp,
            "event_type": self.event_type,
        }


# ---------------------------------------------------------------------------
# Program Dependency Graph (PDG) Models
# ---------------------------------------------------------------------------

@dataclass
class PDGNode:
    node_id: int
    line_number: int
    source_code: str
    statement_type: str
    reads: List[str] = field(default_factory=list)
    writes: List[str] = field(default_factory=list)
    function_name: str = "<module>"
    executed: bool = False
    execution_count: int = 0
    runtime_values: Dict[str, List[Any]] = field(default_factory=dict)
    failure_related: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "line_number": self.line_number,
            "source_code": self.source_code,
            "statement_type": self.statement_type,
            "reads": self.reads,
            "writes": self.writes,
            "function_name": self.function_name,
            "executed": self.executed,
            "execution_count": self.execution_count,
            "runtime_values": {
                k: [str(v) for v in vals] for k, vals in self.runtime_values.items()
            },
            "failure_related": self.failure_related,
        }


@dataclass
class PDGEdge:
    source_id: int
    target_id: int
    dependency_type: DependencyType
    variable: Optional[str] = None
    label: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "dependency_type": self.dependency_type.value,
            "variable": self.variable,
            "label": self.label,
        }


@dataclass
class ProgramDependencyGraph:
    nodes: Dict[int, PDGNode] = field(default_factory=dict)
    edges: List[PDGEdge] = field(default_factory=list)
    entry_node_id: Optional[int] = None
    failure_node_ids: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": {str(k): v.to_dict() for k, v in self.nodes.items()},
            "edges": [e.to_dict() for e in self.edges],
            "entry_node_id": self.entry_node_id,
            "failure_node_ids": self.failure_node_ids,
        }


# ---------------------------------------------------------------------------
# Counterfactual & Fault Localization Models
# ---------------------------------------------------------------------------

@dataclass
class CriticalVariable:
    variable_name: str
    definition_line: int
    use_lines: List[int] = field(default_factory=list)
    observed_value: Any = None
    expected_value: Any = None
    expected_value_source: str = "UNRESOLVED"
    confidence: float = 0.0
    inference_explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variable_name": self.variable_name,
            "definition_line": self.definition_line,
            "use_lines": self.use_lines,
            "observed_value": str(self.observed_value) if self.observed_value is not None else None,
            "expected_value": str(self.expected_value) if self.expected_value is not None else None,
            "expected_value_source": self.expected_value_source,
            "confidence": self.confidence,
            "inference_explanation": self.inference_explanation,
        }


@dataclass
class CandidateCause:
    rank: int
    node_id: int
    line_number: int
    statement_code: str
    variable_name: str
    observed_value: Any = None
    expected_value: Any = None
    proximity_score: float = 0.0
    dependency_score: float = 0.0
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "node_id": self.node_id,
            "line_number": self.line_number,
            "statement_code": self.statement_code,
            "variable_name": self.variable_name,
            "observed_value": str(self.observed_value) if self.observed_value is not None else None,
            "expected_value": str(self.expected_value) if self.expected_value is not None else None,
            "proximity_score": self.proximity_score,
            "dependency_score": self.dependency_score,
            "explanation": self.explanation,
        }


@dataclass
class Intervention:
    target_variable: str
    target_line: int
    observed_value: Any
    counterfactual_value: Any
    operation_type: str = "assign" # e.g. "assign", "expression_replace"
    modified_code: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_variable": self.target_variable,
            "target_line": self.target_line,
            "observed_value": str(self.observed_value),
            "counterfactual_value": str(self.counterfactual_value),
            "operation_type": self.operation_type,
            "modified_code": self.modified_code,
        }


@dataclass
class CounterfactualResult:
    candidate_rank: int
    intervention: Intervention
    original_outcome: str
    counterfactual_outcome: str
    original_actual_output: Optional[str] = None
    counterfactual_output: Optional[str] = None
    causal_effect: CausalEffect = CausalEffect.UNRESOLVED
    execution_time: float = 0.0
    status: str = "EXECUTED"
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_rank": self.candidate_rank,
            "intervention": self.intervention.to_dict(),
            "original_outcome": self.original_outcome,
            "counterfactual_outcome": self.counterfactual_outcome,
            "original_actual_output": self.original_actual_output,
            "counterfactual_output": self.counterfactual_output,
            "causal_effect": self.causal_effect.value,
            "execution_time": self.execution_time,
            "status": self.status,
            "explanation": self.explanation,
        }


@dataclass
class FaultLocation:
    file: str
    line_number: int
    statement_code: str
    function_name: str
    causal_variable: str
    evidence_score: float = 0.0
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file,
            "line_number": self.line_number,
            "statement_code": self.statement_code,
            "function_name": self.function_name,
            "causal_variable": self.causal_variable,
            "evidence_score": self.evidence_score,
            "confidence": self.confidence,
        }


@dataclass
class RootCauseDiagnosis:
    root_cause_status: str  # e.g. "VALIDATED", "UNRESOLVED"
    candidate_explanation: str
    causal_variable: str
    fault_statement: str
    fault_line: int
    evidence_summary: str
    counterfactual_validated: bool = False
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "root_cause_status": self.root_cause_status,
            "candidate_explanation": self.candidate_explanation,
            "causal_variable": self.causal_variable,
            "fault_statement": self.fault_statement,
            "fault_line": self.fault_line,
            "evidence_summary": self.evidence_summary,
            "counterfactual_validated": self.counterfactual_validated,
            "confidence": self.confidence,
        }


# ---------------------------------------------------------------------------
# Complete Objective 2 Result per Task
# ---------------------------------------------------------------------------

@dataclass
class Objective2Result:
    trace_id: str
    dataset: str
    task_id: str
    error_category: str
    analysis_status: AnalysisStatus
    skip_reason: Optional[str] = None

    input_record: Optional[Objective2InputRecord] = None
    scm: Optional[StructuralCausalModel] = None
    pdg: Optional[ProgramDependencyGraph] = None
    runtime_events_count: int = 0

    failure_line: Optional[int] = None
    failure_statement: Optional[str] = None

    candidates: List[CandidateCause] = field(default_factory=list)
    critical_variable: Optional[CriticalVariable] = None
    counterfactual_results: List[CounterfactualResult] = field(
        default_factory=list
    )

    fault_location: Optional[FaultLocation] = None
    root_cause: Optional[RootCauseDiagnosis] = None

    ground_truth_matched: Optional[bool] = None
    ground_truth_fault_line: Optional[int] = None

    execution_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "dataset": self.dataset,
            "task_id": self.task_id,
            "error_category": self.error_category,
            "analysis_status": self.analysis_status.value,
            "skip_reason": self.skip_reason,
            "input_record": self.input_record.to_dict() if self.input_record else None,
            "scm": self.scm.to_dict() if self.scm else None,
            "pdg": self.pdg.to_dict() if self.pdg else None,
            "runtime_events_count": self.runtime_events_count,
            "failure_line": self.failure_line,
            "failure_statement": self.failure_statement,
            "candidates": [c.to_dict() for c in self.candidates],
            "critical_variable": (
                self.critical_variable.to_dict() if self.critical_variable else None
            ),
            "counterfactual_results": [
                cf.to_dict() for cf in self.counterfactual_results
            ],
            "fault_location": (
                self.fault_location.to_dict() if self.fault_location else None
            ),
            "root_cause": (
                self.root_cause.to_dict() if self.root_cause else None
            ),
            "ground_truth_matched": self.ground_truth_matched,
            "ground_truth_fault_line": self.ground_truth_fault_line,
            "execution_time": round(self.execution_time, 4),
        }


@dataclass
class Objective2Summary:
    total_corpus_size: int = 0
    eligible_cases: int = 0
    analyzed_cases: int = 0
    skipped_cases: int = 0
    unresolved_cases: int = 0
    failed_cases: int = 0

    root_cause_accuracy: str = "N/A" # "num/den (pct%)" or "NOT_AVAILABLE"
    fault_location_accuracy: str = "N/A"
    critical_variable_accuracy: str = "N/A"
    top_1_fault_accuracy: str = "N/A"
    top_3_fault_accuracy: str = "N/A"
    top_5_fault_accuracy: str = "N/A"
    counterfactual_success_rate: str = "N/A"
    ground_truth_status: str = "NOT_AVAILABLE"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_corpus_size": self.total_corpus_size,
            "eligible_cases": self.eligible_cases,
            "analyzed_cases": self.analyzed_cases,
            "skipped_cases": self.skipped_cases,
            "unresolved_cases": self.unresolved_cases,
            "failed_cases": self.failed_cases,
            "root_cause_accuracy": self.root_cause_accuracy,
            "fault_location_accuracy": self.fault_location_accuracy,
            "critical_variable_accuracy": self.critical_variable_accuracy,
            "top_1_fault_accuracy": self.top_1_fault_accuracy,
            "top_3_fault_accuracy": self.top_3_fault_accuracy,
            "top_5_fault_accuracy": self.top_5_fault_accuracy,
            "counterfactual_success_rate": self.counterfactual_success_rate,
            "ground_truth_status": self.ground_truth_status,
        }
