# Objective 2 Annotation Schema & Guidelines

## Overview
This document specifies the human ground-truth annotation methodology for evaluating Objective 2's causal root cause analysis and fault localization system.

## Annotation Fields

1. **Task ID**: Unique benchmark identifier (e.g. `HE001`, `MB001`).
2. **Dataset**: `HumanEval` or `MBPP`.
3. **Generated Code**: Full source code of the LLM-generated function.
4. **Error Category**: Objective 1 classification (`Wrong-Output Error`, `Runtime Exception`, etc.).
5. **Human Root Cause**: High-level semantic explanation of why the failure occurred (e.g. *"Incorrect filtering condition selects odd elements instead of even elements"*).
6. **Human Fault Line**: Exact 1-indexed line number in the generated code where the defective statement resides.
7. **Human Fault Statement**: Exact text of the defective code line.
8. **Human Causal Variable**: Primary variable whose state mediates the failure (e.g. `total`, `count`).
9. **Evidence**: Supporting rationale from code inspection or test input/output analysis.
10. **Annotator ID**: Unique identifier for the annotator (e.g. `Annotator_1`, `Annotator_2`, `Annotator_3`).

## Annotator Agreement Protocol
- Minimum of 3 independent annotators per evaluated record.
- Majority vote aggregation determines consensus ground truth.
- Inter-annotator agreement is computed using **Fleiss' Kappa** ($\kappa$).
