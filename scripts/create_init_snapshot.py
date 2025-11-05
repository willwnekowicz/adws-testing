#!/usr/bin/env python3
"""Create a snapshot from a successful init workspace.

This script creates a reusable snapshot from a workspace created by the init process,
allowing efficient testing of SDLC and other workflows without re-running init each time.
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.snapshot import SnapshotManager


def create_init_snapshot(
    source_workspace: Path,
    snapshot_name: str = "init-complete",
    description: str = None
):
    """Create a snapshot from an init workspace.

    Args:
        source_workspace: Path to the initialized workspace
        snapshot_name: Name for the snapshot
        description: Description of the snapshot
    """
    # Initialize snapshot manager
    manager = SnapshotManager(Path.cwd())

    # Default description if not provided
    if description is None:
        description = (
            "Complete initialized project workspace with all phases completed: "
            "git, github, structure, docs, frontend, cloudflare, prefect, and configuration"
        )

    # Create the snapshot
    snapshot_path = manager.create_snapshot(
        source_workspace=source_workspace,
        name=snapshot_name,
        description=description,
        tags=["init", "complete", "all-phases"],
        set_as_default=True
    )

    print(f"✓ Snapshot '{snapshot_name}' created successfully")
    print(f"  Path: {snapshot_path}")
    print(f"  Set as default: Yes")

    # Show snapshot info
    info = manager.get_snapshot_info(snapshot_name)
    print(f"\nSnapshot Details:")
    print(f"  Files: {info['files_count']}")
    print(f"  Directories: {info['dirs_count']}")
    print(f"  Size: {info['size_bytes'] / (1024 * 1024):.2f} MB")

    return snapshot_path


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create a snapshot from a successful init workspace"
    )
    parser.add_argument(
        "workspace",
        help="Path to the initialized workspace to snapshot"
    )
    parser.add_argument(
        "--name",
        default="init-complete",
        help="Name for the snapshot (default: init-complete)"
    )
    parser.add_argument(
        "--description",
        help="Description for the snapshot"
    )

    args = parser.parse_args()

    # Validate workspace path
    workspace_path = Path(args.workspace)
    if not workspace_path.exists():
        print(f"Error: Workspace does not exist: {workspace_path}")
        sys.exit(1)

    # Check if workspace looks valid
    expected_dirs = [".git", "apps", "documentation", "scripts"]
    missing = [d for d in expected_dirs if not (workspace_path / d).exists()]
    if missing:
        print(f"Warning: Workspace may be incomplete, missing: {missing}")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)

    try:
        create_init_snapshot(
            source_workspace=workspace_path,
            snapshot_name=args.name,
            description=args.description
        )
    except Exception as e:
        print(f"Error creating snapshot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()