"""Simple check implementations for basic validations."""

import os
import re
import time
import subprocess
from pathlib import Path
from typing import Optional, Any, List, Dict, Union
from .base import BaseCheck, CheckResult, CheckType
import logging
import json

logger = logging.getLogger(__name__)


class FileExistsCheck(BaseCheck):
    """Check if a file exists."""

    def __init__(self, name: str, file_path: str):
        """Initialize file existence check.

        Args:
            name: Check name
            file_path: Path to file relative to workspace
        """
        super().__init__(name, CheckType.SIMPLE)
        self.file_path = file_path

    def execute(self, **kwargs) -> CheckResult:
        """Check if file exists."""
        if not self.workspace_path:
            return self._create_result(
                passed=False,
                error="No workspace path set"
            )

        full_path = self.workspace_path / self.file_path
        exists = full_path.exists()

        return self._create_result(
            passed=exists,
            details=f"File {'exists' if exists else 'does not exist'}: {self.file_path}"
        )


class FileNotExistsCheck(BaseCheck):
    """Check that a file does NOT exist."""

    def __init__(self, name: str, file_path: str):
        """Initialize file non-existence check.

        Args:
            name: Check name
            file_path: Path to file relative to workspace
        """
        super().__init__(name, CheckType.SIMPLE)
        self.file_path = file_path

    def execute(self, **kwargs) -> CheckResult:
        """Check that file does not exist."""
        if not self.workspace_path:
            return self._create_result(
                passed=False,
                error="No workspace path set"
            )

        full_path = self.workspace_path / self.file_path
        exists = full_path.exists()

        return self._create_result(
            passed=not exists,
            details=f"File {'should not exist but does' if exists else 'correctly does not exist'}: {self.file_path}"
        )


class FileContentCheck(BaseCheck):
    """Check file content against patterns."""

    def __init__(self, name: str, file_path: str,
                 contains: Optional[List[str]] = None,
                 regex: Optional[str] = None,
                 not_contains: Optional[List[str]] = None):
        """Initialize file content check.

        Args:
            name: Check name
            file_path: Path to file relative to workspace
            contains: List of strings that must be present
            regex: Regular expression pattern that must match
            not_contains: List of strings that must not be present
        """
        super().__init__(name, CheckType.SIMPLE)
        self.file_path = file_path
        self.contains = contains or []
        self.regex = regex
        self.not_contains = not_contains or []

    def execute(self, **kwargs) -> CheckResult:
        """Check file content."""
        if not self.workspace_path:
            return self._create_result(
                passed=False,
                error="No workspace path set"
            )

        full_path = self.workspace_path / self.file_path

        if not full_path.exists():
            return self._create_result(
                passed=False,
                details=f"File not found: {self.file_path}"
            )

        try:
            content = full_path.read_text()
        except Exception as e:
            return self._create_result(
                passed=False,
                error=f"Error reading file: {e}"
            )

        results = []

        # Check for required content
        for required in self.contains:
            if required in content:
                results.append(f"✓ Found: '{required}'")
            else:
                results.append(f"✗ Missing: '{required}'")

        # Check regex pattern
        if self.regex:
            pattern = re.compile(self.regex, re.MULTILINE | re.DOTALL)
            if pattern.search(content):
                results.append(f"✓ Regex matched: {self.regex}")
            else:
                results.append(f"✗ Regex not matched: {self.regex}")

        # Check for forbidden content
        for forbidden in self.not_contains:
            if forbidden not in content:
                results.append(f"✓ Not present: '{forbidden}'")
            else:
                results.append(f"✗ Found forbidden: '{forbidden}'")

        # Determine overall pass/fail
        passed = all(
            (all(req in content for req in self.contains),
             not self.regex or re.search(self.regex, content, re.MULTILINE | re.DOTALL),
             all(forb not in content for forb in self.not_contains))
        )

        return self._create_result(
            passed=passed,
            details="\n".join(results)
        )


class GitBranchCheck(BaseCheck):
    """Check current git branch."""

    def __init__(self, name: str, expected_branch: str):
        """Initialize git branch check.

        Args:
            name: Check name
            expected_branch: Expected branch name
        """
        super().__init__(name, CheckType.SIMPLE)
        self.expected_branch = expected_branch

    def execute(self, **kwargs) -> CheckResult:
        """Check current git branch."""
        if not self.workspace_path:
            return self._create_result(
                passed=False,
                error="No workspace path set"
            )

        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.workspace_path,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return self._create_result(
                    passed=False,
                    details=f"Git command failed: {result.stderr}"
                )

            current_branch = result.stdout.strip()
            passed = current_branch == self.expected_branch

            return self._create_result(
                passed=passed,
                details=f"Current branch: '{current_branch}', Expected: '{self.expected_branch}'"
            )

        except Exception as e:
            return self._create_result(
                passed=False,
                error=f"Error checking git branch: {e}"
            )


class GitConfigCheck(BaseCheck):
    """Check git configuration."""

    def __init__(self, name: str, required_branches: Optional[List[str]] = None,
                 required_remotes: Optional[List[str]] = None):
        """Initialize git config check.

        Args:
            name: Check name
            required_branches: List of branches that should exist
            required_remotes: List of remotes that should exist
        """
        super().__init__(name, CheckType.SIMPLE)
        self.required_branches = required_branches or []
        self.required_remotes = required_remotes or []

    def execute(self, **kwargs) -> CheckResult:
        """Check git configuration."""
        if not self.workspace_path:
            return self._create_result(
                passed=False,
                error="No workspace path set"
            )

        results = []
        all_passed = True

        # Check branches
        if self.required_branches:
            try:
                result = subprocess.run(
                    ["git", "branch", "-a"],
                    cwd=self.workspace_path,
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    branches = result.stdout
                    for branch in self.required_branches:
                        if branch in branches:
                            results.append(f"✓ Branch exists: {branch}")
                        else:
                            results.append(f"✗ Branch missing: {branch}")
                            all_passed = False
                else:
                    results.append(f"✗ Failed to list branches: {result.stderr}")
                    all_passed = False

            except Exception as e:
                results.append(f"✗ Error checking branches: {e}")
                all_passed = False

        # Check remotes
        if self.required_remotes:
            try:
                result = subprocess.run(
                    ["git", "remote", "-v"],
                    cwd=self.workspace_path,
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    remotes = result.stdout
                    for remote in self.required_remotes:
                        if remote in remotes:
                            results.append(f"✓ Remote exists: {remote}")
                        else:
                            results.append(f"✗ Remote missing: {remote}")
                            all_passed = False
                else:
                    results.append(f"✗ Failed to list remotes: {result.stderr}")
                    all_passed = False

            except Exception as e:
                results.append(f"✗ Error checking remotes: {e}")
                all_passed = False

        return self._create_result(
            passed=all_passed,
            details="\n".join(results) if results else "No checks performed"
        )


class DurationCheck(BaseCheck):
    """Check execution duration."""

    def __init__(self, name: str, max_duration: float):
        """Initialize duration check.

        Args:
            name: Check name
            max_duration: Maximum allowed duration in seconds
        """
        super().__init__(name, CheckType.SIMPLE)
        self.max_duration = max_duration

    def execute(self, duration: float = None, **kwargs) -> CheckResult:
        """Check if duration is within limit.

        Args:
            duration: Actual duration in seconds
        """
        if duration is None:
            return self._create_result(
                passed=False,
                error="No duration provided"
            )

        passed = duration <= self.max_duration

        return self._create_result(
            passed=passed,
            details=f"Duration: {duration:.2f}s, Max: {self.max_duration:.2f}s"
        )


class DirectoryStructureCheck(BaseCheck):
    """Check directory structure."""

    def __init__(self, name: str, required_dirs: Optional[List[str]] = None,
                 required_files: Optional[List[str]] = None):
        """Initialize directory structure check.

        Args:
            name: Check name
            required_dirs: List of directories that should exist
            required_files: List of files that should exist
        """
        super().__init__(name, CheckType.SIMPLE)
        self.required_dirs = required_dirs or []
        self.required_files = required_files or []

    def execute(self, **kwargs) -> CheckResult:
        """Check directory structure."""
        if not self.workspace_path:
            return self._create_result(
                passed=False,
                error="No workspace path set"
            )

        results = []
        all_passed = True

        # Check directories
        for dir_path in self.required_dirs:
            full_path = self.workspace_path / dir_path
            if full_path.is_dir():
                results.append(f"✓ Directory exists: {dir_path}")
            else:
                results.append(f"✗ Directory missing: {dir_path}")
                all_passed = False

        # Check files
        for file_path in self.required_files:
            full_path = self.workspace_path / file_path
            if full_path.is_file():
                results.append(f"✓ File exists: {file_path}")
            else:
                results.append(f"✗ File missing: {file_path}")
                all_passed = False

        return self._create_result(
            passed=all_passed,
            details="\n".join(results) if results else "No structure checks performed"
        )


class JSONValidationCheck(BaseCheck):
    """Check if a file contains valid JSON."""

    def __init__(self, name: str, file_path: str,
                 schema: Optional[dict] = None):
        """Initialize JSON validation check.

        Args:
            name: Check name
            file_path: Path to JSON file
            schema: Optional JSON schema to validate against
        """
        super().__init__(name, CheckType.SIMPLE)
        self.file_path = file_path
        self.schema = schema

    def execute(self, **kwargs) -> CheckResult:
        """Check JSON validity."""
        if not self.workspace_path:
            return self._create_result(
                passed=False,
                error="No workspace path set"
            )

        full_path = self.workspace_path / self.file_path

        if not full_path.exists():
            return self._create_result(
                passed=False,
                details=f"File not found: {self.file_path}"
            )

        try:
            content = full_path.read_text()
            data = json.loads(content)

            # Optionally validate against schema
            if self.schema:
                import jsonschema
                jsonschema.validate(data, self.schema)
                return self._create_result(
                    passed=True,
                    details=f"Valid JSON with schema validation"
                )

            return self._create_result(
                passed=True,
                details=f"Valid JSON"
            )

        except json.JSONDecodeError as e:
            return self._create_result(
                passed=False,
                details=f"Invalid JSON: {e}"
            )
        except jsonschema.ValidationError as e:
            return self._create_result(
                passed=False,
                details=f"Schema validation failed: {e}"
            )
        except Exception as e:
            return self._create_result(
                passed=False,
                error=f"Error validating JSON: {e}"
            )