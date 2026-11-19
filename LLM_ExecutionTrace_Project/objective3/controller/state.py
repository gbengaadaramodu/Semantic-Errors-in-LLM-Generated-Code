"""
Objective 3 — State Machine.

Maintains the explicit finite-state controller tracking for a single task.
"""

from __future__ import annotations

import logging
from typing import List

from objective3.models import ControllerState

logger = logging.getLogger(__name__)


class TaskStateMachine:
    """Explicit state machine for the repair loop."""

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        self.current_state = ControllerState.INITIALIZED
        self.state_history: List[ControllerState] = [self.current_state]

    def transition_to(self, new_state: ControllerState) -> None:
        """Transition to a new state and record the transition."""
        logger.debug(
            "[Task %s] State transition: %s → %s",
            self.task_id,
            self.current_state.value,
            new_state.value,
        )
        self.current_state = new_state
        self.state_history.append(new_state)

    def is_terminal(self) -> bool:
        """Return True if the machine is in a terminal state."""
        return self.current_state in (
            ControllerState.SUCCESS,
            ControllerState.FAILED,
            ControllerState.TERMINATED,
        )
