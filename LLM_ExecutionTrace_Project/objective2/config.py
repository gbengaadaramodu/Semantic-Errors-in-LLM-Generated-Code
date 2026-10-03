"""
Objective 2 Configuration Module.

Provides path resolution, timeout parameters, sandbox controls, logging setup, 
and operational defaults using standard `pathlib.Path`.
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class Objective2Paths:
    """Directory paths for Objective 2 inputs and output artifacts."""

    project_root: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent
    )
    objective2_dir: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent
    )

    # Input paths
    validation_corpus_json: Path = field(default=Path())
    generated_code_dir: Path = field(default=Path())
    datasets_dir: Path = field(default=Path())
    selected_tasks_dir: Path = field(default=Path())

    # Output paths
    output_dir: Path = field(default=Path())
    scm_dir: Path = field(default=Path())
    pdg_dir: Path = field(default=Path())
    runtime_traces_dir: Path = field(default=Path())
    counterfactual_dir: Path = field(default=Path())
    diagnosis_dir: Path = field(default=Path())
    reports_dir: Path = field(default=Path())

    # Annotation / Ground truth
    annotation_dir: Path = field(default=Path())
    ground_truth_excel: Path = field(default=Path())

    def __post_init__(self) -> None:
        if not self.validation_corpus_json.name:
            self.validation_corpus_json = (
                self.project_root / "annotation" / "Validation_Corpus.json"
            )
        if not self.generated_code_dir.name:
            self.generated_code_dir = self.project_root / "generated_code"
        if not self.datasets_dir.name:
            self.datasets_dir = self.project_root / "datasets"
        if not self.selected_tasks_dir.name:
            self.selected_tasks_dir = self.project_root / "selected_tasks"

        if not self.output_dir.name:
            self.output_dir = self.objective2_dir / "output"

        self.scm_dir = self.output_dir / "scm"
        self.pdg_dir = self.output_dir / "pdg"
        self.runtime_traces_dir = self.output_dir / "runtime_traces"
        self.counterfactual_dir = self.output_dir / "counterfactual"
        self.diagnosis_dir = self.output_dir / "diagnosis"
        self.reports_dir = self.output_dir / "reports"

        self.annotation_dir = self.objective2_dir / "annotation"
        self.ground_truth_excel = (
            self.annotation_dir / "objective2_ground_truth.xlsx"
        )

    def ensure_directories(self) -> None:
        """Create all required output directories if they do not exist."""
        for d in [
            self.output_dir,
            self.scm_dir,
            self.pdg_dir,
            self.runtime_traces_dir,
            self.counterfactual_dir,
            self.diagnosis_dir,
            self.reports_dir,
            self.annotation_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)


@dataclass
class ExecutionConfig:
    """Sandbox and tracer execution configuration parameters."""

    sandbox_timeout: float = 5.0
    counterfactual_timeout: float = 5.0
    python_executable: str = field(
        default_factory=lambda: (
            r"C:\Users\gsadaramodu\.local\bin\python3.14.exe"
            if Path(r"C:\Users\gsadaramodu\.local\bin\python3.14.exe").exists()
            else sys.executable
        )
    )
    max_trace_events: int = 2000
    max_serialized_var_size: int = 1000


@dataclass
class CausalAnalysisConfig:
    """Causal analysis and candidate ranking configuration."""

    top_k: int = 5
    supported_error_types: List[str] = field(
        default_factory=lambda: [
            "Wrong-Output Error",
            "Runtime Exception",
        ]
    )
    random_seed: int = 42
    allow_all_errors: bool = False


@dataclass
class Objective2Config:
    """Global configuration object for Objective 2."""

    paths: Objective2Paths = field(default_factory=Objective2Paths)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    analysis: CausalAnalysisConfig = field(default_factory=CausalAnalysisConfig)
    verbose: bool = False
