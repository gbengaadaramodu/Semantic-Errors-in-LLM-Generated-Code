"""
Objective 3 — Main Execution Script.

Runs the integrated closed-loop self-correction architecture.
Coordinates the loaders, controllers, engines, and exporters.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List

from objective3.config import Objective3Config
from objective3.controller.controller import RepairController
from objective3.evaluation.trajectory_metrics import TrajectoryMetrics
from objective3.exporter.csv_exporter import CsvExporter
from objective3.exporter.excel_exporter import ExcelExporter
from objective3.exporter.json_exporter import JsonExporter
from objective3.input.benchmark_loader import BenchmarkLoader
from objective3.input.objective1_loader import Objective1Loader
from objective3.input.objective2_loader import Objective2Loader
from objective3.models import TaskTrajectory
from objective3.repair.repair_engine import RepairEngine

logger = logging.getLogger(__name__)


def setup_logging(level: str) -> None:
    """Configure console logging."""
    num_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=num_level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def run_objective3(config: Objective3Config, task_limit: int = 0) -> None:
    """Run the main Objective 3 pipeline."""
    setup_logging(config.log_level)
    logger.info("Starting Objective 3 Pipeline")
    logger.info("Output directory: %s", config.paths.output_dir)

    # 1. Initialize loaders
    obj1_loader = Objective1Loader(config)
    obj2_loader = Objective2Loader(config)
    benchmark_loader = BenchmarkLoader(config)

    # 2. Get target tasks
    # Objective 3 repairs tasks that failed initially (ErrorCategory != CORRECT)
    failed_profiles = obj1_loader.load_failed_tasks()
    logger.info("Loaded %d failed tasks from Objective 1 corpus.", len(failed_profiles))

    if task_limit > 0:
        failed_profiles = failed_profiles[:task_limit]
        logger.info("Applying task limit. Processing %d tasks.", len(failed_profiles))

    # 3. Initialize engine and controller
    repair_engine = RepairEngine(config)
    controller = RepairController(config, repair_engine, obj2_loader)

    # 4. Main loop
    trajectories: List[TaskTrajectory] = []

    for idx, profile in enumerate(failed_profiles, 1):
        logger.info("Processing task %d/%d: %s", idx, len(failed_profiles), profile.trace_id)
        
        task = benchmark_loader.load_task(profile.trace_id)
        if not task:
            logger.error("Skipping %s: could not load benchmark task.", profile.trace_id)
            continue

        # Load initial source code (Mode A: from disk)
        code_path = config.paths.generated_code_dir / f"{profile.trace_id}.py"
        if not code_path.exists():
            logger.error("Skipping %s: initial generated code not found at %s", profile.trace_id, code_path)
            continue

        initial_source = code_path.read_text(encoding="utf-8")

        # Run closed-loop repair
        trajectory = controller.run_task(task, initial_source)
        trajectories.append(trajectory)

        # Save repaired code if successful
        if trajectory.successful:
            last_valid = [it for it in trajectory.iterations if it.ast_merge_result and it.ast_merge_result.success]
            if last_valid:
                final_code = last_valid[-1].source_code
                out_path = config.paths.repaired_code_dir / f"{profile.trace_id}_repaired.py"
                out_path.write_text(final_code, encoding="utf-8")

    logger.info("All tasks processed. Computing metrics...")

    # 5. Evaluate and Export
    evaluator = TrajectoryMetrics()
    summary = evaluator.compute_summary(trajectories)
    final_results = evaluator.extract_final_results(trajectories)

    logger.info("Objective 3 Run Summary:")
    for k, v in summary.to_dict().items():
        logger.info("  %s: %s", k, v)

    json_exporter = JsonExporter(config.paths.trajectories_dir)
    json_exporter.export_trajectories(trajectories)
    json_exporter.export_summary(summary.to_dict())

    csv_exporter = CsvExporter(config.paths.output_dir)
    csv_exporter.export_final_results(final_results)
    csv_exporter.export_iteration_history(trajectories)

    excel_exporter = ExcelExporter(config.paths.output_dir)
    excel_exporter.export(final_results, trajectories, summary.to_dict())

    logger.info("Objective 3 Pipeline completed successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Objective 3 — Closed-Loop Self-Correction")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of tasks to process (for testing)")
    parser.add_argument("--model", type=str, help="Ollama model name override")
    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG logging")
    
    args = parser.parse_args()

    config = Objective3Config()
    
    if args.verbose:
        config.log_level = "DEBUG"
        config.verbose = True
        
    if args.model:
        config.ollama.model = args.model

    run_objective3(config, args.limit)


if __name__ == "__main__":
    main()
