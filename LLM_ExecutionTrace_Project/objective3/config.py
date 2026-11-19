"""
Objective 3 — Central Configuration.

All tuneable parameters for Objective 3 are defined here.
Override via command-line arguments (see main.py) or environment variables.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Resolve project root: two levels up from this file
# (objective3/ → LLM_ExecutionTrace_Project/)
# ---------------------------------------------------------------------------

_OBJ3_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _OBJ3_DIR.parent


# ---------------------------------------------------------------------------
# Path Configuration
# ---------------------------------------------------------------------------

@dataclass
class Obj3PathConfig:
    """File-system paths consumed and produced by Objective 3."""

    project_root: Path = field(default_factory=lambda: _PROJECT_ROOT)
    objective3_dir: Path = field(default_factory=lambda: _OBJ3_DIR)

    # ── Inputs ──────────────────────────────────────────────────────────────
    # Objective 1 Validation_Corpus.json (list of execution records)
    objective1_corpus: Path = field(
        default_factory=lambda: _PROJECT_ROOT / "annotation" / "Validation_Corpus.json"
    )

    # Objective 2 per-task diagnosis files (directory of <trace_id>.json files)
    objective2_diagnosis_dir: Path = field(
        default_factory=lambda: _PROJECT_ROOT / "objective2" / "output" / "diagnosis"
    )

    # Generated code from Objective 1 (used in Mode A)
    generated_code_dir: Path = field(
        default_factory=lambda: _PROJECT_ROOT / "generated_code"
    )

    # Dataset prompt files (task specifications)
    prompts_dir: Path = field(
        default_factory=lambda: _PROJECT_ROOT / "prompts"
    )

    # ── Outputs ─────────────────────────────────────────────────────────────
    output_dir: Path = field(
        default_factory=lambda: _OBJ3_DIR / "output"
    )
    trajectories_dir: Path = field(default_factory=lambda: Path())
    repaired_code_dir: Path = field(default_factory=lambda: Path())
    executions_dir: Path = field(default_factory=lambda: Path())
    prompts_out_dir: Path = field(default_factory=lambda: Path())
    summaries_dir: Path = field(default_factory=lambda: Path())

    def __post_init__(self) -> None:
        if not self.trajectories_dir.name:
            self.trajectories_dir = self.output_dir / "trajectories"
        if not self.repaired_code_dir.name:
            self.repaired_code_dir = self.output_dir / "repaired_code"
        if not self.executions_dir.name:
            self.executions_dir = self.output_dir / "executions"
        if not self.prompts_out_dir.name:
            self.prompts_out_dir = self.output_dir / "prompts"
        if not self.summaries_dir.name:
            self.summaries_dir = self.output_dir / "summaries"

    def ensure_dirs(self) -> None:
        """Create all output directories if they do not already exist."""
        for attr_name, path in vars(self).items():
            if isinstance(path, Path) and (
                attr_name.endswith("_dir") or attr_name == "output_dir"
            ):
                path.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Ollama Configuration
# ---------------------------------------------------------------------------

@dataclass
class Obj3OllamaConfig:
    """Ollama LLM configuration for code generation and repair."""

    base_url: str = "http://localhost:11434"
    model: str = "codellama:13b"
    temperature: float = 0.2
    max_tokens: int = 4096
    request_timeout: int = 600   # seconds
    max_retries: int = 3
    retry_backoff: float = 2.0


# ---------------------------------------------------------------------------
# Execution Configuration
# ---------------------------------------------------------------------------

@dataclass
class Obj3ExecutionConfig:
    """Sandboxed code execution settings."""

    execution_timeout: float = 10.0   # seconds per execution
    python_executable: str = field(
        default_factory=lambda: (
            r"C:\Users\gsadaramodu\.local\bin\python3.14.exe"
            if Path(r"C:\Users\gsadaramodu\.local\bin\python3.14.exe").exists()
            else sys.executable
        )
    )


# ---------------------------------------------------------------------------
# Repair Controller Configuration
# ---------------------------------------------------------------------------

@dataclass
class Obj3ControllerConfig:
    """Closed-loop repair controller settings."""

    max_iterations: int = 5
    oscillation_window: int = 3         # number of recent programs to check
    escalation_threshold: int = 2       # same-error stalls before escalating


# ---------------------------------------------------------------------------
# Top-Level Objective 3 Configuration
# ---------------------------------------------------------------------------

@dataclass
class Objective3Config:
    """Aggregated configuration for all Objective 3 subsystems."""

    paths: Obj3PathConfig = field(default_factory=Obj3PathConfig)
    ollama: Obj3OllamaConfig = field(default_factory=Obj3OllamaConfig)
    execution: Obj3ExecutionConfig = field(default_factory=Obj3ExecutionConfig)
    controller: Obj3ControllerConfig = field(default_factory=Obj3ControllerConfig)
    log_level: str = "INFO"
    verbose: bool = False

    # Experiment hook: allows Objective 4 to inject condition labels
    experiment_condition: Optional[str] = None

    def __post_init__(self) -> None:
        self.paths.ensure_dirs()

    def to_dict(self) -> dict:
        """Serialise the full configuration to a plain dictionary."""
        import dataclasses

        def _convert(obj):
            if dataclasses.is_dataclass(obj):
                return {k: _convert(v) for k, v in dataclasses.asdict(obj).items()}
            if isinstance(obj, Path):
                return str(obj)
            return obj

        return _convert(self)
