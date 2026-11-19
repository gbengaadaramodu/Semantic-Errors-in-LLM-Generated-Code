"""
Objective 3 — Integrated Closed-Loop Self-Correction Architecture.

This package implements the closed-loop repair cycle described in:

    "Development of a Causal Diagnosis Model for Self-Correction
     in Large Language Model-Generated Code"

It consumes outputs from Objective 1 (error classification) and
Objective 2 (causal root-cause diagnosis) to drive iterative,
feedback-controlled code repair.

Feedback Paths
--------------
Path 1: Execution → Objective 1 error profile → Objective 2
Path 2: Objective 2 diagnostic report → Repair prompt → LLM → Repair
Path 3: Repaired execution outcome → State controller → Terminate/Re-diagnose/Escalate
"""

__version__ = "1.0.0"
__author__ = "PhD Research — Objective 3"
