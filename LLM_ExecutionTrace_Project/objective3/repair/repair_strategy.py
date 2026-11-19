"""
Objective 3 — Repair Strategy Selector.

Escalates the repair strategy when the same error repeats or oscillation
is detected. The escalation ladder is:

    LOCAL_MODIFICATION
        ↓ (same-error stall)
    BROADER_LOCAL_MODIFICATION
        ↓ (oscillation or repeated stall)
    STRUCTURAL_REDESIGN
"""

from __future__ import annotations

import logging
from typing import List

from objective3.models import (
    ErrorSignature,
    RepairStrategy,
)

logger = logging.getLogger(__name__)


class RepairStrategySelector:
    """
    Determines the appropriate repair strategy for a given controller state.

    The selector is stateless — it takes the current signature history and
    escalation counter and returns the next strategy deterministically.
    """

    ESCALATION_LADDER: List[RepairStrategy] = [
        RepairStrategy.LOCAL_MODIFICATION,
        RepairStrategy.BROADER_LOCAL_MODIFICATION,
        RepairStrategy.STRUCTURAL_REDESIGN,
    ]

    def select(
        self,
        current_strategy: RepairStrategy,
        same_error_count: int,
        oscillation_detected: bool,
        escalation_threshold: int = 2,
    ) -> tuple[RepairStrategy, bool]:
        """
        Return (next_strategy, escalated).

        Escalation occurs when:
          - same_error_count >= escalation_threshold, OR
          - oscillation_detected is True

        Parameters
        ----------
        current_strategy      : Current repair strategy in use.
        same_error_count      : How many consecutive iterations produced the same error signature.
        oscillation_detected  : Whether the oscillation detector fired.
        escalation_threshold  : Same-error stall count before escalating (default 2).

        Returns
        -------
        (RepairStrategy, bool)  The next strategy and whether escalation occurred.
        """
        should_escalate = (
            same_error_count >= escalation_threshold or oscillation_detected
        )

        if not should_escalate:
            return current_strategy, False

        # Find current position in ladder and advance
        try:
            idx = self.ESCALATION_LADDER.index(current_strategy)
        except ValueError:
            idx = 0

        next_idx = min(idx + 1, len(self.ESCALATION_LADDER) - 1)
        next_strategy = self.ESCALATION_LADDER[next_idx]

        if next_strategy == current_strategy:
            logger.warning(
                "Already at maximum strategy %s; cannot escalate further.",
                current_strategy.value,
            )
            return current_strategy, False

        logger.info(
            "Strategy escalated: %s → %s (same_error_count=%d, oscillation=%s)",
            current_strategy.value,
            next_strategy.value,
            same_error_count,
            oscillation_detected,
        )
        return next_strategy, True

    def strategy_for_new_error(
        self, previous_strategy: RepairStrategy
    ) -> RepairStrategy:
        """
        When a NEW_ERROR appears, reset to LOCAL_MODIFICATION unless the
        previous strategy was already STRUCTURAL_REDESIGN (preserve escalation
        to avoid cycling).
        """
        if previous_strategy == RepairStrategy.STRUCTURAL_REDESIGN:
            return RepairStrategy.STRUCTURAL_REDESIGN
        return RepairStrategy.LOCAL_MODIFICATION

    @staticmethod
    def strategy_label(strategy: RepairStrategy) -> str:
        """Human-readable strategy description for prompt injection."""
        labels = {
            RepairStrategy.LOCAL_MODIFICATION: (
                "Perform a targeted local modification at the identified fault location."
            ),
            RepairStrategy.BROADER_LOCAL_MODIFICATION: (
                "Perform a broader correction around the identified fault location, "
                "considering the enclosing block and related logic."
            ),
            RepairStrategy.STRUCTURAL_REDESIGN: (
                "Previous local modifications failed to resolve the failure. "
                "Redesign the faulty functional block using an alternative implementation "
                "strategy while preserving the function signature and specification."
            ),
        }
        return labels.get(strategy, "Repair the identified defect.")
