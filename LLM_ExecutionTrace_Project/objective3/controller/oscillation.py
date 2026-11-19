"""
Objective 3 — Oscillation Detector.

Oscillation occurs when two non-identical programs produce the same
error signature within a recent window of iterations.
Example: Program A → Error X, Program B → Error X, where A != B.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from typing import List

from objective3.config import Obj3ControllerConfig
from objective3.models import ErrorSignature

logger = logging.getLogger(__name__)


@dataclass
class ProgramStateRecord:
    iteration: int
    source_hash: str
    error_signature: ErrorSignature


class OscillationDetector:
    """
    Tracks program states across iterations to detect oscillation loops.
    """

    def __init__(self, config: Obj3ControllerConfig) -> None:
        self.config = config
        self.history: List[ProgramStateRecord] = []

    def record_state(
        self, iteration: int, source_code: str, error_signature: ErrorSignature
    ) -> bool:
        """
        Record the state and return True if oscillation is detected.
        """
        source_hash = self._hash_source(source_code)
        
        # Check for oscillation in the recent history window
        window = self.config.oscillation_window
        recent_history = self.history[-window:] if window > 0 else self.history

        oscillation = False
        for record in recent_history:
            # Same error signature but different source code
            if (
                record.error_signature == error_signature
                and record.source_hash != source_hash
            ):
                logger.warning(
                    "Oscillation detected! Iteration %d has same error signature as "
                    "iteration %d but different source code.",
                    iteration,
                    record.iteration,
                )
                oscillation = True
                break

        # Record this state
        self.history.append(
            ProgramStateRecord(iteration, source_hash, error_signature)
        )
        
        return oscillation

    def _hash_source(self, source: str) -> str:
        """Create a hash of the normalized source code."""
        # Simple normalization: strip trailing whitespace from each line
        normalized = "\n".join(line.rstrip() for line in source.splitlines())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def reset(self) -> None:
        """Reset the history for a new task."""
        self.history.clear()
