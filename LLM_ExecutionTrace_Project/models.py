"""
LLM Execution Trace Project — Shared Data Models

Canonical data structures used across the execution-trace pipeline.

The experiment uses five error categories:

    1. Syntax Error
    2. Runtime Exception
    3. Wrong-Output Error
    4. Assertion Failure
    5. Timeout Error

"Correct" is treated as a successful execution outcome rather than
an error category.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class ErrorCategory(Enum):
    """
    Classification outcomes produced by the rule-based parser.

    Five values represent error categories; CORRECT represents
    successful execution.
    """

    CORRECT = "Correct"
    SYNTAX_ERROR = "Syntax Error"
    RUNTIME_EXCEPTION = "Runtime Exception"
    WRONG_OUTPUT = "Wrong-Output Error"
    ASSERTION_FAILURE = "Assertion Failure"
    TIMEOUT = "Timeout Error"


@dataclass
class Task:
    """
    Unified representation of a HumanEval or MBPP task.
    """

    trace_id: str
    dataset: str
    task_id: str

    prompt: str
    entry_point: str

    test_code: str
    test_imports: str = ""

    problem_summary: str = ""


@dataclass
class SandboxResult:
    """
    Raw result returned by the sandbox/subprocess executor.
    """

    stdout: str = ""
    stderr: str = ""
    returncode: int = 0
    timed_out: bool = False
    execution_time: float = 0.0


@dataclass
class RuntimeEvidence:
    """
    Structured evidence collected from execution.

    The first group of fields represents raw runtime evidence.

    The second group represents benchmark-test evidence and is used
    to distinguish wrong-output errors from genuine assertion failures.
    """

    # ---------------------------------------------------------
    # Raw runtime evidence
    # ---------------------------------------------------------

    stdout: str = ""
    stderr: str = ""
    traceback: str = ""

    exception_type: str = ""
    exception_message: str = ""

    execution_time: float = 0.0
    timed_out: bool = False
    exit_code: int = 0

    # ---------------------------------------------------------
    # Test-result evidence
    # ---------------------------------------------------------

    tests_passed: Optional[bool] = None
    tests_failed: int = 0

    # ---------------------------------------------------------
    # Output comparison
    # ---------------------------------------------------------

    expected_output: Optional[str] = None
    actual_output: Optional[str] = None

    # ---------------------------------------------------------
    # Assertion origin
    #
    # Possible values:
    #   "generated_code"
    #   "benchmark_test"
    #   None
    # ---------------------------------------------------------

    assertion_source: Optional[str] = None

    # ---------------------------------------------------------
    # Additional diagnostic information
    # ---------------------------------------------------------

    assertion_failed: bool = False

    def to_dict(self) -> dict:
        """
        Serialize runtime evidence into a JSON/Excel-friendly dictionary.
        """

        return {
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
        }


@dataclass
class ExecutionResult:
    """
    Complete execution record for one benchmark task.

    Combines task metadata, runtime evidence, and the prediction
    produced by the rule-based parser.
    """

    trace_id: str
    dataset: str
    task_id: str
    problem_summary: str

    execution_status: str

    evidence: RuntimeEvidence = field(
        default_factory=RuntimeEvidence
    )

    parser_prediction: str = ""

    def to_dict(self) -> dict:
        """
        Serialize the complete execution result.
        """

        return {
            "trace_id": self.trace_id,
            "dataset": self.dataset,
            "task_id": self.task_id,
            "problem_summary": self.problem_summary,
            "execution_status": self.execution_status,

            **self.evidence.to_dict(),

            "parser_prediction": self.parser_prediction,
        }