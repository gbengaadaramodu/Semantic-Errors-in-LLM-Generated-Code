"""
Objective 3 — Data Models.

Strongly-typed dataclasses representing:
  - ErrorProfile       : Objective 1 adapter output
  - FaultLocation      : Line-range fault localization
  - ConfidenceScore    : Structured confidence from Objective 2
  - StructuredDiagnosticReport : Objective 2 adapter output
  - RepairIteration    : A single repair cycle record
  - TaskTrajectory     : Complete per-task repair history
  - ControllerDecision : State controller output
  - FinalTaskResult    : Task-level summary for Objective 4
  - RunSummary         : Descriptive statistics across all tasks
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ErrorCategory(str, Enum):
    """Objective 1 error categories. Maps to research taxonomy."""
    CORRECT = "Correct"
    SYNTAX_ERROR = "Syntax Error"
    RUNTIME_EXCEPTION = "Runtime Exception"
    WRONG_OUTPUT = "Wrong-Output Error"
    ASSERTION_FAILURE = "Assertion Failure"
    TIMEOUT = "Timeout Error"
    UNKNOWN = "Unknown"


class DiagnosisStatus(str, Enum):
    """
    Diagnosis certainty as produced by Objective 2.
    These three values must remain distinct — never upgrade UNRESOLVED to VALIDATED.
    """
    VALIDATED = "VALIDATED"
    CANDIDATE = "CANDIDATE"
    UNRESOLVED = "UNRESOLVED"
    SKIPPED = "SKIPPED"           # Objective 2 skipped this error type
    FAILED = "FAILED"             # Objective 2 pipeline error


class RepairStrategy(str, Enum):
    """Repair strategy, escalated on stall or oscillation."""
    LOCAL_MODIFICATION = "LOCAL_MODIFICATION"
    BROADER_LOCAL_MODIFICATION = "BROADER_LOCAL_MODIFICATION"
    STRUCTURAL_REDESIGN = "STRUCTURAL_REDESIGN"


class ControllerState(str, Enum):
    """Finite state machine states for the repair controller."""
    INITIALIZED = "INITIALIZED"
    GENERATING = "GENERATING"
    EXECUTING = "EXECUTING"
    CLASSIFIED = "CLASSIFIED"
    DIAGNOSED = "DIAGNOSED"
    REPAIR_PROMPT_CREATED = "REPAIR_PROMPT_CREATED"
    REPAIR_GENERATED = "REPAIR_GENERATED"
    AST_MERGED = "AST_MERGED"
    VALIDATING = "VALIDATING"
    REEXECUTING = "REEXECUTING"
    EVALUATING = "EVALUATING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TERMINATED = "TERMINATED"


class RepairOutcome(str, Enum):
    """Outcome classification after each repair attempt."""
    PASS = "PASS"
    SAME_ERROR = "SAME_ERROR"
    NEW_ERROR = "NEW_ERROR"
    REGRESSION = "REGRESSION"
    INVALID_REPAIR = "INVALID_REPAIR"
    OSCILLATION = "OSCILLATION"
    MAX_ITERATIONS = "MAX_ITERATIONS"


class TerminationReason(str, Enum):
    """Why the repair loop was stopped."""
    INITIAL_SUCCESS = "INITIAL_SUCCESS"
    PASS = "PASS"
    MAX_ITERATIONS = "MAX_ITERATIONS"
    OSCILLATION = "OSCILLATION"
    INVALID_REPAIR_EXHAUSTED = "INVALID_REPAIR_EXHAUSTED"
    ANALYSIS_FAILURE = "ANALYSIS_FAILURE"


# ---------------------------------------------------------------------------
# Objective 1 Adapter Model
# ---------------------------------------------------------------------------

@dataclass
class ErrorProfile:
    """
    Normalized Objective 1 output for a single execution attempt.

    Produced by the Objective1Loader adapter from either:
      - The Validation_Corpus.json (initial program)
      - A fresh execution during the repair loop
    """
    task_id: str
    trace_id: str
    benchmark: str                      # "HumanEval" | "MBPP"

    error_category: ErrorCategory = ErrorCategory.UNKNOWN
    execution_status: str = ""          # Raw status string

    # Execution evidence
    stdout: str = ""
    stderr: str = ""
    traceback: str = ""
    exception_type: str = ""
    exception_message: str = ""
    execution_time: float = 0.0
    timed_out: bool = False
    exit_code: int = 0

    # Test result
    tests_passed: Optional[bool] = None
    tests_failed: int = 0

    # Output comparison
    expected_output: Optional[str] = None
    actual_output: Optional[str] = None

    # Assertion details
    assertion_source: Optional[str] = None
    assertion_failed: bool = False

    # Raw parser prediction from Obj1
    parser_prediction: str = ""

    # Failure line extracted from traceback
    failure_line: Optional[int] = None

    def is_passing(self) -> bool:
        """Return True if this profile represents a passing execution."""
        return (
            self.error_category == ErrorCategory.CORRECT
            or self.tests_passed is True
            or (
                self.execution_status.lower() in ("passed", "correct", "success")
                and not self.assertion_failed
            )
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "trace_id": self.trace_id,
            "benchmark": self.benchmark,
            "error_category": self.error_category.value,
            "execution_status": self.execution_status,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "traceback": self.traceback,
            "exception_type": self.exception_type,
            "exception_message": self.exception_message,
            "execution_time": round(self.execution_time, 6),
            "timed_out": self.timed_out,
            "exit_code": self.exit_code,
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_failed,
            "expected_output": self.expected_output,
            "actual_output": self.actual_output,
            "assertion_source": self.assertion_source,
            "assertion_failed": self.assertion_failed,
            "parser_prediction": self.parser_prediction,
            "failure_line": self.failure_line,
        }


# ---------------------------------------------------------------------------
# Objective 2 Adapter Models
# ---------------------------------------------------------------------------

@dataclass
class FaultLocation:
    """
    Line-range fault localization produced by Objective 2.
    Used by the repair prompt builder to extract the faulty code block.
    """
    start_line: int
    end_line: int
    statement_code: str = ""
    function_name: str = ""
    causal_variable: str = ""
    file_name: str = ""
    evidence_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_line": self.start_line,
            "end_line": self.end_line,
            "statement_code": self.statement_code,
            "function_name": self.function_name,
            "causal_variable": self.causal_variable,
            "file_name": self.file_name,
            "evidence_score": self.evidence_score,
        }


@dataclass
class ConfidenceScore:
    """Structured confidence rating from Objective 2."""
    level: str = "LOW"          # "HIGH" | "MEDIUM" | "LOW"
    value: float = 0.0          # [0.0, 1.0]
    multi_node: bool = False    # True if boundary expansion occurred

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level,
            "value": round(self.value, 4),
            "multi_node": self.multi_node,
        }


@dataclass
class StructuredDiagnosticReport:
    """
    Objective 2 adapter output — the five mandatory methodology fields
    plus supporting information.

    Scientific invariant: diagnosis_status must faithfully reflect Obj2 output.
    UNRESOLVED must never be silently upgraded to VALIDATED.
    """
    # ── Five mandatory methodology fields ───────────────────────────────────
    error_category: ErrorCategory = ErrorCategory.UNKNOWN
    fault_location: Optional[FaultLocation] = None
    causal_explanation: str = ""
    repair_strategy: str = ""
    confidence: ConfidenceScore = field(default_factory=ConfidenceScore)

    # ── Diagnosis status (must not be fabricated) ────────────────────────────
    diagnosis_status: DiagnosisStatus = DiagnosisStatus.UNRESOLVED

    # ── Supporting Objective 2 fields ────────────────────────────────────────
    causal_node: Optional[str] = None
    causal_variable: Optional[str] = None
    observed_value: Optional[str] = None
    expected_value: Optional[str] = None
    counterfactual_validated: bool = False

    # Tracking
    task_id: str = ""
    trace_id: str = ""
    source: str = "OBJECTIVE2"     # "OBJECTIVE2" | "FRESH_DIAGNOSIS" | "INHERITED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "trace_id": self.trace_id,
            "error_category": self.error_category.value,
            "fault_location": self.fault_location.to_dict() if self.fault_location else None,
            "causal_explanation": self.causal_explanation,
            "repair_strategy": self.repair_strategy,
            "confidence": self.confidence.to_dict(),
            "diagnosis_status": self.diagnosis_status.value,
            "causal_node": self.causal_node,
            "causal_variable": self.causal_variable,
            "observed_value": self.observed_value,
            "expected_value": self.expected_value,
            "counterfactual_validated": self.counterfactual_validated,
            "source": self.source,
        }


# ---------------------------------------------------------------------------
# Task Specification
# ---------------------------------------------------------------------------

@dataclass
class BenchmarkTask:
    """
    A single benchmark task specification consumed by Objective 3.
    """
    trace_id: str
    task_id: str
    benchmark: str              # "HumanEval" | "MBPP"
    specification: str          # Natural language description + function signature
    entry_point: str            # Function name
    test_code: str              # Benchmark test harness
    test_imports: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "task_id": self.task_id,
            "benchmark": self.benchmark,
            "specification": self.specification,
            "entry_point": self.entry_point,
            "test_code": self.test_code,
            "test_imports": self.test_imports,
        }


# ---------------------------------------------------------------------------
# Error Signature
# ---------------------------------------------------------------------------

@dataclass
class ErrorSignature:
    """
    Deterministic fingerprint for a failed execution.
    Used for same-error and oscillation detection.
    Normalizes unstable information (addresses, timestamps) before hashing.
    """
    error_category: str
    fault_location_key: str     # "<start_line>-<end_line>" or "none"
    output_discrepancy: str     # Normalized output difference pattern

    # Computed fields
    raw_signature: str = field(init=False, default="")
    signature_hash: str = field(init=False, default="")

    def __post_init__(self) -> None:
        self.raw_signature = (
            f"{self.error_category}|{self.fault_location_key}|{self.output_discrepancy}"
        )
        self.signature_hash = hashlib.sha256(
            self.raw_signature.encode("utf-8")
        ).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_category": self.error_category,
            "fault_location_key": self.fault_location_key,
            "output_discrepancy": self.output_discrepancy,
            "raw_signature": self.raw_signature,
            "signature_hash": self.signature_hash,
        }

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ErrorSignature):
            return False
        return self.signature_hash == other.signature_hash

    def __hash__(self) -> int:
        return hash(self.signature_hash)


# ---------------------------------------------------------------------------
# AST Merge Record
# ---------------------------------------------------------------------------

@dataclass
class ASTMergeResult:
    """Records the outcome of an AST-based repair merge."""
    success: bool
    merged_code: str = ""
    boundary_expanded: bool = False
    uncertainty: str = "LOW"          # "LOW" | "HIGH"
    error_message: str = ""
    signature_preserved: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "boundary_expanded": self.boundary_expanded,
            "uncertainty": self.uncertainty,
            "error_message": self.error_message,
            "signature_preserved": self.signature_preserved,
        }


# ---------------------------------------------------------------------------
# Regression Record
# ---------------------------------------------------------------------------

@dataclass
class RegressionRecord:
    """Tracks test regressions introduced by a repair."""
    regression_detected: bool = False
    previously_passing_tests: List[str] = field(default_factory=list)
    currently_passing_tests: List[str] = field(default_factory=list)
    regressed_tests: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "regression_detected": self.regression_detected,
            "previously_passing_tests": self.previously_passing_tests,
            "currently_passing_tests": self.currently_passing_tests,
            "regressed_tests": self.regressed_tests,
        }


# ---------------------------------------------------------------------------
# Controller Decision
# ---------------------------------------------------------------------------

@dataclass
class ControllerDecision:
    """Output of the state-tracking controller after each repair evaluation."""
    outcome: RepairOutcome
    next_strategy: RepairStrategy = RepairStrategy.LOCAL_MODIFICATION
    escalated: bool = False
    oscillation_detected: bool = False
    terminate: bool = False
    termination_reason: Optional[TerminationReason] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "outcome": self.outcome.value,
            "next_strategy": self.next_strategy.value,
            "escalated": self.escalated,
            "oscillation_detected": self.oscillation_detected,
            "terminate": self.terminate,
            "termination_reason": (
                self.termination_reason.value if self.termination_reason else None
            ),
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# Repair Iteration Record
# ---------------------------------------------------------------------------

@dataclass
class RepairIteration:
    """
    Complete record for one repair cycle.
    Iteration 0 = initial generation and execution.
    Iteration 1–5 = repair attempts.
    """
    iteration: int
    source_code: str

    # Execution
    execution_result: Optional[ErrorProfile] = None
    error_signature: Optional[ErrorSignature] = None

    # Diagnosis (from Objective 2 adapter or fresh)
    diagnostic_report: Optional[StructuredDiagnosticReport] = None
    diagnosis_inherited: bool = False   # True if reusing old diagnosis

    # Repair (iterations 1+)
    repair_prompt: str = ""
    raw_llm_response: str = ""
    repaired_block: str = ""
    ast_merge_result: Optional[ASTMergeResult] = None
    repair_strategy_used: RepairStrategy = RepairStrategy.LOCAL_MODIFICATION

    # Regression
    regression: Optional[RegressionRecord] = None

    # Controller
    controller_decision: Optional[ControllerDecision] = None
    controller_state: ControllerState = ControllerState.INITIALIZED

    # Model metadata
    model_name: str = ""
    temperature: float = 0.0
    execution_duration: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "iteration": self.iteration,
            "source_code": self.source_code,
            "execution_result": (
                self.execution_result.to_dict() if self.execution_result else None
            ),
            "error_signature": (
                self.error_signature.to_dict() if self.error_signature else None
            ),
            "diagnostic_report": (
                self.diagnostic_report.to_dict() if self.diagnostic_report else None
            ),
            "diagnosis_inherited": self.diagnosis_inherited,
            "repair_prompt": self.repair_prompt,
            "raw_llm_response": self.raw_llm_response,
            "repaired_block": self.repaired_block,
            "ast_merge_result": (
                self.ast_merge_result.to_dict() if self.ast_merge_result else None
            ),
            "repair_strategy_used": self.repair_strategy_used.value,
            "regression": (
                self.regression.to_dict() if self.regression else None
            ),
            "controller_decision": (
                self.controller_decision.to_dict()
                if self.controller_decision
                else None
            ),
            "controller_state": self.controller_state.value,
            "model_name": self.model_name,
            "temperature": self.temperature,
            "execution_duration": round(self.execution_duration, 6),
        }


# ---------------------------------------------------------------------------
# Task Trajectory
# ---------------------------------------------------------------------------

@dataclass
class TaskTrajectory:
    """
    Complete repair trajectory for one benchmark task.
    Preserved in full for Objective 4 analysis.
    """
    task_id: str
    trace_id: str
    benchmark: str
    task: Optional[BenchmarkTask] = None

    iterations: List[RepairIteration] = field(default_factory=list)

    # Final result
    successful: bool = False
    final_status: str = "FAILED"
    initial_status: str = "UNKNOWN"
    termination_reason: Optional[TerminationReason] = None
    iterations_used: int = 0

    initial_error_category: str = ""
    final_error_category: Optional[str] = None

    regression_detected: bool = False
    oscillation_detected: bool = False

    diagnosis_status: str = DiagnosisStatus.UNRESOLVED.value

    # Task-level failure (pipeline exception)
    analysis_failure: bool = False
    failure_type: str = ""
    failure_message: str = ""
    stack_trace: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "trace_id": self.trace_id,
            "benchmark": self.benchmark,
            "task": self.task.to_dict() if self.task else None,
            "iterations": [it.to_dict() for it in self.iterations],
            "successful": self.successful,
            "final_status": self.final_status,
            "initial_status": self.initial_status,
            "termination_reason": (
                self.termination_reason.value if self.termination_reason else None
            ),
            "iterations_used": self.iterations_used,
            "initial_error_category": self.initial_error_category,
            "final_error_category": self.final_error_category,
            "regression_detected": self.regression_detected,
            "oscillation_detected": self.oscillation_detected,
            "diagnosis_status": self.diagnosis_status,
            "analysis_failure": self.analysis_failure,
            "failure_type": self.failure_type,
            "failure_message": self.failure_message,
            "stack_trace": self.stack_trace,
        }


# ---------------------------------------------------------------------------
# Final Task Result
# ---------------------------------------------------------------------------

@dataclass
class FinalTaskResult:
    """
    Compact final result per task — required raw data for Objective 4.
    """
    task_id: str
    trace_id: str
    benchmark: str

    successful: bool = False
    initial_status: str = "FAILED"
    final_status: str = "FAILED"
    termination_reason: Optional[str] = None
    iterations_used: int = 0

    initial_error_category: str = ""
    final_error_category: Optional[str] = None

    regression_detected: bool = False
    oscillation_detected: bool = False
    diagnosis_status: str = DiagnosisStatus.UNRESOLVED.value

    analysis_failure: bool = False

    # Objective 4 raw data fields
    repair_attempts: int = 0
    execution_attempts: int = 0
    same_error_stalls: int = 0
    new_error_transitions: int = 0
    escalations: int = 0
    strategy_at_termination: str = RepairStrategy.LOCAL_MODIFICATION.value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "trace_id": self.trace_id,
            "benchmark": self.benchmark,
            "successful": self.successful,
            "initial_status": self.initial_status,
            "final_status": self.final_status,
            "termination_reason": self.termination_reason,
            "iterations_used": self.iterations_used,
            "initial_error_category": self.initial_error_category,
            "final_error_category": self.final_error_category,
            "regression_detected": self.regression_detected,
            "oscillation_detected": self.oscillation_detected,
            "diagnosis_status": self.diagnosis_status,
            "analysis_failure": self.analysis_failure,
            "repair_attempts": self.repair_attempts,
            "execution_attempts": self.execution_attempts,
            "same_error_stalls": self.same_error_stalls,
            "new_error_transitions": self.new_error_transitions,
            "escalations": self.escalations,
            "strategy_at_termination": self.strategy_at_termination,
        }


# ---------------------------------------------------------------------------
# Run Summary (descriptive statistics only)
# ---------------------------------------------------------------------------

@dataclass
class RunSummary:
    """
    Descriptive system-operation statistics for one Objective 3 run.
    These are architecture metrics, NOT Objective 4 comparative results.
    """
    total_tasks: int = 0
    initially_passing: int = 0
    entered_repair: int = 0
    successfully_repaired: int = 0
    reached_max_iterations: int = 0
    same_error_stalls: int = 0
    new_error_transitions: int = 0
    regressions_detected: int = 0
    oscillations_detected: int = 0
    analysis_failures: int = 0

    mean_iterations: float = 0.0
    median_iterations: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tasks": self.total_tasks,
            "initially_passing": self.initially_passing,
            "entered_repair": self.entered_repair,
            "successfully_repaired": self.successfully_repaired,
            "reached_max_iterations": self.reached_max_iterations,
            "same_error_stalls": self.same_error_stalls,
            "new_error_transitions": self.new_error_transitions,
            "regressions_detected": self.regressions_detected,
            "oscillations_detected": self.oscillations_detected,
            "analysis_failures": self.analysis_failures,
            "mean_iterations": round(self.mean_iterations, 3),
            "median_iterations": self.median_iterations,
        }
