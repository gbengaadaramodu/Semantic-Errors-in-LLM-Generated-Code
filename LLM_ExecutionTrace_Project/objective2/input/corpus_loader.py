"""
Corpus Loader Module.

Reads exported Objective 1 corpora (.json, .csv, .xlsx, or log directory),
normalizes missing fields, and returns typed Objective2InputRecord instances.
"""

import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Union

from objective2.models import Objective2InputRecord

logger = logging.getLogger(__name__)


class CorpusLoader:
    """
    Fault-tolerant loader for Objective 1 corpus files.
    """

    def __init__(self, input_path: Path) -> None:
        self.input_path = Path(input_path)

    def load_records(self) -> List[Objective2InputRecord]:
        """
        Load records from JSON, CSV, XLSX, or a log directory.
        """
        if not self.input_path.exists():
            raise FileNotFoundError(f"Input path does not exist: {self.input_path}")

        records: List[Objective2InputRecord] = []

        if self.input_path.is_dir():
            records = self._load_from_directory(self.input_path)
        elif self.input_path.suffix.lower() == ".json":
            records = self._load_from_json(self.input_path)
        elif self.input_path.suffix.lower() == ".csv":
            records = self._load_from_csv(self.input_path)
        elif self.input_path.suffix.lower() in (".xlsx", ".xls"):
            records = self._load_from_excel(self.input_path)
        else:
            raise ValueError(f"Unsupported file format: {self.input_path.suffix}")

        logger.info(
            "Successfully loaded %d records from %s", len(records), self.input_path
        )
        return records

    def _load_from_json(self, json_file: Path) -> List[Objective2InputRecord]:
        """Load from a single JSON file (array of records or single object)."""
        try:
            with open(json_file, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception as exc:
            logger.error("Failed to parse JSON file %s: %s", json_file, exc)
            return []

        if isinstance(data, dict):
            data = [data]

        records: List[Objective2InputRecord] = []
        for raw in data:
            rec = self._parse_dict_record(raw)
            if rec is not None:
                records.append(rec)
        return records

    def _load_from_directory(self, dir_path: Path) -> List[Objective2InputRecord]:
        """Load from a directory containing individual JSON log files."""
        json_files = sorted(dir_path.glob("*.json"))
        records: List[Objective2InputRecord] = []
        for f in json_files:
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    raw = json.load(fh)
                rec = self._parse_dict_record(raw)
                if rec is not None:
                    records.append(rec)
            except Exception as exc:
                logger.warning("Could not read log file %s: %s", f.name, exc)
        return records

    def _load_from_csv(self, csv_file: Path) -> List[Objective2InputRecord]:
        """Load from a CSV corpus file."""
        records: List[Objective2InputRecord] = []
        try:
            with open(csv_file, "r", encoding="utf-8", errors="replace") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    rec = self._parse_dict_record(dict(row))
                    if rec is not None:
                        records.append(rec)
        except Exception as exc:
            logger.error("Failed to parse CSV file %s: %s", csv_file, exc)
        return records

    def _load_from_excel(self, excel_file: Path) -> List[Objective2InputRecord]:
        """Load from an Excel corpus file using openpyxl."""
        records: List[Objective2InputRecord] = []
        try:
            import openpyxl

            wb = openpyxl.load_workbook(excel_file, data_only=True)
            sheet = wb.active
            rows = list(sheet.iter_rows(values_only=True))
            if not rows:
                return []
            headers = [str(h) if h is not None else "" for h in rows[0]]
            for r in rows[1:]:
                row_dict = {headers[i]: r[i] for i in range(min(len(headers), len(r)))}
                rec = self._parse_dict_record(row_dict)
                if rec is not None:
                    records.append(rec)
        except Exception as exc:
            logger.error("Failed to parse Excel file %s: %s", excel_file, exc)
        return records

    def _parse_dict_record(self, raw: Dict[str, Any]) -> Union[Objective2InputRecord, None]:
        """Convert a raw dictionary into an Objective2InputRecord with safe fallbacks."""
        if not isinstance(raw, dict):
            return None

        trace_id = str(raw.get("trace_id") or raw.get("trace_id", "")).strip()
        task_id = str(raw.get("task_id") or "").strip()
        dataset = str(raw.get("dataset") or "").strip()

        if not trace_id and not task_id:
            return None

        def to_bool(val: Any) -> Union[bool, None]:
            if val is None or val == "":
                return None
            if isinstance(val, bool):
                return val
            s = str(val).strip().lower()
            if s in ("true", "1", "yes"):
                return True
            if s in ("false", "0", "no"):
                return False
            return None

        def to_int(val: Any, default: int = 0) -> int:
            try:
                return int(val)
            except (ValueError, TypeError):
                return default

        def to_float(val: Any, default: float = 0.0) -> float:
            try:
                return float(val)
            except (ValueError, TypeError):
                return default

        return Objective2InputRecord(
            trace_id=trace_id or task_id,
            dataset=dataset or ("HumanEval" if trace_id.startswith("HE") else "MBPP"),
            task_id=task_id or trace_id,
            problem_summary=str(raw.get("problem_summary") or ""),
            execution_status=str(raw.get("execution_status") or ""),
            stdout=str(raw.get("stdout") or ""),
            stderr=str(raw.get("stderr") or ""),
            traceback=str(raw.get("traceback") or ""),
            exception_type=str(raw.get("exception_type") or ""),
            exception_message=str(raw.get("exception_message") or ""),
            execution_time=to_float(raw.get("execution_time")),
            timed_out=bool(to_bool(raw.get("timed_out")) or False),
            exit_code=to_int(raw.get("exit_code")),
            tests_passed=to_bool(raw.get("tests_passed")),
            tests_failed=to_int(raw.get("tests_failed")),
            expected_output=raw.get("expected_output"),
            actual_output=raw.get("actual_output"),
            assertion_source=raw.get("assertion_source"),
            assertion_failed=bool(to_bool(raw.get("assertion_failed")) or False),
            parser_prediction=str(raw.get("parser_prediction") or ""),
        )
