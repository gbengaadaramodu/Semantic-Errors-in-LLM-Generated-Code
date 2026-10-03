"""
Runtime Trace Capture Module using `sys.settrace`.

Captures execution events (call, line, return, exception) and local variable state
under process execution. Safely serializes local variables and prevents infinite
recursion or tracing standard library functions.
"""

import os
import sys
import time
import traceback
from typing import Any, Dict, List, Optional

from objective2.models import EventType, RuntimeEvent


def safe_serialize(val: Any, max_depth: int = 2, max_len: int = 500) -> Any:
    """
    Safely serialize dynamic Python objects to JSON-friendly primitives.
    """
    if val is None or isinstance(val, (int, float, bool, str)):
        return val

    if max_depth <= 0:
        return repr(val)[:max_len]

    try:
        if isinstance(val, (list, tuple, set)):
            items = list(val)[:20] # truncate long collections
            res = [safe_serialize(x, max_depth - 1, max_len) for x in items]
            return res if isinstance(val, list) else (tuple(res) if isinstance(val, tuple) else res)
        elif isinstance(val, dict):
            res_dict = {}
            for k, v in list(val.items())[:20]:
                res_dict[str(k)] = safe_serialize(v, max_depth - 1, max_len)
            return res_dict
    except Exception:
        pass

    try:
        return repr(val)[:max_len]
    except Exception:
        return "<unserializable>"


class RuntimeTracer:
    """
    Context manager that attaches `sys.settrace` to record execution events
    occurring within a target target filename.
    """

    def __init__(self, target_filename: str, max_events: int = 2000) -> None:
        self.target_filename = os.path.abspath(target_filename)
        self.max_events = max_events
        self.events: List[RuntimeEvent] = []
        self._event_counter = 0
        self._disabled = False

    def __enter__(self) -> "RuntimeTracer":
        self.events.clear()
        self._event_counter = 0
        self._disabled = False
        sys.settrace(self._trace_func)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        sys.settrace(None)
        self._disabled = True

    def _trace_func(self, frame: Any, event: str, arg: Any) -> Optional[Any]:
        if self._disabled:
            return None

        # Check maximum events safety cap
        if self._event_counter >= self.max_events:
            sys.settrace(None)
            self._disabled = True
            raise RuntimeError("Max trace events reached - aborting execution to prevent infinite loop")

        # Filter: only trace functions defined inside target_filename
        code_file = frame.f_code.co_filename
        if not code_file:
            return self._trace_func

        try:
            abs_code_file = os.path.abspath(code_file)
        except Exception:
            return self._trace_func

        if abs_code_file != self.target_filename:
            return self._trace_func

        event_type_map = {
            "call": EventType.CALL,
            "line": EventType.LINE,
            "return": EventType.RETURN,
            "exception": EventType.EXCEPTION,
        }

        if event not in event_type_map:
            return self._trace_func

        self._event_counter += 1
        t_stamp = time.perf_counter()

        # Capture locals safely
        locals_copy = {}
        for k, v in frame.f_locals.items():
            if not k.startswith("__"):
                locals_copy[k] = safe_serialize(v)

        ret_val = None
        exc_dict = None

        if event == "return":
            ret_val = safe_serialize(arg)
        elif event == "exception" and isinstance(arg, tuple) and len(arg) >= 2:
            exc_type, exc_value, _ = arg
            exc_dict = {
                "type": getattr(exc_type, "__name__", str(exc_type)),
                "message": str(exc_value),
            }

        ev = RuntimeEvent(
            event_id=self._event_counter,
            timestamp=t_stamp,
            event_type=event_type_map[event],
            filename=abs_code_file,
            function_name=frame.f_code.co_name,
            line_number=frame.f_lineno,
            local_variables=locals_copy,
            return_value=ret_val,
            exception=exc_dict,
        )

        self.events.append(ev)
        return self._trace_func
