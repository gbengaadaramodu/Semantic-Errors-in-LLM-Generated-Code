"""
Objective 2 CLI Entry Point.

Command-line interface for executing the Objective 2 Causal Root Cause Analysis Pipeline.

Usage:
    python -m objective2.main --input annotation/Validation_Corpus.json
    python -m objective2.main --input annotation/Validation_Corpus.json --error-type wrong-output --limit 10
"""

import argparse
import logging
import sys
from pathlib import Path

from objective2.config import Objective2Config
from objective2.pipeline import Objective2Pipeline


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Objective 2: Causal Root Cause Analysis Pipeline for LLM-Generated Code",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--input",
        type=str,
        default="annotation/Validation_Corpus.json",
        help="Input corpus file (.json, .csv, .xlsx) or execution logs directory",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="objective2/output",
        help="Directory to write output artifacts and reports",
    )
    parser.add_argument(
        "--error-type",
        type=str,
        default="all",
        help="Filter by error type (wrong-output, runtime-exception, all)",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Filter by dataset (HumanEval, MBPP)",
    )
    parser.add_argument(
        "--task-id",
        type=str,
        default=None,
        help="Filter by specific task ID or trace ID (e.g. HE001, HumanEval/163)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of cases to analyze",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of candidate cause variables to evaluate",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Sandbox execution timeout per counterfactual evaluation in seconds",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (reserved for parallel processing)",
    )
    parser.add_argument(
        "--ground-truth",
        type=str,
        default="objective2/annotation/objective2_ground_truth.xlsx",
        help="Path to ground truth Excel file for evaluation",
    )
    parser.add_argument(
        "--export-format",
        type=str,
        default="all",
        choices=["json", "csv", "excel", "all"],
        help="Output export formats to generate",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose debug logging",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load and select cases without executing counterfactual analysis",
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    config = Objective2Config()
    if args.output:
        config.paths.output_dir = Path(args.output).resolve()
        config.paths.ensure_directories()
    config.execution.sandbox_timeout = args.timeout
    config.execution.counterfactual_timeout = args.timeout
    config.analysis.top_k = args.top_k
    config.verbose = args.verbose

    pipeline = Objective2Pipeline(config)

    if args.dry_run:
        logging.info("DRY RUN MODE: Loading corpus and selecting cases...")
        records = pipeline.corpus_loader.load_records()
        selected = pipeline._select_cases(
            records,
            error_type_filter=args.error_type,
            dataset_filter=args.dataset,
            task_id_filter=args.task_id,
            limit=args.limit,
        )
        print(f"Dry run selection completed: {len(selected)} cases selected.")
        return

    results, summary = pipeline.run(
        input_path=Path(args.input),
        error_type_filter=args.error_type,
        dataset_filter=args.dataset,
        task_id_filter=args.task_id,
        limit=args.limit,
        ground_truth_path=Path(args.ground_truth),
    )

    print("\n" + "=" * 60)
    print("  OBJECTIVE 2 CAUSAL DIAGNOSIS SUMMARY")
    print("=" * 60)
    print(f"Total Corpus Size         : {summary.total_corpus_size}")
    print(f"Eligible Cases            : {summary.eligible_cases}")
    print(f"Analyzed Cases            : {summary.analyzed_cases}")
    print(f"Skipped Cases             : {summary.skipped_cases}")
    print(f"Unresolved Cases          : {summary.unresolved_cases}")
    print(f"Failed Cases              : {summary.failed_cases}")
    print(f"Counterfactual Success    : {summary.counterfactual_success_rate}")
    print(f"Ground Truth Status       : {summary.ground_truth_status}")
    print(f"Fault Location Accuracy   : {summary.fault_location_accuracy}")
    print("=" * 60)


if __name__ == "__main__":
    main()
