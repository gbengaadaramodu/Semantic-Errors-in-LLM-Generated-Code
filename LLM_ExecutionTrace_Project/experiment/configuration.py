"""
Task selection and configuration logic.

Loads HumanEval and MBPP datasets, randomly samples tasks,
and creates unified Task objects for the pipeline.
"""

import csv
import json
import random
import re
import logging
from pathlib import Path
from typing import List, Tuple

from models import Task
from config import ProjectConfig

logger = logging.getLogger(__name__)


class TaskSelector:
    """Selects and manages benchmark tasks from HumanEval and MBPP."""

    def __init__(self, config: ProjectConfig):
        self.config = config

    # ──────────────────────────────────────────
    #  Dataset loading
    # ──────────────────────────────────────────

    def load_humaneval(self) -> List[dict]:
        """Load HumanEval.csv using csv.DictReader."""
        path = self.config.paths.humaneval_path
        logger.info("Loading HumanEval dataset from %s", path)
        with open(path, "r", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))

    def load_mbpp(self) -> List[dict]:
        """Load sanitized-mbpp.json."""
        path = self.config.paths.mbpp_path
        logger.info("Loading MBPP dataset from %s", path)
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    # ──────────────────────────────────────────
    #  Task selection
    # ──────────────────────────────────────────

    @staticmethod
    def _extract_entry_point(code: str) -> str:
        """Extract the first function name from a code snippet."""
        match = re.search(r"def\s+(\w+)\s*\(", code)
        return match.group(1) if match else ""

    def select_tasks(self) -> List[Task]:
        """Randomly sample 150 HE + 150 MBPP tasks and return unified Task objects."""
        rng = random.Random(self.config.task_selection.random_seed)

        he_data = self.load_humaneval()
        mb_data = self.load_mbpp()

        he_sample = rng.sample(
            he_data,
            min(len(he_data), self.config.task_selection.humaneval_sample_size),
        )
        mb_sample = rng.sample(
            mb_data,
            min(len(mb_data), self.config.task_selection.mbpp_sample_size),
        )

        tasks: List[Task] = []

        # ── HumanEval ─────────────────────────
        for i, row in enumerate(he_sample, 1):
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

        # ── MBPP ──────────────────────────────
        for i, row in enumerate(mb_sample, 1):
            code = row.get("code", "")
            entry_point = self._extract_entry_point(code)
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

        logger.info("Selected %d tasks (%d HE + %d MB).",
                     len(tasks), len(he_sample), len(mb_sample))
        return tasks

    # ──────────────────────────────────────────
    #  Persistence
    # ──────────────────────────────────────────

    def save_selections(self, tasks: List[Task]) -> None:
        """Save selected task IDs to humaneval_150.csv and mbpp_150.csv."""
        self.config.paths.selected_tasks_dir.mkdir(parents=True, exist_ok=True)

        he_path = self.config.paths.humaneval_selected
        mb_path = self.config.paths.mbpp_selected

        he_ids = [t.task_id for t in tasks if t.dataset == "HumanEval"]
        mb_ids = [t.task_id for t in tasks if t.dataset == "MBPP"]

        with open(he_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["task_id"])
            for tid in he_ids:
                writer.writerow([tid])

        with open(mb_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["task_id"])
            for tid in mb_ids:
                writer.writerow([tid])

        logger.info("Saved task selections → %s, %s", he_path, mb_path)

    def load_selections(self) -> Tuple[List[str], List[str]]:
        """Load previously saved task ID selections."""
        he_ids: List[str] = []
        mb_ids: List[str] = []

        he_path = self.config.paths.humaneval_selected
        if he_path.exists():
            with open(he_path, "r", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                he_ids = [row["task_id"] for row in reader]

        mb_path = self.config.paths.mbpp_selected
        if mb_path.exists():
            with open(mb_path, "r", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                mb_ids = [row["task_id"] for row in reader]

        return he_ids, mb_ids
