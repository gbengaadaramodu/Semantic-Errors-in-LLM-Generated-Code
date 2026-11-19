"""
objective2_loader.py
--------------------
Loads Objective 2 diagnosis JSON files and maps them to typed
StructuredDiagnosticReport objects for consumption by Objective 3 stages.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from objective3.models import (
    ConfidenceScore,
    DiagnosisStatus,
    ErrorCategory,
    FaultLocation,
    StructuredDiagnosticReport,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Status mapping
# ---------------------------------------------------------------------------
_STATUS_MAP: Dict[str, DiagnosisStatus] = {
    "validated": DiagnosisStatus.VALIDATED,
    "candidate": DiagnosisStatus.CANDIDATE,
    "unresolved": DiagnosisStatus.UNRESOLVED,
}

# ---------------------------------------------------------------------------
# Error-category → repair strategy mapping
# ---------------------------------------------------------------------------
_REPAIR_STRATEGY_MAP: Dict[str, str] = {
    "wrong-output error": (
        "Correct the faulty computational logic identified at the fault location."
    ),
    "wrong output error": (
        "Correct the faulty computational logic identified at the fault location."
    ),
    "wrong output": (
        "Correct the faulty computational logic identified at the fault location."
    ),
    "assertion failure": (
        "Correct the faulty computational logic identified at the fault location."
    ),
    "assertion error": (
        "Correct the faulty computational logic identified at the fault location."
    ),
    "runtime exception": (
        "Fix the runtime error by addressing the exception chain at the fault location."
    ),
    "runtime error": (
        "Fix the runtime error by addressing the exception chain at the fault location."
    ),
    "syntax error": "Fix the syntactic error at the identified boundary.",
    "timeout error": "Optimize the algorithmic complexity at the fault location.",
    "timeout": "Optimize the algorithmic complexity at the fault location.",
}

_DEFAULT_REPAIR_STRATEGY = "Repair the identified defect at the fault location."


def _map_status(raw: str) -> DiagnosisStatus:
    """Map a raw root_cause_status string to a :class:`DiagnosisStatus`.

    Normalises by stripping and lower-casing. Anything unrecognised becomes
    ``DiagnosisStatus.UNRESOLVED``.
    """
    return _STATUS_MAP.get(raw.strip().lower(), DiagnosisStatus.UNRESOLVED)


def _map_confidence(score: float) -> ConfidenceScore:
    """Build a :class:`ConfidenceScore` from a float in [0, 1].

    Thresholds:
    - ``>= 0.7`` → 'HIGH'
    - ``>= 0.4`` → 'MEDIUM'
    - otherwise → 'LOW'
    """
    if score >= 0.7:
        level = "HIGH"
    elif score >= 0.4:
        level = "MEDIUM"
    else:
        level = "LOW"
    return ConfidenceScore(value=score, level=level)


def _repair_strategy_for(error_category_raw: str) -> str:
    """Return the appropriate repair strategy string for *error_category_raw*."""
    return _REPAIR_STRATEGY_MAP.get(
        error_category_raw.strip().lower(), _DEFAULT_REPAIR_STRATEGY
    )


def _build_fault_location(fault_dict: dict) -> Optional[FaultLocation]:
    """Construct a :class:`FaultLocation` from an Obj2 fault_location dict.

    Returns ``None`` if the dict is empty or has no usable line information.
    """
    if not fault_dict:
        return None

    # Obj2 may use 'line_number', 'start_line', or 'line'
    raw_line: Optional[int] = (
        fault_dict.get("line_number")
        or fault_dict.get("start_line")
        or fault_dict.get("line")
    )
    if raw_line is None:
        return None

    try:
        line = int(raw_line)
    except (TypeError, ValueError):
        return None

    end_line: int = fault_dict.get("end_line") or line

    return FaultLocation(
        start_line=line,
        end_line=end_line,
        function_name=fault_dict.get("function_name", "") or fault_dict.get("scope", ""),
        statement_code=fault_dict.get("code_snippet", "") or fault_dict.get("statement_code", ""),
    )


def _build_report(trace_id: str, data: dict) -> Optional[StructuredDiagnosticReport]:
    """Convert a raw Objective 2 JSON dict to a :class:`StructuredDiagnosticReport`.

    Parameters
    ----------
    trace_id:
        The trace ID (e.g. ``'HE001'``).
    data:
        The parsed JSON content of the per-task diagnosis file.

    Returns
    -------
    StructuredDiagnosticReport or None
        ``None`` if the data is structurally invalid.
    """
    # Support top-level wrapper keys used by some Obj2 writers
    for key in ("result", "diagnosis", "data"):
        if key in data and isinstance(data[key], dict):
            data = data[key]
            break

    root_cause: dict = data.get("root_cause", {})
    fault_dict: dict = data.get("fault_location", {})

    # --- Status ---
    raw_status: str = root_cause.get("root_cause_status", "unresolved")
    status = _map_status(raw_status)

    # --- Confidence ---
    raw_confidence = root_cause.get("confidence", 0.0)
    try:
        confidence_val = float(raw_confidence)
    except (TypeError, ValueError):
        confidence_val = 0.0
    confidence = _map_confidence(confidence_val)

    # --- Fault location ---
    fault_location = _build_fault_location(fault_dict)

    # --- Causal explanation ---
    candidate_explanation: str = root_cause.get("candidate_explanation", "")
    evidence_summary: str = data.get("evidence_summary", "")
    if candidate_explanation and evidence_summary:
        causal_explanation = f"{candidate_explanation}\n\n{evidence_summary}"
    else:
        causal_explanation = candidate_explanation or evidence_summary

    # --- Error category (for repair strategy) ---
    raw_error_category: str = data.get("error_category", "")
    repair_strategy = _repair_strategy_for(raw_error_category)

    # --- ErrorCategory enum ---
    from objective3.models import ErrorCategory as EC  # local import to avoid circularity

    _ec_map: Dict[str, EC] = {
        "wrong-output error": EC.WRONG_OUTPUT,
        "wrong output error": EC.WRONG_OUTPUT,
        "wrong output": EC.WRONG_OUTPUT,
        "syntax error": EC.SYNTAX_ERROR,
        "runtime exception": EC.RUNTIME_EXCEPTION,
        "runtime error": EC.RUNTIME_EXCEPTION,
        "assertion failure": EC.ASSERTION_FAILURE,
        "assertion error": EC.ASSERTION_FAILURE,
        "timeout error": EC.TIMEOUT,
        "timeout": EC.TIMEOUT,
        "correct": EC.CORRECT,
    }
    error_category: EC = _ec_map.get(raw_error_category.strip().lower(), EC.UNKNOWN)

    # --- Build supporting evidence list ---
    supporting_evidence: List[str] = data.get("supporting_evidence", [])
    if not supporting_evidence and evidence_summary:
        supporting_evidence = [evidence_summary]

    return StructuredDiagnosticReport(
        
        
        confidence=confidence,
        fault_location=fault_location,
        causal_explanation=causal_explanation,
        repair_strategy=repair_strategy,
        error_category=error_category,
        
        
        
        
    )


class Objective2Loader:
    """Loads per-task Objective 2 diagnosis files from a diagnosis directory.

    Parameters
    ----------
    config:
        An ``Obj3PathConfig`` whose ``obj2_diagnosis_dir`` attribute points to
        ``objective2/output/diagnosis/``.
    """

    def __init__(self, config) -> None:
        self.config = config
        self._cache: Dict[str, StructuredDiagnosticReport] = {}
        self._scanned = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _diagnosis_dir(self) -> Path:
        return Path(self.config.paths.objective2_diagnosis_dir)

    def _load_file(self, json_path: Path, trace_id: str) -> Optional[StructuredDiagnosticReport]:
        """Parse a single diagnosis JSON file and return a report."""
        try:
            with json_path.open("r", encoding="utf-8") as fh:
                data: dict = json.load(fh)
        except FileNotFoundError:
            logger.debug("Diagnosis file not found: %s", json_path)
            return None
        except json.JSONDecodeError as exc:
            logger.error("JSON decode error in %s: %s", json_path, exc)
            return None
        except Exception as exc:
            logger.error("Unexpected error reading %s: %s", json_path, exc)
            return None

        report = _build_report(trace_id, data)
        if report is None:
            logger.warning("Could not build StructuredDiagnosticReport from %s", json_path)
        return report

    def _scan_all(self) -> None:
        """Eagerly load all JSON files in the diagnosis directory into cache."""
        if self._scanned:
            return

        diag_dir = self._diagnosis_dir()
        if not diag_dir.exists():
            logger.warning("Diagnosis directory does not exist: %s", diag_dir)
            self._scanned = True
            return

        for json_file in sorted(diag_dir.glob("*.json")):
            trace_id = json_file.stem  # e.g. 'HE001'
            if trace_id in self._cache:
                continue
            report = self._load_file(json_file, trace_id)
            if report is not None:
                self._cache[trace_id] = report

        logger.info("Loaded %d diagnosis reports from %s.", len(self._cache), diag_dir)
        self._scanned = True

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_diagnosis(self, trace_id: str) -> Optional[StructuredDiagnosticReport]:
        """Return the :class:`StructuredDiagnosticReport` for *trace_id*, or ``None``.

        Parameters
        ----------
        trace_id:
            E.g. ``'HE001'`` or ``'MB336'``.
        """
        trace_id = trace_id.strip()

        if trace_id in self._cache:
            return self._cache[trace_id]

        # Attempt to load the specific file without scanning the whole dir
        json_path = self._diagnosis_dir() / f"{trace_id}.json"
        report = self._load_file(json_path, trace_id)
        if report is not None:
            self._cache[trace_id] = report
        return report

    def load_all_diagnoses(self) -> Dict[str, StructuredDiagnosticReport]:
        """Return a mapping of trace_id → :class:`StructuredDiagnosticReport` for all tasks."""
        self._scan_all()
        return dict(self._cache)

    def has_diagnosis(self, trace_id: str) -> bool:
        """Return ``True`` if a diagnosis file exists for *trace_id*.

        Parameters
        ----------
        trace_id:
            E.g. ``'HE001'``.
        """
        trace_id = trace_id.strip()
        if trace_id in self._cache:
            return True
        json_path = self._diagnosis_dir() / f"{trace_id}.json"
        return json_path.exists()
