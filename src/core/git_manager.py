"""Git operations manager for handling repository checkouts and setup."""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Tuple
import git
from git import Repo
import logging

logger = logging.getLogger(__name__)


class GitManager:
    """Manages Git repository operations for testing."""

    def __init__(self, repo_path: str):
        """Initialize GitManager.

        Args:
            repo_path: Path to the source repository
        """
        self.repo_path = Path(repo_path).expanduser().resolve()
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {self.repo_path}")

        if not (self.repo_path / ".git").exists():
            raise ValueError(f"Path is not a git repository: {self.repo_path}")

        self.repo = Repo(self.repo_path)
        logger.info(f"GitManager initialized with repo: {self.repo_path}")

    def get_current_info(self) -> Tuple[str, str]:
        """Get current commit hash and branch name.

        Returns:
            Tuple of (commit_hash, branch_name)
        """
        commit_hash = self.repo.head.commit.hexsha
        try:
            branch_name = self.repo.active_branch.name
        except TypeError:
            # Detached HEAD state
            branch_name = "detached"

        return commit_hash, branch_name

    def checkout(self, ref: str) -> str:
        """Checkout a specific branch or commit.

        Args:
            ref: Branch name or commit hash

        Returns:
            The commit hash after checkout
        """
        try:
            self.repo.git.checkout(ref)
            logger.info(f"Checked out: {ref}")
            return self.repo.head.commit.hexsha
        except git.GitCommandError as e:
            logger.error(f"Failed to checkout {ref}: {e}")
            raise

    def create_test_workspace(self, run_id: str, base_path: str = "./runs", use_temp_dir: bool = False, use_dist: bool = False) -> Path:
        """Create an isolated workspace for testing.

        This creates a copy of the repository without .git directory
        for test isolation.

        Args:
            run_id: Unique run identifier
            base_path: Base directory for test runs
            use_temp_dir: If True, create workspace in system temp directory
            use_dist: If True, copy from dist/ directory instead of repository root

        Returns:
            Path to the created workspace
        """
        if use_temp_dir:
            # Create workspace in temp directory for complete isolation
            temp_base = Path(tempfile.gettempdir()) / "adws-testing"
            workspace_path = temp_base / run_id / "workspace"
            workspace_path.mkdir(parents=True, exist_ok=True)

            # Create a symlink in the normal runs directory for easy access
            runs_path = Path(base_path) / run_id
            runs_path.mkdir(parents=True, exist_ok=True)
            symlink_path = runs_path / "workspace"
            if symlink_path.exists() or symlink_path.is_symlink():
                symlink_path.unlink()
            try:
                symlink_path.symlink_to(workspace_path)
                logger.info(f"Created symlink from {symlink_path} to {workspace_path}")
            except OSError:
                # Symlink creation might fail on some systems
                logger.warning(f"Could not create symlink, using temp workspace directly")
        else:
            workspace_path = Path(base_path) / run_id / "workspace"
            workspace_path.mkdir(parents=True, exist_ok=True)

        # Copy from dist directory if specified, otherwise copy repository
        if use_dist:
            dist_path = self.repo_path / "dist"
            if not dist_path.exists():
                raise ValueError(f"dist/ directory not found at {dist_path}. Build required before testing.")
            self._copy_dist(dist_path, workspace_path)
        else:
            self._copy_repository(self.repo_path, workspace_path)

        logger.info(f"Created test workspace: {workspace_path}")
        return workspace_path

    def _copy_dist(self, src: Path, dst: Path):
        """Copy dist directory contents.

        Args:
            src: Source dist directory path
            dst: Destination path
        """
        # Copy all contents from dist to workspace root
        for item in src.iterdir():
            src_item = src / item.name
            dst_item = dst / item.name

            if src_item.is_dir():
                shutil.copytree(src_item, dst_item, dirs_exist_ok=True)
            else:
                shutil.copy2(src_item, dst_item)

        logger.info(f"Copied dist contents to workspace: {dst}")

    def _copy_repository(self, src: Path, dst: Path):
        """Copy repository contents, excluding .git and other files.

        Args:
            src: Source repository path
            dst: Destination path
        """
        ignore_patterns = {'.git', '.gitignore', '__pycache__', '*.pyc', 'logs', 'runs', '*.db'}

        for item in src.iterdir():
            if item.name in ignore_patterns:
                continue

            src_item = src / item.name
            dst_item = dst / item.name

            if src_item.is_dir():
                if not any(pattern in str(src_item) for pattern in ignore_patterns):
                    shutil.copytree(src_item, dst_item, ignore=shutil.ignore_patterns(*ignore_patterns))
            else:
                if not any(pattern in item.name for pattern in ignore_patterns):
                    shutil.copy2(src_item, dst_item)

    def prepare_for_project_init(self, workspace_path: Path):
        """Prepare workspace for project-init test.

        Removes files except .claude directory (needed for slash commands).

        Args:
            workspace_path: Path to the workspace
        """
        # Remove contents except .claude (needed for slash commands)
        if workspace_path.exists():
            for item in workspace_path.iterdir():
                # Keep .claude directory for slash commands
                if item.name == '.claude':
                    continue

                if item.is_dir():
                    shutil.rmtree(item)
                    logger.info(f"Removed directory: {item}")
                else:
                    item.unlink()
                    logger.info(f"Removed file: {item}")

            logger.info(f"Cleared contents (except .claude) from {workspace_path} for project-init test")

    def get_available_branches(self) -> list:
        """Get list of available branches.

        Returns:
            List of branch names
        """
        return [branch.name for branch in self.repo.branches]

    def get_available_tags(self) -> list:
        """Get list of available tags.

        Returns:
            List of tag names
        """
        return [tag.name for tag in self.repo.tags]

    def get_commit_info(self, commit_hash: str) -> dict:
        """Get information about a specific commit.

        Args:
            commit_hash: Commit hash

        Returns:
            Dictionary with commit information
        """
        try:
            commit = self.repo.commit(commit_hash)
            return {
                "hash": commit.hexsha,
                "author": str(commit.author),
                "email": commit.author.email,
                "message": commit.message,
                "date": commit.committed_datetime.isoformat()
            }
        except git.BadName:
            logger.error(f"Invalid commit hash: {commit_hash}")
            return {}

    def stash_changes(self) -> bool:
        """Stash any uncommitted changes.

        Returns:
            True if changes were stashed
        """
        if self.repo.is_dirty():
            self.repo.git.stash("save", "Test run stash")
            logger.info("Stashed uncommitted changes")
            return True
        return False

    def restore_stash(self):
        """Restore the most recent stash."""
        try:
            self.repo.git.stash("pop")
            logger.info("Restored stashed changes")
        except git.GitCommandError:
            logger.warning("No stash to restore")

    def reset_to_original(self, original_commit: str, original_branch: str):
        """Reset repository to original state.

        Args:
            original_commit: Original commit hash
            original_branch: Original branch name
        """
        try:
            if original_branch != "detached":
                self.repo.git.checkout(original_branch)
            else:
                self.repo.git.checkout(original_commit)
            logger.info(f"Reset to original state: {original_branch}@{original_commit[:8]}")
        except git.GitCommandError as e:
            logger.error(f"Failed to reset to original state: {e}")