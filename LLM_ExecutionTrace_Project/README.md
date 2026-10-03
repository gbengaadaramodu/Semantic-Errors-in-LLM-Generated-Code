# LLM Execution Trace & Causal Diagnosis Pipeline

This directory contains the core implementation of the research pipeline for:
1. **Objective 1**: Automated error taxonomy classification (`parser/`, `executor/`, `main.py`).
2. **Objective 2**: Causal root cause analysis and fault localization (`objective2/`).

---

## Directory Overview

- `main.py`: CLI entry point for task selection, code generation, execution, classification, and export.
- `config.py`: Global configuration parameters and directory paths.
- `models.py`: Shared data models (`Task`, `ExecutionResult`, `ErrorCategory`).
- `evaluate_reproducibility.py`: Reproducibility verification script.
- `datasets/`: HumanEval and MBPP benchmark datasets.
- `prompts/`: 300 assembled Code Llama prompts.
- `generated_code/`: 300 generated Python programs from Code Llama 13B.
- `execution_logs/`: Per-task runtime execution traces.
- `executor/`: Sandboxed subprocess runner and timing instrumentation.
- `parser/`: Rule-based error classifier and 5-category taxonomy.
- `annotation/`: Validation corpora and human annotator response workbooks.
- `objective2/`: Causal diagnosis engine (SCM, PDG, counterfactual intervention, fault localization).

---

## Quick Usage

```bash
# 1. Run all reproducibility verifications (Fleiss' Kappa, accuracy, test suite)
python evaluate_reproducibility.py

# 2. Run unit tests
python -m unittest discover -s objective2/tests

# 3. Run Objective 1 classification & export
python main.py classify
python main.py export

# 4. Run Objective 2 causal fault localization
python -m objective2.main --input annotation/Validation_Corpus_100.json
```

For complete documentation and reviewer reproduction protocol, please see the top-level [README.md](../README.md) and [REPRODUCIBILITY.md](../REPRODUCIBILITY.md).
