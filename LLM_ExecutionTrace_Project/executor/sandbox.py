"""Sandbox execution module for running arbitrary code."""

import subprocess
import time
import logging
from pathlib import Path

from models import SandboxResult

logger = logging.getLogger(__name__)

class Sandbox:
    """Executes Python code in an isolated subprocess."""
    
    def __init__(self, timeout: int = 30, python_executable: str = 'python'):
        self.timeout = timeout
        self.python_executable = python_executable

    def execute(self, script_path: Path) -> SandboxResult:
        """Run script in subprocess."""
        start_time = time.perf_counter()
        
        try:
            result = subprocess.run(
                [self.python_executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            execution_time = time.perf_counter() - start_time
            return SandboxResult(
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
                timed_out=False,
                execution_time=execution_time
            )
        except subprocess.TimeoutExpired as e:
            execution_time = time.perf_counter() - start_time
            stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
            stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
            return SandboxResult(
                stdout=stdout,
                stderr=stderr,
                returncode=-1,
                timed_out=True,
                execution_time=execution_time
            )
        except Exception as e:
            logger.error(f"Sandbox execution failed: {e}")
            execution_time = time.perf_counter() - start_time
            return SandboxResult(
                stdout="",
                stderr=str(e),
                returncode=-1,
                timed_out=False,
                execution_time=execution_time
            )
