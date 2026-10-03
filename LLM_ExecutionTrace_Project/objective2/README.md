# Objective 2: Causal Root Cause Analysis for LLM-Generated Code

## Research Objective

Objective 2 implements an independent causal diagnosis pipeline to determine the causal origin of semantic/execution failures in LLM-generated Python programs and locate the specific program statements responsible for those failures.

```
Specification (S) -> Generated Code (C) -> Execution Trace (E) -> Outcome (O)
                                                ^
                                                |
                                          Test Suite (T)
```

## Diagnosis Pipeline

```
Specification
     ↓
Generated Code
     ↓
Execution
     ↓
Program Dependency Graph (PDG)
     ↓
Runtime Evidence (sys.settrace)
     ↓
Candidate Causal Variables
     ↓
Counterfactual Intervention: do(X = x)
     ↓
Re-execution (Safe Process Sandbox)
     ↓
Root Cause Diagnosis
     ↓
Fault Location
```

## Key Architectural Principles

1. **Independent Implementation**: Objective 2 does NOT import or call `parser/classifier.py`, `parser/rules.py`, or `parser/taxonomy.py`. It operates purely on exported corpus files (`Validation_Corpus.json`, `.csv`, `.xlsx`, or execution log directories).
2. **Structural Causal Model (SCM)**: Explicit SCM graph artifacts ($S \to C \to E \to O$, $T \to E \to O$) exported to JSON and Graphviz DOT formats.
3. **Program Dependency Graph (PDG)**: Static AST parsing + Data Dependency analysis + Control Dependency analysis + Dynamic `sys.settrace` runtime event annotations.
4. **Counterfactual Intervention Engine**: Operationalizes Pearl's $do(X = x)$ through AST transformations and re-execution in isolated process sandboxes.
5. **Causal Criteria**: Recognizes $FAIL \to PASS$ outcomes as true causal evidence. $FAIL \to FAIL$ is non-causal evidence. Invalid states/timeouts are classified as `UNRESOLVED`.
6. **Ground Truth Evaluation**: Multi-annotator Fleiss' Kappa calculation and objective comparison against human ground truth.

---

## Directory Structure

```
objective2/
├── __init__.py
├── config.py
├── models.py
├── pipeline.py
├── main.py
├── README.md
├── input/
│   ├── corpus_loader.py
│   └── trace_loader.py
├── scm/
│   ├── variables.py
│   ├── graph.py
│   └── structural_model.py
├── pdg/
│   ├── ast_parser.py
│   ├── nodes.py
│   ├── data_dependencies.py
│   ├── control_dependencies.py
│   ├── runtime_trace.py
│   ├── runtime_annotator.py
│   ├── graph_builder.py
│   └── traversal.py
├── counterfactual/
│   ├── intervention.py
│   ├── expected_values.py
│   ├── executor.py
│   ├── evaluator.py
│   └── diagnosis.py
├── fault_localization/
│   ├── candidate_generator.py
│   ├── ranker.py
│   ├── locator.py
│   └── root_cause.py
├── annotation/
│   ├── annotation_schema.md
│   ├── fleiss_kappa.py
│   ├── ground_truth_builder.py
│   └── objective2_ground_truth.xlsx
├── exporters/
│   ├── json_exporter.py
│   ├── csv_exporter.py
│   └── excel_exporter.py
├── output/
│   ├── scm/
│   ├── pdg/
│   ├── runtime_traces/
│   ├── counterfactual/
│   ├── diagnosis/
│   └── reports/
└── tests/
    ├── test_ast_parser.py
    ├── test_scm.py
    ├── test_pdg.py
    ├── test_runtime_trace.py
    ├── test_counterfactual.py
    ├── test_fault_localization.py
    └── test_pipeline.py
```

---

## CLI Usage Examples

### 1. Default Execution on Full Validation Corpus
```bash
python -m objective2.main --input annotation/Validation_Corpus.json
```

### 2. Filter by Error Category
```bash
python -m objective2.main --input annotation/Validation_Corpus.json --error-type wrong-output
```

### 3. Analyze First 10 Records with Verbose Logging
```bash
python -m objective2.main --input annotation/Validation_Corpus.json --limit 10 --verbose
```

### 4. Target Specific Task ID
```bash
python -m objective2.main --input annotation/Validation_Corpus.json --task-id HE001
```

### 5. Evaluate Against Human Ground Truth
```bash
python -m objective2.main --input annotation/Validation_Corpus.json --ground-truth objective2/annotation/objective2_ground_truth.xlsx
```

---

## Output Artifacts

Upon completion, outputs are generated in `objective2/output/`:

- `reports/objective2_summary.json`: Global execution & accuracy metrics.
- `reports/Objective2_Results.xlsx`: Research-friendly multi-sheet Excel workbook (`Summary`, `Causal_Diagnosis`, `PDG_Evidence`, `Counterfactual_Results`, `Fault_Location`, `Runtime_Evidence`, `Ground_Truth`, `Error_Analysis`).
- `reports/objective2_results.csv`, `counterfactual_results.csv`, `fault_location_results.csv`.
- `diagnosis/{trace_id}.json`: Per-case machine-readable diagnosis record.
- `scm/{trace_id}.json` and `{trace_id}.dot`: SCM representation.
- `pdg/{trace_id}.json` and `{trace_id}.dot`: PDG structure with runtime annotations.
- `counterfactual/{trace_id}.json`: Per-case attempted counterfactual interventions.

---

## Running Unit Tests

Run the complete test suite:
```bash
pytest objective2/tests/ -v
```
