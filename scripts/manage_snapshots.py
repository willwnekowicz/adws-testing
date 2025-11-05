#!/usr/bin/env python3
"""Manage workspace snapshots.

This script provides commands to list, restore, delete, and manage workspace snapshots.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.snapshot import SnapshotManager


def list_snapshots(manager: SnapshotManager):
    """List all available snapshots."""
    snapshots = manager.list_snapshots()

    if not snapshots:
        print("No snapshots found.")
        return

    print(f"\nAvailable Snapshots ({len(snapshots)}):")
    print("-" * 80)

    for snap in snapshots:
        # Format creation time
        created = datetime.fromisoformat(snap["created_at"])
        created_str = created.strftime("%Y-%m-%d %H:%M:%S")

        # Format size
        size_mb = snap["size_bytes"] / (1024 * 1024)

        # Default indicator
        default = " [DEFAULT]" if snap["is_default"] else ""

        print(f"\n{snap['name']}{default}")
        print(f"  Created: {created_str}")
        print(f"  Size: {size_mb:.2f} MB")
        print(f"  Files: {snap['files_count']:,}")
        print(f"  Directories: {snap['dirs_count']:,}")

        if snap["description"]:
            print(f"  Description: {snap['description']}")

        if snap["tags"]:
            print(f"  Tags: {', '.join(snap['tags'])}")


def restore_snapshot(manager: SnapshotManager, name: str, target: Path = None):
    """Restore a snapshot to a workspace."""
    try:
        workspace = manager.restore_snapshot(name=name, target_workspace=target)
        print(f"✓ Snapshot '{name}' restored to: {workspace}")
        return workspace
    except Exception as e:
        print(f"Error restoring snapshot: {e}")
        sys.exit(1)


def delete_snapshot(manager: SnapshotManager, name: str):
    """Delete a snapshot."""
    try:
        # Confirm deletion
        response = input(f"Delete snapshot '{name}'? This cannot be undone. (y/n): ")
        if response.lower() != 'y':
            print("Deletion cancelled.")
            return

        manager.delete_snapshot(name)
        print(f"✓ Snapshot '{name}' deleted")
    except Exception as e:
        print(f"Error deleting snapshot: {e}")
        sys.exit(1)


def set_default(manager: SnapshotManager, name: str):
    """Set the default snapshot."""
    try:
        manager.set_default_snapshot(name)
        print(f"✓ Default snapshot set to '{name}'")
    except Exception as e:
        print(f"Error setting default: {e}")
        sys.exit(1)


def info_snapshot(manager: SnapshotManager, name: str = None):
    """Show detailed information about a snapshot."""
    try:
        info = manager.get_snapshot_info(name)

        print(f"\nSnapshot: {info['name']}")
        print("-" * 40)

        # Format creation time
        created = datetime.fromisoformat(info["created_at"])
        created_str = created.strftime("%Y-%m-%d %H:%M:%S")

        print(f"Created: {created_str}")
        print(f"Path: {info['path']}")
        print(f"Exists: {'Yes' if info['exists'] else 'No (missing!)'}")
        print(f"Is Default: {'Yes' if info['is_default'] else 'No'}")

        # Format size
        size_mb = info["size_bytes"] / (1024 * 1024)
        print(f"Size: {size_mb:.2f} MB")
        print(f"Files: {info['files_count']:,}")
        print(f"Directories: {info['dirs_count']:,}")

        if info["description"]:
            print(f"\nDescription:")
            print(f"  {info['description']}")

        if info["tags"]:
            print(f"\nTags: {', '.join(info['tags'])}")

        if info.get("source_workspace"):
            print(f"\nOriginal Source: {info['source_workspace']}")

    except Exception as e:
        print(f"Error getting snapshot info: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Manage workspace snapshots"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # List command
    list_parser = subparsers.add_parser("list", help="List all snapshots")

    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore a snapshot")
    restore_parser.add_argument("name", help="Name of snapshot to restore")
    restore_parser.add_argument(
        "--target",
        help="Target directory for restoration (creates temp if not specified)"
    )

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a snapshot")
    delete_parser.add_argument("name", help="Name of snapshot to delete")

    # Set default command
    default_parser = subparsers.add_parser(
        "set-default",
        help="Set the default snapshot"
    )
    default_parser.add_argument("name", help="Name of snapshot to set as default")

    # Info command
    info_parser = subparsers.add_parser("info", help="Show snapshot details")
    info_parser.add_argument(
        "name",
        nargs="?",
        help="Name of snapshot (uses default if not specified)"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Initialize snapshot manager
    manager = SnapshotManager(Path.cwd())

    # Execute command
    if args.command == "list":
        list_snapshots(manager)
    elif args.command == "restore":
        target = Path(args.target) if args.target else None
        restore_snapshot(manager, args.name, target)
    elif args.command == "delete":
        delete_snapshot(manager, args.name)
    elif args.command == "set-default":
        set_default(manager, args.name)
    elif args.command == "info":
        info_snapshot(manager, args.name)


if __name__ == "__main__":
    main()