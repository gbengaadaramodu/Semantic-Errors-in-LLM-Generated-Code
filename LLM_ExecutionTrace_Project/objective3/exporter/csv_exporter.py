"""
Objective 3 — CSV Exporter.

Exports flattened data suitable for Objective 4 R/Pandas ingestion.
Produces two tables:
  1. Flat final results (1 row per task)
  2. Iteration history (1 row per repair iteration)
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import List

from objective3.models import FinalTaskResult, TaskTrajectory


class CsvExporter:
    """Exports structured data to CSV format."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_final_results(self, results: List[FinalTaskResult]) -> Path:
        """Export flat final task results."""
        if not results:
            return self.output_dir / "final_results.csv"

        path = self.output_dir / "final_results.csv"
        fieldnames = list(results[0].to_dict().keys())

        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in results:
                writer.writerow(r.to_dict())
        return path

    def export_iteration_history(self, trajectories: List[TaskTrajectory]) -> Path:
        """Export a flattened iteration history (1 row = 1 iteration)."""
        path = self.output_dir / "iteration_history.csv"
        
        fieldnames = [
            "trace_id", "task_id", "benchmark", "iteration", 
            "strategy_used", "diagnosis_status", "error_category", 
            "outcome", "escalated", "oscillation", "duration", "model"
        ]

        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for t in trajectories:
                for it in t.iterations:
                    row = {
                        "trace_id": t.trace_id,
                        "task_id": t.task_id,
                        "benchmark": t.benchmark,
                        "iteration": it.iteration,
                        "strategy_used": it.repair_strategy_used.value if it.iteration > 0 else "NONE",
                        "diagnosis_status": it.diagnostic_report.diagnosis_status.value if it.diagnostic_report else "NONE",
                        "error_category": it.execution_result.error_category.value if it.execution_result else "UNKNOWN",
                        "outcome": it.controller_decision.outcome.value if it.controller_decision else "NONE",
                        "escalated": it.controller_decision.escalated if it.controller_decision else False,
                        "oscillation": it.controller_decision.oscillation_detected if it.controller_decision else False,
                        "duration": round(it.execution_duration, 3),
                        "model": it.model_name,
                    }
                    writer.writerow(row)
        return path
