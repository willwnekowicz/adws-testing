"""Workspace snapshot management for efficient testing.

This module provides functionality to create, manage, and restore workspace
snapshots from successful init processes. This allows testing the SDLC flow
and other workflows without re-running the lengthy init process each time.
"""

import json
import logging
import shutil
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class SnapshotManager:
    """Manages workspace snapshots for test reuse."""

    def __init__(self, base_dir: Path):
        """Initialize snapshot manager.

        Args:
            base_dir: Base directory for storing snapshots
        """
        self.base_dir = Path(base_dir)
        self.snapshots_dir = self.base_dir / "snapshots"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.snapshots_dir / "metadata.json"
        self._load_metadata()

    def _load_metadata(self):
        """Load snapshot metadata from disk."""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {
                "snapshots": {},
                "default": None
            }

    def _save_metadata(self):
        """Save snapshot metadata to disk."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def create_snapshot(
        self,
        source_workspace: Path,
        name: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        set_as_default: bool = False
    ) -> Path:
        """Create a new workspace snapshot.

        Args:
            source_workspace: Path to the workspace to snapshot
            name: Name for the snapshot
            description: Optional description
            tags: Optional list of tags (e.g., ["init", "frontend", "cloudflare"])
            set_as_default: Whether to set this as the default snapshot

        Returns:
            Path to the created snapshot
        """
        if not source_workspace.exists():
            raise ValueError(f"Source workspace does not exist: {source_workspace}")

        # Create snapshot directory
        snapshot_dir = self.snapshots_dir / name
        if snapshot_dir.exists():
            logger.warning(f"Snapshot {name} already exists, overwriting")
            shutil.rmtree(snapshot_dir)

        logger.info(f"Creating snapshot '{name}' from {source_workspace}")

        # Copy workspace to snapshot
        shutil.copytree(source_workspace, snapshot_dir, symlinks=True)

        # Store metadata
        self.metadata["snapshots"][name] = {
            "created_at": datetime.now().isoformat(),
            "source_workspace": str(source_workspace),
            "description": description,
            "tags": tags or [],
            "files_count": sum(1 for _ in snapshot_dir.rglob("*") if _.is_file()),
            "dirs_count": sum(1 for _ in snapshot_dir.rglob("*") if _.is_dir()),
            "size_bytes": sum(f.stat().st_size for f in snapshot_dir.rglob("*") if f.is_file())
        }

        if set_as_default:
            self.metadata["default"] = name

        self._save_metadata()
        logger.info(f"Snapshot '{name}' created successfully at {snapshot_dir}")
        return snapshot_dir

    def restore_snapshot(
        self,
        name: Optional[str] = None,
        target_workspace: Optional[Path] = None,
        overlay_dirs: Optional[Dict[str, Path]] = None
    ) -> Path:
        """Restore a workspace from a snapshot.

        Args:
            name: Name of snapshot to restore (uses default if None)
            target_workspace: Where to restore the snapshot (creates temp if None)
            overlay_dirs: Dict of directories to overlay after restore
                         e.g., {".adws": Path("/path/to/latest/.adws")}

        Returns:
            Path to the restored workspace
        """
        # Determine which snapshot to use
        if name is None:
            name = self.metadata.get("default")
            if name is None:
                raise ValueError("No snapshot specified and no default set")

        if name not in self.metadata["snapshots"]:
            raise ValueError(f"Snapshot '{name}' not found")

        snapshot_dir = self.snapshots_dir / name
        if not snapshot_dir.exists():
            raise ValueError(f"Snapshot directory missing: {snapshot_dir}")

        # Determine target workspace
        if target_workspace is None:
            # Create a temporary workspace
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target_workspace = self.base_dir / "temp_workspaces" / f"workspace_{timestamp}"

        target_workspace = Path(target_workspace)

        # Clean target if it exists
        if target_workspace.exists():
            logger.warning(f"Target workspace exists, cleaning: {target_workspace}")
            shutil.rmtree(target_workspace)

        # Restore snapshot
        logger.info(f"Restoring snapshot '{name}' to {target_workspace}")
        shutil.copytree(snapshot_dir, target_workspace, symlinks=True)

        # Apply overlays if specified
        if overlay_dirs:
            for rel_path, source_path in overlay_dirs.items():
                if not source_path.exists():
                    logger.warning(f"Overlay source does not exist: {source_path}")
                    continue

                target_path = target_workspace / rel_path

                # Remove existing directory if present
                if target_path.exists():
                    logger.info(f"Removing existing {rel_path} for overlay")
                    if target_path.is_dir():
                        shutil.rmtree(target_path)
                    else:
                        target_path.unlink()

                # Copy overlay
                logger.info(f"Applying overlay: {rel_path} from {source_path}")
                if source_path.is_dir():
                    shutil.copytree(source_path, target_path, symlinks=True)
                else:
                    shutil.copy2(source_path, target_path)

        logger.info(f"Workspace restored successfully at {target_workspace}")
        return target_workspace

    def list_snapshots(self) -> List[Dict]:
        """List all available snapshots.

        Returns:
            List of snapshot metadata dictionaries
        """
        snapshots = []
        for name, metadata in self.metadata["snapshots"].items():
            snapshot_info = metadata.copy()
            snapshot_info["name"] = name
            snapshot_info["is_default"] = (name == self.metadata.get("default"))
            snapshot_info["path"] = str(self.snapshots_dir / name)
            snapshots.append(snapshot_info)

        # Sort by creation time
        snapshots.sort(key=lambda x: x["created_at"], reverse=True)
        return snapshots

    def delete_snapshot(self, name: str):
        """Delete a snapshot.

        Args:
            name: Name of snapshot to delete
        """
        if name not in self.metadata["snapshots"]:
            raise ValueError(f"Snapshot '{name}' not found")

        snapshot_dir = self.snapshots_dir / name
        if snapshot_dir.exists():
            logger.info(f"Deleting snapshot '{name}'")
            shutil.rmtree(snapshot_dir)

        del self.metadata["snapshots"][name]

        # Clear default if it was this snapshot
        if self.metadata.get("default") == name:
            self.metadata["default"] = None

        self._save_metadata()
        logger.info(f"Snapshot '{name}' deleted")

    def set_default_snapshot(self, name: str):
        """Set the default snapshot.

        Args:
            name: Name of snapshot to set as default
        """
        if name not in self.metadata["snapshots"]:
            raise ValueError(f"Snapshot '{name}' not found")

        self.metadata["default"] = name
        self._save_metadata()
        logger.info(f"Default snapshot set to '{name}'")

    def get_snapshot_info(self, name: Optional[str] = None) -> Dict:
        """Get detailed information about a snapshot.

        Args:
            name: Name of snapshot (uses default if None)

        Returns:
            Snapshot metadata dictionary
        """
        if name is None:
            name = self.metadata.get("default")
            if name is None:
                raise ValueError("No snapshot specified and no default set")

        if name not in self.metadata["snapshots"]:
            raise ValueError(f"Snapshot '{name}' not found")

        info = self.metadata["snapshots"][name].copy()
        info["name"] = name
        info["is_default"] = (name == self.metadata.get("default"))
        info["path"] = str(self.snapshots_dir / name)

        # Check if snapshot still exists
        snapshot_dir = self.snapshots_dir / name
        info["exists"] = snapshot_dir.exists()

        return info