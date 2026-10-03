"""Unit tests for sys.settrace Runtime Tracer."""
import os
import tempfile
import unittest
from objective2.pdg.runtime_trace import RuntimeTracer

class TestRuntimeTrace(unittest.TestCase):
    def test_runtime_tracer(self):
        code = """def add(a, b):
    res = a + b
    return res

add(2, 3)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "sample.py")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)

            tracer = RuntimeTracer(file_path)
            with tracer:
                exec_globals = {"__file__": file_path}
                exec(compile(code, file_path, "exec"), exec_globals)

            self.assertGreater(len(tracer.events), 0)
            lines = [ev.line_number for ev in tracer.events]
            self.assertTrue(2 in lines or 3 in lines)

if __name__ == "__main__":
    unittest.main()
