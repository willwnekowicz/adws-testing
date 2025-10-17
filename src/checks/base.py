"""Base classes for test checks."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CheckType(Enum):
    """Types of checks available."""
    SIMPLE = "simple"
    LLM_JUDGE = "llm_judge"


class CheckStatus(Enum):
    """Status of a check execution."""
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class CheckResult:
    """Result of a check execution."""
    name: str
    check_type: CheckType
    status: CheckStatus
    passed: bool
    details: Optional[str] = None
    artifacts: Optional[List[str]] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "name": self.name,
            "check_type": self.check_type.value,
            "status": self.status.value,
            "passed": self.passed,
            "details": self.details,
            "artifacts": self.artifacts,
            "error": self.error
        }


class BaseCheck(ABC):
    """Abstract base class for all checks."""

    def __init__(self, name: str, check_type: CheckType = CheckType.SIMPLE):
        """Initialize a check.

        Args:
            name: Name of the check
            check_type: Type of check
        """
        self.name = name
        self.check_type = check_type
        self.workspace_path: Optional[Path] = None
        self.artifacts_path: Optional[Path] = None

    def set_context(self, workspace_path: Path, artifacts_path: Path):
        """Set the context for the check execution.

        Args:
            workspace_path: Path to the test workspace
            artifacts_path: Path to store artifacts
        """
        self.workspace_path = workspace_path
        self.artifacts_path = artifacts_path

    @abstractmethod
    def execute(self, **kwargs) -> CheckResult:
        """Execute the check.

        Returns:
            CheckResult with the outcome
        """
        pass

    def _create_result(self, passed: bool, details: Optional[str] = None,
                      artifacts: Optional[List[str]] = None,
                      error: Optional[str] = None) -> CheckResult:
        """Helper to create a CheckResult.

        Args:
            passed: Whether the check passed
            details: Additional details
            artifacts: List of artifact paths
            error: Error message if any

        Returns:
            CheckResult instance
        """
        status = CheckStatus.PASSED if passed else CheckStatus.FAILED
        if error:
            status = CheckStatus.ERROR

        return CheckResult(
            name=self.name,
            check_type=self.check_type,
            status=status,
            passed=passed,
            details=details,
            artifacts=artifacts,
            error=error
        )


class CompositeCheck(BaseCheck):
    """A check that combines multiple sub-checks."""

    def __init__(self, name: str, checks: List[BaseCheck],
                 require_all: bool = True):
        """Initialize a composite check.

        Args:
            name: Name of the composite check
            checks: List of checks to execute
            require_all: Whether all checks must pass
        """
        super().__init__(name, CheckType.SIMPLE)
        self.checks = checks
        self.require_all = require_all

    def set_context(self, workspace_path: Path, artifacts_path: Path):
        """Set context for all sub-checks."""
        super().set_context(workspace_path, artifacts_path)
        for check in self.checks:
            check.set_context(workspace_path, artifacts_path)

    def execute(self, **kwargs) -> CheckResult:
        """Execute all sub-checks.

        Returns:
            CheckResult with combined outcome
        """
        results = []
        all_passed = True
        any_passed = False
        details_list = []
        all_artifacts = []

        for check in self.checks:
            try:
                result = check.execute(**kwargs)
                results.append(result)

                if result.passed:
                    any_passed = True
                else:
                    all_passed = False

                if result.details:
                    details_list.append(f"{check.name}: {result.details}")

                if result.artifacts:
                    all_artifacts.extend(result.artifacts)

            except Exception as e:
                logger.error(f"Error in check {check.name}: {e}")
                all_passed = False
                details_list.append(f"{check.name}: ERROR - {str(e)}")

        # Determine overall pass/fail
        if self.require_all:
            passed = all_passed
        else:
            passed = any_passed

        details = "\n".join(details_list) if details_list else None

        return self._create_result(
            passed=passed,
            details=details,
            artifacts=all_artifacts if all_artifacts else None
        )


class CheckRegistry:
    """Registry for managing available checks."""

    def __init__(self):
        """Initialize the check registry."""
        self._checks: Dict[str, BaseCheck] = {}

    def register(self, check: BaseCheck):
        """Register a check.

        Args:
            check: Check to register
        """
        self._checks[check.name] = check
        logger.debug(f"Registered check: {check.name}")

    def get(self, name: str) -> Optional[BaseCheck]:
        """Get a check by name.

        Args:
            name: Name of the check

        Returns:
            Check instance or None
        """
        return self._checks.get(name)

    def list_checks(self) -> List[str]:
        """List all registered check names.

        Returns:
            List of check names
        """
        return list(self._checks.keys())

    def execute_checks(self, check_names: List[str],
                      workspace_path: Path,
                      artifacts_path: Path,
                      **kwargs) -> List[CheckResult]:
        """Execute multiple checks.

        Args:
            check_names: Names of checks to execute
            workspace_path: Path to test workspace
            artifacts_path: Path for artifacts
            **kwargs: Additional arguments for checks

        Returns:
            List of CheckResults
        """
        results = []

        for name in check_names:
            check = self.get(name)
            if not check:
                logger.warning(f"Check not found: {name}")
                results.append(CheckResult(
                    name=name,
                    check_type=CheckType.SIMPLE,
                    status=CheckStatus.ERROR,
                    passed=False,
                    error=f"Check '{name}' not found in registry"
                ))
                continue

            check.set_context(workspace_path, artifacts_path)

            try:
                result = check.execute(**kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Error executing check {name}: {e}")
                results.append(CheckResult(
                    name=name,
                    check_type=check.check_type,
                    status=CheckStatus.ERROR,
                    passed=False,
                    error=str(e)
                ))

        return results