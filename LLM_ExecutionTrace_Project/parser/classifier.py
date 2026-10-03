"""
Rule-Based Execution Trace Classifier.

This module applies the diagnostic rules defined in rules.py to
structured runtime evidence and assigns one of the five error
categories or the Correct outcome.

Classification categories:

    1. Syntax Error
    2. Runtime Exception
    3. Wrong-Output Error
    4. Assertion Failure
    5. Timeout Error

Correct is treated as a successful execution outcome.

The classifier is intentionally deterministic: the same runtime
evidence always produces the same classification.
"""

import logging
from typing import Dict, List, Optional

from models import ExecutionResult

from .taxonomy import ErrorCategory
from .rules import (
    AssertionFailureRule,
    CorrectRule,
    RuntimeExceptionRule,
    SyntaxErrorRule,
    TimeoutRule,
    WrongOutputRule,
)


logger = logging.getLogger(__name__)


class RuleBasedParser:
    """
    Rule-based classifier for execution traces.

    Rules are evaluated in a fixed priority order. The first rule
    whose conditions match the runtime evidence determines the
    classification.

    Priority:

        1. Timeout Error
        2. Syntax Error
        3. Assertion Failure
        4. Runtime Exception
        5. Wrong-Output Error
        6. Correct

    An execution trace that does not satisfy any rule remains
    Unclassified rather than being silently forced into a category.
    """

    def __init__(self) -> None:
        """
        Initialize the classifier and its ordered rules.
        """

        self.rules = [
            TimeoutRule(),
            SyntaxErrorRule(),
            AssertionFailureRule(),
            RuntimeExceptionRule(),
            WrongOutputRule(),
            CorrectRule(),
        ]

    # ---------------------------------------------------------
    # Single-trace classification
    # ---------------------------------------------------------

    def classify(
        self,
        result: ExecutionResult,
    ) -> Optional[ErrorCategory]:
        """
        Classify a single execution result.

        Parameters
        ----------
        result:
            ExecutionResult containing the runtime evidence
            collected from the sandbox.

        Returns
        -------
        Optional[ErrorCategory]
            The category assigned by the first matching rule.

            Returns None when the available evidence does not
            satisfy any classification rule.
        """

        evidence = result.evidence

        for rule in self.rules:

            try:
                matched = rule.matches(evidence)

            except Exception as exc:
                logger.exception(
                    "Error evaluating rule %s for trace %s: %s",
                    rule.__class__.__name__,
                    result.trace_id,
                    exc,
                )
                continue

            if not matched:
                continue

            category = rule.category

            result.parser_prediction = category.value

            logger.debug(
                "Trace %s classified as '%s' using %s.",
                result.trace_id,
                category.value,
                rule.__class__.__name__,
            )

            return category

        # Do not silently classify an unknown trace as Wrong Output.
        result.parser_prediction = ""

        logger.warning(
            "Trace %s could not be classified from the available "
            "runtime evidence.",
            result.trace_id,
        )

        return None

    # ---------------------------------------------------------
    # Multiple-trace classification
    # ---------------------------------------------------------

    def classify_all(
        self,
        results: List[ExecutionResult],
    ) -> Dict[str, int]:
        """
        Classify a collection of execution results.

        Parameters
        ----------
        results:
            List of ExecutionResult objects.

        Returns
        -------
        Dict[str, int]
            Number of traces assigned to each category.

        An additional 'Unclassified' key records traces for which
        no rule matched.
        """

        summary_counts: Dict[str, int] = {
            category.value: 0
            for category in ErrorCategory
        }

        summary_counts["Unclassified"] = 0

        for result in results:

            category = self.classify(result)

            if category is None:

                summary_counts["Unclassified"] += 1

                logger.warning(
                    "Trace %s (%s) remains unclassified.",
                    result.trace_id,
                    result.task_id,
                )

                continue

            summary_counts[category.value] += 1

            logger.info(
                "Trace %s (%s) classified as '%s'.",
                result.trace_id,
                result.task_id,
                category.value,
            )

        return summary_counts

    # ---------------------------------------------------------
    # Summary of existing predictions
    # ---------------------------------------------------------

    def get_summary(
        self,
        results: List[ExecutionResult],
    ) -> Dict[str, int]:
        """
        Return classification counts from predictions already
        stored in the ExecutionResult objects.

        This method does not execute the rules again.

        Parameters
        ----------
        results:
            List of ExecutionResult objects.

        Returns
        -------
        Dict[str, int]
            Counts for each taxonomy category and Unclassified.
        """

        summary_counts: Dict[str, int] = {
            category.value: 0
            for category in ErrorCategory
        }

        summary_counts["Unclassified"] = 0

        for result in results:

            prediction = result.parser_prediction

            if not prediction:
                summary_counts["Unclassified"] += 1
                continue

            if prediction not in summary_counts:
                logger.warning(
                    "Unknown parser prediction '%s' for trace %s.",
                    prediction,
                    result.trace_id,
                )

                summary_counts["Unclassified"] += 1
                continue

            summary_counts[prediction] += 1

        return summary_counts

    # ---------------------------------------------------------
    # Utility methods
    # ---------------------------------------------------------

    def get_category_names(self) -> List[str]:
        """
        Return the names of all supported classification outcomes.
        """

        return [
            category.value
            for category in ErrorCategory
        ]

    def get_unclassified(
        self,
        results: List[ExecutionResult],
    ) -> List[ExecutionResult]:
        """
        Return all execution results that could not be classified.

        This is useful during development because unclassified traces
        should be investigated rather than silently assigned to an
        arbitrary category.
        """

        return [
            result
            for result in results
            if not result.parser_prediction
        ]