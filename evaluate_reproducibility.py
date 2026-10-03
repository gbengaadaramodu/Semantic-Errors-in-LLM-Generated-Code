#!/usr/bin/env python3
"""
Root Entrypoint for Reproducibility Evaluation
==============================================
Convenience wrapper that runs the artifact evaluation suite
from the repository root.
"""

import sys
import subprocess
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent
    script = root / "LLM_ExecutionTrace_Project" / "evaluate_reproducibility.py"
    if not script.exists():
        print(f"Error: {script} not found.")
        sys.exit(1)

    cmd = [sys.executable, str(script)]
    result = subprocess.run(cmd, cwd=str(script.parent))
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
