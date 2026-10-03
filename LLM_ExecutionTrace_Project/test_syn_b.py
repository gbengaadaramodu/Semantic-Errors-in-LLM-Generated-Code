from objective2.pipeline import Objective2Pipeline
from objective2.config import Objective2Config
from objective2.models import Objective2InputRecord

record = Objective2InputRecord(
    trace_id="SYN_B",
    dataset="HumanEval",
    task_id="Synthetic/B",
    generated_code="def divide(a, b):\n    return a / b\n",
    entry_point="divide",
    test_code="def check(candidate):\n    assert candidate(10, 0) == 0\n",
    execution_status="Failed",
    exception_type="ZeroDivisionError",
    exception_message="division by zero",
    traceback='File "SYN_B.py", line 2, in divide\n    return a / b\nZeroDivisionError: division by zero',
    parser_prediction="Runtime Exception",
)
config = Objective2Config()
pipe = Objective2Pipeline(config)
res = pipe.analyze_single_case(record)
print("Failure line:", res.failure_line)
print("Fault line:", res.fault_location.line_number)
