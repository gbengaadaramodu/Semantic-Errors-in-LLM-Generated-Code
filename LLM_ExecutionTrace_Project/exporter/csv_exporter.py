"""
Exports execution results to a CSV file.
"""

import csv
import logging
from pathlib import Path
from typing import List

from models import ExecutionResult

logger = logging.getLogger(__name__)

HEADERS = [
    "TraceID", "Dataset", "TaskID", "Problem Summary", "Execution Status",
    "stdout", "stderr", "Traceback", "Execution Time", "Parser Prediction",
    "Annotator1", "Annotator2", "Annotator3",
]


class CsvExporter:
    """Exports execution results to CSV format."""

    def __init__(self, output_path: Path):
        self.output_path = Path(output_path)

    def export(self, results: List[ExecutionResult]) -> Path:
        """Write all results to CSV with the annotation schema columns."""
        logger.info("Exporting results to CSV → %s", self.output_path)

        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.output_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=HEADERS)
            writer.writeheader()

            for r in results:
                ev = r.evidence
                writer.writerow({
                    "TraceID": r.trace_id,
                    "Dataset": r.dataset,
                    "TaskID": r.task_id,
                    "Problem Summary": r.problem_summary,
                    "Execution Status": r.execution_status,
                    "stdout": ev.stdout,
                    "stderr": ev.stderr,
                    "Traceback": ev.traceback,
                    "Execution Time": f"{ev.execution_time:.3f}",
                    "Parser Prediction": r.parser_prediction,
                    "Annotator1": "",
                    "Annotator2": "",
                    "Annotator3": "",
                })

        logger.info("CSV export complete (%d rows).", len(results))
        return self.output_path
