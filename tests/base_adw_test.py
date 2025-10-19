"""Base class for ADW (AI Developer Workflow) tests.

This module provides common patterns and utilities for testing ADW scripts.
ADW tests are integration tests that validate complete workflows from start
to finish, as opposed to slash command tests which are unit tests.

Example:
    ```python
    from tests.base_adw_test import BaseAdwTest
    from src.checks.adw import AdwExecutionCheck

    class AdwInitTest(BaseAdwTest):
        def get_adw_name(self) -> str:
            return "adw_init.py"

        def get_adw_args(self) -> List[str]:
            return ["my-project"]

        def get_specific_checks(self) -> List[BaseCheck]:
            return [
                AdwExecutionCheck("adw_executes"),
                # ... more checks
            ]
    ```
"""

import sys
from pathlib import Path
from typing import List, Optional
from abc import ABC, abstractmethod
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import Config
from src.core.adw_runner import AdwRunner, AdwResult
from src.checks.base import BaseCheck
from src.checks.adw import (
    AdwExecutionCheck,
    PythonScriptValidityCheck,
    ClaudeExecutionCheck
)

logger = logging.getLogger(__name__)


class BaseAdwTest(ABC):
    """Base class for all ADW tests.

    Provides common patterns for:
    - Setting up ADW execution environment
    - Running ADW scripts with proper isolation
    - Validating ADW execution and outcomes
    - Checking final project state

    Subclasses must implement:
    - get_adw_name(): Return the ADW script name
    - get_adw_args(): Return arguments for the ADW
    - get_specific_checks(): Return test-specific checks
    """

    def __init__(self, config: Config):
        """Initialize the ADW test.

        Args:
            config: Configuration instance
        """
        self.config = config
        self.adw_runner = AdwRunner(config)

    @abstractmethod
    def get_adw_name(self) -> str:
        """Get the name of the ADW script to test.

        Returns:
            ADW script name (e.g., "adw_init.py")
        """
        pass

    @abstractmethod
    def get_adw_args(self) -> List[str]:
        """Get arguments to pass to the ADW script.

        Returns:
            List of command-line arguments
        """
        pass

    @abstractmethod
    def get_specific_checks(self) -> List[BaseCheck]:
        """Get test-specific checks.

        Returns:
            List of check instances specific to this ADW
        """
        pass

    def get_adw_checks(self, adw_result: AdwResult,
                       script_path: Path) -> List[BaseCheck]:
        """Get standard ADW checks that apply to all ADW tests.

        Args:
            adw_result: Result from ADW execution
            script_path: Path to the ADW script

        Returns:
            List of standard check instances
        """
        checks = []

        # Check 1: Script is valid Python
        checks.append(PythonScriptValidityCheck(
            name="adw_script_valid",
            script_path=script_path
        ))

        # Check 2: ADW executed successfully
        checks.append(AdwExecutionCheck(
            name="adw_execution_success",
            adw_result=adw_result,
            max_duration=self.config.adw.adw_timeout
        ))

        # Check 3: Claude was executed (for non-dry-run tests)
        checks.append(ClaudeExecutionCheck(
            name="claude_executed",
            adw_result=adw_result
        ))

        return checks

    def setup_adw_workspace(self, workspace: Path):
        """Set up the workspace for ADW execution.

        Default implementation does nothing. Override to add setup logic.

        Args:
            workspace: Path to the workspace directory
        """
        pass

    def validate_adw_execution(self, result: AdwResult) -> bool:
        """Validate that ADW execution was successful.

        Args:
            result: AdwResult from execution

        Returns:
            True if execution was successful
        """
        if not result.success:
            logger.error(f"ADW execution failed: {result.error_message}")
            logger.error(f"Stderr: {result.stderr}")
            return False

        logger.info(f"ADW executed successfully in {result.duration:.2f}s")
        return True

    def validate_claude_execution(self, result: AdwResult) -> bool:
        """Validate that Claude was executed by the ADW.

        Args:
            result: AdwResult from execution

        Returns:
            True if Claude execution was detected
        """
        if not result.claude_executed:
            logger.warning("Claude execution not detected in ADW output")
            return False

        logger.info("Claude execution detected in ADW output")
        return True

    def validate_project_outcome(self, workspace: Path) -> bool:
        """Validate the final project state after ADW execution.

        Default implementation checks for basic project structure.
        Override to add specific validations.

        Args:
            workspace: Path to the workspace directory

        Returns:
            True if project outcome is valid
        """
        # Check workspace exists
        if not workspace.exists():
            logger.error(f"Workspace does not exist: {workspace}")
            return False

        logger.info(f"Workspace exists: {workspace}")
        return True

    def run_adw(
        self,
        workspace: Path,
        args: Optional[List[str]] = None,
        dry_run: bool = False
    ) -> AdwResult:
        """Run the ADW script.

        Args:
            workspace: Workspace directory for execution
            args: Additional arguments (defaults to get_adw_args())
            dry_run: Whether to run in dry-run mode

        Returns:
            AdwResult from execution
        """
        # Get ADW script path
        adw_name = self.get_adw_name()
        script_path = self.adw_runner.get_adw_path(adw_name)

        # Get arguments
        if args is None:
            args = self.get_adw_args()

        # Setup workspace
        self.setup_adw_workspace(workspace)

        # Execute ADW
        logger.info(f"Running ADW: {adw_name} with args: {args}")
        result = self.adw_runner.execute_adw(
            script_path=script_path,
            args=args,
            workspace=workspace,
            dry_run=dry_run
        )

        return result

    def get_all_checks(self, adw_result: AdwResult,
                       script_path: Path) -> List[BaseCheck]:
        """Get all checks for this ADW test.

        Combines standard ADW checks with test-specific checks.

        Args:
            adw_result: Result from ADW execution
            script_path: Path to the ADW script

        Returns:
            List of all check instances
        """
        checks = []

        # Add standard ADW checks
        checks.extend(self.get_adw_checks(adw_result, script_path))

        # Add test-specific checks
        checks.extend(self.get_specific_checks())

        return checks

    def print_result_summary(self, adw_result: AdwResult):
        """Print a summary of the ADW execution result.

        Args:
            adw_result: Result from ADW execution
        """
        print(f"\n{'='*60}")
        print(f"ADW Execution Summary: {self.get_adw_name()}")
        print(f"{'='*60}")
        print(f"Success: {adw_result.success}")
        print(f"Exit Code: {adw_result.exit_code}")
        print(f"Duration: {adw_result.duration:.2f}s")
        print(f"Claude Executed: {adw_result.claude_executed}")

        if adw_result.error_message:
            print(f"Error: {adw_result.error_message}")

        if adw_result.stdout:
            print(f"\nStdout (first 500 chars):")
            print(adw_result.stdout[:500])

        if adw_result.stderr:
            print(f"\nStderr (first 500 chars):")
            print(adw_result.stderr[:500])

        print(f"{'='*60}\n")


def run_adw_test_standalone(
    test_class,
    config_path: str = "config.yaml",
    model: Optional[str] = None,
    dry_run: bool = False
):
    """Helper function to run an ADW test standalone.

    This is useful for testing individual ADW tests during development.

    Args:
        test_class: ADW test class (subclass of BaseAdwTest)
        config_path: Path to configuration file
        model: Model to use (optional)
        dry_run: Whether to run in dry-run mode

    Returns:
        AdwResult from execution
    """
    import tempfile
    import shutil

    # Load configuration
    config = Config(config_path)

    # Validate configuration
    errors = config.validate()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        return None

    # Create test instance
    test = test_class(config)

    # Create temporary workspace
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir)

        # Run ADW
        result = test.run_adw(workspace, dry_run=dry_run)

        # Print summary
        test.print_result_summary(result)

        # Get and execute checks
        script_path = test.adw_runner.get_adw_path(test.get_adw_name())
        checks = test.get_all_checks(result, script_path)

        print("\nCheck Results:")
        print("-" * 60)

        passed = 0
        failed = 0

        for check in checks:
            check.set_context(workspace, workspace / "artifacts")
            check_result = check.execute(adw_result=result, script_path=script_path)

            status = "✓" if check_result.passed else "✗"
            print(f"  {status} {check_result.name}")

            if not check_result.passed:
                if check_result.details:
                    print(f"    Details: {check_result.details}")
                if check_result.error:
                    print(f"    Error: {check_result.error}")
                failed += 1
            else:
                passed += 1

        print("-" * 60)
        print(f"Summary: {passed} passed, {failed} failed")

        return result
