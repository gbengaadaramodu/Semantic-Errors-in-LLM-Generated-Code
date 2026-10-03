"""
Safe Counterfactual Executor Module.

Executes modified counterfactual programs in an isolated process sandbox without
modifying original source files.
"""

import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple

from objective2.config import ExecutionConfig
from objective2.models import Objective2InputRecord

logger = logging.getLogger(__name__)


class SafeCounterfactualExecutor:
    """
    Safely runs intervened counterfactual code against benchmark test suites.
    """

    def __init__(self, config: ExecutionConfig) -> None:
        self.config = config

    def _extract_failing_assert(self, traceback_str: Optional[str]) -> Optional[str]:
        if not traceback_str: return None
        for line in traceback_str.splitlines():
            line = line.strip()
            if line.startswith("assert "):
                # Strip trailing comments or message tuples if necessary, but raw string is usually fine
                return line
        return None

    def execute_intervened(
        self,
        record: Objective2InputRecord,
        intervened_code: str,
    ) -> Tuple[str, str, str]:
        """
        Executes intervened code with test suite in a subprocess.
        Returns: (outcome: "Completed"/"Failed"/"Timeout", stdout: str, stderr: str)
        """
        parts = []
        dataset = record.dataset.strip().upper()
        
        # Single-Trace Isolation: Extract only the specific failing assertion
        failing_assert = self._extract_failing_assert(record.traceback)

        if dataset == "MBPP":
            if record.test_imports:
                parts.append(record.test_imports)
                parts.append("\n\n")
            parts.append(intervened_code)
            parts.append("\n\n")
            if failing_assert:
                parts.append(failing_assert)
            else:
                parts.append(record.test_code)
            parts.append("\n")
        else: # HumanEval
            parts.append(intervened_code)
            parts.append("\n\n")
            if failing_assert:
                # HumanEval assertions use 'candidate' as the function name alias inside check()
                if record.entry_point:
                    failing_assert = failing_assert.replace("candidate", record.entry_point)
                parts.append(failing_assert)
            else:
                parts.append(record.test_code)
                if record.entry_point:
                    parts.append(f"\ncheck({record.entry_point})\n")

        full_script = "".join(parts)

        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "counterfactual_script.py"
            script_path.write_text(full_script, encoding="utf-8")

            try:
                proc = subprocess.run(
                    [self.config.python_executable, str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=self.config.counterfactual_timeout,
                )
                if proc.returncode == 0:
                    return "Completed", proc.stdout, proc.stderr
                else:
                    return "Failed", proc.stdout, proc.stderr
            except subprocess.TimeoutExpired:
                return "Timeout", "", "Execution timed out"
            except Exception as exc:
                return "Failed", "", str(exc)
