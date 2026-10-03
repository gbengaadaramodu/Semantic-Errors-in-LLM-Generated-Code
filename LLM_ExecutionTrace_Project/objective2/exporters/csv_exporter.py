"""
CSV Exporter Module.

Generates `objective2_results.csv`, `counterfactual_results.csv`, and `fault_location_results.csv`.
"""

import csv
import logging
from pathlib import Path
from typing import List

from objective2.config import Objective2Paths
from objective2.models import Objective2Result

logger = logging.getLogger(__name__)


class CSVExporter:
    """
    Exports CSV reports for analytical data processing.
    """

    def __init__(self, paths: Objective2Paths) -> None:
        self.paths = paths

    def export(self, results: List[Objective2Result]) -> None:
        self.paths.ensure_directories()
        self._export_main_results_csv(results)
        self._export_counterfactual_csv(results)
        self._export_fault_location_csv(results)
        logger.info("CSV export completed successfully.")

    def _export_main_results_csv(self, results: List[Objective2Result]) -> None:
        csv_path = self.paths.reports_dir / "objective2_results.csv"
        headers = [
            "trace_id",
            "dataset",
            "task_id",
            "error_category",
            "analysis_status",
            "skip_reason",
            "failure_line",
            "fault_line",
            "fault_statement",
            "causal_variable",
            "counterfactual_validated",
            "confidence",
            "execution_time",
        ]

        try:
            with open(csv_path, "w", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                writer.writerow(headers)
                for r in results:
                    fl_line = r.fault_location.line_number if r.fault_location else ""
                    fl_stmt = r.fault_location.statement_code if r.fault_location else ""
                    var = r.fault_location.causal_variable if r.fault_location else ""
                    cf_val = r.root_cause.counterfactual_validated if r.root_cause else False
                    conf = r.root_cause.confidence if r.root_cause else 0.0

                    writer.writerow([
                        r.trace_id,
                        r.dataset,
                        r.task_id,
                        r.error_category,
                        r.analysis_status.value,
                        r.skip_reason or "",
                        r.failure_line or "",
                        fl_line,
                        fl_stmt,
                        var,
                        cf_val,
                        conf,
                        r.execution_time,
                    ])
        except Exception as exc:
            logger.error("Failed writing objective2_results.csv: %s", exc)

    def _export_counterfactual_csv(self, results: List[Objective2Result]) -> None:
        csv_path = self.paths.reports_dir / "counterfactual_results.csv"
        headers = [
            "trace_id",
            "candidate_rank",
            "target_variable",
            "target_line",
            "observed_value",
            "counterfactual_value",
            "original_outcome",
            "counterfactual_outcome",
            "causal_effect",
            "execution_time",
        ]

        try:
            with open(csv_path, "w", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                writer.writerow(headers)
                for r in results:
                    for cf in r.counterfactual_results:
                        writer.writerow([
                            r.trace_id,
                            cf.candidate_rank,
                            cf.intervention.target_variable,
                            cf.intervention.target_line,
                            cf.intervention.observed_value,
                            cf.intervention.counterfactual_value,
                            cf.original_outcome,
                            cf.counterfactual_outcome,
                            cf.causal_effect.value,
                            cf.execution_time,
                        ])
        except Exception as exc:
            logger.error("Failed writing counterfactual_results.csv: %s", exc)

    def _export_fault_location_csv(self, results: List[Objective2Result]) -> None:
        csv_path = self.paths.reports_dir / "fault_location_results.csv"
        headers = [
            "trace_id",
            "dataset",
            "file",
            "line_number",
            "statement_code",
            "function_name",
            "causal_variable",
            "evidence_score",
            "confidence",
            "ground_truth_matched",
        ]

        try:
            with open(csv_path, "w", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                writer.writerow(headers)
                for r in results:
                    if r.fault_location:
                        fl = r.fault_location
                        writer.writerow([
                            r.trace_id,
                            r.dataset,
                            fl.file,
                            fl.line_number,
                            fl.statement_code,
                            fl.function_name,
                            fl.causal_variable,
                            fl.evidence_score,
                            fl.confidence,
                            r.ground_truth_matched if r.ground_truth_matched is not None else "",
                        ])
        except Exception as exc:
            logger.error("Failed writing fault_location_results.csv: %s", exc)
