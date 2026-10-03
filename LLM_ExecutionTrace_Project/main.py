#!/usr/bin/env python3
"""
LLM Execution Trace Project — CLI Entry Point

Provides an argparse-based command-line interface with subcommands
for each pipeline stage, plus a ``run-all`` command for the full
end-to-end experiment.

Usage examples
--------------
    python main.py select              # Step 1: Select 150+150 tasks
    python main.py generate            # Step 2: Generate code via Ollama
    python main.py execute             # Step 3: Execute tests & capture traces
    python main.py classify            # Step 4: Rule-based classification
    python main.py export              # Step 5: Generate annotation workbook
    python main.py run-all             # Run full pipeline end-to-end
    python main.py run-all --from-stage execute   # Resume from Stage 3
    python main.py run-all --from-stage classify  # Resume from Stage 4
    python main.py run-all --from-stage export    # Resume from Stage 5
"""

import argparse
import logging
import sys

from config import ProjectConfig
from experiment.experiment_manager import ExperimentManager
from experiment.logger import setup_logging

STAGES = ["select", "generate", "execute", "classify", "export"]


def _build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser with subcommands."""

    parser = argparse.ArgumentParser(
        prog="LLM_ExecutionTrace",
        description="LLM Execution Trace Pipeline — HumanEval + MBPP benchmark analysis",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Override the random seed for task selection (default: 42)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of tasks to process (useful for testing)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose (DEBUG-level) console output",
    )

    subparsers = parser.add_subparsers(dest="command", help="Pipeline stage to run")

    # ── Individual stages ─────────────────────
    subparsers.add_parser("select",   help="Select 150 HumanEval + 150 MBPP tasks")
    subparsers.add_parser("generate", help="Generate code via Ollama (Code Llama 13B)")
    subparsers.add_parser("execute",  help="Execute tests and capture runtime traces")
    subparsers.add_parser("classify", help="Run rule-based error classification")
    subparsers.add_parser("export",   help="Generate annotation workbook (Excel/CSV/JSON)")

    # ── Full pipeline ─────────────────────────
    run_all = subparsers.add_parser(
        "run-all",
        help="Run the complete pipeline end-to-end",
    )
    run_all.add_argument(
        "--from-stage",
        dest="from_stage",
        choices=["generate", "execute", "classify", "export"],
        default=None,
        help=(
            "Resume the pipeline from a specific stage, reusing already "
            "completed earlier stages.  For example, use --from-stage execute "
            "to skip task selection and code generation and go straight to "
            "running the benchmark tests against the already-generated code."
        ),
    )

    return parser


def main() -> int:
    """Parse arguments and dispatch to the appropriate pipeline stage."""

    parser = _build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    # ── Build configuration ───────────────────
    config = ProjectConfig()

    if args.seed is not None:
        config.task_selection.random_seed = args.seed

    if args.limit is not None:
        limit_he = args.limit // 2 + (args.limit % 2)
        limit_mb = args.limit // 2
        config.task_selection.humaneval_sample_size = limit_he
        config.task_selection.mbpp_sample_size = limit_mb

    # ── Setup logging ─────────────────────────
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logging(config.paths.project_root, level=log_level)

    logger.info("=" * 60)
    logger.info("LLM Execution Trace Project")
    logger.info("=" * 60)
    logger.info("Command   : %s", args.command)
    logger.info("Model     : %s", config.ollama.model_name)
    logger.info("Seed      : %d", config.task_selection.random_seed)
    if args.limit:
        logger.info("Limit     : %d", args.limit)
    if args.command == "run-all" and getattr(args, "from_stage", None):
        logger.info("From stage: %s", args.from_stage)
    logger.info("-" * 60)

    # ── Create experiment manager ─────────────
    manager = ExperimentManager(config=config)

    # ── Dispatch ──────────────────────────────
    try:
        if args.command == "select":
            tasks = manager.run_selection()
            logger.info("Selected %d tasks.", len(tasks))

        elif args.command == "generate":
            tasks = manager.run_selection()
            manager.run_generation(tasks)

        elif args.command == "execute":
            tasks = manager.load_selected_tasks()
            manager.run_execution(tasks)

        elif args.command == "classify":
            tasks  = manager.load_selected_tasks()
            results = manager.run_execution(tasks)
            manager.run_classification(results)

        elif args.command == "export":
            tasks   = manager.load_selected_tasks()
            results = manager.run_execution(tasks)
            manager.run_classification(results)
            manager.run_export(results)

        elif args.command == "run-all":
            from_stage = getattr(args, "from_stage", None)
            manager.run_all(from_stage=from_stage)

        else:
            parser.print_help()
            return 1

    except KeyboardInterrupt:
        logger.warning("Pipeline interrupted by user.")
        return 130
    except Exception as exc:
        logger.exception("Pipeline failed: %s", exc)
        return 1

    logger.info("=" * 60)
    logger.info("Pipeline stage '%s' completed successfully.", args.command)
    logger.info("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
