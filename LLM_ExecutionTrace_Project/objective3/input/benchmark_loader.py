"""
benchmark_loader.py
-------------------
Loads HumanEval and MBPP benchmark tasks from the datasets/ and prompts/
directories, returning typed BenchmarkTask objects.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from objective3.models import BenchmarkTask

logger = logging.getLogger(__name__)


class BenchmarkLoader:
    """Loads HumanEval and MBPP benchmark tasks.

    Parameters
    ----------
    config:
        An ``Obj3PathConfig`` instance whose attributes supply all relevant
        directory / file paths used by this loader.
    """

    def __init__(self, config) -> None:
        self.config = config
        self._he_tasks: Optional[Dict[str, BenchmarkTask]] = None
        self._mb_tasks: Optional[Dict[str, BenchmarkTask]] = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_humaneval_csv(self) -> Dict[str, BenchmarkTask]:
        """Parse HumanEval.csv and return a mapping of trace-id → BenchmarkTask."""
        csv_path = Path(self.config.paths.project_root) / "datasets" / "HumanEval.csv"
        if not csv_path.exists():
            logger.warning("HumanEval CSV not found at %s", csv_path)
            return {}

        try:
            df = pd.read_csv(csv_path)
        except Exception as exc:
            logger.error("Failed to read HumanEval CSV: %s", exc)
            return {}

        required_cols = {"task_id", "prompt", "entry_point", "test", "canonical_solution"}
        missing = required_cols - set(df.columns)
        if missing:
            logger.error("HumanEval CSV is missing columns: %s", missing)
            return {}

        # Sort by task_id so HE001 → index 0, HE002 → index 1, etc.
        df = df.sort_values("task_id").reset_index(drop=True)

        tasks: Dict[str, BenchmarkTask] = {}
        for idx, row in df.iterrows():
            trace_id = f"HE{int(idx) + 1:03d}"
            spec = self._load_prompt_file(trace_id) or str(row.get("prompt", ""))
            task = BenchmarkTask(
                trace_id=trace_id,
                task_id=str(row.get("task_id", "")),
                benchmark="HumanEval",
                specification=spec,
                entry_point=str(row.get("entry_point", "")),
                test_code=str(row.get("test", "")),
            )
            tasks[trace_id] = task

        logger.info("Loaded %d HumanEval tasks.", len(tasks))
        return tasks

    def _load_mbpp_json(self) -> Dict[str, BenchmarkTask]:
        """Parse sanitized-mbpp.json and return a mapping of trace-id → BenchmarkTask."""
        json_path = Path(self.config.paths.project_root) / "datasets" / "sanitized-mbpp.json"
        if not json_path.exists():
            logger.warning("MBPP JSON not found at %s", json_path)
            return {}

        try:
            with json_path.open("r", encoding="utf-8") as fh:
                records: List[dict] = json.load(fh)
        except Exception as exc:
            logger.error("Failed to read MBPP JSON: %s", exc)
            return {}

        tasks: Dict[str, BenchmarkTask] = {}
        for record in records:
            raw_task_id = record.get("task_id")
            if raw_task_id is None:
                logger.debug("Skipping MBPP record with no task_id: %s", record)
                continue

            trace_id = f"MB{int(raw_task_id):03d}"
            spec = self._load_prompt_file(trace_id) or str(record.get("text", ""))
            entry_point = self._extract_entry_point(str(record.get("code", "")))
            test_list: List[str] = record.get("test_list", [])
            test_setup: str = record.get("test_setup_code", "")
            test_code = "\n".join(test_list)
            if test_setup:
                test_code = test_setup + "\n" + test_code

            task = BenchmarkTask(
                trace_id=trace_id,
                task_id=f"MBPP/{int(raw_task_id)}",
                benchmark="MBPP",
                specification=spec,
                entry_point=entry_point,
                test_code=test_code,
            )
            tasks[trace_id] = task

        logger.info("Loaded %d MBPP tasks.", len(tasks))
        return tasks

    def _load_prompt_file(self, trace_id: str) -> Optional[str]:
        """Return the content of prompts/<trace_id>.txt if it exists."""
        prompts_dir = Path(self.config.paths.prompts_dir)
        prompt_file = prompts_dir / f"{trace_id}.txt"
        if prompt_file.exists():
            try:
                return prompt_file.read_text(encoding="utf-8").strip()
            except Exception as exc:
                logger.warning("Could not read prompt file %s: %s", prompt_file, exc)
        return None

    @staticmethod
    def _extract_entry_point(code: str) -> str:
        """Extract the name of the first ``def`` statement in *code*.

        Returns an empty string if no function definition is found.
        """
        match = re.search(r"^\s*def\s+([A-Za-z_]\w*)\s*\(", code, re.MULTILINE)
        return match.group(1) if match else ""

    # ------------------------------------------------------------------
    # Cache management
    # ------------------------------------------------------------------

    def _ensure_he_loaded(self) -> Dict[str, BenchmarkTask]:
        if self._he_tasks is None:
            self._he_tasks = self._load_humaneval_csv()
        return self._he_tasks

    def _ensure_mb_loaded(self) -> Dict[str, BenchmarkTask]:
        if self._mb_tasks is None:
            self._mb_tasks = self._load_mbpp_json()
        return self._mb_tasks

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_task(self, trace_id: str) -> Optional[BenchmarkTask]:
        """Return the :class:`BenchmarkTask` for *trace_id*, or ``None``.

        Parameters
        ----------
        trace_id:
            A string like ``'HE001'`` (HumanEval) or ``'MB336'`` (MBPP).
        """
        trace_id = trace_id.strip().upper()
        if trace_id.startswith("HE"):
            return self._ensure_he_loaded().get(trace_id)
        if trace_id.startswith("MB"):
            return self._ensure_mb_loaded().get(trace_id)
        logger.warning("Unknown trace_id prefix for '%s'.", trace_id)
        return None

    def load_all_tasks(self) -> Dict[str, BenchmarkTask]:
        """Return a merged mapping of all HumanEval and MBPP tasks."""
        tasks: Dict[str, BenchmarkTask] = {}
        tasks.update(self._ensure_he_loaded())
        tasks.update(self._ensure_mb_loaded())
        return tasks
