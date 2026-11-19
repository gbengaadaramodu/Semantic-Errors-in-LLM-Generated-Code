"""
Objective 3 — Regression Detector.

Compares test results before and after repair to identify regressions.

A repair causes regression when previously-passing tests fail after the repair.
A regression is recorded but does NOT cause immediate termination —
the controller decides whether to preserve the previous version.

The system never silently ignores regressions.
"""

from __future__ import annotations

import logging
from typing import Dict, List

from objective3.models import RegressionRecord

logger = logging.getLogger(__name__)


class RegressionDetector:
    """
    Detects test regressions introduced by a repair.
    """

    def detect(
        self,
        before_results: Dict[str, bool],
        after_results: Dict[str, bool],
    ) -> RegressionRecord:
        """
        Compare before/after test results and produce a RegressionRecord.

        Parameters
        ----------
        before_results : Dict[test_id → passed] before repair.
        after_results  : Dict[test_id → passed] after repair.

        Returns
        -------
        RegressionRecord with full details.
        """
        previously_passing = [tid for tid, p in before_results.items() if p]
        currently_passing = [tid for tid, p in after_results.items() if p]

        previously_passing_set = set(previously_passing)
        currently_passing_set = set(currently_passing)

        regressed = list(previously_passing_set - currently_passing_set)
        regression_detected = len(regressed) > 0

        if regression_detected:
            logger.warning(
                "Regression detected: %d test(s) that previously passed now fail: %s",
                len(regressed),
                regressed,
            )
        else:
            logger.debug("No regression detected.")

        return RegressionRecord(
            regression_detected=regression_detected,
            previously_passing_tests=sorted(previously_passing),
            currently_passing_tests=sorted(currently_passing),
            regressed_tests=sorted(regressed),
        )
