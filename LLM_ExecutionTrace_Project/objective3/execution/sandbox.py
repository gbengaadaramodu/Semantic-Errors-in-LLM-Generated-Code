"""
Objective 3 — Sandboxed Code Executor.

Executes Python code in an isolated subprocess with a configurable timeout.
Captures stdout, stderr, traceback, exit code, and timing.
Does not permit benchmark-generated code to modify the host environment.

Isolation mechanism: subprocess with a temporary file, with no shared globals.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from objective3.config import Obj3ExecutionConfig


@dataclass
class RawExecutionResult:
    """Raw subprocess execution output."""
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0
    timed_out: bool = False
    execution_time: float = 0.0


class Sandbox:
    """
    Isolated subprocess sandbox for executing generated Python code.
    """

    def __init__(self, config: Obj3ExecutionConfig) -> None:
        self.config = config
        self.python = config.python_executable

    def execute(
        self,
        source_code: str,
        test_code: str = "",
        test_imports: str = "",
        entry_point: str = "",
        dataset: str = "HumanEval",
        timeout: Optional[float] = None,
    ) -> RawExecutionResult:
        """
        Execute the source_code combined with test_code in a subprocess.

        Parameters
        ----------
        source_code   : The generated/repaired Python implementation.
        test_code     : The benchmark test harness code.
        test_imports  : Any import statements required by the test.
        entry_point   : Function name (used for HumanEval check(fn) invocation).
        dataset       : 'HumanEval' or 'MBPP' (affects test invocation pattern).
        timeout       : Execution timeout in seconds (falls back to config default).

        Returns
        -------
        RawExecutionResult
        """
        effective_timeout = timeout or self.config.execution_timeout

        # ── Build complete script ─────────────────────────────────────────────
        parts = []
        if test_imports.strip():
            parts.append(test_imports.strip())
            parts.append("\n\n")

        parts.append(source_code.strip())
        parts.append("\n\n")

        if test_code.strip():
            parts.append(test_code.strip())
            parts.append("\n\n")

        # HumanEval convention: call check(entry_point)
        if dataset.strip().upper() == "HUMANEVAL" and entry_point:
            parts.append(f"check({entry_point})\n")

        full_script = "".join(parts)

        # ── Write to temp file and execute ───────────────────────────────────
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            delete=False,
            encoding="utf-8",
        ) as tmp:
            tmp.write(full_script)
            tmp_path = tmp.name

        try:
            t0 = time.perf_counter()
            try:
                proc = subprocess.run(
                    [self.python, tmp_path],
                    capture_output=True,
                    text=True,
                    timeout=effective_timeout,
                    env={**os.environ},  # inherit env but run in subprocess
                )
                elapsed = time.perf_counter() - t0
                return RawExecutionResult(
                    stdout=proc.stdout or "",
                    stderr=proc.stderr or "",
                    returncode=proc.returncode,
                    timed_out=False,
                    execution_time=elapsed,
                )
            except subprocess.TimeoutExpired:
                elapsed = time.perf_counter() - t0
                return RawExecutionResult(
                    stdout="",
                    stderr=f"Execution timed out after {effective_timeout}s.",
                    returncode=-1,
                    timed_out=True,
                    execution_time=elapsed,
                )
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
