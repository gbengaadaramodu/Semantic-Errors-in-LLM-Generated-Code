"""
Objective 3 — Integrated Closed-Loop Controller.

The master orchestration module for Objective 3. For a single task, it coordinates:
  1. Initial Execution & Classification
  2. Objective 2 Diagnosis matching
  3. The Repair Iteration Loop
     - Prompt Generation
     - LLM Repair
     - AST Merging
     - Execution & Regression checking
     - State evaluation (SAME_ERROR, NEW_ERROR, OSCILLATION)
     - Strategy Escalation

Produces the complete TaskTrajectory.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

from objective3.ast_merge.merger import ASTMerger
from objective3.config import Objective3Config
from objective3.controller.oscillation import OscillationDetector
from objective3.controller.signatures import ErrorSignatureGenerator
from objective3.controller.state import TaskStateMachine
from objective3.execution.executor import Executor
from objective3.execution.regression import RegressionDetector
from objective3.execution.test_runner import TestRunner
from objective3.input.objective2_loader import Objective2Loader
from objective3.models import (
    BenchmarkTask,
    ControllerDecision,
    ControllerState,
    DiagnosisStatus,
    ErrorCategory,
    RepairIteration,
    RepairOutcome,
    RepairStrategy,
    StructuredDiagnosticReport,
    TaskTrajectory,
    TerminationReason,
)
from objective3.repair.repair_engine import RepairEngine
from objective3.repair.repair_strategy import RepairStrategySelector

logger = logging.getLogger(__name__)


class RepairController:
    """
    Main orchestration controller for the Objective 3 closed-loop repair architecture.
    """

    def __init__(
        self,
        config: Objective3Config,
        repair_engine: RepairEngine,
        obj2_loader: Objective2Loader,
    ) -> None:
        self.config = config
        self.repair_engine = repair_engine
        self.obj2_loader = obj2_loader

        # Subsystems
        self.executor = Executor(config.execution)
        self.test_runner = TestRunner(config.execution)
        self.regression_detector = RegressionDetector()
        self.ast_merger = ASTMerger()
        self.sig_generator = ErrorSignatureGenerator()
        self.strategy_selector = RepairStrategySelector()

    def run_task(
        self,
        task: BenchmarkTask,
        initial_source: str,
    ) -> TaskTrajectory:
        """
        Execute the complete repair trajectory for a single task.
        """
        logger.info("=" * 60)
        logger.info("Starting repair loop for task %s", task.trace_id)
        logger.info("=" * 60)

        # Initialize tracking
        trajectory = TaskTrajectory(
            task_id=task.task_id, trace_id=task.trace_id, benchmark=task.benchmark, task=task
        )
        fsm = TaskStateMachine(task.trace_id)
        osc_detector = OscillationDetector(self.config.controller)

        # State tracking variables
        current_source = initial_source
        current_strategy = RepairStrategy.LOCAL_MODIFICATION
        same_error_count = 0
        iteration_count = 0

        # Current diagnosis & signature
        current_report: Optional[StructuredDiagnosticReport] = None
        prev_signature = None

        # Base test pass state for regression detection
        base_passing_tests: Dict[str, bool] = {}

        try:
            # ── Iteration 0: Initial Execution ────────────────────────────────
            fsm.transition_to(ControllerState.EXECUTING)
            iter0_profile = self.executor.execute(task, current_source)
            iter0_sig = self.sig_generator.generate(iter0_profile)
            base_passing_tests = self.test_runner.run_tests(task, current_source)

            trajectory.initial_error_category = iter0_profile.error_category.value
            trajectory.initial_status = iter0_profile.execution_status

            iter0_record = RepairIteration(
                iteration=0,
                source_code=current_source,
                execution_result=iter0_profile,
                error_signature=iter0_sig,
                controller_state=ControllerState.EXECUTING,
            )
            trajectory.iterations.append(iter0_record)

            if iter0_profile.is_passing():
                fsm.transition_to(ControllerState.SUCCESS)
                self._finalize_success(trajectory, TerminationReason.INITIAL_SUCCESS)
                logger.info("Task %s initially passing. Stopping.", task.trace_id)
                return trajectory

            # Not passing — get initial diagnosis from Objective 2 output
            fsm.transition_to(ControllerState.DIAGNOSED)
            current_report = self._get_diagnosis(task.trace_id, iter0_profile)
            iter0_record.diagnostic_report = current_report
            prev_signature = iter0_sig

            osc_detector.record_state(0, current_source, iter0_sig)

            # ── Iteration 1 to MAX ────────────────────────────────────────────
            while iteration_count < self.config.controller.max_iterations:
                iteration_count += 1
                logger.info("--- %s Iteration %d ---", task.trace_id, iteration_count)

                fsm.transition_to(ControllerState.REPAIR_GENERATED)

                # 1. Generate Repair
                if current_strategy == RepairStrategy.STRUCTURAL_REDESIGN:
                    repair_result = self.repair_engine.repair_structural_redesign(
                        task=task,
                        current_source=current_source,
                        error_history=f"Prior signature: {prev_signature.raw_signature}",
                        iteration=iteration_count,
                    )
                else:
                    if not current_report:
                        current_report = self._get_fallback_diagnosis(iter0_profile)

                    repair_result = self.repair_engine.repair(
                        task=task,
                        diagnostic_report=current_report,
                        current_source=current_source,
                        repair_strategy=current_strategy,
                        iteration=iteration_count,
                    )

                iter_record = RepairIteration(
                    iteration=iteration_count,
                    source_code=current_source,  # will be updated if merge succeeds
                    repair_prompt=repair_result.repair_prompt,
                    raw_llm_response=repair_result.raw_llm_response,
                    repaired_block=repair_result.repaired_code,
                    repair_strategy_used=current_strategy,
                    model_name=repair_result.model_used,
                    temperature=repair_result.temperature_used,
                    execution_duration=repair_result.duration_seconds,
                    diagnostic_report=current_report,
                    controller_state=fsm.current_state,
                )

                if not repair_result.success:
                    # Parse failed
                    self._handle_invalid_repair(
                        fsm, iter_record, trajectory, current_strategy
                    )
                    if fsm.is_terminal():
                        break
                    continue

                # 2. AST Merge
                fsm.transition_to(ControllerState.AST_MERGED)
                if current_strategy == RepairStrategy.STRUCTURAL_REDESIGN:
                    merge_result = self.ast_merger.merge_full_replacement(
                        original_source=current_source,
                        repair_code=repair_result.repaired_code,
                        entry_point=task.entry_point,
                    )
                else:
                    start_line = (
                        current_report.fault_location.start_line
                        if current_report and current_report.fault_location
                        else 1
                    )
                    end_line = (
                        current_report.fault_location.end_line
                        if current_report and current_report.fault_location
                        else len(current_source.splitlines())
                    )
                    merge_result = self.ast_merger.merge(
                        original_source=current_source,
                        repair_code=repair_result.repaired_code,
                        entry_point=task.entry_point,
                        start_line=start_line,
                        end_line=end_line,
                    )

                iter_record.ast_merge_result = merge_result
                if not merge_result.success:
                    self._handle_invalid_repair(
                        fsm, iter_record, trajectory, current_strategy
                    )
                    if fsm.is_terminal():
                        break
                    continue

                # Merge succeeded — execute
                candidate_source = merge_result.merged_code
                iter_record.source_code = candidate_source

                fsm.transition_to(ControllerState.REEXECUTING)
                exec_profile = self.executor.execute(task, candidate_source)
                exec_sig = self.sig_generator.generate(exec_profile)
                test_results = self.test_runner.run_tests(task, candidate_source)

                iter_record.execution_result = exec_profile
                iter_record.error_signature = exec_sig

                # 3. Regression Detection
                regression = self.regression_detector.detect(
                    base_passing_tests, test_results
                )
                iter_record.regression = regression
                if regression.regression_detected:
                    trajectory.regression_detected = True

                # 4. State Evaluation
                fsm.transition_to(ControllerState.EVALUATING)

                # Did it pass?
                if exec_profile.is_passing() and not regression.regression_detected:
                    # Success
                    decision = ControllerDecision(
                        outcome=RepairOutcome.PASS, terminate=True, termination_reason=TerminationReason.PASS
                    )
                    iter_record.controller_decision = decision
                    iter_record.controller_state = ControllerState.SUCCESS
                    trajectory.iterations.append(iter_record)
                    self._finalize_success(trajectory, TerminationReason.PASS, exec_profile)
                    logger.info("Task %s REPAIRED on iteration %d.", task.trace_id, iteration_count)
                    break

                # Not passing. Evaluate failure type.
                if regression.regression_detected:
                    # Regression — discard source code change, do not count as same error
                    decision = ControllerDecision(
                        outcome=RepairOutcome.REGRESSION,
                        next_strategy=current_strategy,
                        notes="Regression detected. Candidate discarded.",
                    )
                    iter_record.controller_decision = decision
                    trajectory.iterations.append(iter_record)
                    continue

                # No regression, but still failing. Commit the code change.
                current_source = candidate_source
                base_passing_tests = test_results  # new baseline

                # Check oscillation
                is_oscillation = osc_detector.record_state(
                    iteration_count, current_source, exec_sig
                )
                if is_oscillation:
                    trajectory.oscillation_detected = True

                if exec_sig == prev_signature:
                    same_error_count += 1
                    outcome = RepairOutcome.SAME_ERROR
                else:
                    same_error_count = 0
                    outcome = RepairOutcome.NEW_ERROR
                    prev_signature = exec_sig
                    # NEW ERROR requires fresh diagnosis
                    current_report = self._get_fallback_diagnosis(exec_profile)
                    iter_record.diagnosis_inherited = False

                # Escalation logic
                next_strategy, escalated = self.strategy_selector.select(
                    current_strategy=current_strategy,
                    same_error_count=same_error_count,
                    oscillation_detected=is_oscillation,
                    escalation_threshold=self.config.controller.escalation_threshold,
                )

                if outcome == RepairOutcome.NEW_ERROR and not escalated:
                    next_strategy = self.strategy_selector.strategy_for_new_error(current_strategy)

                decision = ControllerDecision(
                    outcome=outcome,
                    next_strategy=next_strategy,
                    escalated=escalated,
                    oscillation_detected=is_oscillation,
                )
                iter_record.controller_decision = decision
                trajectory.iterations.append(iter_record)

                current_strategy = next_strategy
                if escalated:
                    same_error_count = 0  # reset after escalation

            # End of max iterations loop
            if not fsm.is_terminal():
                fsm.transition_to(ControllerState.FAILED)
                self._finalize_failure(trajectory, TerminationReason.MAX_ITERATIONS)

        except Exception as exc:
            logger.error("Controller pipeline exception for %s: %s", task.trace_id, exc, exc_info=True)
            fsm.transition_to(ControllerState.FAILED)
            trajectory.analysis_failure = True
            trajectory.failure_type = type(exc).__name__
            trajectory.failure_message = str(exc)
            self._finalize_failure(trajectory, TerminationReason.ANALYSIS_FAILURE)

        return trajectory

    def _get_diagnosis(
        self, trace_id: str, profile: ErrorProfile
    ) -> StructuredDiagnosticReport:
        """Fetch Objective 2 diagnosis or fallback to basic profile."""
        report = self.obj2_loader.load_diagnosis(trace_id)
        if report:
            # Objective 3 MUST NOT alter the diagnosis status
            return report

        logger.info("No Objective 2 diagnosis for %s. Generating fallback.", trace_id)
        return self._get_fallback_diagnosis(profile)

    def _get_fallback_diagnosis(self, profile: ErrorProfile) -> StructuredDiagnosticReport:
        """Create a fallback report from Objective 1 profile when Obj2 is absent/new error."""
        return StructuredDiagnosticReport(
            error_category=profile.error_category,
            causal_explanation="Fresh failure signature with no historical Obj2 causal diagnosis.",
            diagnosis_status=DiagnosisStatus.UNRESOLVED,  # Strictly UNRESOLVED
            
            
            
        )

    def _handle_invalid_repair(
        self,
        fsm: TaskStateMachine,
        record: RepairIteration,
        trajectory: TaskTrajectory,
        strategy: RepairStrategy,
    ) -> None:
        """Handle a syntax error or failed AST merge."""
        decision = ControllerDecision(
            outcome=RepairOutcome.INVALID_REPAIR,
            next_strategy=strategy,
            notes="Invalid code or failed merge.",
        )
        record.controller_decision = decision
        trajectory.iterations.append(record)

        # Allow continuing, but if all iterations are invalid it hits MAX_ITERATIONS naturally
        logger.warning("Invalid repair on iteration %d.", record.iteration)

    def _finalize_success(
        self, trajectory: TaskTrajectory, reason: TerminationReason, final_profile: Optional[ErrorProfile] = None
    ) -> None:
        trajectory.successful = True
        trajectory.final_status = "SUCCESS"
        trajectory.termination_reason = reason
        trajectory.iterations_used = len(trajectory.iterations) - 1
        if final_profile:
            trajectory.final_error_category = final_profile.error_category.value
        else:
            trajectory.final_error_category = ErrorCategory.CORRECT.value

    def _finalize_failure(self, trajectory: TaskTrajectory, reason: TerminationReason) -> None:
        trajectory.successful = False
        trajectory.final_status = "FAILED"
        trajectory.termination_reason = reason
        trajectory.iterations_used = len(trajectory.iterations) - 1
        if trajectory.iterations:
            last = trajectory.iterations[-1]
            if last.execution_result:
                trajectory.final_error_category = last.execution_result.error_category.value
