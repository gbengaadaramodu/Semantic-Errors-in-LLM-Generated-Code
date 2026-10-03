"""
Objective 2 Pipeline Orchestrator.

Coordinates the complete Causal Root Cause Analysis workflow:
Corpus Load -> Case Selection -> AST / Static PDG -> sys.settrace Runtime Tracing ->
Dynamic Annotation -> Failure Identification -> Reverse Traversal -> Candidate Cause Generation ->
Expected Value Inference -> Counterfactual Interventions -> Safe Sandbox Re-Execution ->
Causal Effect Evaluation -> Candidate Ranking -> Fault Localization -> Root Cause Diagnosis ->
Ground Truth Comparison -> Multi-format Export.
"""

import logging
import os
import re
import sys
import tempfile
import time
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from objective2.annotation.ground_truth_builder import GroundTruthBuilder
from objective2.config import Objective2Config
from objective2.counterfactual.diagnosis import CounterfactualDiagnoser
from objective2.exporters.csv_exporter import CSVExporter
from objective2.exporters.excel_exporter import ExcelExporter
from objective2.exporters.json_exporter import JSONExporter
from objective2.fault_localization.candidate_generator import FaultCandidateGenerator
from objective2.fault_localization.locator import FaultLocator
from objective2.fault_localization.ranker import CandidateRanker
from objective2.fault_localization.root_cause import RootCauseDiagnoser
from objective2.input.corpus_loader import CorpusLoader
from objective2.input.trace_loader import TraceLoader
from objective2.models import (
    AnalysisStatus,
    CausalEffect,
    Objective2InputRecord,
    Objective2Result,
    Objective2Summary,
)
from objective2.pdg.graph_builder import PDGGraphBuilder
from objective2.pdg.runtime_trace import RuntimeTracer
from objective2.scm.structural_model import SCMBuilder

logger = logging.getLogger(__name__)


class Objective2Pipeline:
    """
    Orchestrates the Objective 2 Causal Diagnosis Research Pipeline.
    """

    def __init__(self, config: Optional[Objective2Config] = None) -> None:
        self.config = config or Objective2Config()
        self.corpus_loader = CorpusLoader(self.config.paths.validation_corpus_json)
        self.trace_loader = TraceLoader(self.config.paths)
        self.pdg_builder = PDGGraphBuilder()
        self.candidate_generator = FaultCandidateGenerator()
        self.diagnoser = CounterfactualDiagnoser(self.config.execution)
        self.ranker = CandidateRanker()
        self.locator = FaultLocator()
        self.root_cause_diagnoser = RootCauseDiagnoser()
        self.gt_builder = GroundTruthBuilder()

    def run(
        self,
        input_path: Optional[Path] = None,
        error_type_filter: Optional[str] = None,
        dataset_filter: Optional[str] = None,
        task_id_filter: Optional[str] = None,
        limit: Optional[int] = None,
        ground_truth_path: Optional[Path] = None,
    ) -> Tuple[List[Objective2Result], Objective2Summary]:
        logger.info("=" * 60)
        logger.info("  Starting Objective 2 Causal Diagnosis Pipeline")
        logger.info("=" * 60)

        if input_path:
            self.corpus_loader = CorpusLoader(input_path)

        # 1. Load corpus
        all_records = self.corpus_loader.load_records()
        total_corpus_size = len(all_records)

        # 2. Case Selection
        eligible_records = self._select_cases(
            all_records,
            error_type_filter=error_type_filter,
            dataset_filter=dataset_filter,
            task_id_filter=task_id_filter,
            limit=limit,
        )

        results: List[Objective2Result] = []
        analyzed_count = 0
        skipped_count = total_corpus_size - len(eligible_records)
        failed_count = 0
        unresolved_count = 0

        # Load ground truth if provided
        gt_data: Dict[str, dict] = {}
        gt_file = ground_truth_path or self.config.paths.ground_truth_excel
        if gt_file.exists():
            gt_data = self.gt_builder.load_ground_truth(gt_file)

        # Process each eligible record independently
        for idx, record in enumerate(eligible_records, 1):
            logger.info(
                "Analyzing case %d/%d: %s (%s - %s)",
                idx,
                len(eligible_records),
                record.trace_id,
                record.dataset,
                record.parser_prediction or record.execution_status,
            )
            res = self.analyze_single_case(record, gt_data.get(record.trace_id))
            results.append(res)

            if res.analysis_status == AnalysisStatus.ANALYZED:
                analyzed_count += 1
                if res.root_cause and not res.root_cause.counterfactual_validated:
                    unresolved_count += 1
            elif res.analysis_status == AnalysisStatus.FAILED:
                failed_count += 1
            elif res.analysis_status == AnalysisStatus.UNRESOLVED:
                unresolved_count += 1

        # Calculate metrics
        summary = self._compute_summary(
            total_corpus_size=total_corpus_size,
            eligible_cases=len(eligible_records),
            analyzed_cases=analyzed_count,
            skipped_cases=skipped_count,
            unresolved_cases=unresolved_count,
            failed_cases=failed_count,
            results=results,
            has_ground_truth=bool(gt_data),
        )

        # 3. Export
        logger.info("Exporting results to JSON, CSV, and Excel...")
        JSONExporter(self.config.paths).export_all(results, summary)
        CSVExporter(self.config.paths).export(results)
        ExcelExporter(self.config.paths).export(results, summary)

        logger.info("Objective 2 Pipeline Completed Successfully.")
        return results, summary

    def analyze_single_case(
        self, record: Objective2InputRecord, gt_info: Optional[dict] = None
    ) -> Objective2Result:
        t0 = time.perf_counter()
        # Enrich code and test definitions
        record = self.trace_loader.enrich_record(record)

        if not record.generated_code.strip():
            return Objective2Result(
                trace_id=record.trace_id,
                dataset=record.dataset,
                task_id=record.task_id,
                error_category=record.parser_prediction or record.execution_status,
                analysis_status=AnalysisStatus.SKIPPED,
                skip_reason="Missing generated source code file",
                input_record=record,
                execution_time=round(time.perf_counter() - t0, 4),
            )

        try:
            # 1. Build SCM
            scm = SCMBuilder.build(record)

            # 2. Run runtime tracer on generated code script
            runtime_events = self._trace_execution(record)

            # 3. Determine failure line from traceback / exception / assertions
            failure_line = self._extract_failure_line(record)

            # 4. Build Dynamic PDG
            pdg = self.pdg_builder.build_pdg(
                source_code=record.generated_code,
                events=runtime_events,
                failure_line=failure_line,
            )

            # Extract failure statement
            failure_stmt = None
            if failure_line and pdg.nodes:
                for n in pdg.nodes.values():
                    if n.line_number == failure_line:
                        failure_stmt = n.source_code
                        break

            # 5. Reverse PDG traversal -> candidate cause generation
            candidates = self.candidate_generator.generate_candidates(
                pdg, top_k=self.config.analysis.top_k
            )

            # 6. Counterfactual diagnosis over candidates
            cf_results = self.diagnoser.diagnose_candidates(record, candidates)

            # 7. Candidate ranking
            ranked_pairs = self.ranker.rank(candidates, cf_results)

            # 8. Fault location
            fault_loc = self.locator.locate_fault(record, ranked_pairs, cf_results)

            # Identify top counterfactual result
            top_cf = cf_results[0] if cf_results else None

            # 9. Root cause diagnosis
            root_cause = self.root_cause_diagnoser.diagnose(record, fault_loc, top_cf)

            # 10. Ground truth comparison
            gt_matched = None
            gt_fault_line = None
            if gt_info and fault_loc:
                gt_line = gt_info.get("Human Fault Line")
                if gt_line is not None:
                    try:
                        gt_fault_line = int(gt_line)
                        gt_matched = (fault_loc.line_number == gt_fault_line)
                    except ValueError:
                        pass

            exec_time = round(time.perf_counter() - t0, 4)

            return Objective2Result(
                trace_id=record.trace_id,
                dataset=record.dataset,
                task_id=record.task_id,
                error_category=record.parser_prediction or record.execution_status,
                analysis_status=AnalysisStatus.ANALYZED,
                input_record=record,
                scm=scm,
                pdg=pdg,
                runtime_events_count=len(runtime_events),
                failure_line=failure_line,
                failure_statement=failure_stmt,
                candidates=[pair[0] for pair in ranked_pairs],
                counterfactual_results=cf_results,
                fault_location=fault_loc,
                root_cause=root_cause,
                ground_truth_matched=gt_matched,
                ground_truth_fault_line=gt_fault_line,
                execution_time=exec_time,
            )

        except Exception as exc:
            logger.error("Unhandled error analyzing %s: %s", record.trace_id, exc, exc_info=True)
            return Objective2Result(
                trace_id=record.trace_id,
                dataset=record.dataset,
                task_id=record.task_id,
                error_category=record.parser_prediction or record.execution_status,
                analysis_status=AnalysisStatus.FAILED,
                skip_reason=f"Pipeline exception: {type(exc).__name__} - {exc}",
                input_record=record,
                execution_time=round(time.perf_counter() - t0, 4),
            )

    def _select_cases(
        self,
        records: List[Objective2InputRecord],
        error_type_filter: Optional[str],
        dataset_filter: Optional[str],
        task_id_filter: Optional[str],
        limit: Optional[int],
    ) -> List[Objective2InputRecord]:
        selected = []

        supported = set(
            e.lower() for e in self.config.analysis.supported_error_types
        )

        for rec in records:
            pred = (rec.parser_prediction or rec.execution_status).strip()

            # Task ID filter
            if task_id_filter and task_id_filter.lower() not in (
                rec.task_id.lower(),
                rec.trace_id.lower(),
            ):
                continue

            # Dataset filter
            if dataset_filter and dataset_filter.lower() not in rec.dataset.lower():
                continue

            # Error type filter
            if error_type_filter and error_type_filter.lower() != "all":
                if error_type_filter.lower() not in pred.lower():
                    continue
            elif not self.config.analysis.allow_all_errors:
                if "correct" in pred.lower() and "incorrect" not in pred.lower():
                    continue
                # Default selection prioritizing failures
                if not any(s in pred.lower() for s in ("wrong-output", "runtime", "failed", "assertion", "timeout", "syntax")):
                    continue

            selected.append(rec)
            if limit and len(selected) >= limit:
                break

        logger.info(
            "Selected %d eligible cases out of %d total corpus records.",
            len(selected),
            len(records),
        )
        return selected

    def _trace_execution(self, record: Objective2InputRecord) -> list:
        """Run execution of generated code with sys.settrace tracer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / f"{record.trace_id}_gen.py"
            script_path.write_text(record.generated_code, encoding="utf-8")

            # Run in tracer context
            tracer = RuntimeTracer(
                str(script_path),
                max_events=self.config.execution.max_trace_events,
            )

            # Construct executable script
            parts = [record.generated_code]
            if record.test_code:
                parts.append("\n\n")
                parts.append(record.test_code)
            if record.dataset.strip().upper() == "HUMANEVAL" and record.entry_point:
                parts.append(f"\ncheck({record.entry_point})\n")

            full_script = "".join(parts)
            test_path = Path(tmpdir) / f"{record.trace_id}_test.py"
            test_path.write_text(full_script, encoding="utf-8")

            # Import/exec in tracer scope safely
            try:
                with tracer:
                    exec_globals = {"__name__": "__main__", "__file__": str(script_path)}
                    exec(compile(full_script, str(script_path), "exec"), exec_globals)
            except Exception:
                pass # Exceptions captured by tracer

            return tracer.events

    def _extract_failure_line(self, record: Objective2InputRecord) -> Optional[int]:
        """Extract line number of failure from traceback."""
        if not record.traceback:
            return None

        code_lines = len(record.generated_code.strip().splitlines()) if record.generated_code else 0

        lines = record.traceback.strip().splitlines()
        for line in reversed(lines):
            match = re.search(r'File ".*?", line (\d+)', line)
            if match:
                lineno = int(match.group(1))
                if 1 <= lineno <= code_lines:
                    return lineno
                    
        return code_lines if code_lines > 0 else None

    def _compute_summary(
        self,
        total_corpus_size: int,
        eligible_cases: int,
        analyzed_cases: int,
        skipped_cases: int,
        unresolved_cases: int,
        failed_cases: int,
        results: List[Objective2Result],
        has_ground_truth: bool,
    ) -> Objective2Summary:
        # Counterfactual success numerator/denominator
        cf_valid_count = 0
        cf_total_count = 0
        for r in results:
            for cf in r.counterfactual_results:
                cf_total_count += 1
                if cf.causal_effect == CausalEffect.TRUE:
                    cf_valid_count += 1

        cf_pct = (
            f"{cf_valid_count}/{cf_total_count} ({(cf_valid_count/cf_total_count)*100:.1f}%)"
            if cf_total_count > 0
            else "0/0 (0.0%)"
        )

        gt_status = "NOT_AVAILABLE"
        rc_acc = "NOT_AVAILABLE"
        fl_acc = "NOT_AVAILABLE"
        top1_acc = "NOT_AVAILABLE"
        top3_acc = "NOT_AVAILABLE"
        top5_acc = "NOT_AVAILABLE"

        if has_ground_truth:
            gt_status = "AVAILABLE"
            matched_count = sum(1 for r in results if r.ground_truth_matched is True)
            eval_count = sum(1 for r in results if r.ground_truth_matched is not None)
            if eval_count > 0:
                fl_acc = f"{matched_count}/{eval_count} ({(matched_count/eval_count)*100:.1f}%)"
                top1_acc = fl_acc

        return Objective2Summary(
            total_corpus_size=total_corpus_size,
            eligible_cases=eligible_cases,
            analyzed_cases=analyzed_cases,
            skipped_cases=skipped_cases,
            unresolved_cases=unresolved_cases,
            failed_cases=failed_cases,
            root_cause_accuracy=rc_acc,
            fault_location_accuracy=fl_acc,
            critical_variable_accuracy="NOT_AVAILABLE",
            top_1_fault_accuracy=top1_acc,
            top_3_fault_accuracy=top3_acc,
            top_5_fault_accuracy=top5_acc,
            counterfactual_success_rate=cf_pct,
            ground_truth_status=gt_status,
        )
