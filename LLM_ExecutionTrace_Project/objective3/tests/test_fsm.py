"""Tests for Controller logic."""
import unittest

from objective3.controller.state import TaskStateMachine
from objective3.models import ControllerState

class TestStateMachine(unittest.TestCase):
    def test_state_transitions(self):
        fsm = TaskStateMachine("T01")
        self.assertEqual(fsm.current_state, ControllerState.INITIALIZED)
        
        fsm.transition_to(ControllerState.EXECUTING)
        self.assertEqual(fsm.current_state, ControllerState.EXECUTING)
        
        self.assertFalse(fsm.is_terminal())
        fsm.transition_to(ControllerState.SUCCESS)
        self.assertTrue(fsm.is_terminal())

if __name__ == "__main__":
    unittest.main()
