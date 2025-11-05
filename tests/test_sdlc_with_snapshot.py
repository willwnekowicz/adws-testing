#!/usr/bin/env python3
"""Test SDLC workflows using workspace snapshots.

This test validates SDLC workflows (feature, bug, chore) using pre-initialized
workspace snapshots, avoiding the need to run init for each test.
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import Config
from src.core.snapshot_runner import SnapshotTestRunner
from src.checks.sdlc import get_sdlc_checks


def test_sdlc_feature(runner: SnapshotTestRunner, model: str = "sonnet"):
    """Test SDLC feature workflow.

    Args:
        runner: Snapshot test runner
        model: Model to use
    """
    print("\n" + "=" * 60)
    print("Testing SDLC Feature Workflow")
    print("=" * 60)

    # Run feature test
    run_id = runner.run_sdlc_test(
        workflow_type="feature",
        description="Add user authentication with JWT tokens",
        model=model
    )

    print(f"✓ Feature test completed: {run_id}")
    return run_id


def test_sdlc_bug(runner: SnapshotTestRunner, model: str = "sonnet"):
    """Test SDLC bug workflow.

    Args:
        runner: Snapshot test runner
        model: Model to use
    """
    print("\n" + "=" * 60)
    print("Testing SDLC Bug Workflow")
    print("=" * 60)

    # Run bug test
    run_id = runner.run_sdlc_test(
        workflow_type="bug",
        description="Fix memory leak in data processing pipeline",
        model=model
    )

    print(f"✓ Bug test completed: {run_id}")
    return run_id


def test_sdlc_chore(runner: SnapshotTestRunner, model: str = "sonnet"):
    """Test SDLC chore workflow.

    Args:
        runner: Snapshot test runner
        model: Model to use
    """
    print("\n" + "=" * 60)
    print("Testing SDLC Chore Workflow")
    print("=" * 60)

    # Run chore test
    run_id = runner.run_sdlc_test(
        workflow_type="chore",
        description="Update dependencies and improve build configuration",
        model=model
    )

    print(f"✓ Chore test completed: {run_id}")
    return run_id


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test SDLC workflows using workspace snapshots"
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--model",
        choices=["sonnet", "haiku"],
        default="sonnet",
        help="Model to use for testing"
    )
    parser.add_argument(
        "--workflow",
        choices=["feature", "bug", "chore", "all"],
        default="all",
        help="Which workflow to test"
    )
    parser.add_argument(
        "--snapshot",
        help="Name of snapshot to use (uses default if not specified)"
    )

    args = parser.parse_args()

    # Load configuration
    config = Config(args.config)

    # Validate configuration
    errors = config.validate()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    # Initialize snapshot runner
    runner = SnapshotTestRunner(config)

    # Check if we have a snapshot
    snapshots = runner.snapshot_manager.list_snapshots()
    if not snapshots:
        print("Error: No snapshots available")
        print("Please run 'python scripts/create_init_snapshot.py' first")
        sys.exit(1)

    if args.snapshot:
        # Verify specified snapshot exists
        if args.snapshot not in [s["name"] for s in snapshots]:
            print(f"Error: Snapshot '{args.snapshot}' not found")
            print("Available snapshots:")
            for s in snapshots:
                print(f"  - {s['name']}")
            sys.exit(1)
    else:
        # Use default
        default = runner.snapshot_manager.metadata.get("default")
        if not default:
            print("Error: No default snapshot set")
            print("Set one with: python scripts/manage_snapshots.py set-default <name>")
            sys.exit(1)
        print(f"Using default snapshot: {default}")

    # Run tests
    run_ids = []

    try:
        if args.workflow == "all":
            run_ids.append(test_sdlc_feature(runner, args.model))
            run_ids.append(test_sdlc_bug(runner, args.model))
            run_ids.append(test_sdlc_chore(runner, args.model))
        elif args.workflow == "feature":
            run_ids.append(test_sdlc_feature(runner, args.model))
        elif args.workflow == "bug":
            run_ids.append(test_sdlc_bug(runner, args.model))
        elif args.workflow == "chore":
            run_ids.append(test_sdlc_chore(runner, args.model))

        print("\n" + "=" * 60)
        print("SDLC Test Summary")
        print("=" * 60)
        print(f"Tests run: {len(run_ids)}")
        print(f"Model used: {args.model}")
        print(f"Snapshot used: {args.snapshot or runner.snapshot_manager.metadata.get('default')}")
        print("\nRun IDs:")
        for run_id in run_ids:
            print(f"  - {run_id}")

        print("\n✓ All SDLC tests completed successfully!")

    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error running tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()