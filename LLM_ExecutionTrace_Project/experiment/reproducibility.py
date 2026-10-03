"""
Metadata collection and reproducibility logging.

Generates an ``experiment.json`` file capturing the exact model,
environment, task selection, execution results, and classification
summary for full reproducibility of the experiment.
"""

import sys
import json
import platform
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from models import Task, ExecutionResult
from config import ProjectConfig
from ollama.client import OllamaClient

logger = logging.getLogger(__name__)


class ReproducibilityLogger:
    """Gathers and persists experiment metadata."""

    def __init__(self, config: ProjectConfig):
        self.config = config

    def collect_metadata(
        self,
        tasks: List[Task],
        results: List[ExecutionResult],
        classification_summary: Dict[str, int],
    ) -> dict:
        """Build the experiment.json metadata dictionary."""

        # Count pass/fail
        passed = sum(1 for r in results if r.execution_status == "Passed")
        failed = len(results) - passed

        # Query Ollama version
        try:
            client = OllamaClient(self.config.ollama)
            ollama_version = client.get_version()
        except Exception:
            ollama_version = "unknown"

        metadata = {
            "experiment_id": f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "model": {
                "name": self.config.ollama.model_name,
                "ollama_version": ollama_version,
                "temperature": self.config.ollama.temperature,
                "max_tokens": self.config.ollama.max_tokens,
            },
            "environment": {
                "python_version": sys.version,
                "platform": platform.platform(),
                "hostname": platform.node(),
            },
            "task_selection": {
                "random_seed": self.config.task_selection.random_seed,
                "humaneval_count": self.config.task_selection.humaneval_sample_size,
                "mbpp_count": self.config.task_selection.mbpp_sample_size,
                "humaneval_task_ids": [
                    t.task_id for t in tasks if t.dataset == "HumanEval"
                ],
                "mbpp_task_ids": [
                    t.task_id for t in tasks if t.dataset == "MBPP"
                ],
            },
            "execution": {
                "timeout_seconds": self.config.execution.execution_timeout,
                "total_tasks": len(tasks),
                "passed": passed,
                "failed": failed,
            },
            "classification_summary": classification_summary,
        }
        return metadata

    @staticmethod
    def save(metadata: dict, output_path: Path) -> None:
        """Write metadata dict to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as fh:
            json.dump(metadata, fh, indent=2, default=str)
        logger.info("Saved experiment metadata → %s", output_path)
