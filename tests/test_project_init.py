"""Test case for the /project-init slash command."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import Config
from src.core.runner import TestRunner
from src.checks.simple import (
    FileExistsCheck,
    FileContentCheck,
    GitBranchCheck,
    GitConfigCheck,
    DirectoryStructureCheck,
    DurationCheck
)
from src.checks.base import CompositeCheck


def get_project_init_checks():
    """Get checks for project-init test.

    Returns:
        List of check instances
    """
    checks = []

    # Check 1: README.md should exist
    checks.append(FileExistsCheck(
        name="readme_exists",
        file_path="README.md"
    ))

    # Check 2: README.md should have content
    checks.append(FileContentCheck(
        name="readme_has_content",
        file_path="README.md",
        contains=["#"],  # Should have at least a heading
        not_contains=[]
    ))

    # Check 3: Git should be initialized
    checks.append(DirectoryStructureCheck(
        name="git_initialized",
        required_dirs=[".git"],
        required_files=[]
    ))

    # Check 4: Should have main and staging branches
    checks.append(GitConfigCheck(
        name="git_branches_configured",
        required_branches=["main", "staging"],
        required_remotes=[]
    ))

    # Check 5: Should be on staging branch
    checks.append(GitBranchCheck(
        name="on_staging_branch",
        expected_branch="staging"
    ))

    # Check 6: Should complete within reasonable time
    checks.append(DurationCheck(
        name="execution_time",
        max_duration=120  # 2 minutes max
    ))

    # Create a composite check for project initialization
    project_init_complete = CompositeCheck(
        name="project_init_complete",
        checks=[
            FileExistsCheck("readme_check", "README.md"),
            GitBranchCheck("branch_check", "staging")
        ],
        require_all=True
    )
    checks.append(project_init_complete)

    return checks


def run_project_init_test(config_path: str = None):
    """Run the project-init test.

    Args:
        config_path: Optional path to configuration file

    Returns:
        List of run IDs
    """
    # Load configuration
    config = Config(config_path)

    # Validate configuration
    errors = config.validate()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        return []

    # Initialize runner
    runner = TestRunner(config)

    # Get checks
    checks = get_project_init_checks()

    # Run tests with both models
    print("Running project-init test...")
    run_ids = runner.run_multiple_tests(
        test_name="project-init",
        models=["sonnet", "haiku"],
        checks=checks
    )

    print(f"Completed test runs: {run_ids}")

    # Print results
    for run_id in run_ids:
        results = runner.get_run_results(run_id)
        if results:
            print(f"\nRun {run_id}:")
            print(f"  Model: {results['model']}")
            print(f"  Status: {results['status']}")

            for test_case in results['test_cases']:
                print(f"  Test: {test_case['name']}")
                for result in test_case['results']:
                    status = "✓" if result['passed'] else "✗"
                    print(f"    {status} {result['check_name']}")
                    if result['details'] and not result['passed']:
                        print(f"      Details: {result['details'][:100]}...")

    return run_ids


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run project-init test")
    parser.add_argument(
        "--config",
        help="Path to configuration file",
        default="config.yaml"
    )
    parser.add_argument(
        "--model",
        help="Specific model to test (sonnet or haiku)",
        choices=["sonnet", "haiku"],
        default=None
    )
    parser.add_argument(
        "--commit",
        help="Specific commit to test",
        default=None
    )
    parser.add_argument(
        "--branch",
        help="Specific branch to test",
        default=None
    )

    args = parser.parse_args()

    # Run test
    try:
        # Load configuration
        config = Config(args.config)

        # Initialize runner
        runner = TestRunner(config)

        # Get checks
        checks = get_project_init_checks()

        # Run test
        if args.model:
            # Run with specific model
            run_id = runner.run_test(
                test_name="project-init",
                model=args.model,
                commit=args.commit,
                branch=args.branch,
                checks=checks
            )
            print(f"Test run completed: {run_id}")

            # Show results
            results = runner.get_run_results(run_id)
            if results:
                print(f"\nResults for run {run_id}:")
                print(f"  Model: {results['model']}")
                print(f"  Status: {results['status']}")

                for test_case in results['test_cases']:
                    print(f"  Test: {test_case['name']}")
                    passed = 0
                    failed = 0
                    for result in test_case['results']:
                        if result['passed']:
                            passed += 1
                        else:
                            failed += 1
                        status = "✓" if result['passed'] else "✗"
                        print(f"    {status} {result['check_name']}")
                        if result['details'] and not result['passed']:
                            for line in result['details'].split('\n')[:3]:
                                if line.strip():
                                    print(f"      {line}")

                    print(f"  Summary: {passed} passed, {failed} failed")
        else:
            # Run with all models
            run_ids = runner.run_multiple_tests(
                test_name="project-init",
                commit=args.commit,
                branch=args.branch,
                checks=checks
            )
            print(f"Test runs completed: {run_ids}")

            # Show summary
            for run_id in run_ids:
                results = runner.get_run_results(run_id)
                if results:
                    print(f"\nRun {run_id} ({results['model']}): {results['status']}")

    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error running test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)