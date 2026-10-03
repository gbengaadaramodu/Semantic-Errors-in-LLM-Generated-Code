"""
JSON Exporter Module.

Exports machine-readable per-task JSON diagnosis reports, SCM, PDG, runtime traces,
counterfactual results, and global summary statistics.
"""

import json
import logging
from pathlib import Path
from typing import List

from objective2.config import Objective2Paths
from objective2.models import Objective2Result, Objective2Summary
from objective2.pdg.graph_builder import PDGGraphBuilder
from objective2.scm.graph import SCMGraph

logger = logging.getLogger(__name__)


class JSONExporter:
    """
    Exports detailed JSON artifacts for research reproducibility.
    """

    def __init__(self, paths: Objective2Paths) -> None:
        self.paths = paths

    def export_all(
        self, results: List[Objective2Result], summary: Objective2Summary
    ) -> None:
        self.paths.ensure_directories()

        for res in results:
            self._export_case_json(res)

        self._export_summary_json(summary)
        logger.info("JSON export completed successfully.")

    def _export_case_json(self, res: Objective2Result) -> None:
        # 1. Main diagnosis JSON
        diag_path = self.paths.diagnosis_dir / f"{res.trace_id}.json"
        try:
            with open(diag_path, "w", encoding="utf-8") as fh:
                json.dump(res.to_dict(), fh, indent=2, default=str)
        except Exception as exc:
            logger.error("Failed writing diagnosis JSON for %s: %s", res.trace_id, exc)

        # 2. SCM JSON & DOT
        if res.scm:
            scm_path = self.paths.scm_dir / f"{res.trace_id}.json"
            dot_path = self.paths.scm_dir / f"{res.trace_id}.dot"
            try:
                with open(scm_path, "w", encoding="utf-8") as fh:
                    json.dump(res.scm.to_dict(), fh, indent=2)
                dot_text = SCMGraph.to_dot(res.scm)
                dot_path.write_text(dot_text, encoding="utf-8")
            except Exception as exc:
                logger.error("Failed writing SCM for %s: %s", res.trace_id, exc)

        # 3. PDG JSON & DOT
        if res.pdg:
            pdg_path = self.paths.pdg_dir / f"{res.trace_id}.json"
            dot_path = self.paths.pdg_dir / f"{res.trace_id}.dot"
            try:
                with open(pdg_path, "w", encoding="utf-8") as fh:
                    json.dump(res.pdg.to_dict(), fh, indent=2)
                dot_text = PDGGraphBuilder.to_dot(res.pdg)
                dot_path.write_text(dot_text, encoding="utf-8")
            except Exception as exc:
                logger.error("Failed writing PDG for %s: %s", res.trace_id, exc)

        # 4. Counterfactual results JSON
        if res.counterfactual_results:
            cf_path = self.paths.counterfactual_dir / f"{res.trace_id}.json"
            try:
                with open(cf_path, "w", encoding="utf-8") as fh:
                    json.dump(
                        [cf.to_dict() for cf in res.counterfactual_results],
                        fh,
                        indent=2,
                        default=str,
                    )
            except Exception as exc:
                logger.error("Failed writing counterfactual for %s: %s", res.trace_id, exc)

    def _export_summary_json(self, summary: Objective2Summary) -> None:
        summary_path = self.paths.reports_dir / "objective2_summary.json"
        try:
            with open(summary_path, "w", encoding="utf-8") as fh:
                json.dump(summary.to_dict(), fh, indent=2)
        except Exception as exc:
            logger.error("Failed writing objective2_summary.json: %s", exc)
