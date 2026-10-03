"""
Runtime evidence collection module.

Converts raw SandboxResult information into structured
RuntimeEvidence used by the rule-based classifier.
"""

import logging
import re
from typing import Optional, Tuple

from models import RuntimeEvidence, SandboxResult

logger = logging.getLogger(__name__)


class RuntimeCollector:
    """
    Extracts structured runtime evidence from sandbox execution results.

    This class focuses on low-level runtime information such as
    stdout, stderr, traceback, exception type, timeout and execution time.

    Test-specific interpretation should be performed by a separate
    test-outcome analysis component.
    """

    EXCEPTION_PATTERN = re.compile(
        r"^([A-Za-z_][A-Za-z0-9_]*(?:Error|Exception|Warning))"
        r"(?:\s*:\s*(.*))?$"
    )

    def collect(
        self,
        sandbox_result: SandboxResult,
    ) -> RuntimeEvidence:
        """
        Convert a SandboxResult into RuntimeEvidence.
        """

        stderr = sandbox_result.stderr or ""

        traceback_text = self._extract_traceback(stderr)

        exception_type, exception_message = (
            self._extract_exception(stderr)
        )

        return RuntimeEvidence(
            stdout=sandbox_result.stdout or "",
            stderr=stderr,
            traceback=traceback_text,
            exception_type=exception_type,
            exception_message=exception_message,
            execution_time=sandbox_result.execution_time,
            timed_out=sandbox_result.timed_out,
            exit_code=sandbox_result.returncode,
        )

    @staticmethod
    def _extract_traceback(stderr: str) -> str:
        """
        Extract the traceback block from stderr.

        Standard Python tracebacks begin with:

            Traceback (most recent call last):

        Syntax-related errors may not always contain a standard
        traceback block, so the complete stderr is returned when
        a syntax-related exception is detected.
        """

        if not stderr:
            return ""

        marker = "Traceback (most recent call last):"

        index = stderr.rfind(marker)

        if index != -1:
            return stderr[index:].strip()

        syntax_markers = (
            "SyntaxError:",
            "IndentationError:",
            "TabError:",
        )

        if any(marker in stderr for marker in syntax_markers):
            return stderr.strip()

        return ""

    @classmethod
    def _extract_exception(
        cls,
        stderr: str,
    ) -> Tuple[str, str]:
        """
        Extract the final Python exception type and message.

        Returns:

            (exception_type, exception_message)

        Example:

            ("TypeError", "unsupported operand type(s)")
        """

        if not stderr:
            return "", ""

        lines = stderr.strip().splitlines()

        for line in reversed(lines):

            line = line.strip()

            match = cls.EXCEPTION_PATTERN.match(line)

            if not match:
                continue

            exception_type = match.group(1)

            exception_message = (
                match.group(2) or ""
            ).strip()

            return exception_type, exception_message

        return "", ""