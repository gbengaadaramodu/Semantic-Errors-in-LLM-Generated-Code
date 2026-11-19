"""
Objective 3 — Error Signature Generator.

Produces a deterministic fingerprint for failed executions.
Used to identify same-error stalls and oscillation loops.
Normalizes unstable information like memory addresses and timestamps.
"""

from __future__ import annotations

import re

from objective3.models import ErrorProfile, ErrorSignature


class ErrorSignatureGenerator:
    """Generates normalized ErrorSignatures from ErrorProfiles."""

    def generate(self, profile: ErrorProfile) -> ErrorSignature:
        """
        Generate a deterministic error signature.
        """
        if profile.is_passing():
            return ErrorSignature(
                error_category="CORRECT",
                fault_location_key="none",
                output_discrepancy="none",
            )

        # 1. Error category
        category = profile.error_category.value

        # 2. Fault location key (line number)
        if profile.failure_line is not None:
            location_key = f"line_{profile.failure_line}"
        else:
            location_key = "none"

        # 3. Output discrepancy pattern
        discrepancy = self._extract_discrepancy(profile)

        return ErrorSignature(
            error_category=category,
            fault_location_key=location_key,
            output_discrepancy=discrepancy,
        )

    def _extract_discrepancy(self, profile: ErrorProfile) -> str:
        """Extract a stable discrepancy pattern from stderr/stdout/exception."""
        if profile.exception_type and profile.exception_message:
            msg = self._normalize_message(profile.exception_message)
            return f"{profile.exception_type}:{msg}"

        if profile.stderr:
            # Grab the last non-empty line of stderr
            lines = [L for L in profile.stderr.strip().splitlines() if L.strip()]
            if lines:
                return self._normalize_message(lines[-1])

        return "unknown_discrepancy"

    def _normalize_message(self, message: str) -> str:
        """Normalize memory addresses, timestamps, and quotes."""
        msg = message
        # Remove object memory addresses like 0x000001B6A4C2E9A0
        msg = re.sub(r"0x[0-9a-fA-F]+", "0xADDR", msg)
        # Remove timestamp-like numbers (simple heuristic)
        msg = re.sub(r"\d{10,}", "TIMESTAMP", msg)
        return msg.strip()
