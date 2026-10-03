"""
Trace Loader Module.

Enriches Objective2InputRecord with generated code from `generated_code/{trace_id}.py`
and benchmark test specifications from `datasets/HumanEval.csv` or `datasets/sanitized-mbpp.json`.
"""

import csv
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

from objective2.config import Objective2Paths
from objective2.models import Objective2InputRecord

logger = logging.getLogger(__name__)


class TraceLoader:
    """
    Loads source code files and task definitions for input records.
    """

    def __init__(self, paths: Objective2Paths) -> None:
        self.paths = paths
        self._he_cache: Optional[Dict[str, dict]] = None
        self._mb_cache: Optional[Dict[str, dict]] = None

    def enrich_record(self, record: Objective2InputRecord) -> Objective2InputRecord:
        """
        Populates generated_code, entry_point, test_code, and test_imports
        for the given record.
        """
        # 1. Read generated code file
        code_path = self.paths.generated_code_dir / f"{record.trace_id}.py"
        if code_path.exists():
            try:
                record.generated_code = code_path.read_text(encoding="utf-8")
            except Exception as exc:
                logger.warning("Failed to read code for %s: %s", record.trace_id, exc)
                record.generated_code = ""
        else:
            logger.warning("Generated code file not found for %s", record.trace_id)

        # 2. Look up task definition & benchmark test suite
        dataset = record.dataset.strip().upper()
        if dataset in ("HUMANEVAL", "HE"):
            self._load_humaneval_tasks()
            if self._he_cache and record.task_id in self._he_cache:
                task_data = self._he_cache[record.task_id]
                record.test_code = task_data.get("test", "")
                record.entry_point = task_data.get("entry_point", "")
                if not record.problem_summary:
                    record.problem_summary = task_data.get("prompt", "")[:80]

        elif dataset in ("MBPP", "MB"):
            self._load_mbpp_tasks()
            key = str(record.task_id)
            if self._mb_cache and key in self._mb_cache:
                task_data = self._mb_cache[key]
                test_list = task_data.get("test_list", [])
                test_imports = task_data.get("test_imports", [])
                record.test_code = "\n".join(test_list)
                record.test_imports = "\n".join(test_imports)

                # Deduce entry point from code or prompt
                code = task_data.get("code", "")
                match = re.search(r"def\s+(\w+)\s*\(", code)
                record.entry_point = match.group(1) if match else ""
                if not record.problem_summary:
                    record.problem_summary = task_data.get("prompt", "")[:80]

        # If entry point is still unknown, try inferring from generated_code
        if not record.entry_point and record.generated_code:
            match = re.search(r"def\s+(\w+)\s*\(", record.generated_code)
            if match:
                record.entry_point = match.group(1)

        return record

    def _load_humaneval_tasks(self) -> None:
        if self._he_cache is not None:
            return
        self._he_cache = {}
        he_file = self.paths.datasets_dir / "HumanEval.csv"
        if not he_file.exists():
            logger.warning("HumanEval dataset file not found at %s", he_file)
            return
        try:
            with open(he_file, "r", encoding="utf-8", errors="replace") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    self._he_cache[row["task_id"]] = row
        except Exception as exc:
            logger.error("Failed loading HumanEval.csv: %s", exc)

    def _load_mbpp_tasks(self) -> None:
        if self._mb_cache is not None:
            return
        self._mb_cache = {}
        mb_file = self.paths.datasets_dir / "sanitized-mbpp.json"
        if not mb_file.exists():
            logger.warning("MBPP dataset file not found at %s", mb_file)
            return
        try:
            with open(mb_file, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            for row in data:
                self._mb_cache[str(row["task_id"])] = row
        except Exception as exc:
            logger.error("Failed loading sanitized-mbpp.json: %s", exc)
