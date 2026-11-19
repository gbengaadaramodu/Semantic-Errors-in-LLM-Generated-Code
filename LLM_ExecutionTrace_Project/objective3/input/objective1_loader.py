"""
objective1_loader.py
--------------------
Loads Objective 1 outputs (Validation_Corpus.json) and converts them into
typed ErrorProfile objects for use by Objective 3 stages.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

from objective3.models import ErrorCategory, ErrorProfile

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mapping from raw string labels → ErrorCategory enum values
# ---------------------------------------------------------------------------
_CATEGORY_MAP: Dict[str, ErrorCategory] = {
    "wrong-output error": ErrorCategory.WRONG_OUTPUT,
    "wrong output error": ErrorCategory.WRONG_OUTPUT,
    "wrong output": ErrorCategory.WRONG_OUTPUT,
    "syntax error": ErrorCategory.SYNTAX_ERROR,
    "runtime exception": ErrorCategory.RUNTIME_EXCEPTION,
    "runtime error": ErrorCategory.RUNTIME_EXCEPTION,
    "assertion failure": ErrorCategory.ASSERTION_FAILURE,
    "assertion error": ErrorCategory.ASSERTION_FAILURE,
    "timeout error": ErrorCategory.TIMEOUT,
    "timeout": ErrorCategory.TIMEOUT,
    "correct": ErrorCategory.CORRECT,
}

# Regex to extract the last "File ..., line N" from a traceback string
_TRACEBACK_LINE_RE = re.compile(r'File\s+"[^"]*",\s+line\s+(\d+)', re.IGNORECASE)


def _parse_category(raw: str) -> ErrorCategory:
    """Map a raw ``parser_prediction`` string to an :class:`ErrorCategory`.

    Normalises the input (strip + lower) before lookup; falls back to
    ``ErrorCategory.UNKNOWN`` for unrecognised values.
    """
    normalised = raw.strip().lower()
    return _CATEGORY_MAP.get(normalised, ErrorCategory.UNKNOWN)


def _extract_failure_line(traceback: Optional[str]) -> Optional[int]:
    """Return the last line number mentioned in *traceback*, or ``None``."""
    if not traceback:
        return None
    matches = _TRACEBACK_LINE_RE.findall(traceback)
    if matches:
        try:
            return int(matches[-1])
        except ValueError:
            pass
    return None


def _map_record(record: dict) -> Optional[ErrorProfile]:
    """Convert a single raw JSON dict to an :class:`ErrorProfile`.

    Returns ``None`` and logs a warning if mandatory fields are absent.
    """
    trace_id = record.get("trace_id") or record.get("task_id")
    if trace_id is None:
        logger.warning("Record missing 'trace_id'/'task_id'; skipping: %s", list(record.keys()))
        return None

    trace_id = str(trace_id).strip()
    raw_category = str(record.get("parser_prediction", record.get("error_category", "")))
    category = _parse_category(raw_category)

    traceback_text: Optional[str] = record.get("traceback") or record.get("error_trace")
    failure_line = _extract_failure_line(traceback_text)

    return ErrorProfile(
        task_id=record.get("task_id", ""),
        trace_id=trace_id,
        benchmark=record.get("dataset", ""),
        error_category=category,
        execution_status=record.get("execution_status", ""),
        stdout=record.get("stdout", ""),
        stderr=record.get("stderr", ""),
        traceback=traceback_text or "",
        exception_type=record.get("exception_type", ""),
        exception_message=record.get("exception_message", ""),
        execution_time=record.get("execution_time", 0.0),
        timed_out=record.get("timed_out", False),
        exit_code=record.get("exit_code", 1),
        tests_passed=record.get("tests_passed"),
        tests_failed=record.get("tests_failed", 0),
        expected_output=record.get("expected_output"),
        actual_output=record.get("actual_output"),
        assertion_source=record.get("assertion_source"),
        assertion_failed=record.get("assertion_failed", False),
        parser_prediction=raw_category,
        failure_line=failure_line,
    )


class Objective1Loader:
    """Loads and exposes Objective 1 validation corpus entries.

    Parameters
    ----------
    config:
        An ``Obj3PathConfig`` whose ``validation_corpus_path`` attribute
        points to ``Validation_Corpus.json``.
    """

    def __init__(self, config) -> None:
        self.config = config
        self._cache: Optional[List[ErrorProfile]] = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_source(self) -> Path:
        """Return the resolved path to the validation corpus file."""
        return Path(self.config.paths.objective1_corpus)

    def _load_raw(self) -> List[dict]:
        """Read and parse the validation corpus; supports JSON and CSV."""
        source = self._resolve_source()
        if not source.exists():
            raise FileNotFoundError(f"Validation corpus not found: {source}")

        suffix = source.suffix.lower()

        if suffix == ".json":
            with source.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                # Some corpora wrap the list under a key
                for key in ("tasks", "records", "data", "results"):
                    if key in data and isinstance(data[key], list):
                        return data[key]
                return [data]
            raise ValueError(f"Unexpected JSON structure in {source}")

        if suffix == ".csv":
            import csv
            records: List[dict] = []
            with source.open("r", encoding="utf-8", newline="") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    records.append(dict(row))
            return records

        if source.is_dir():
            # If a directory is given, load all JSON files within it
            records = []
            for json_file in sorted(source.glob("*.json")):
                try:
                    with json_file.open("r", encoding="utf-8") as fh:
                        item = json.load(fh)
                    if isinstance(item, list):
                        records.extend(item)
                    elif isinstance(item, dict):
                        records.append(item)
                except Exception as exc:
                    logger.warning("Failed to read %s: %s", json_file, exc)
            return records

        raise ValueError(f"Unsupported validation corpus format: {suffix}")

    def _build_cache(self) -> List[ErrorProfile]:
        if self._cache is not None:
            return self._cache

        raw_records = self._load_raw()
        profiles: List[ErrorProfile] = []
        for record in raw_records:
            profile = _map_record(record)
            if profile is not None:
                profiles.append(profile)

        logger.info("Loaded %d ErrorProfiles from validation corpus.", len(profiles))
        self._cache = profiles
        return self._cache

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_all(self) -> List[ErrorProfile]:
        """Return all :class:`ErrorProfile` entries from the validation corpus."""
        return self._build_cache()

    def load_by_trace_id(self, trace_id: str) -> Optional[ErrorProfile]:
        """Return the :class:`ErrorProfile` for *trace_id*, or ``None``.

        Parameters
        ----------
        trace_id:
            E.g. ``'HE001'`` or ``'MB336'``.
        """
        trace_id = trace_id.strip()
        for profile in self._build_cache():
            if profile.trace_id == trace_id:
                return profile
        logger.debug("No ErrorProfile found for trace_id='%s'.", trace_id)
        return None

    def load_failed_tasks(self) -> List[ErrorProfile]:
        """Return all profiles whose category is not ``ErrorCategory.CORRECT``.

        Useful for focusing downstream processing on genuinely failing tasks.
        """
        return [p for p in self._build_cache() if p.error_category != ErrorCategory.CORRECT]
