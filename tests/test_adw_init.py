"""Test case for the adw_init.py ADW script.

This test validates that the adw_init ADW (AI Developer Workflow) correctly
orchestrates the /project-init slash command to set up new projects.

This is an integration test, testing the complete workflow from ADW script
execution through to final project state.
"""

import sys
from pathlib import Path
from typing import List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import Config
from src.core.runner import TestRunner
from src.checks.base import BaseCheck, CompositeCheck
from src.checks.simple import (
    FileExistsCheck,
    FileContentCheck,
    GitBranchCheck,
    GitConfigCheck,
    DirectoryStructureCheck
)
from src.checks.adw import (
    AdwExecutionCheck,
    PythonScriptValidityCheck,
    AdwOutputCheck,
    ClaudeExecutionCheck
)
from tests.base_adw_test import BaseAdwTest, run_adw_test_standalone
from tests.test_project_init import get_project_init_checks


def get_adw_init_checks(adw_result=None, script_path=None):
    """Get checks for adw_init test.

    Args:
        adw_result: AdwResult instance from execution
        script_path: Path to the ADW script

    Returns:
        List of check instances
    """
    checks = []

    # ADW-specific checks
    if script_path:
        checks.append(PythonScriptValidityCheck(
            name="adw_script_valid",
            script_path=script_path
        ))

    if adw_result:
        checks.append(AdwExecutionCheck(
            name="adw_execution_success",
            adw_result=adw_result,
            max_duration=600  # 10 minutes max
        ))

        checks.append(ClaudeExecutionCheck(
            name="claude_executed",
            adw_result=adw_result
        ))

        checks.append(AdwOutputCheck(
            name="adw_output_check",
            adw_result=adw_result,
            not_contains=["Error", "Failed", "Exception"]  # Should not have errors
        ))

    # Include all project-init checks to validate final state
    # These checks validate that the ADW correctly executed /project-init
    project_checks = get_project_init_checks()
    checks.extend(project_checks)

    return checks


class AdwInitTest(BaseAdwTest):
    """Test class for adw_init.py workflow."""

    def __init__(self, config: Config, project_name: str = "test-project"):
        """Initialize the test.

        Args:
            config: Configuration instance
            project_name: Name of project to create
        """
        super().__init__(config)
        self.project_name = project_name

    def get_adw_name(self) -> str:
        """Get the ADW script name.

        Returns:
            ADW script name
        """
        return "adw_init.py"

    def get_adw_args(self) -> List[str]:
        """Get arguments for the ADW script.

        Returns:
            List of arguments
        """
        return [self.project_name]

    def get_specific_checks(self) -> List[BaseCheck]:
        """Get ADW-init specific checks.

        These are checks specific to the adw_init workflow beyond
        the standard ADW checks and project-init checks.

        Returns:
            List of check instances
        """
        checks = []

        # Additional checks specific to adw_init
        # (Currently adw_init just wraps project-init, so project-init checks cover it)
        # Future: Add checks for ADW-specific features like progress indicators, etc.

        return checks

    def setup_adw_workspace(self, workspace: Path):
        """Set up workspace for adw_init execution.

        Args:
            workspace: Path to workspace directory
        """
        # adw_init should work in an empty directory
        # No special setup needed
        pass

    def validate_project_outcome(self, workspace: Path) -> bool:
        """Validate the final project state.

        Args:
            workspace: Path to workspace directory

        Returns:
            True if project is valid
        """
        # Check workspace exists
        if not workspace.exists():
            return False

        # Check key project files exist
        readme = workspace / "README.md"
        git_dir = workspace / ".git"

        if not readme.exists():
            return False

        if not git_dir.exists():
            return False

        return True


def run_adw_init_test(config_path: str = None):
    """Run the adw_init test.

    Args:
        config_path: Optional path to configuration file

    Returns:
        List of run IDs
    """
    # Load configuration
    config = Config(config_path)

    # Validate configuration
    errors = config.validate()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        return []

    # Initialize runner
    runner = TestRunner(config)

    # Get checks - we'll populate these after ADW execution
    # For now, use project-init checks as baseline
    checks = get_project_init_checks()

    print("Running adw-init test...")
    # Note: This will be integrated with the runner in the next step
    # For now, this is a placeholder showing the intended usage

    run_ids = []
    # TODO: Integrate with TestRunner to execute ADW tests

    return run_ids


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run adw_init test")
    parser.add_argument(
        "--config",
        help="Path to configuration file",
        default="config.yaml"
    )
    parser.add_argument(
        "--model",
        help="Specific model to test (sonnet or haiku)",
        choices=["sonnet", "haiku"],
        default="sonnet"
    )
    parser.add_argument(
        "--project-name",
        help="Name of project to create",
        default="test-project"
    )
    parser.add_argument(
        "--dry-run",
        help="Run in dry-run mode",
        action="store_true"
    )

    args = parser.parse_args()

    # Run test standalone
    try:
        print(f"Testing adw_init.py with model: {args.model}")
        print(f"Project name: {args.project_name}")
        if args.dry_run:
            print("Running in DRY-RUN mode")
        print("")

        # Create test instance
        config = Config(args.config)

        # Create test
        test = AdwInitTest(config, project_name=args.project_name)

        # Run standalone
        result = run_adw_test_standalone(
            AdwInitTest,
            config_path=args.config,
            model=args.model,
            dry_run=args.dry_run
        )

        if result and result.success:
            print("\n✓ ADW test passed!")
            sys.exit(0)
        else:
            print("\n✗ ADW test failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error running test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
