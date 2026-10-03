"""
Root Cause Diagnoser Module.

Synthesizes structural dependency evidence, runtime traces, and counterfactual
intervention outcomes to produce an evidence-backed semantic root-cause diagnosis.
"""

from typing import Optional

from objective2.models import (
    CausalEffect,
    CounterfactualResult,
    FaultLocation,
    Objective2InputRecord,
    RootCauseDiagnosis,
)


class RootCauseDiagnoser:
    """
    Generates evidence-backed semantic root cause descriptions.
    """

    def diagnose(
        self,
        record: Objective2InputRecord,
        fault_location: Optional[FaultLocation],
        top_cf_result: Optional[CounterfactualResult],
    ) -> Optional[RootCauseDiagnosis]:
        if not fault_location:
            return RootCauseDiagnosis(
                root_cause_status="UNRESOLVED",
                candidate_explanation="Unable to isolate specific causal fault location from execution trace.",
                causal_variable="UNRESOLVED",
                fault_statement="",
                fault_line=0,
                evidence_summary="Insufficient execution or dependency trace evidence.",
                counterfactual_validated=False,
                confidence=0.0,
            )

        cf_validated = (
            top_cf_result is not None
            and top_cf_result.causal_effect == CausalEffect.TRUE
        )

        # Formulate specific semantic explanation based on error category & statement
        category = record.parser_prediction or record.execution_status
        stmt = fault_location.statement_code
        var = fault_location.causal_variable

        if "Wrong-Output" in category or record.assertion_failed:
            if "if" in stmt or "elif" in stmt:
                desc = (
                    f"Defective filtering condition '{stmt}' at line {fault_location.line_number} "
                    f"selects incorrect elements, modifying variable '{var}'."
                )
            elif "=" in stmt:
                desc = (
                    f"Incorrect state computation at line {fault_location.line_number} ('{stmt}') "
                    f"produces invalid variable state for '{var}'."
                )
            else:
                desc = (
                    f"Semantic mismatch at line {fault_location.line_number} ('{stmt}') "
                    f"causes return value mismatch."
                )
        elif "Runtime" in category or record.exception_type:
            desc = (
                f"Runtime exception ({record.exception_type}: {record.exception_message}) "
                f"triggered at statement '{stmt}' (line {fault_location.line_number}) "
                f"involving variable '{var}'."
            )
        else:
            desc = (
                f"Execution divergence at line {fault_location.line_number} ('{stmt}') "
                f"affecting variable '{var}'."
            )

        evidence = (
            f"Reverse PDG traversal traced failure from line {record.exit_code or fault_location.line_number} "
            f"to statement line {fault_location.line_number}. "
        )

        if cf_validated:
            evidence += f"Counterfactual intervention do({var} = expected) successfully restored PASS state."
        else:
            evidence += "Structural dependency identified; counterfactual validation unconfirmed or unresolved."

        status = "VALIDATED" if cf_validated else "UNRESOLVED"

        return RootCauseDiagnosis(
            root_cause_status=status,
            candidate_explanation=desc,
            causal_variable=var,
            fault_statement=stmt,
            fault_line=fault_location.line_number,
            evidence_summary=evidence,
            counterfactual_validated=cf_validated,
            confidence=fault_location.confidence,
        )
