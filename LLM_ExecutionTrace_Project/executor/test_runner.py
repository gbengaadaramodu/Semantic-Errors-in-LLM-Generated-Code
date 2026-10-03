"""
Module for constructing and executing HumanEval and MBPP test scripts.
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

from models import ExecutionResult, Task
from .sandbox import Sandbox
from .trace_capture import RuntimeCollector

logger = logging.getLogger(__name__)


class TestRunner:
    """
    Constructs benchmark test scripts, executes them in the sandbox,
    and collects structured runtime evidence.
    """

    def __init__(
        self,
        sandbox: Sandbox,
        collector: RuntimeCollector,
        generated_code_dir: Path,
    ) -> None:

        self.sandbox = sandbox
        self.collector = collector
        self.generated_code_dir = Path(generated_code_dir)

    # ---------------------------------------------------------
    # Script construction
    # ---------------------------------------------------------

    def build_test_script(
        self,
        task: Task,
        generated_code_path: Path,
    ) -> str:
        """
        Construct a self-contained test script.

        HumanEval:

            generated code
            test/check function
            check(entry_point)

        MBPP:

            test imports
            generated code
            benchmark tests
        """

        try:
            generated_code = generated_code_path.read_text(
                encoding="utf-8"
            )
        except (OSError, UnicodeDecodeError) as exc:

            logger.error(
                "Unable to read generated code from %s: %s",
                generated_code_path,
                exc,
            )

            generated_code = ""

        parts: list[str] = []

        dataset = task.dataset.strip().upper()

        if dataset == "MBPP":

            if task.test_imports:
                parts.append(task.test_imports)
                parts.append("\n\n")

            parts.append(generated_code)
            parts.append("\n\n")

            parts.append(task.test_code)
            parts.append("\n")

        elif dataset == "HUMANEVAL":

            parts.append(generated_code)
            parts.append("\n\n")

            parts.append(task.test_code)
            parts.append("\n")

            if task.entry_point:
                parts.append(
                    f"\ncheck({task.entry_point})\n"
                )

        else:

            raise ValueError(
                f"Unsupported dataset: {task.dataset}"
            )

        return "".join(parts)

    # ---------------------------------------------------------
    # Execution
    # ---------------------------------------------------------

    def run_test(
        self,
        task: Task,
    ) -> ExecutionResult:
        """
        Build and execute the benchmark test script.

        Runtime evidence is collected from the sandbox. Test-level
        interpretation should be performed after collection.
        """

        generated_code_path = (
            self.generated_code_dir
            / f"{task.trace_id}.py"
        )

        # Read generated code so we can inspect it for internal asserts.
        try:
            generated_code = generated_code_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            generated_code = ""

        test_script = self.build_test_script(
            task,
            generated_code_path,
        )

        temp_path: Optional[Path] = None

        try:

            with tempfile.NamedTemporaryFile(
                suffix=".py",
                delete=False,
                mode="w",
                encoding="utf-8",
            ) as tmp:

                tmp.write(test_script)

                temp_path = Path(tmp.name)

            sandbox_result = self.sandbox.execute(
                temp_path
            )

            evidence = self.collector.collect(
                sandbox_result
            )

            # Derive test-level fields from raw sandbox result.
            # tests_passed = True  → all benchmark tests passed (exit 0, no timeout)
            # tests_passed = False → process exited with an error
            if evidence.timed_out:
                execution_status = "Timeout"
                evidence.tests_passed = False

            elif evidence.exit_code == 0:
                execution_status = "Completed"
                evidence.tests_passed = True

            else:
                execution_status = "Failed"
                evidence.tests_passed = False

            # Determine the origin of any AssertionError so the
            # classifier can distinguish Wrong-Output Error from
            # Assertion Failure.
            if evidence.exception_type == "AssertionError":
                evidence.assertion_failed = True
                evidence.assertion_source = self._determine_assertion_source(
                    task, evidence.traceback, generated_code
                )

            return ExecutionResult(
                trace_id=task.trace_id,
                dataset=task.dataset,
                task_id=task.task_id,
                problem_summary=task.problem_summary,
                execution_status=execution_status,
                evidence=evidence,
            )

        finally:

            if temp_path is not None:

                try:
                    temp_path.unlink(
                        missing_ok=True
                    )

                except OSError as exc:

                    logger.warning(
                        "Failed to remove temporary file %s: %s",
                        temp_path,
                        exc,
                    )

    # ---------------------------------------------------------
    # Assertion source detection
    # ---------------------------------------------------------

    def _determine_assertion_source(
            self,
            task: Task,
            traceback_text: str,
            generated_code: str,
        ) -> str:
            """
            Determine whether an AssertionError came from the benchmark
            test harness or from an ``assert`` statement inside the
            generated function body.
            """
            if not traceback_text:
                return "benchmark_test"

            # 1. Isolate the innermost frame (the exact point of failure)
            # Python tracebacks print the most recent call last.
            lines = traceback_text.strip().splitlines()
            last_frame = ""
            for line in reversed(lines):
                # Python stack frames start with 'File' and contain 'in <function_name>'
                if line.strip().startswith("File "):
                    last_frame = line
                    break

            dataset = task.dataset.strip().upper()
            
            # 2. Confirm if the generated AST even contains an assert
            has_internal_assert = self._code_contains_assert(generated_code)

            if dataset == "HUMANEVAL":
                # If the LAST frame is the check() function, the harness failed.
                if "in check" in last_frame:
                    return "benchmark_test"
                
                # If the LAST frame is the entry point OR a helper function, 
                # and the AST contains an assert, it is an internal failure.
                if has_internal_assert:
                    return "generated_code"
                    
                return "benchmark_test"

            elif dataset == "MBPP":
                # MBPP benchmark asserts are top-level, meaning their final 
                # frame will always be <module>.
                if "in <module>" in last_frame:
                    return "benchmark_test"
                
                # If the final frame is inside a function (entry point or helper),
                # and the AST contains an assert, it is an internal failure.
                if has_internal_assert:
                    return "generated_code"
                    
                return "benchmark_test"

            return "benchmark_test"

    @staticmethod
    def _code_contains_assert(source_code: str) -> bool:
        """
        Check whether ``source_code`` contains an actual Python
        ``assert`` statement using AST parsing.

        This avoids false positives from the word 'assert' appearing
        inside comments or string literals.
        """
        import ast

        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            # If the code cannot be parsed, we cannot confirm
            # the presence of an assert statement.
            return False

        return any(
            isinstance(node, ast.Assert)
            for node in ast.walk(tree)
        )