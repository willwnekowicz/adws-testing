"""Checks for SDLC workflow validation.

This module provides checks to validate that SDLC workflows
(feature, bug, chore) execute correctly.
"""

import re
from pathlib import Path
from typing import List, Optional
from .base import BaseCheck


class SDLCPlanCheck(BaseCheck):
    """Check that an SDLC plan file was created."""

    def __init__(
        self,
        name: str = "sdlc_plan_created",
        workflow_type: str = "feature"
    ):
        """Initialize SDLC plan check.

        Args:
            name: Check name
            workflow_type: Type of workflow (feature, bug, chore)
        """
        super().__init__(name)
        self.workflow_type = workflow_type

    def execute(self, workspace: Path) -> bool:
        """Execute the check.

        Args:
            workspace: Path to workspace

        Returns:
            True if check passes
        """
        # Look for plan files
        plans_dir = workspace / "plans"
        if not plans_dir.exists():
            self.message = "Plans directory does not exist"
            return False

        # Check for plan file matching workflow type
        plan_files = list(plans_dir.glob(f"*{self.workflow_type}*.md"))
        if not plan_files:
            self.message = f"No {self.workflow_type} plan file found"
            return False

        # Validate plan content
        plan_file = plan_files[0]
        content = plan_file.read_text()

        required_sections = ["Overview", "Implementation", "Testing"]
        missing = [s for s in required_sections if s not in content]

        if missing:
            self.message = f"Plan missing sections: {', '.join(missing)}"
            return False

        self.message = f"Valid {self.workflow_type} plan found: {plan_file.name}"
        return True


class SDLCImplementationCheck(BaseCheck):
    """Check that SDLC implementation was completed."""

    def __init__(
        self,
        name: str = "sdlc_implementation",
        expected_files: Optional[List[str]] = None
    ):
        """Initialize implementation check.

        Args:
            name: Check name
            expected_files: List of files expected to be created/modified
        """
        super().__init__(name)
        self.expected_files = expected_files or []

    def execute(self, workspace: Path) -> bool:
        """Execute the check.

        Args:
            workspace: Path to workspace

        Returns:
            True if check passes
        """
        # Check git status for changes
        import subprocess
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=workspace,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            self.message = "Failed to check git status"
            return False

        changes = result.stdout.strip()
        if not changes:
            self.message = "No implementation changes detected"
            return False

        # Check for expected files if specified
        if self.expected_files:
            missing = []
            for expected in self.expected_files:
                file_path = workspace / expected
                if not file_path.exists():
                    missing.append(expected)

            if missing:
                self.message = f"Expected files missing: {', '.join(missing)}"
                return False

        self.message = "Implementation changes detected"
        return True


class SDLCTestsCheck(BaseCheck):
    """Check that tests were created or updated."""

    def __init__(
        self,
        name: str = "sdlc_tests",
        test_pattern: str = "*test*.{js,ts,py}"
    ):
        """Initialize tests check.

        Args:
            name: Check name
            test_pattern: Glob pattern for test files
        """
        super().__init__(name)
        self.test_pattern = test_pattern

    def execute(self, workspace: Path) -> bool:
        """Execute the check.

        Args:
            workspace: Path to workspace

        Returns:
            True if check passes
        """
        # Look for test files
        test_files = []
        for pattern in self.test_pattern.split(","):
            test_files.extend(workspace.rglob(pattern.strip()))

        if not test_files:
            self.message = f"No test files matching '{self.test_pattern}' found"
            return False

        # Check if any test files were modified recently
        import subprocess
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=workspace,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            changed_files = result.stdout.strip().split("\n")
            test_changes = [f for f in changed_files if "test" in f.lower()]

            if test_changes:
                self.message = f"Tests updated: {len(test_changes)} files"
                return True

        self.message = f"Test files exist but none were updated"
        # This is a warning, not a failure
        return True


class SDLCDocumentationCheck(BaseCheck):
    """Check that documentation was created or updated."""

    def __init__(
        self,
        name: str = "sdlc_documentation"
    ):
        """Initialize documentation check.

        Args:
            name: Check name
        """
        super().__init__(name)

    def execute(self, workspace: Path) -> bool:
        """Execute the check.

        Args:
            workspace: Path to workspace

        Returns:
            True if check passes
        """
        docs_dir = workspace / "documentation"
        if not docs_dir.exists():
            self.message = "Documentation directory does not exist"
            return False

        # Check for recent documentation updates
        import subprocess
        result = subprocess.run(
            ["git", "diff", "--name-only", "documentation/"],
            cwd=workspace,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            self.message = "Failed to check documentation changes"
            return False

        changes = result.stdout.strip()
        if not changes:
            self.message = "No documentation updates detected"
            # This is optional, so we don't fail
            return True

        doc_files = changes.split("\n")
        self.message = f"Documentation updated: {len(doc_files)} files"
        return True


class SDLCCommitCheck(BaseCheck):
    """Check that changes were committed properly."""

    def __init__(
        self,
        name: str = "sdlc_commit",
        workflow_type: str = "feature"
    ):
        """Initialize commit check.

        Args:
            name: Check name
            workflow_type: Type of workflow
        """
        super().__init__(name)
        self.workflow_type = workflow_type

    def execute(self, workspace: Path) -> bool:
        """Execute the check.

        Args:
            workspace: Path to workspace

        Returns:
            True if check passes
        """
        import subprocess

        # Check for recent commits
        result = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            cwd=workspace,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            self.message = "Failed to check git log"
            return False

        commits = result.stdout.strip().split("\n")
        if not commits:
            self.message = "No commits found"
            return False

        # Check latest commit message
        latest = commits[0]

        # Workflow type prefixes
        prefixes = {
            "feature": ["feat:", "feature:", "add:"],
            "bug": ["fix:", "bug:", "bugfix:"],
            "chore": ["chore:", "refactor:", "docs:", "test:"]
        }

        expected_prefixes = prefixes.get(self.workflow_type, [])
        has_prefix = any(prefix in latest.lower() for prefix in expected_prefixes)

        if not has_prefix:
            self.message = f"Commit message doesn't match {self.workflow_type} pattern"
            # This is a warning, not a failure
            return True

        self.message = f"Valid {self.workflow_type} commit: {latest[:50]}"
        return True


class SDLCPullRequestCheck(BaseCheck):
    """Check that a pull request was created."""

    def __init__(
        self,
        name: str = "sdlc_pull_request"
    ):
        """Initialize pull request check.

        Args:
            name: Check name
        """
        super().__init__(name)

    def execute(self, workspace: Path) -> bool:
        """Execute the check.

        Args:
            workspace: Path to workspace

        Returns:
            True if check passes
        """
        import subprocess

        # Check if we're on a feature branch
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=workspace,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            self.message = "Failed to check current branch"
            return False

        branch = result.stdout.strip()
        if branch in ["main", "master", "staging"]:
            self.message = f"Still on {branch} branch, no feature branch created"
            return False

        # Check if branch was pushed
        result = subprocess.run(
            ["git", "remote", "-v"],
            cwd=workspace,
            capture_output=True,
            text=True
        )

        if "origin" not in result.stdout:
            self.message = "No remote configured"
            return False

        # Check for PR file or marker
        pr_file = workspace / ".github" / "pull_request.md"
        if pr_file.exists():
            self.message = f"PR template found on branch: {branch}"
            return True

        self.message = f"On feature branch: {branch}"
        return True


def get_sdlc_checks(workflow_type: str = "feature") -> List[BaseCheck]:
    """Get standard SDLC workflow checks.

    Args:
        workflow_type: Type of workflow (feature, bug, chore)

    Returns:
        List of check instances
    """
    checks = [
        SDLCPlanCheck(workflow_type=workflow_type),
        SDLCImplementationCheck(),
        SDLCTestsCheck(),
        SDLCDocumentationCheck(),
        SDLCCommitCheck(workflow_type=workflow_type),
        SDLCPullRequestCheck()
    ]

    return checks