"""Context manager for timing code execution."""

import time

class ExecutionTimer:
    """A simple context manager for timing execution duration."""
    
    def __init__(self):
        self._start_time = 0.0
        self._end_time = 0.0
        
    def __enter__(self) -> "ExecutionTimer":
        self._start_time = time.perf_counter()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._end_time = time.perf_counter()
        
    @property
    def elapsed(self) -> float:
        """Returns elapsed time in seconds."""
        if self._end_time == 0.0:
            return time.perf_counter() - self._start_time
        return self._end_time - self._start_time
