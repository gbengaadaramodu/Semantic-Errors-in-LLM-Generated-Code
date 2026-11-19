"""Tests for the execution regression tracking logic."""
import unittest

from objective3.execution.regression import RegressionDetector
from objective3.models import RegressionRecord

class TestRegressionDetector(unittest.TestCase):
    def setUp(self):
        self.detector = RegressionDetector()

    def test_no_regression(self):
        before = {"t1": True, "t2": False}
        after = {"t1": True, "t2": True}
        res = self.detector.detect(before, after)
        self.assertFalse(res.regression_detected)
        self.assertEqual(res.regressed_tests, [])

    def test_regression_detected(self):
        before = {"t1": True, "t2": True}
        after = {"t1": False, "t2": True}
        res = self.detector.detect(before, after)
        self.assertTrue(res.regression_detected)
        self.assertEqual(res.regressed_tests, ["t1"])

    def test_new_failing_but_not_regression(self):
        before = {"t1": False}
        after = {"t1": False, "t2": False}
        res = self.detector.detect(before, after)
        self.assertFalse(res.regression_detected)

if __name__ == "__main__":
    unittest.main()
