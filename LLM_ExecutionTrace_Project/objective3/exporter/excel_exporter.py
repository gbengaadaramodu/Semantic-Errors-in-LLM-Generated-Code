"""
Objective 3 — Excel Exporter.

Consolidates all metrics and final results into a single multi-sheet
Excel workbook for easy human review.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

from objective3.models import FinalTaskResult, TaskTrajectory

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

logger = logging.getLogger(__name__)


class ExcelExporter:
    """Exports structured data to a multi-sheet Excel workbook using pandas."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(
        self,
        final_results: List[FinalTaskResult],
        trajectories: List[TaskTrajectory],
        summary: Dict[str, Any],
        filename: str = "Objective3_Results.xlsx",
    ) -> Optional[Path]:
        """
        Export all results to a single Excel file.
        Returns the path to the written file, or None if pandas is not installed.
        """
        if not PANDAS_AVAILABLE:
            logger.warning(
                "Pandas not available. Skipping Excel export. "
                "Install with `pip install pandas openpyxl`."
            )
            return None

        path = self.output_dir / filename

        # 1. Final Results DataFrame
        df_results = pd.DataFrame([r.to_dict() for r in final_results])

        # 2. Iteration History DataFrame
        rows = []
        for t in trajectories:
            for it in t.iterations:
                rows.append({
                    "trace_id": t.trace_id,
                    "benchmark": t.benchmark,
                    "iteration": it.iteration,
                    "strategy": it.repair_strategy_used.value if it.iteration > 0 else "NONE",
                    "diagnosis": it.diagnostic_report.diagnosis_status.value if it.diagnostic_report else "NONE",
                    "error_category": it.execution_result.error_category.value if it.execution_result else "UNKNOWN",
                    "outcome": it.controller_decision.outcome.value if it.controller_decision else "NONE",
                    "escalated": it.controller_decision.escalated if it.controller_decision else False,
                    "duration": round(it.execution_duration, 3),
                })
        df_iters = pd.DataFrame(rows)

        # 3. Summary DataFrame
        df_summary = pd.DataFrame(list(summary.items()), columns=["Metric", "Value"])

        # Write to Excel
        try:
            with pd.ExcelWriter(path, engine="openpyxl") as writer:
                df_results.to_excel(writer, sheet_name="Final_Results", index=False)
                df_iters.to_excel(writer, sheet_name="Iteration_History", index=False)
                df_summary.to_excel(writer, sheet_name="Run_Summary", index=False)
            logger.info("Exported Excel results to %s", path)
            return path
        except Exception as exc:
            logger.error("Failed to write Excel file: %s", exc)
            return None
