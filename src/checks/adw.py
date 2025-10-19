"""ADW-specific check classes."""

import ast
from pathlib import Path
from typing import Optional, List
import logging
import re

from .base import BaseCheck, CheckResult, CheckType

logger = logging.getLogger(__name__)


class AdwExecutionCheck(BaseCheck):
    """Check that ADW script executed successfully."""

    def __init__(self, name: str, adw_result=None, max_duration: Optional[float] = None):
        """Initialize check.

        Args:
            name: Check name
            adw_result: AdwResult instance from execution
            max_duration: Maximum acceptable duration in seconds
        """
        super().__init__(name, CheckType.SIMPLE)
        self.adw_result = adw_result
        self.max_duration = max_duration

    def execute(self, adw_result=None, **kwargs) -> CheckResult:
        """Execute the check.

        Args:
            adw_result: AdwResult instance (can be passed here or in __init__)
            **kwargs: Additional arguments

        Returns:
            CheckResult
        """
        result = adw_result or self.adw_result

        if not result:
            return self._create_result(
                passed=False,
                error="No ADW result provided to check"
            )

        # Check if execution was successful
        if not result.success:
            details = f"ADW execution failed with exit code {result.exit_code}"
            if result.error_message:
                details += f"\nError: {result.error_message}"
            if result.stderr:
                details += f"\nStderr: {result.stderr[:500]}"

            return self._create_result(
                passed=False,
                details=details
            )

        # Check duration if specified
        if self.max_duration and result.duration > self.max_duration:
            return self._create_result(
                passed=False,
                details=f"ADW execution took {result.duration:.2f}s (max: {self.max_duration}s)"
            )

        # Success
        details = f"ADW executed successfully in {result.duration:.2f}s"
        if result.claude_executed:
            details += " (Claude execution detected)"

        return self._create_result(
            passed=True,
            details=details
        )


class AdwOutputCheck(BaseCheck):
    """Check ADW output for expected patterns."""

    def __init__(
        self,
        name: str,
        adw_result=None,
        contains: Optional[List[str]] = None,
        not_contains: Optional[List[str]] = None,
        regex_patterns: Optional[List[str]] = None
    ):
        """Initialize check.

        Args:
            name: Check name
            adw_result: AdwResult instance
            contains: Strings that must be in output
            not_contains: Strings that must not be in output
            regex_patterns: Regex patterns that must match
        """
        super().__init__(name, CheckType.SIMPLE)
        self.adw_result = adw_result
        self.contains = contains or []
        self.not_contains = not_contains or []
        self.regex_patterns = regex_patterns or []

    def execute(self, adw_result=None, **kwargs) -> CheckResult:
        """Execute the check.

        Args:
            adw_result: AdwResult instance
            **kwargs: Additional arguments

        Returns:
            CheckResult
        """
        result = adw_result or self.adw_result

        if not result:
            return self._create_result(
                passed=False,
                error="No ADW result provided to check"
            )

        # Combine stdout and stderr for checking
        output = result.stdout + "\n" + result.stderr

        # Check required strings
        for pattern in self.contains:
            if pattern not in output:
                return self._create_result(
                    passed=False,
                    details=f"Expected output to contain: '{pattern}'"
                )

        # Check forbidden strings
        for pattern in self.not_contains:
            if pattern in output:
                return self._create_result(
                    passed=False,
                    details=f"Output should not contain: '{pattern}'"
                )

        # Check regex patterns
        for pattern in self.regex_patterns:
            if not re.search(pattern, output, re.MULTILINE):
                return self._create_result(
                    passed=False,
                    details=f"Output should match regex: '{pattern}'"
                )

        return self._create_result(
            passed=True,
            details="Output matches all expected patterns"
        )


class PythonScriptValidityCheck(BaseCheck):
    """Check that ADW script is valid Python."""

    def __init__(self, name: str, script_path: Optional[Path] = None):
        """Initialize check.

        Args:
            name: Check name
            script_path: Path to script to validate
        """
        super().__init__(name, CheckType.SIMPLE)
        self.script_path = script_path

    def execute(self, script_path: Optional[Path] = None, **kwargs) -> CheckResult:
        """Execute the check.

        Args:
            script_path: Path to script (can be passed here or in __init__)
            **kwargs: Additional arguments

        Returns:
            CheckResult
        """
        path = script_path or self.script_path

        if not path:
            return self._create_result(
                passed=False,
                error="No script path provided"
            )

        if not path.exists():
            return self._create_result(
                passed=False,
                details=f"Script does not exist: {path}"
            )

        # Read script content
        try:
            content = path.read_text()
        except Exception as e:
            return self._create_result(
                passed=False,
                error=f"Cannot read script: {e}"
            )

        # Check shebang
        lines = content.split('\n')
        if not lines or not lines[0].startswith('#!'):
            return self._create_result(
                passed=False,
                details="Script missing shebang line"
            )

        # Validate Python syntax
        try:
            ast.parse(content)
        except SyntaxError as e:
            return self._create_result(
                passed=False,
                details=f"Invalid Python syntax: {e}"
            )

        return self._create_result(
            passed=True,
            details="Script is valid Python with proper shebang"
        )


class UvDependencyCheck(BaseCheck):
    """Check that ADW script has valid uv dependency block."""

    def __init__(self, name: str, script_path: Optional[Path] = None,
                 required_dependencies: Optional[List[str]] = None):
        """Initialize check.

        Args:
            name: Check name
            script_path: Path to script to validate
            required_dependencies: Dependencies that must be present
        """
        super().__init__(name, CheckType.SIMPLE)
        self.script_path = script_path
        self.required_dependencies = required_dependencies or []

    def execute(self, script_path: Optional[Path] = None, **kwargs) -> CheckResult:
        """Execute the check.

        Args:
            script_path: Path to script
            **kwargs: Additional arguments

        Returns:
            CheckResult
        """
        path = script_path or self.script_path

        if not path:
            return self._create_result(
                passed=False,
                error="No script path provided"
            )

        if not path.exists():
            return self._create_result(
                passed=False,
                details=f"Script does not exist: {path}"
            )

        # Read script content
        try:
            content = path.read_text()
        except Exception as e:
            return self._create_result(
                passed=False,
                error=f"Cannot read script: {e}"
            )

        # Check for uv dependencies block (PEP 723)
        if '# /// script' not in content and '# /// pyproject' not in content:
            return self._create_result(
                passed=False,
                details="Script missing uv dependencies block (# /// script)"
            )

        # Extract dependencies
        dep_match = re.search(r'dependencies\s*=\s*\[(.*?)\]', content, re.DOTALL)
        if not dep_match and self.required_dependencies:
            return self._create_result(
                passed=False,
                details="Script has uv block but no dependencies listed"
            )

        if dep_match:
            deps_str = dep_match.group(1)
            found_deps = [d.strip().strip('"\'') for d in deps_str.split(',') if d.strip()]

            # Check required dependencies
            for required in self.required_dependencies:
                # Allow version specifiers
                required_base = required.split('>=')[0].split('==')[0].split('~=')[0]
                if not any(required_base in dep for dep in found_deps):
                    return self._create_result(
                        passed=False,
                        details=f"Missing required dependency: {required}"
                    )

            details = f"Valid uv dependencies block with {len(found_deps)} dependencies"
            return self._create_result(
                passed=True,
                details=details
            )

        return self._create_result(
            passed=True,
            details="Valid uv dependencies block"
        )


class ClaudeExecutionCheck(BaseCheck):
    """Check that Claude CLI was executed by the ADW."""

    def __init__(self, name: str, adw_result=None):
        """Initialize check.

        Args:
            name: Check name
            adw_result: AdwResult instance
        """
        super().__init__(name, CheckType.SIMPLE)
        self.adw_result = adw_result

    def execute(self, adw_result=None, **kwargs) -> CheckResult:
        """Execute the check.

        Args:
            adw_result: AdwResult instance
            **kwargs: Additional arguments

        Returns:
            CheckResult
        """
        result = adw_result or self.adw_result

        if not result:
            return self._create_result(
                passed=False,
                error="No ADW result provided to check"
            )

        if not result.claude_executed:
            return self._create_result(
                passed=False,
                details="Claude CLI execution not detected in ADW output"
            )

        return self._create_result(
            passed=True,
            details="Claude CLI was executed by ADW"
        )
