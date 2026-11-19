"""
Objective 3 — Repair Engine.

Orchestrates one complete repair attempt:
    1. Build the repair prompt (4-component, deterministic)
    2. Submit to Ollama repair model
    3. Parse the raw response
    4. Return the repair block and metadata

The repair engine is stateless — state is maintained by the controller.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from objective3.config import Objective3Config
from objective3.models import (
    BenchmarkTask,
    RepairStrategy,
    StructuredDiagnosticReport,
)
from objective3.ollama.client import OllamaClient
from objective3.ollama.generator import OllamaCodeGenerator
from objective3.repair.patch_parser import ParseResult, PatchParser
from objective3.repair.repair_prompt import RepairPromptBuilder
from objective3.repair.repair_strategy import RepairStrategySelector

logger = logging.getLogger(__name__)


@dataclass
class RepairResult:
    """Complete result of one repair engine invocation."""
    success: bool
    repair_prompt: str = ""
    raw_llm_response: str = ""
    repaired_code: str = ""
    model_used: str = ""
    temperature_used: float = 0.0
    duration_seconds: float = 0.0
    parse_result: Optional[ParseResult] = None
    error_message: str = ""

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "repair_prompt_length": len(self.repair_prompt),
            "raw_llm_response_length": len(self.raw_llm_response),
            "repaired_code_length": len(self.repaired_code),
            "model_used": self.model_used,
            "temperature_used": self.temperature_used,
            "duration_seconds": round(self.duration_seconds, 3),
            "parse_result": (
                self.parse_result.to_dict() if self.parse_result else None
            ),
            "error_message": self.error_message,
        }


class RepairEngine:
    """
    Executes one repair cycle:
      Diagnostic Report → Prompt → LLM → Parse → Repaired Code.

    Does not manage state or iterations — that is the controller's responsibility.
    """

    def __init__(
        self,
        config: Objective3Config,
        ollama_client: Optional[OllamaClient] = None,
    ) -> None:
        self.config = config
        self._ollama_client = ollama_client or OllamaClient(config.ollama)
        self._generator = OllamaCodeGenerator(self._ollama_client)
        self._prompt_builder = RepairPromptBuilder()
        self._patch_parser = PatchParser()
        self._strategy_selector = RepairStrategySelector()

    def repair(
        self,
        task: BenchmarkTask,
        diagnostic_report: StructuredDiagnosticReport,
        current_source: str,
        repair_strategy: RepairStrategy = RepairStrategy.LOCAL_MODIFICATION,
        iteration: int = 1,
        save_prompt_to: Optional[Path] = None,
    ) -> RepairResult:
        """
        Execute one repair attempt.

        Parameters
        ----------
        task               : Benchmark task (provides specification).
        diagnostic_report  : Objective 2 diagnostic report.
        current_source     : Current (failing) Python source code.
        repair_strategy    : Active repair strategy.
        iteration          : Current iteration number (for logging/saving).
        save_prompt_to     : If provided, save the prompt to this file.

        Returns
        -------
        RepairResult with success flag and all relevant data.
        """
        t0 = time.perf_counter()

        # ── Step 1: Build repair prompt ──────────────────────────────────────
        logger.info(
            "Building repair prompt (iter=%d, strategy=%s, diagnosis=%s).",
            iteration,
            repair_strategy.value,
            diagnostic_report.diagnosis_status.value,
        )
        try:
            prompt = self._prompt_builder.build(
                task=task,
                diagnostic_report=diagnostic_report,
                current_source=current_source,
                repair_strategy=repair_strategy,
                iteration=iteration,
            )
        except Exception as exc:
            logger.error("Failed to build repair prompt: %s", exc)
            return RepairResult(
                success=False,
                error_message=f"Prompt construction failed: {exc}",
                duration_seconds=time.perf_counter() - t0,
            )

        # Save prompt to file if requested
        if save_prompt_to:
            try:
                save_prompt_to.parent.mkdir(parents=True, exist_ok=True)
                save_prompt_to.write_text(prompt, encoding="utf-8")
            except Exception as exc:
                logger.warning("Could not save prompt to %s: %s", save_prompt_to, exc)

        # ── Step 2: Generate repair via Ollama ───────────────────────────────
        logger.info(
            "Submitting repair prompt to Ollama (model=%s).",
            self.config.ollama.model,
        )
        try:
            raw_response, model_used = self._generator.generate_repair(prompt)
        except Exception as exc:
            logger.error("Ollama generation failed: %s", exc)
            return RepairResult(
                success=False,
                repair_prompt=prompt,
                error_message=f"Ollama generation failed: {exc}",
                duration_seconds=time.perf_counter() - t0,
                model_used=self.config.ollama.model,
                temperature_used=self.config.ollama.temperature,
            )

        # ── Step 3: Parse the response ───────────────────────────────────────
        parse_result = self._patch_parser.parse(raw_response)

        duration = time.perf_counter() - t0

        if not parse_result.success:
            logger.warning(
                "Repair parse failed (iter=%d): %s",
                iteration,
                parse_result.error_message,
            )
            return RepairResult(
                success=False,
                repair_prompt=prompt,
                raw_llm_response=raw_response,
                model_used=model_used,
                temperature_used=self.config.ollama.temperature,
                duration_seconds=duration,
                parse_result=parse_result,
                error_message=parse_result.error_message,
            )

        logger.info(
            "Repair generated successfully (iter=%d, code_length=%d chars).",
            iteration,
            len(parse_result.extracted_code),
        )
        return RepairResult(
            success=True,
            repair_prompt=prompt,
            raw_llm_response=raw_response,
            repaired_code=parse_result.extracted_code,
            model_used=model_used,
            temperature_used=self.config.ollama.temperature,
            duration_seconds=duration,
            parse_result=parse_result,
        )

    def repair_structural_redesign(
        self,
        task: BenchmarkTask,
        current_source: str,
        error_history: str,
        iteration: int = 1,
    ) -> RepairResult:
        """
        Structural redesign fallback — used when no valid diagnostic report
        is available but escalation to STRUCTURAL_REDESIGN is required.
        """
        t0 = time.perf_counter()
        prompt = self._prompt_builder.build_structural_redesign_prompt(
            task=task,
            current_source=current_source,
            error_history=error_history,
        )
        try:
            raw_response, model_used = self._generator.generate_repair(prompt)
        except Exception as exc:
            return RepairResult(
                success=False,
                repair_prompt=prompt,
                error_message=f"Ollama generation failed: {exc}",
                duration_seconds=time.perf_counter() - t0,
            )
        parse_result = self._patch_parser.parse(raw_response)
        duration = time.perf_counter() - t0
        return RepairResult(
            success=parse_result.success,
            repair_prompt=prompt,
            raw_llm_response=raw_response,
            repaired_code=parse_result.extracted_code if parse_result.success else "",
            model_used=model_used,
            temperature_used=self.config.ollama.temperature,
            duration_seconds=duration,
            parse_result=parse_result,
            error_message="" if parse_result.success else parse_result.error_message,
        )
