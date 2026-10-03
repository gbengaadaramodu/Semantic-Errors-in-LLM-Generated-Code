"""Top-level code executor — orchestrates test execution for all tasks."""

import json
import logging
from pathlib import Path
from typing import List

from models import Task, ExecutionResult, RuntimeEvidence
from config import ProjectConfig
from .sandbox import Sandbox
from .trace_capture import RuntimeCollector
from .test_runner import TestRunner

logger = logging.getLogger(__name__)


class CodeExecutor:
    """Executes generated code for every task and persists execution logs."""

    def __init__(self, config: ProjectConfig):
        self.config = config
        self.sandbox = Sandbox(
            timeout=config.execution.execution_timeout,
            python_executable=config.execution.python_executable,
        )
        self.collector = RuntimeCollector()
        self.test_runner = TestRunner(
            sandbox=self.sandbox,
            collector=self.collector,
            generated_code_dir=config.paths.generated_code_dir,
        )
        self.execution_logs_dir = config.paths.execution_logs_dir
        self.execution_logs_dir.mkdir(parents=True, exist_ok=True)

    # ──────────────────────────────────────────
    #  Bulk execution
    # ──────────────────────────────────────────

    def execute_all(self, tasks: List[Task]) -> List[ExecutionResult]:
        """Iterate over all tasks, run tests, save each result."""
        results: List[ExecutionResult] = []
        total = len(tasks)

        for idx, task in enumerate(tasks, 1):
            logger.info("Executing task %d/%d : %s (%s)", idx, total, task.trace_id, task.task_id)
            try:
                result = self.test_runner.run_test(task)
            except Exception as exc:
                logger.error("Unhandled error executing %s: %s", task.trace_id, exc)
                result = ExecutionResult(
                    trace_id=task.trace_id,
                    dataset=task.dataset,
                    task_id=task.task_id,
                    problem_summary=task.problem_summary,
                    execution_status="Failed",
                    evidence=RuntimeEvidence(
                        stderr=str(exc),
                        exception_type=type(exc).__name__,
                        exception_message=str(exc),
                        exit_code=-1,
                    ),
                )
            self.save_execution_log(result)
            results.append(result)

        self.print_summary(results)
        return results

    # ──────────────────────────────────────────
    #  Persistence
    # ──────────────────────────────────────────

    def save_execution_log(self, result: ExecutionResult) -> Path:
        """Write result.to_dict() as JSON to execution_logs/{trace_id}.json."""
        log_path = self.execution_logs_dir / f"{result.trace_id}.json"
        try:
            with open(log_path, "w", encoding="utf-8") as fh:
                json.dump(result.to_dict(), fh, indent=2, default=str)
            logger.debug("Saved execution log → %s", log_path)
        except Exception as exc:
            logger.error("Failed to save execution log for %s: %s", result.trace_id, exc)
        return log_path

    def load_execution_log(self, trace_id: str) -> ExecutionResult:
        """Read JSON and reconstruct an ExecutionResult."""
        log_path = self.execution_logs_dir / f"{trace_id}.json"
        with open(log_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        # Separate evidence fields from top-level fields
        evidence_keys = {
            "stdout", "stderr", "traceback", "exception_type",
            "exception_message", "execution_time", "timed_out", "exit_code",
        }
        evidence_data = {k: data.pop(k) for k in list(data.keys()) if k in evidence_keys}
        evidence = RuntimeEvidence(**evidence_data)

        return ExecutionResult(
            trace_id=data["trace_id"],
            dataset=data["dataset"],
            task_id=data["task_id"],
            problem_summary=data.get("problem_summary", ""),
            execution_status=data["execution_status"],
            evidence=evidence,
            parser_prediction=data.get("parser_prediction", ""),
        )

    # ──────────────────────────────────────────
    #  Summary
    # ──────────────────────────────────────────

    def print_summary(self, results: List[ExecutionResult]) -> None:
        """Log execution outcome counts."""
        completed = sum(1 for r in results if r.execution_status == "Completed")
        failed    = sum(1 for r in results if r.execution_status == "Failed")
        timed_out = sum(1 for r in results if r.execution_status == "Timeout")

        logger.info("=" * 40)
        logger.info("  Execution Summary")
        logger.info("  Total Tasks  : %d", len(results))
        logger.info("  Completed    : %d", completed)
        logger.info("  Failed       : %d", failed)
        logger.info("  Timed Out    : %d", timed_out)
        logger.info("=" * 40)
