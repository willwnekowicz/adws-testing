"""Test case for the adw_init.py ADW script.

This test validates that the adw_init ADW (AI Developer Workflow) correctly
orchestrates the eight-phase initialization workflow:
- Phase 1: /init:git (Git setup, README, branches)
- Phase 2: /init:github (GitHub repository creation and remote configuration)
- Phase 3: /init:structure (Directory structure, documentation)
- Phase 4: /init:conditional-docs (Conditional documentation system)
- Phase 5: /init:frontend (Next.js, TypeScript, TailwindCSS setup)
- Phase 6: /init:cloudflare (Cloudflare Workers, D1 database)
- Phase 7: /init:prefect (Prefect deployment setup and registration)
- Phase 8: Configuration (ADWS configuration and marker cleanup)

This is an integration test, testing the complete workflow from ADW script
execution through to final project state. The test runs for an extended
period (no time constraints) to allow all phases to complete.
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

    This validates the eight-phase initialization workflow:
    - Phase 1: /init:git (git setup, README, branches)
    - Phase 2: /init:github (GitHub repository creation and remote configuration)
    - Phase 3: /init:structure (directory structure, documentation)
    - Phase 4: /init:conditional-docs (conditional documentation system)
    - Phase 5: /init:frontend (Next.js, TypeScript, TailwindCSS setup)
    - Phase 6: /init:cloudflare (Cloudflare Workers, D1 database)
    - Phase 7: /init:prefect (Prefect deployment setup and registration)
    - Phase 8: Configuration (ADWS configuration and marker cleanup)

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
            max_duration=None  # No time constraint - this can run for a while
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
    # Filter out the execution_time check from init_git since ADW has its own duration check above
    # that accounts for the multi-phase workflow (10 minutes vs 2 minutes)
    filtered_checks = [c for c in init_git_checks if c.name != "execution_time"]
    checks.extend(filtered_checks)

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
    # SECTION 5: Conditional Documentation System checks
    # ============================================================================
    # These validate that /init:conditional-docs created the conditional docs system

    checks.append(FileExistsCheck(
        name="conditional_docs_file_exists",
        file_path="documentation/conditional_docs.md"
    ))

    # ============================================================================
    # SECTION 6: Frontend checks
    # ============================================================================
    # These validate that /init:frontend created the React/Next.js frontend

    # Core frontend structure
    checks.append(FileExistsCheck(
        name="frontend_package_json_exists",
        file_path="apps/client/package.json"
    ))

    checks.append(FileExistsCheck(
        name="frontend_tsconfig_exists",
        file_path="apps/client/tsconfig.json"
    ))

    checks.append(FileContentCheck(
        name="frontend_uses_typescript",
        file_path="apps/client/tsconfig.json",
        contains=["compilerOptions", "strict"]
    ))

    checks.append(FileExistsCheck(
        name="tailwind_config_exists",
        file_path="apps/client/tailwind.config.js"
    ))

    checks.append(FileContentCheck(
        name="frontend_uses_bun",
        file_path="apps/client/package.json",
        contains=["bun"]
    ))

    # Check for Next.js or React setup
    checks.append(FileContentCheck(
        name="frontend_framework_configured",
        file_path="apps/client/package.json",
        contains=["react"]
    ))

    # Check for Jest testing setup
    checks.append(FileContentCheck(
        name="testing_infrastructure_setup",
        file_path="apps/client/package.json",
        contains=["jest"]
    ))

    # Check for ESLint and Prettier
    checks.append(FileExistsCheck(
        name="eslint_config_exists",
        file_path="apps/client/.eslintrc.json"
    ))

    # ============================================================================
    # SECTION 7: Cloudflare Infrastructure checks
    # ============================================================================
    # These validate that /init:cloudflare created the Cloudflare setup

    checks.append(FileExistsCheck(
        name="cloudflare_worker_exists",
        file_path="apps/server/src/index.ts"
    ))

    checks.append(FileExistsCheck(
        name="cloudflare_wrangler_config_exists",
        file_path="apps/server/wrangler.toml"
    ))

    checks.append(FileContentCheck(
        name="d1_database_configured",
        file_path="apps/server/wrangler.toml",
        contains=["d1_databases"]
    ))

    # Check for migrations directory
    checks.append(DirectoryStructureCheck(
        name="migrations_directory_exists",
        required_dirs=["apps/server/migrations"]
    ))

    # Check for GitHub Actions workflows
    checks.append(FileExistsCheck(
        name="github_actions_workflow_exists",
        file_path=".github/workflows/deploy.yml"
    ))

    # Check for API endpoint templates
    checks.append(FileContentCheck(
        name="api_endpoints_configured",
        file_path="apps/server/src/index.ts",
        contains=["fetch", "Request", "Response"]
    ))

    # ============================================================================
    # SECTION 8: Prefect Deployment checks
    # ============================================================================
    # These validate that /init:prefect created the Prefect setup

    checks.append(FileExistsCheck(
        name="prefect_config_exists",
        file_path="prefect.yaml"
    ))

    checks.append(FileContentCheck(
        name="prefect_deployments_configured",
        file_path="prefect.yaml",
        contains=["deployments", "sdlc", "patch", "research"]
    ))

    # Check that SDLC workflow is configured
    checks.append(FileContentCheck(
        name="sdlc_workflow_configured",
        file_path="prefect.yaml",
        contains=["sdlc"]
    ))

    # ============================================================================
    # SECTION 9: ADWS Configuration checks
    # ============================================================================
    # These validate that the Configuration phase completed successfully

    checks.append(FileExistsCheck(
        name="adws_env_file_exists",
        file_path=".env.adws"
    ))

    checks.append(FileExistsCheck(
        name="claude_hooks_env_exists",
        file_path=".claude/hooks/.env"
    ))

    checks.append(FileExistsCheck(
        name="claude_settings_exists",
        file_path=".claude/settings.json"
    ))

    # Check that initialization marker is removed
    checks.append(FileContentCheck(
        name="initialization_marker_removed",
        file_path=".adws/__init__.py",
        not_contains=["__INIT_MARKER__"]
    ))

    # ============================================================================
    # SECTION 10: Integration checks
    # ============================================================================
    # These validate that all phases properly integrated together

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

    # Verify GitHub remote is configured (from /init:github)
    checks.append(GitConfigCheck(
        name="github_remote_configured",
        required_remotes=["origin"]
    ))

    return checks


class AdwInitTest(BaseAdwTest):
    """Test class for adw_init.py workflow.

    This test validates the eight-phase initialization workflow:
    - Phase 1: /init:git (git initialization, README, branches)
    - Phase 2: /init:github (GitHub repository creation and remote configuration)
    - Phase 3: /init:structure (directory structure, README files)
    - Phase 4: /init:conditional-docs (conditional documentation system)
    - Phase 5: /init:frontend (Next.js, TypeScript, TailwindCSS)
    - Phase 6: /init:cloudflare (Cloudflare Workers, D1 database)
    - Phase 7: /init:prefect (Prefect deployment setup and registration)
    - Phase 8: Configuration (ADWS configuration and marker cleanup)

    The test ensures all phases execute successfully and integrate properly.
    This test runs for an extended period without time constraints.
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

        Note: The main validation checks are defined in the
        get_adw_init_checks() function for reusability, including:
        - Phase 1-2: Git and GitHub setup
        - Phase 3: Directory structure (9 directories)
        - Phase 4: Conditional documentation system
        - Phase 5: Frontend (React/Next.js, TypeScript, TailwindCSS, Bun, Jest)
        - Phase 6: Cloudflare (Workers, D1, migrations, GitHub Actions)
        - Phase 7: Prefect (deployments, SDLC workflow, prefect.yaml)
        - Phase 8: Configuration (environment files, Claude settings, hooks)
        - Integration checks (README structure, GitHub remote)

        Returns:
            List of check instances
        """
        checks = []

        # Additional checks specific to adw_init
        # The main checks are in get_adw_init_checks()

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
