"""Test case for the adw_init.py ADW script.

This test validates that the adw_init ADW (AI Developer Workflow) correctly
orchestrates the /init-git and /init-structure slash commands to set up new projects.

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
from tests.test_init_git import get_init_git_checks


def get_adw_init_checks(adw_result=None, script_path=None):
    """Get checks for adw_init test.

    This validates the two-phase initialization workflow:
    - Phase 1: /init-git (git setup, README, branches)
    - Phase 2: /init-structure (directory structure, documentation)

    Args:
        adw_result: AdwResult instance from execution
        script_path: Path to the ADW script

    Returns:
        List of check instances
    """
    checks = []

    # ============================================================================
    # SECTION 1: ADW-specific checks
    # ============================================================================
    # These validate that the ADW script itself is valid and executed correctly

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

    # ============================================================================
    # SECTION 2: Init-git checks
    # ============================================================================
    # These validate that the ADW correctly executed /init-git
    # (git initialization, main README, branches, etc.)

    init_git_checks = get_init_git_checks()
    checks.extend(init_git_checks)

    # ============================================================================
    # SECTION 3: Directory structure checks
    # ============================================================================
    # These validate that /init-structure created all expected directories

    checks.append(DirectoryStructureCheck(
        name="directory_structure_created",
        required_dirs=[
            "documentation",
            "documentation/research",
            "documentation/brainstorming",
            "documentation/specs",
            "documentation/implementations",
            "scripts",
            "apps",
            "apps/client",
            "apps/server"
        ]
    ))

    # ============================================================================
    # SECTION 4: README file checks
    # ============================================================================
    # These validate that README files exist in key directories

    checks.append(FileExistsCheck(
        name="documentation_readme_exists",
        file_path="documentation/README.md"
    ))

    checks.append(FileExistsCheck(
        name="scripts_readme_exists",
        file_path="scripts/README.md"
    ))

    checks.append(FileExistsCheck(
        name="apps_readme_exists",
        file_path="apps/README.md"
    ))

    # ============================================================================
    # SECTION 5: Integration checks
    # ============================================================================
    # These validate that /init-structure properly integrated with /init-git
    # by updating the main README to document the new structure

    checks.append(FileContentCheck(
        name="main_readme_documents_structure",
        file_path="README.md",
        contains=[
            "Project Structure",
            "documentation/",
            "scripts/",
            "apps/"
        ]
    ))

    return checks


class AdwInitTest(BaseAdwTest):
    """Test class for adw_init.py workflow.

    This test validates the two-phase initialization workflow:
    - Phase 1: /init-git (git initialization, README, branches)
    - Phase 2: /init-structure (directory structure, README files)

    The test ensures both phases execute successfully and integrate properly.
    """

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
        the standard ADW checks and init-git checks.

        Note: The main validation checks (including directory structure,
        README files, and integration checks) are defined in the
        get_adw_init_checks() function for reusability.

        Returns:
            List of check instances
        """
        checks = []

        # Additional checks specific to adw_init
        # The main checks are in get_adw_init_checks() which includes:
        # - Directory structure validation (9 directories)
        # - README file existence checks (documentation, scripts, apps)
        # - Integration checks (main README documents structure)

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

        This provides early validation before detailed checks run.
        Validates both /init-git and /init-structure outcomes.

        Args:
            workspace: Path to workspace directory

        Returns:
            True if project is valid
        """
        # Check workspace exists
        if not workspace.exists():
            print("✗ Workspace does not exist")
            return False

        # Check key project files exist (from /init-git)
        readme = workspace / "README.md"
        git_dir = workspace / ".git"

        if not readme.exists():
            print("✗ Main README.md does not exist")
            return False

        if not git_dir.exists():
            print("✗ Git directory does not exist")
            return False

        # Check critical directory structure (from /init-structure)
        critical_dirs = ["documentation", "scripts", "apps"]
        for dir_name in critical_dirs:
            dir_path = workspace / dir_name
            if not dir_path.exists():
                print(f"✗ Critical directory missing: {dir_name}/")
                return False
            if not dir_path.is_dir():
                print(f"✗ Expected directory but found file: {dir_name}")
                return False

        print("✓ Basic project structure validation passed")
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
    # For now, use init-git checks as baseline
    checks = get_init_git_checks()

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
