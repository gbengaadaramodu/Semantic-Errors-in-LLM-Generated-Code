"""
Objective 3 — Test Runner.

Provides granular per-test execution results for regression detection.
Runs test cases individually to identify which specific tests pass/fail.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Tuple

from objective3.config import Obj3ExecutionConfig
from objective3.execution.sandbox import Sandbox
from objective3.models import BenchmarkTask

logger = logging.getLogger(__name__)


class TestRunner:
    """
    Runs individual test cases to support regression detection.
    """

    def __init__(self, config: Obj3ExecutionConfig) -> None:
        self.config = config
        self.sandbox = Sandbox(config)

    def run_tests(
        self,
        task: BenchmarkTask,
        source_code: str,
    ) -> Dict[str, bool]:
        """
        Run all tests and return a dict mapping test_id → passed.

        For regression detection, we identify individual assertion lines
        and run them in isolation where possible.

        For benchmarks with a unified check() function, we run the complete
        test harness and report a single 'ALL_TESTS' result.

        Parameters
        ----------
        task        : Benchmark task.
        source_code : Python source to test.

        Returns
        -------
        Dict[str, bool]: test_id → True/False
        """
        # Extract individual assertions from test code
        individual_tests = self._extract_individual_assertions(task)

        if len(individual_tests) <= 1:
            # Run as a single block
            result = self.sandbox.execute(
                source_code=source_code,
                test_code=task.test_code,
                test_imports=task.test_imports,
                entry_point=task.entry_point,
                dataset=task.benchmark,
            )
            return {"ALL_TESTS": result.returncode == 0}

        # Run each assertion individually
        results: Dict[str, bool] = {}
        for test_id, test_snippet in individual_tests.items():
            result = self.sandbox.execute(
                source_code=source_code,
                test_code=test_snippet,
                test_imports=task.test_imports,
                entry_point=task.entry_point,
                dataset="NONE",  # Don't add check() call for isolated tests
            )
            results[test_id] = (result.returncode == 0)

        return results

    def _extract_individual_assertions(
        self, task: BenchmarkTask
    ) -> Dict[str, str]:
        """
        Extract individual assert statements from the test code.
        Returns dict mapping 'assert_N' → assertion snippet.
        """
        if not task.test_code:
            return {}

        # For MBPP, test_list items are individual tests
        lines = task.test_code.strip().splitlines()
        assertions = {}
        count = 0
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("assert "):
                count += 1
                # Wrap in a minimal runnable snippet
                assertions[f"assert_{count}"] = stripped

        if not assertions:
            return {"ALL_TESTS": task.test_code}

        return assertions

    def get_passing_test_ids(
        self,
        task: BenchmarkTask,
        source_code: str,
    ) -> List[str]:
        """Return list of test IDs that pass with the given source code."""
        results = self.run_tests(task, source_code)
        return [tid for tid, passed in results.items() if passed]
