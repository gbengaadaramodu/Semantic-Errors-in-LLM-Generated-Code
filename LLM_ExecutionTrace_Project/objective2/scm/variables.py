"""
SCM Variables Module.

Defines standard high-level SCM variables:
    S = Specification / Problem Prompt
    C = LLM-Generated Source Code
    E = Runtime Execution Trace & Variable States
    T = Benchmark Test Suite
    O = Observed Outcome (Completed/Failed)
"""

from typing import Dict
from objective2.models import SCMVariable


class SCMVariables:
    """Factory and manager for standard SCM variables."""

    @staticmethod
    def create_default_variables() -> Dict[str, SCMVariable]:
        return {
            "S": SCMVariable(
                name="Specification",
                symbol="S",
                description="Problem description, prompt, and target function signature",
            ),
            "C": SCMVariable(
                name="GeneratedCode",
                symbol="C",
                description="LLM-generated Python source code implementation",
            ),
            "E": SCMVariable(
                name="ExecutionTrace",
                symbol="E",
                description="Observable runtime trace events, variable states, and stdout/stderr",
            ),
            "T": SCMVariable(
                name="TestSuite",
                symbol="T",
                description="Benchmark assertions, inputs, and check function harness",
            ),
            "O": SCMVariable(
                name="Outcome",
                symbol="O",
                description="Final test execution outcome (Completed/Failed/Timeout)",
            ),
        }
