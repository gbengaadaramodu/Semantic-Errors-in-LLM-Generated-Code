"""
Objective 3 — Code Executor.

Wraps the sandbox to produce structured ErrorProfile results.
Classifies raw execution output into Objective 1 error categories
by re-running the Objective 1 classification logic on fresh executions.

This is used for iterative repair executions, not the initial corpus load.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from objective3.config import Obj3ExecutionConfig
from objective3.execution.sandbox import RawExecutionResult, Sandbox
from objective3.models import (
    BenchmarkTask,
    ErrorCategory,
    ErrorProfile,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Re-implemented Objective 1 classification rules
# (lightweight replication for fresh executions — does not duplicate Obj1 code)
# ---------------------------------------------------------------------------

def classify_execution(result: RawExecutionResult) -> ErrorCategory:
    """
    Classify a raw execution result into an error category.
    Follows the same logic as Objective 1's rule-based parser.
    """
    if result.timed_out:
        return ErrorCategory.TIMEOUT

    if result.returncode == 0 and not result.stderr.strip():
        return ErrorCategory.CORRECT

    stderr = result.stderr or ""
    combined = stderr + "\n" + (result.stdout or "")

    # Syntax Error
    if "SyntaxError" in combined or "IndentationError" in combined:
        return ErrorCategory.SYNTAX_ERROR

    # Timeout (sometimes returned as TimeoutError in stderr)
    if "TimeoutError" in combined or "time limit" in combined.lower():
        return ErrorCategory.TIMEOUT

    # Assertion Failure from benchmark tests
    if "AssertionError" in combined:
        # Check if assertion is from benchmark test vs generated code
        if "benchmark" in combined.lower() or "check(" in combined or "Test " in combined:
            return ErrorCategory.ASSERTION_FAILURE
        return ErrorCategory.ASSERTION_FAILURE

    # Runtime Exception
    runtime_exceptions = [
        "NameError", "TypeError", "ValueError", "AttributeError",
        "IndexError", "KeyError", "ZeroDivisionError", "RecursionError",
        "OverflowError", "RuntimeError", "StopIteration", "NotImplementedError",
        "ImportError", "ModuleNotFoundError", "FileNotFoundError",
        "IOError", "OSError", "MemoryError",
    ]
    for exc in runtime_exceptions:
        if exc in combined:
            return ErrorCategory.RUNTIME_EXCEPTION

    # Wrong Output (returncode != 0, stderr has assertion or output mismatch)
    if result.returncode != 0:
        return ErrorCategory.WRONG_OUTPUT

    return ErrorCategory.UNKNOWN


def extract_failure_line(traceback_text: str, code: str) -> Optional[int]:
    """
    Extract the line number of the failure from a traceback.
    Only returns lines within the generated code's range.
    """
    if not traceback_text:
        return None

    code_line_count = len(code.strip().splitlines()) if code else 0
    lines = traceback_text.strip().splitlines()

    for line in reversed(lines):
        match = re.search(r'File ".*?", line (\d+)', line)
        if match:
            lineno = int(match.group(1))
            if code_line_count > 0 and 1 <= lineno <= code_line_count:
                return lineno

    return None


class Executor:
    """
    Executes generated/repaired code and returns a structured ErrorProfile.
    """

    def __init__(self, config: Obj3ExecutionConfig) -> None:
        self.config = config
        self.sandbox = Sandbox(config)

    def execute(
        self,
        task: BenchmarkTask,
        source_code: str,
        timeout: Optional[float] = None,
    ) -> ErrorProfile:
        """
        Execute the source code with the task's test harness.

        Parameters
        ----------
        task        : Benchmark task providing test_code and entry_point.
        source_code : The Python source to execute.
        timeout     : Override execution timeout.

        Returns
        -------
        ErrorProfile representing the execution result.
        """
        logger.debug(
            "Executing code for task %s (dataset=%s).",
            task.trace_id,
            task.benchmark,
        )

        raw = self.sandbox.execute(
            source_code=source_code,
            test_code=task.test_code,
            test_imports=task.test_imports,
            entry_point=task.entry_point,
            dataset=task.benchmark,
            timeout=timeout,
        )

        error_cat = classify_execution(raw)
        failure_line = None
        if error_cat != ErrorCategory.CORRECT:
            failure_line = extract_failure_line(raw.stderr, source_code)

        tests_passed = (raw.returncode == 0 and not raw.timed_out)

        # Classify as correct if tests pass
        if tests_passed and error_cat == ErrorCategory.UNKNOWN:
            error_cat = ErrorCategory.CORRECT

        execution_status = "Passed" if tests_passed else "Failed"

        # Extract exception info from stderr
        exc_type, exc_msg = self._extract_exception(raw.stderr)

        logger.debug(
            "Execution complete: status=%s, category=%s, time=%.3fs.",
            execution_status,
            error_cat.value,
            raw.execution_time,
        )

        return ErrorProfile(
            task_id=task.task_id,
            trace_id=task.trace_id,
            benchmark=task.benchmark,
            error_category=error_cat,
            execution_status=execution_status,
            stdout=raw.stdout,
            stderr=raw.stderr,
            traceback=raw.stderr,  # stderr contains the traceback in Python
            exception_type=exc_type,
            exception_message=exc_msg,
            execution_time=raw.execution_time,
            timed_out=raw.timed_out,
            exit_code=raw.returncode,
            tests_passed=tests_passed,
            tests_failed=0 if tests_passed else 1,
            expected_output=None,
            actual_output=None,
            assertion_source=(
                "benchmark_test"
                if error_cat == ErrorCategory.ASSERTION_FAILURE
                else None
            ),
            assertion_failed=(error_cat == ErrorCategory.ASSERTION_FAILURE),
            parser_prediction=error_cat.value,
            failure_line=failure_line,
        )

    def _extract_exception(self, stderr: str) -> tuple[str, str]:
        """Extract exception type and message from stderr."""
        if not stderr:
            return "", ""

        lines = stderr.strip().splitlines()
        for line in reversed(lines):
            stripped = line.strip()
            if ":" in stripped and not stripped.startswith("File "):
                parts = stripped.split(":", 1)
                exc_type = parts[0].strip()
                exc_msg = parts[1].strip() if len(parts) > 1 else ""
                # Validate it looks like an exception class name
                if exc_type and exc_type[0].isupper() and " " not in exc_type:
                    return exc_type, exc_msg
        return "", ""
