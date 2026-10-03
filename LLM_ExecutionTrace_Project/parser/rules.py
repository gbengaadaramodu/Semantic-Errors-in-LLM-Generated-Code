"""
Individual rule classes for the rule-based execution-trace classifier.

Each rule evaluates structured RuntimeEvidence and returns True when
the evidence satisfies the operational definition of its category.
"""

from models import ErrorCategory, RuntimeEvidence


class TimeoutRule:
    """Matches executions that exceeded the configured time limit."""

    @property
    def category(self) -> ErrorCategory:
        return ErrorCategory.TIMEOUT

    def matches(self, evidence: RuntimeEvidence) -> bool:
        return evidence.timed_out is True


class SyntaxErrorRule:
    """
    Matches Python syntax-related errors.

    These errors occur before normal program execution begins.
    """

    SYNTAX_ERRORS = {
        "SyntaxError",
        "IndentationError",
        "TabError",
    }

    @property
    def category(self) -> ErrorCategory:
        return ErrorCategory.SYNTAX_ERROR

    def matches(self, evidence: RuntimeEvidence) -> bool:
        return evidence.exception_type in self.SYNTAX_ERRORS


class RuntimeExceptionRule:
    """
    Matches uncaught runtime exceptions.

    Syntax-related errors and AssertionError are handled by
    separate rules and are therefore excluded here.
    """

    KNOWN_RUNTIME_EXCEPTIONS = {
        "TypeError",
        "ValueError",
        "NameError",
        "IndexError",
        "KeyError",
        "AttributeError",
        "ZeroDivisionError",
        "ImportError",
        "ModuleNotFoundError",
        "FileNotFoundError",
        "OSError",
        "RecursionError",
        "MemoryError",
        "OverflowError",
        "StopIteration",
        "UnboundLocalError",
    }

    EXCLUDED_EXCEPTIONS = {
        "SyntaxError",
        "IndentationError",
        "TabError",
        "AssertionError",
    }

    @property
    def category(self) -> ErrorCategory:
        return ErrorCategory.RUNTIME_EXCEPTION

    def matches(self, evidence: RuntimeEvidence) -> bool:

        exception_type = evidence.exception_type

        if not exception_type:
            return False

        if exception_type in self.EXCLUDED_EXCEPTIONS:
            return False

        if exception_type in self.KNOWN_RUNTIME_EXCEPTIONS:
            return True

        # Catch other Python Error/Exception classes that were not
        # explicitly enumerated above.
        if (
            exception_type.endswith("Error")
            or exception_type.endswith("Exception")
        ):
            return True

        return False


class WrongOutputRule:
    """
    Matches cases where the generated function ran but returned an
    incorrect value, detected by the benchmark test harness.

    The only reliable signal is when the test runner has determined
    that the AssertionError originated from the benchmark harness
    (``assertion_source == "benchmark_test"``).

    Failed executions with no detectable Python exception are NOT
    automatically classified as Wrong-Output Error, because a
    non-zero exit without a traceback does not constitute evidence
    that the function produced an incorrect value.
    """

    @property
    def category(self) -> ErrorCategory:
        return ErrorCategory.WRONG_OUTPUT

    def matches(self, evidence: RuntimeEvidence) -> bool:

        if evidence.timed_out:
            return False

        if evidence.tests_passed is not False:
            return False

        # Benchmark harness caught a wrong return value via assert.
        return evidence.assertion_source == "benchmark_test"


class AssertionFailureRule:
    """
    Matches assertion failures where the LLM's generated code itself
    contains an ``assert`` statement that fires at runtime.

    This is distinct from Wrong-Output Error, where the benchmark
    harness fires an assertion to detect an incorrect return value.
    """

    @property
    def category(self) -> ErrorCategory:
        return ErrorCategory.ASSERTION_FAILURE

    def matches(self, evidence: RuntimeEvidence) -> bool:

        if evidence.exception_type != "AssertionError":
            return False

        # Only Assertion Failure when the assert came from inside
        # the generated function, not from the benchmark harness.
        return evidence.assertion_source == "generated_code"


class CorrectRule:
    """
    Matches executions for which all benchmark tests passed.
    """

    @property
    def category(self) -> ErrorCategory:
        return ErrorCategory.CORRECT

    def matches(self, evidence: RuntimeEvidence) -> bool:

        return (
            evidence.timed_out is False
            and evidence.tests_passed is True
            and evidence.exit_code == 0
        )

