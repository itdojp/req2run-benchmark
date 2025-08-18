#!/usr/bin/env python3
"""
Req2Run CLI interface
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Optional
import json

from .core import Problem, Evaluator, Difficulty
from .runner import Runner
from .reporter import Reporter

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def evaluate_command(args):
    """Execute evaluation for a single problem"""
    try:
        # Load problem
        logger.info(f"Loading problem: {args.problem}")
        problem = Problem.load(args.problem, Path(args.problems_dir))

        # Create evaluator
        evaluator = Evaluator(
            problem=problem,
            environment=args.environment,
            timeout=args.timeout,
            working_dir=Path(args.working_dir) if args.working_dir else None,
        )

        # Run evaluation
        logger.info(f"Evaluating submission: {args.submission}")
        result = evaluator.evaluate(
            submission_path=Path(args.submission),
            submission_id=args.submission_id,
            verbose=args.verbose,
        )

        # Save results
        if args.output:
            output_dir = Path(args.output)
            result.save(output_dir)
            logger.info(f"Results saved to {output_dir}")

        # Print summary
        print(f"\n{'='*60}")
        print(f"Evaluation Complete: {result.problem_id}")
        print(f"{'='*60}")
        print(f"Submission ID: {result.submission_id}")
        print(f"Total Score: {result.total_score:.2%}")
        print(f"Status: {result.status.upper()}")
        print(f"Execution Time: {result.execution_time:.1f}s")
        print(f"\nMetrics:")
        print(f"  - Functional Coverage: {result.functional_coverage:.2%}")
        print(f"  - Test Pass Rate: {result.test_pass_rate:.2%}")
        print(f"  - Performance Score: {result.performance_score:.2%}")
        print(f"  - Security Score: {result.security_score:.2%}")
        print(f"  - Code Quality: {result.code_quality_score:.2%}")

        # Return exit code based on status
        return 0 if result.status == "passed" else 1

    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def batch_evaluate_command(args):
    """Execute batch evaluation for multiple problems"""
    try:
        problems_dir = Path(args.problems_dir)
        results = []

        # Determine which problems to evaluate
        if args.difficulty:
            difficulty = Difficulty(args.difficulty)
            problem_files = list((problems_dir / difficulty.value).glob("*.yaml"))
        elif args.category:
            problem_files = []
            for diff_dir in problems_dir.iterdir():
                if diff_dir.is_dir():
                    problem_files.extend(diff_dir.glob(f"*{args.category}*.yaml"))
        else:
            # Evaluate all problems
            problem_files = list(problems_dir.rglob("*.yaml"))

        logger.info(f"Found {len(problem_files)} problems to evaluate")

        # Run evaluations
        for problem_file in problem_files:
            try:
                problem = Problem.from_yaml(problem_file)
                logger.info(f"Evaluating problem: {problem.problem_id}")

                evaluator = Evaluator(
                    problem=problem, environment=args.environment, timeout=args.timeout
                )

                result = evaluator.evaluate(
                    submission_path=Path(args.submission), verbose=args.verbose
                )

                results.append(result)

            except Exception as e:
                logger.error(f"Failed to evaluate {problem_file}: {str(e)}")
                continue

        # Save batch results
        if args.output:
            output_dir = Path(args.output)
            output_dir.mkdir(parents=True, exist_ok=True)

            for result in results:
                result.save(output_dir / result.problem_id)

            # Create summary report
            summary = {
                "total_problems": len(results),
                "passed": sum(1 for r in results if r.status == "passed"),
                "failed": sum(1 for r in results if r.status == "failed"),
                "average_score": (
                    sum(r.total_score for r in results) / len(results) if results else 0
                ),
                "problems": [
                    {"id": r.problem_id, "score": r.total_score, "status": r.status}
                    for r in results
                ],
            }

            with open(output_dir / "batch_summary.json", "w") as f:
                json.dump(summary, f, indent=2)

            logger.info(f"Batch results saved to {output_dir}")

        # Print summary
        print(f"\n{'='*60}")
        print(f"Batch Evaluation Complete")
        print(f"{'='*60}")
        print(f"Total Problems: {len(results)}")
        print(f"Passed: {sum(1 for r in results if r.status == 'passed')}")
        print(f"Failed: {sum(1 for r in results if r.status == 'failed')}")
        if results:
            print(
                f"Average Score: {sum(r.total_score for r in results) / len(results):.2%}"
            )

        return 0

    except Exception as e:
        logger.error(f"Batch evaluation failed: {str(e)}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def list_command(args):
    """List available problems"""
    try:
        problems_dir = Path(args.problems_dir)
        problems = []

        for diff_dir in problems_dir.iterdir():
            if diff_dir.is_dir():
                for problem_file in diff_dir.glob("*.yaml"):
                    try:
                        problem = Problem.from_yaml(problem_file)
                        problems.append(
                            {
                                "id": problem.problem_id,
                                "title": problem.title,
                                "category": problem.category,
                                "difficulty": problem.difficulty.value,
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Failed to load {problem_file}: {str(e)}")

        # Filter by difficulty or category if specified
        if args.difficulty:
            problems = [p for p in problems if p["difficulty"] == args.difficulty]
        if args.category:
            problems = [p for p in problems if args.category in p["category"]]

        # Sort problems
        problems.sort(key=lambda x: (x["difficulty"], x["category"], x["id"]))

        # Display problems
        if args.format == "json":
            print(json.dumps(problems, indent=2))
        else:
            print(f"\n{'='*80}")
            print(f"{'ID':<15} {'Title':<40} {'Category':<15} {'Difficulty':<10}")
            print(f"{'-'*80}")
            for p in problems:
                print(
                    f"{p['id']:<15} {p['title'][:40]:<40} {p['category']:<15} {p['difficulty']:<10}"
                )
            print(f"\nTotal: {len(problems)} problems")

        return 0

    except Exception as e:
        logger.error(f"Failed to list problems: {str(e)}")
        return 1


def report_command(args):
    """Generate evaluation report"""
    try:
        reporter = Reporter()

        # Load results
        results_path = Path(args.results)
        if results_path.is_file():
            # Single result file
            with open(results_path, "r") as f:
                results_data = json.load(f)
            results = [results_data]
        else:
            # Directory of results
            results = []
            for result_file in results_path.rglob("*_result.json"):
                with open(result_file, "r") as f:
                    results.append(json.load(f))

        logger.info(f"Loaded {len(results)} results")

        # Generate report
        if args.format == "html":
            output_file = args.output or "report.html"
            reporter.generate_html_report(results, output_file)
        elif args.format == "markdown":
            output_file = args.output or "report.md"
            reporter.generate_markdown_report(results, output_file)
        elif args.format == "json":
            output_file = args.output or "report.json"
            reporter.generate_json_report(results, output_file)
        else:
            raise ValueError(f"Unknown report format: {args.format}")

        logger.info(f"Report generated: {output_file}")
        return 0

    except Exception as e:
        logger.error(f"Failed to generate report: {str(e)}")
        return 1


def validate_command(args):
    """Validate problem definition"""
    try:
        problem_file = Path(args.problem)

        # Load and validate problem
        problem = Problem.from_yaml(problem_file)

        # Check required fields
        issues = []

        if not problem.functional_requirements:
            issues.append("No functional requirements defined")

        if not problem.test_cases:
            issues.append("No test cases defined")

        if not problem.evaluation_criteria:
            issues.append("No evaluation criteria defined")

        # Check weights sum to 1.0
        total_weight = sum(ec.weight for ec in problem.evaluation_criteria)
        if abs(total_weight - 1.0) > 0.01:
            issues.append(
                f"Evaluation criteria weights sum to {total_weight}, should be 1.0"
            )

        # Print validation results
        print(f"\nValidation Results for {problem.problem_id}")
        print(f"{'='*60}")

        if issues:
            print("Issues found:")
            for issue in issues:
                print(f"  - {issue}")
            return 1
        else:
            print("✓ Problem definition is valid")
            print(f"\nSummary:")
            print(f"  - Title: {problem.title}")
            print(f"  - Category: {problem.category}")
            print(f"  - Difficulty: {problem.difficulty.value}")
            print(
                f"  - Functional Requirements: {len(problem.functional_requirements)}"
            )
            print(f"  - Test Cases: {len(problem.test_cases)}")
            print(f"  - Evaluation Criteria: {len(problem.evaluation_criteria)}")
            return 0

    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        return 1


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Req2Run Benchmark Evaluation Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Global arguments
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "--problems-dir",
        default="problems",
        help="Directory containing problem definitions (default: problems)",
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # evaluate command
    evaluate_parser = subparsers.add_parser(
        "evaluate", help="Evaluate a single submission"
    )
    evaluate_parser.add_argument(
        "--problem", "-p", required=True, help="Problem ID to evaluate"
    )
    evaluate_parser.add_argument(
        "--submission", "-s", required=True, help="Path to submission"
    )
    evaluate_parser.add_argument("--submission-id", help="Unique submission identifier")
    evaluate_parser.add_argument(
        "--environment", default="docker", choices=["docker", "kubernetes", "local"]
    )
    evaluate_parser.add_argument(
        "--timeout", type=int, default=3600, help="Evaluation timeout in seconds"
    )
    evaluate_parser.add_argument(
        "--working-dir", help="Working directory for evaluation"
    )
    evaluate_parser.add_argument("--output", "-o", help="Output directory for results")

    # batch-evaluate command
    batch_parser = subparsers.add_parser(
        "batch-evaluate", help="Evaluate multiple problems"
    )
    batch_parser.add_argument(
        "--submission", "-s", required=True, help="Path to submission"
    )
    batch_parser.add_argument(
        "--difficulty", choices=["basic", "intermediate", "advanced", "expert"]
    )
    batch_parser.add_argument("--category", help="Filter by category")
    batch_parser.add_argument(
        "--environment", default="docker", choices=["docker", "kubernetes", "local"]
    )
    batch_parser.add_argument(
        "--timeout", type=int, default=3600, help="Evaluation timeout per problem"
    )
    batch_parser.add_argument("--output", "-o", help="Output directory for results")

    # list command
    list_parser = subparsers.add_parser("list", help="List available problems")
    list_parser.add_argument(
        "--difficulty", choices=["basic", "intermediate", "advanced", "expert"]
    )
    list_parser.add_argument("--category", help="Filter by category")
    list_parser.add_argument("--format", choices=["table", "json"], default="table")

    # report command
    report_parser = subparsers.add_parser("report", help="Generate evaluation report")
    report_parser.add_argument(
        "--results", "-r", required=True, help="Path to results file or directory"
    )
    report_parser.add_argument(
        "--format", choices=["html", "markdown", "json"], default="html"
    )
    report_parser.add_argument("--output", "-o", help="Output file path")

    # validate command
    validate_parser = subparsers.add_parser(
        "validate", help="Validate problem definition"
    )
    validate_parser.add_argument(
        "--problem", "-p", required=True, help="Path to problem YAML file"
    )

    # Parse arguments
    args = parser.parse_args()

    # Execute command
    if args.command == "evaluate":
        return evaluate_command(args)
    elif args.command == "batch-evaluate":
        return batch_evaluate_command(args)
    elif args.command == "list":
        return list_command(args)
    elif args.command == "report":
        return report_command(args)
    elif args.command == "validate":
        return validate_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
