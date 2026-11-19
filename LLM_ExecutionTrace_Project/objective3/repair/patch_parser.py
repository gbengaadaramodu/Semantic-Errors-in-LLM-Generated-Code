"""
Objective 3 — Repair Output Parser.

Parses the raw LLM response to extract a valid Python code block.

Supports:
  - Plain Python code (no fences)
  - Fenced code blocks: ```python...``` or ```...```

Rejects:
  - Empty responses
  - Prose-only responses (no function definitions)
  - Responses with multiple ambiguous function definitions (warns but returns first)
  - Malformed code (syntax errors detected here)

The raw LLM response is always preserved separately from the parsed output.
"""

from __future__ import annotations

import ast
import logging
import re
from dataclasses import dataclass
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Patterns for code fence extraction
_FENCE_PATTERN = re.compile(
    r"```(?:python)?\s*\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)

# Minimum check: must contain at least one 'def ' or 'class '
_CODE_CONTENT_PATTERN = re.compile(r"\bdef\s+\w+\s*\(|\bclass\s+\w+")


@dataclass
class ParseResult:
    """Result of parsing a raw LLM repair response."""
    success: bool
    extracted_code: str = ""
    error_message: str = ""
    had_fence: bool = False
    multiple_functions_detected: bool = False
    raw_response: str = ""

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "extracted_code": self.extracted_code,
            "error_message": self.error_message,
            "had_fence": self.had_fence,
            "multiple_functions_detected": self.multiple_functions_detected,
        }


class PatchParser:
    """
    Parses raw LLM output to extract a valid Python code block.
    """

    def parse(self, raw_response: str) -> ParseResult:
        """
        Parse the raw LLM response and extract the corrected Python code.

        Parameters
        ----------
        raw_response : str
            The complete text returned by the repair LLM.

        Returns
        -------
        ParseResult
            success=True if a valid Python code block was extracted.
        """
        if not raw_response or not raw_response.strip():
            logger.warning("Parser received empty LLM response.")
            return ParseResult(
                success=False,
                error_message="Empty LLM response.",
                raw_response=raw_response or "",
            )

        # ── Attempt 1: Extract fenced code block ────────────────────────────
        fenced_matches = _FENCE_PATTERN.findall(raw_response)
        if fenced_matches:
            # Take the first (longest / earliest) fenced block
            code_candidate = fenced_matches[0].strip()
            had_fence = True
        else:
            # ── Attempt 2: Use entire response as plain code ────────────────
            code_candidate = raw_response.strip()
            had_fence = False

        # ── Validate: must contain a function definition ─────────────────────
        if not _CODE_CONTENT_PATTERN.search(code_candidate):
            logger.warning(
                "LLM response contains no function definition; treating as prose-only."
            )
            return ParseResult(
                success=False,
                error_message=(
                    "LLM response contains no function definition. "
                    "Response may be prose-only."
                ),
                had_fence=had_fence,
                raw_response=raw_response,
            )

        # ── Syntax validation ────────────────────────────────────────────────
        try:
            ast.parse(code_candidate)
        except SyntaxError as exc:
            logger.warning(
                "Extracted code has syntax error at line %s: %s",
                exc.lineno,
                exc.msg,
            )
            # Attempt to clean up common LLM artifacts before giving up
            cleaned = self._try_clean(code_candidate)
            if cleaned != code_candidate:
                try:
                    ast.parse(cleaned)
                    code_candidate = cleaned
                    logger.info("Code cleaned successfully after syntax error.")
                except SyntaxError:
                    return ParseResult(
                        success=False,
                        error_message=(
                            f"Extracted code contains a syntax error: "
                            f"line {exc.lineno}: {exc.msg}"
                        ),
                        had_fence=had_fence,
                        raw_response=raw_response,
                    )
            else:
                return ParseResult(
                    success=False,
                    error_message=(
                        f"Extracted code contains a syntax error: "
                        f"line {exc.lineno}: {exc.msg}"
                    ),
                    had_fence=had_fence,
                    raw_response=raw_response,
                )

        # ── Detect multiple top-level function definitions ────────────────────
        multiple_funcs = self._has_multiple_functions(code_candidate)
        if multiple_funcs:
            logger.warning(
                "Multiple function definitions detected in LLM response. "
                "Using complete code block (all functions preserved)."
            )

        logger.debug(
            "Successfully parsed repair code (%d chars, fence=%s, multi_func=%s).",
            len(code_candidate),
            had_fence,
            multiple_funcs,
        )
        return ParseResult(
            success=True,
            extracted_code=code_candidate,
            had_fence=had_fence,
            multiple_functions_detected=multiple_funcs,
            raw_response=raw_response,
        )

    def _try_clean(self, code: str) -> str:
        """
        Attempt to remove common LLM artifacts:
        - Lines starting with '#' that are malformed
        - Trailing non-code prose after a double newline
        """
        # Remove trailing prose after the last function block
        lines = code.splitlines()
        # Find last line with actual code content
        last_code_line = 0
        indent_level_zero_lines = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                last_code_line = i
            if not line.startswith(" ") and not line.startswith("\t") and stripped:
                indent_level_zero_lines.append(i)

        if indent_level_zero_lines and last_code_line < len(lines) - 1:
            # Truncate after last meaningful line
            return "\n".join(lines[: last_code_line + 1])
        return code

    def _has_multiple_functions(self, code: str) -> bool:
        """Return True if there are multiple top-level function definitions."""
        try:
            tree = ast.parse(code)
            top_level_funcs = [
                node for node in ast.iter_child_nodes(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            return len(top_level_funcs) > 1
        except SyntaxError:
            return False
