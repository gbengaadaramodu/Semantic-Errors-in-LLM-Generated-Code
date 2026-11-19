"""
Objective 3 — JSON Exporter.

Preserves the complete, deeply-nested trajectory data required for
Objective 4's qualitative analysis and timeline reconstruction.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from objective3.models import TaskTrajectory


class JsonExporter:
    """Exports full trajectories to JSON files."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_trajectories(self, trajectories: List[TaskTrajectory]) -> Path:
        """Export a list of trajectories to a single JSON list file."""
        data = [t.to_dict() for t in trajectories]
        path = self.output_dir / "all_trajectories.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return path

    def export_individual_trajectory(self, trajectory: TaskTrajectory) -> Path:
        """Export a single trajectory to a dedicated JSON file."""
        path = self.output_dir / f"{trajectory.trace_id}_trajectory.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(trajectory.to_dict(), f, indent=2)
        return path

    def export_summary(self, summary_dict: Dict[str, Any], filename: str = "run_summary.json") -> Path:
        """Export the RunSummary dict."""
        path = self.output_dir / filename
        with path.open("w", encoding="utf-8") as f:
            json.dump(summary_dict, f, indent=2)
        return path
