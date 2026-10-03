"""
LLM Execution Trace Project — Global Configuration

Central configuration for all tuneable parameters used across
the project pipeline: paths, Ollama settings, task selection,
and execution constraints.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import sys



# ──────────────────────────────────────────────
#  Resolve project root (directory containing this file)
# ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent


@dataclass
class PathConfig:
    """All file-system paths, resolved relative to PROJECT_ROOT."""

    project_root: Path = PROJECT_ROOT

    # Input datasets
    datasets_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "datasets")
    humaneval_path: Path = field(
        default_factory=lambda: PROJECT_ROOT / "datasets" / "HumanEval.csv"
    )
    mbpp_path: Path = field(
        default_factory=lambda: PROJECT_ROOT / "datasets" / "sanitized-mbpp.json"
    )

    # Selected task lists
    selected_tasks_dir: Path = field(
        default_factory=lambda: PROJECT_ROOT / "selected_tasks"
    )
    humaneval_selected: Path = field(
        default_factory=lambda: PROJECT_ROOT / "selected_tasks" / "humaneval_150.csv"
    )
    mbpp_selected: Path = field(
        default_factory=lambda: PROJECT_ROOT / "selected_tasks" / "mbpp_150.csv"
    )

    # Prompt archive
    prompts_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "prompts")

    # Generated code
    generated_code_dir: Path = field(
        default_factory=lambda: PROJECT_ROOT / "generated_code"
    )

    # Execution logs
    execution_logs_dir: Path = field(
        default_factory=lambda: PROJECT_ROOT / "execution_logs"
    )

    # Annotation outputs
    annotation_dir: Path = field(
        default_factory=lambda: PROJECT_ROOT / "annotation"
    )

    # Reports
    reports_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "reports")
    figures_dir: Path = field(
        default_factory=lambda: PROJECT_ROOT / "reports" / "figures"
    )

    def ensure_dirs(self) -> None:
        """Create all output directories if they do not exist."""
        for attr_name in vars(self):
            path = getattr(self, attr_name)
            if isinstance(path, Path) and attr_name.endswith("_dir"):
                path.mkdir(parents=True, exist_ok=True)


@dataclass
class OllamaConfig:
    """Ollama / Code Llama generation settings."""

    model_name: str = "codellama:13b"
    base_url: str = "http://localhost:11434"
    temperature: float = 0.0
    max_tokens: int = 2048
    request_timeout: int = 120        # seconds per HTTP request
    max_retries: int = 3
    retry_backoff: float = 2.0        # exponential backoff multiplier


@dataclass
class TaskSelectionConfig:
    """Random sampling parameters for task selection."""

    humaneval_sample_size: int = 164
    mbpp_sample_size: int = 809
    random_seed: int = 42


@dataclass
class ExecutionConfig:
    """Settings for code execution and sandboxing."""

    execution_timeout: float = 5.0    # seconds per task execution
    python_executable: str = field(
        default_factory=lambda: (
            r"C:\Users\gsadaramodu\.local\bin\python3.14.exe"
            if Path(r"C:\Users\gsadaramodu\.local\bin\python3.14.exe").exists()
            else sys.executable
        )
    )


@dataclass
class ProjectConfig:
    """Top-level configuration aggregating all sub-configs."""

    paths: PathConfig = field(default_factory=PathConfig)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    task_selection: TaskSelectionConfig = field(default_factory=TaskSelectionConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)

    def __post_init__(self) -> None:
        self.paths.ensure_dirs()

    def to_dict(self) -> dict:
        """Serialise the full configuration to a plain dictionary."""
        import dataclasses

        def _convert(obj):
            if dataclasses.is_dataclass(obj):
                return {
                    k: _convert(v)
                    for k, v in dataclasses.asdict(obj).items()
                }
            if isinstance(obj, Path):
                return str(obj)
            return obj

        return _convert(self)
