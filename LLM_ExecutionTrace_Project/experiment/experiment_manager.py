"""
Orchestrates the entire LLM Execution Trace experiment pipeline.

Coordinates: TaskSelector → CodeGenerator → CodeExecutor →
RuleBasedParser → AnnotationWorkbook / exporters → experiment.json
"""

import csv
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional

from config import ProjectConfig
from models import Task, ExecutionResult
from ollama.client import OllamaClient
from ollama.prompt_builder import PromptBuilder
from ollama.generator import CodeGenerator
from executor.runner import CodeExecutor
from parser.classifier import RuleBasedParser
from exporter.excel_exporter import AnnotationWorkbook
from exporter.csv_exporter import CsvExporter
from exporter.json_exporter import JsonExporter
from experiment.configuration import TaskSelector
from experiment.reproducibility import ReproducibilityLogger

logger = logging.getLogger(__name__)


class ExperimentManager:
    """Manages the end-to-end experiment pipeline."""

    def __init__(self, config: Optional[ProjectConfig] = None):
        self.config = config or ProjectConfig()
        logger.info("ExperimentManager initialised.")

    # ──────────────────────────────────────────
    #  Task loading helpers
    # ──────────────────────────────────────────

    def load_selected_tasks(self) -> List[Task]:
        """
        Reconstruct the full Task objects from the saved selection CSVs
        and the original datasets.

        This is used when resuming from Stage 3 (execute) onwards so
        that we do not need to re-run selection or regenerate code.
        """
        logger.info("Loading previously selected tasks from disk …")

        selector = TaskSelector(self.config)
        he_ids, mb_ids = selector.load_selections()

        if not he_ids and not mb_ids:
            raise FileNotFoundError(
                "No saved task selections found in "
                f"'{self.config.paths.selected_tasks_dir}'. "
                "Please run 'python main.py select' first."
            )

        # Load full dataset rows
        all_he = selector.load_humaneval()
        all_mb = selector.load_mbpp()

        he_id_set = set(he_ids)
        mb_id_set = set(mb_ids)

        # Index HumanEval rows by task_id
        he_index: Dict[str, dict] = {row["task_id"]: row for row in all_he}
        # Index MBPP rows by str(task_id)
        mb_index: Dict[str, dict] = {str(row["task_id"]): row for row in all_mb}

        tasks: List[Task] = []

        # Rebuild HE tasks preserving original trace_id order (HE001…HE150)
        for i, task_id in enumerate(he_ids, 1):
            row = he_index.get(task_id)
            if row is None:
                logger.warning("HumanEval task_id '%s' not found in dataset; skipping.", task_id)
                continue
            tasks.append(Task(
                trace_id=f"HE{i:03d}",
                dataset="HumanEval",
                task_id=row["task_id"],
                prompt=row["prompt"],
                entry_point=row["entry_point"],
                test_code=row["test"],
                test_imports="",
                problem_summary=row["prompt"][:80],
            ))

        # Rebuild MBPP tasks preserving original trace_id order (MB001…MB150)
        import re
        for i, task_id in enumerate(mb_ids, 1):
            row = mb_index.get(task_id)
            if row is None:
                logger.warning("MBPP task_id '%s' not found in dataset; skipping.", task_id)
                continue
            code = row.get("code", "")
            match = re.search(r"def\s+(\w+)\s*\(", code)
            entry_point = match.group(1) if match else ""
            test_list = row.get("test_list", [])
            test_imports = row.get("test_imports", [])
            tasks.append(Task(
                trace_id=f"MB{i:03d}",
                dataset="MBPP",
                task_id=str(row["task_id"]),
                prompt=row["prompt"],
                entry_point=entry_point,
                test_code="\n".join(test_list),
                test_imports="\n".join(test_imports),
                problem_summary=row["prompt"][:80],
            ))

        logger.info(
            "Loaded %d tasks from saved selections (%d HE + %d MB).",
            len(tasks), len(he_ids), len(mb_ids),
        )
        return tasks

    def load_execution_results(self) -> List[ExecutionResult]:
        """
        Load all execution results from the execution_logs/ directory.

        Used when resuming from Stage 4 (classify) or Stage 5 (export).
        """
        executor = CodeExecutor(self.config)
        logs_dir = self.config.paths.execution_logs_dir

        json_files = sorted(logs_dir.glob("*.json"))
        if not json_files:
            raise FileNotFoundError(
                f"No execution logs found in '{logs_dir}'. "
                "Please run execution first."
            )

        results: List[ExecutionResult] = []
        for path in json_files:
            try:
                result = executor.load_execution_log(path.stem)
                results.append(result)
            except Exception as exc:
                logger.warning("Could not load log %s: %s", path.name, exc)

        logger.info("Loaded %d execution results from disk.", len(results))
        return results

    # ──────────────────────────────────────────
    #  Pipeline stages
    # ──────────────────────────────────────────

    def run_selection(self) -> List[Task]:
        """Step 1: Select 150 HE + 150 MBPP tasks."""
        logger.info("─── Stage 1: Task Selection ───")
        t0 = time.perf_counter()

        selector = TaskSelector(self.config)
        tasks = selector.select_tasks()
        selector.save_selections(tasks)

        logger.info("Task selection completed in %.2fs", time.perf_counter() - t0)
        return tasks

    def run_generation(self, tasks: List[Task]) -> List[Path]:
        """Step 2: Generate code via Ollama (Code Llama 13B)."""
        logger.info("─── Stage 2: Code Generation ───")
        t0 = time.perf_counter()

        client = OllamaClient(self.config.ollama)
        if not client.health_check():
            raise RuntimeError(
                "Ollama is not running. Please start Ollama and ensure "
                f"'{self.config.ollama.model_name}' is pulled."
            )

        prompt_builder = PromptBuilder(self.config.paths.prompts_dir)
        generator = CodeGenerator(
            client=client,
            prompt_builder=prompt_builder,
            output_dir=self.config.paths.generated_code_dir,
        )
        paths = generator.generate_all(tasks)

        logger.info("Code generation completed in %.2fs", time.perf_counter() - t0)
        return paths

    def run_execution(self, tasks: List[Task]) -> List[ExecutionResult]:
        """Step 3: Execute tests and capture runtime traces."""
        logger.info("─── Stage 3: Execution & Testing ───")
        t0 = time.perf_counter()

        executor = CodeExecutor(self.config)
        results = executor.execute_all(tasks)

        logger.info("Execution completed in %.2fs", time.perf_counter() - t0)
        return results

    def run_classification(self, results: List[ExecutionResult]) -> Dict[str, int]:
        """Step 4: Rule-based error classification."""
        logger.info("─── Stage 4: Classification ───")
        t0 = time.perf_counter()

        parser = RuleBasedParser()
        summary = parser.classify_all(results)

        logger.info("Classification summary: %s", summary)
        logger.info("Classification completed in %.2fs", time.perf_counter() - t0)
        return summary

    def run_export(self, results: List[ExecutionResult]) -> None:
        """Step 5: Generate annotation workbook and exports."""
        logger.info("─── Stage 5: Export ───")
        t0 = time.perf_counter()

        xlsx_path = self.config.paths.annotation_dir / "Validation_Corpus.xlsx"
        AnnotationWorkbook(xlsx_path).generate(results)

        csv_path = self.config.paths.annotation_dir / "Validation_Corpus.csv"
        CsvExporter(csv_path).export(results)

        json_path = self.config.paths.annotation_dir / "Validation_Corpus.json"
        JsonExporter(json_path).export(results)

        logger.info("Export completed in %.2fs", time.perf_counter() - t0)

    # ──────────────────────────────────────────
    #  Full pipeline
    # ──────────────────────────────────────────

    def run_all(self, from_stage: Optional[str] = None) -> None:
        """
        Run the complete pipeline end-to-end.

        Parameters
        ----------
        from_stage:
            When provided, earlier stages are skipped and their
            outputs are loaded from disk instead.  Allowed values:

                "execute"  — skip select + generate, load tasks from
                             selected_tasks/ CSVs, run from Stage 3.
                "classify" — skip select + generate + execute, load
                             execution results from execution_logs/.
                "export"   — skip everything up to export, load
                             execution results from execution_logs/.
        """
        logger.info("=" * 60)
        logger.info("  Starting Full Experiment Pipeline")
        if from_stage:
            logger.info("  Resuming from stage: %s", from_stage)
        logger.info("=" * 60)
        total_start = time.perf_counter()

        try:
            # ── Stage 1 & 2: Selection + Generation ──
            if from_stage in (None,):
                tasks = self.run_selection()
                self.run_generation(tasks)

            # ── Stage 3: Execution ────────────────────
            if from_stage in (None, "execute"):
                if from_stage == "execute":
                    tasks = self.load_selected_tasks()
                results = self.run_execution(tasks)

            # ── Stages 4 & 5: Classify + Export ──────
            elif from_stage in ("classify", "export"):
                results = self.load_execution_results()

            # ── Stage 4: Classification ───────────────
            summary = self.run_classification(results)

            # ── Stage 5: Export ───────────────────────
            self.run_export(results)

            # ── Save reproducibility metadata ─────────
            logger.info("─── Saving Experiment Metadata ───")
            repro = ReproducibilityLogger(self.config)
            # For resumed runs we may not have the original task list.
            # Reconstruct it from the execution results' task_id field.
            if from_stage in ("classify", "export"):
                tasks = self.load_selected_tasks()
            metadata = repro.collect_metadata(tasks, results, summary)
            meta_path = self.config.paths.project_root / "experiment.json"
            repro.save(metadata, meta_path)

            elapsed = time.perf_counter() - total_start
            logger.info("=" * 60)
            logger.info("  Pipeline completed successfully in %.2fs", elapsed)
            logger.info("=" * 60)

        except Exception:
            logger.exception("Experiment pipeline failed.")
            raise
