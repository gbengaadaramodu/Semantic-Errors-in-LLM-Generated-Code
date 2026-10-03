# Reproducibility Guide & Reviewer Protocol

This document provides a reviewer-focused reproduction protocol for the research paper:
> **"A Diagnostic Model and Causal Root Cause Analysis Framework for LLM-Generated Code"**

---

## 1. Artifact Highlights & Claims

The artifact evaluates two primary research objectives:

| Objective | Focus | Key Claim / Finding | Verification Mechanism |
|---|---|---|---|
| **Objective 1** | Automated Error Taxonomy Classification | 5-category diagnostic taxonomy; **$\kappa = 0.9865$** Fleiss' Kappa across 3 annotators; **$99.67\%$** automated classifier accuracy against human ground truth on 300 validation traces. | Run `python evaluate_reproducibility.py` or inspect `LLM_ExecutionTrace_Project/annotation/obj1_response/` |
| **Objective 2** | Causal Fault Localization & Root Cause Analysis | SCM and PDG-guided counterfactual interventions ($do(X=x)$) diagnose semantic failures and locate root causes on held-out tasks with **$100\%$** human line agreement across 100 cases. | Run `python -m objective2.main` or inspect `LLM_ExecutionTrace_Project/objective2/output/reports/` |

---

## 2. Requirements & Environment Setup

### Prerequisites
- Python **3.10+** (tested on Python 3.10, 3.11, 3.12, 3.14).
- Operating System: **Windows, Linux (Ubuntu 20.04+), or macOS**.
- Git.

### Setup Instructions

```bash
# Clone repository
git clone <REPOSITORY_URL>
cd <REPOSITORY_NAME>

# (Recommended) Create and activate a clean virtual environment
python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Windows (cmd):
.venv\Scripts\activate.bat

# Install minimal dependencies (openpyxl, requests, pandas)
pip install -r requirements.txt
```

---

## 3. Step 1: One-Minute Sanity Verification (Quick Start)

To quickly reproduce the empirical metrics reported in the paper, run the bundled verification script from the repository root:

```bash
python evaluate_reproducibility.py
```

### Expected Output Summary
```text
==============================================================================
  RESEARCH ARTIFACT EVALUATION & REPRODUCIBILITY VERIFICATION
==============================================================================

1. BENCHMARK DATASET & VALIDATION CORPUS INTEGRITY
   - HumanEval benchmark:     [EXISTS] (196,170 bytes)
   - MBPP benchmark:          [EXISTS] (255,053 bytes)
   - Validation Corpus:       [EXISTS] (591 traces captured)

2. OBJECTIVE 1: ERROR TAXONOMY CLASSIFICATION & INTER-ANNOTATOR AGREEMENT
   - Validation traces:       300 traces
   - Annotators:              3 (Abayomi, James, John)
   - Categories:              Assertion Failure, Runtime Exception, Syntax Error, Timeout Error, Wrong-Output Error
   - Fleiss' Kappa (k):       0.9865 (Almost Perfect Agreement)
   - Classifier Accuracy:     299/300 (99.67%) vs Human Majority

3. OBJECTIVE 2: CAUSAL FAULT LOCALIZATION & INTERVENTION EVALUATION
   - Held-Out Cases:          100 execution failure tasks
   - 3-Way Human Agreement:   100/100 (100.0%)
   - Counterfactual Success:  47/677 (6.9% repair rate)

4. AUTOMATED TEST SUITE VERIFICATION
   - Tests run: 10
   - Failures: 0, Errors: 0 -> [PASSED]
==============================================================================
```

---

## 4. Step 2: Running the Automated Unit Test Suite

Run unit tests verifying the static AST parser, dynamic runtime tracer (`sys.settrace`), Program Dependency Graph (PDG) construction, Structural Causal Model (SCM), counterfactual engine, and fault locator:

```bash
cd LLM_ExecutionTrace_Project
python -m unittest discover -s objective2/tests
```

**Expected Result**: All 10 unit tests pass (`Ran 10 tests in ~0.8s ... OK`).

---

## 5. Step 3: Reproducing Objective 1 (Error Classification Pipeline)

Objective 1 classifies execution logs into the 5-category diagnostic taxonomy:
1. `Syntax Error`
2. `Runtime Exception`
3. `Wrong-Output Error`
4. `Assertion Failure`
5. `Timeout Error`
*(and `Correct` for fully passing programs).*

### A. Run rule-based classification over existing execution logs:
```bash
cd LLM_ExecutionTrace_Project
python main.py classify
```
This inspects `execution_logs/`, applies the classification taxonomy in `parser/rules.py`, and updates internal classification states.

### B. Export the validation corpus:
```bash
python main.py export
```
Exports updated Excel, CSV, and JSON representations to `annotation/Validation_Corpus.xlsx`, `annotation/Validation_Corpus.csv`, and `annotation/Validation_Corpus.json`.

---

## 6. Step 4: Reproducing Objective 2 (Causal Fault Localization)

Objective 2 carries out causal diagnosis and fault localization on failing programs via:
1. **Dynamic Execution Tracing**: Capturing line-by-line runtime events via `sys.settrace`.
2. **Program Dependency Graph (PDG)**: Combining AST data and control dependencies with dynamic runtime state.
3. **Counterfactual Intervention Engine**: Generating intervention values ($do(X = x)$) and executing in an isolated process sandbox.
4. **Fault Localization**: Ranking candidates by causal evidence ($FAIL \to PASS$).

### Execute Causal Analysis on the Corpus:
```bash
cd LLM_ExecutionTrace_Project

# Run on the 100 held-out cases
python -m objective2.main --input annotation/Validation_Corpus_100.json

# Or run with a limit for rapid inspection (e.g., first 5 cases with verbose output)
python -m objective2.main --limit 5 --verbose

# Target a specific trace (e.g., HE001)
python -m objective2.main --task-id HE001 --verbose
```

### Generated Artifacts
Outputs are written to `LLM_ExecutionTrace_Project/objective2/output/`:
- `reports/Objective2_Results.xlsx`: Comprehensive multi-sheet Excel workbook (`Summary`, `Causal_Diagnosis`, `PDG_Evidence`, `Counterfactual_Results`, `Fault_Location`, `Runtime_Evidence`, `Ground_Truth`, `Error_Analysis`).
- `reports/fault_location_results.csv`: Ranked fault lines for each analyzed program.
- `reports/counterfactual_results.csv`: Complete intervention records ($do(X=x)$).
- `diagnosis/{trace_id}.json`: Detailed per-task causal diagnosis.
- `pdg/{trace_id}.json` and `{trace_id}.dot`: Machine-readable PDGs and Graphviz DOT graphs.
- `scm/{trace_id}.json` and `{trace_id}.dot`: SCM structural graphs.

---

## 7. Step 5: (Optional) Full Pipeline Execution from Scratch

The repository includes all pre-generated code, prompts, and execution traces so reviewers can perform complete evaluations without local GPU / LLM infrastructure.

However, if you wish to run the full generative pipeline with Ollama:

1. Install [Ollama](https://ollama.ai) and pull Code Llama 13B:
   ```bash
   ollama pull codellama:13b
   ollama serve
   ```
2. Run the end-to-end pipeline:
   ```bash
   cd LLM_ExecutionTrace_Project
   python main.py run-all
   ```
   *(Or test on a subset using `--limit 5`)*.

---

## 8. Paper-to-Artifact Mapping

| Paper Element | Description | Corresponding File / Directory in Artifact |
|---|---|---|
| **Section 3.1 / 4.2** | Benchmark Datasets (HumanEval, MBPP) | `LLM_ExecutionTrace_Project/datasets/HumanEval.csv`, `sanitized-mbpp.json` |
| **Section 3.2** | Task Selection Protocol (Random seed = 42) | `LLM_ExecutionTrace_Project/selected_tasks/` |
| **Section 3.3** | Code Generation & Prompts (Code Llama 13B) | `LLM_ExecutionTrace_Project/prompts/`, `generated_code/` |
| **Section 3.4** | Sandboxed Execution & Runtime Traces | `LLM_ExecutionTrace_Project/executor/`, `execution_logs/` |
| **Section 3.5 / 4.3** | 5-Category Diagnostic Taxonomy & Classifier | `LLM_ExecutionTrace_Project/parser/`, `annotation/Validation_Corpus.*` |
| **Section 4.3.1** | Human Annotator Protocol (3 Annotators) | `LLM_ExecutionTrace_Project/annotation/obj1_response/` |
| **Section 4.3.2** | Inter-Annotator Agreement (Fleiss' Kappa) | `LLM_ExecutionTrace_Project/objective2/annotation/fleiss_kappa.py` |
| **Section 4.4 / Obj 2** | Structural Causal Model (SCM) | `LLM_ExecutionTrace_Project/objective2/scm/` |
| **Section 4.4 / Obj 2** | Dynamic PDG (`sys.settrace`) | `LLM_ExecutionTrace_Project/objective2/pdg/` |
| **Section 4.4 / Obj 2** | Counterfactual Engine ($do(X=x)$) | `LLM_ExecutionTrace_Project/objective2/counterfactual/` |
| **Section 4.5** | Fault Localization Results | `LLM_ExecutionTrace_Project/objective2/output/reports/` |
| **Section 4.5.1** | Objective 2 Human Ground Truth (100 cases) | `LLM_ExecutionTrace_Project/annotation/obj2_response/` |
