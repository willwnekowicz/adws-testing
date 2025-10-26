"""Test case for the /init-cloudflare slash command."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import Config
from src.core.runner import TestRunner
from src.checks.simple import (
    FileExistsCheck,
    FileContentCheck,
    GitBranchCheck,
    DurationCheck
)
from src.checks.base import CompositeCheck


def get_init_cloudflare_checks():
    """Get checks for init-cloudflare test.

    Returns:
        List of check instances
    """
    checks = []

    # ========================================
    # Section 1: File Existence Checks (1-12)
    # ========================================

    # Check 1: Worker exists
    checks.append(FileExistsCheck(
        name="worker_exists",
        file_path="apps/server/worker/index.js"
    ))

    # Check 2: Wrangler production config exists
    checks.append(FileExistsCheck(
        name="wrangler_prod_exists",
        file_path="apps/server/wrangler.toml"
    ))

    # Check 3: Wrangler development config exists
    checks.append(FileExistsCheck(
        name="wrangler_dev_exists",
        file_path="apps/server/wrangler-dev.toml"
    ))

    # Check 4: Package.json exists
    checks.append(FileExistsCheck(
        name="package_json_exists",
        file_path="apps/server/package.json"
    ))

    # Check 5: Initial migration exists
    checks.append(FileExistsCheck(
        name="migration_exists",
        file_path="apps/server/migrations/0001_initial_setup.sql"
    ))

    # Check 6: Seed file exists
    checks.append(FileExistsCheck(
        name="seed_exists",
        file_path="apps/server/seeds/example-seed.sql"
    ))

    # Check 7: API example exists
    checks.append(FileExistsCheck(
        name="api_example_exists",
        file_path="apps/server/api/example.js"
    ))

    # Check 8: Durable Object example exists
    checks.append(FileExistsCheck(
        name="durable_object_exists",
        file_path="apps/server/durable-objects/example-counter.js"
    ))

    # Check 9: GitHub workflow staging exists
    checks.append(FileExistsCheck(
        name="gh_workflow_staging_exists",
        file_path=".github/workflows/deploy-staging.yml"
    ))

    # Check 10: GitHub workflow production exists
    checks.append(FileExistsCheck(
        name="gh_workflow_prod_exists",
        file_path=".github/workflows/deploy-production.yml"
    ))

    # Check 11: Setup guide exists
    checks.append(FileExistsCheck(
        name="setup_guide_exists",
        file_path="apps/server/CLOUDFLARE_SETUP.md"
    ))

    # Check 12: Server README exists
    checks.append(FileExistsCheck(
        name="server_readme_exists",
        file_path="apps/server/README.md"
    ))

    # ========================================
    # Section 2: Worker Code Validation (13-17)
    # ========================================

    # Check 13: Worker has security features
    checks.append(FileContentCheck(
        name="worker_has_security",
        file_path="apps/server/worker/index.js",
        contains=["shouldBlockPath", "blockedPatterns", ".env", ".git"],
        not_contains=[]
    ))

    # Check 14: Worker has CORS handling
    checks.append(FileContentCheck(
        name="worker_has_cors",
        file_path="apps/server/worker/index.js",
        contains=["handleOptions", "Access-Control-Allow-Origin"],
        not_contains=[]
    ))

    # Check 15: Worker has request ID tracking
    checks.append(FileContentCheck(
        name="worker_has_request_id",
        file_path="apps/server/worker/index.js",
        contains=["generateRequestId", "X-Request-Id", "crypto.randomUUID"],
        not_contains=[]
    ))

    # Check 16: Worker has API routing
    checks.append(FileContentCheck(
        name="worker_has_api_routing",
        file_path="apps/server/worker/index.js",
        contains=["handleApiRequest", "/api/", "env.DB"],
        not_contains=[]
    ))

    # Check 17: Worker serves static assets
    checks.append(FileContentCheck(
        name="worker_has_static_assets",
        file_path="apps/server/worker/index.js",
        contains=["getAssetFromKV", "handleStaticAsset"],
        not_contains=[]
    ))

    # ========================================
    # Section 3: Configuration Validation (18-21)
    # ========================================

    # Check 18: Production wrangler configured
    checks.append(FileContentCheck(
        name="wrangler_prod_configured",
        file_path="apps/server/wrangler.toml",
        contains=["name =", "main =", "d1_databases", "database_id"],
        not_contains=[]
    ))

    # Check 19: Development wrangler configured
    checks.append(FileContentCheck(
        name="wrangler_dev_configured",
        file_path="apps/server/wrangler-dev.toml",
        contains=["name =", "main =", "d1_databases", "development-db"],
        not_contains=[]
    ))

    # Check 20: Package.json has required scripts
    checks.append(FileContentCheck(
        name="package_json_has_scripts",
        file_path="apps/server/package.json",
        contains=['"dev"', '"deploy:staging"', '"deploy:production"', '"migrate:dev"', '"migrate:prod"'],
        not_contains=[]
    ))

    # Check 21: Package.json has dependencies
    checks.append(FileContentCheck(
        name="package_json_has_dependencies",
        file_path="apps/server/package.json",
        contains=["@cloudflare/kv-asset-handler", "wrangler"],
        not_contains=[]
    ))

    # ========================================
    # Section 4: Database Schema Validation (22-25)
    # ========================================

    # Check 22: Migration creates tables
    checks.append(FileContentCheck(
        name="migration_has_tables",
        file_path="apps/server/migrations/0001_initial_setup.sql",
        contains=["CREATE TABLE", "example_table", "example_categories"],
        not_contains=[]
    ))

    # Check 23: Migration creates indexes
    checks.append(FileContentCheck(
        name="migration_has_indexes",
        file_path="apps/server/migrations/0001_initial_setup.sql",
        contains=["CREATE INDEX", "idx_example_status", "idx_example_created"],
        not_contains=[]
    ))

    # Check 24: Migration has foreign keys
    checks.append(FileContentCheck(
        name="migration_has_foreign_keys",
        file_path="apps/server/migrations/0001_initial_setup.sql",
        contains=["FOREIGN KEY", "REFERENCES", "ON DELETE CASCADE"],
        not_contains=[]
    ))

    # Check 25: Migration follows best practices
    checks.append(FileContentCheck(
        name="migration_best_practices",
        file_path="apps/server/migrations/0001_initial_setup.sql",
        contains=["IF NOT EXISTS", "created_at", "updated_at", "unixepoch()"],
        not_contains=[]
    ))

    # ========================================
    # Section 5: CI/CD Workflow Validation (26-30)
    # ========================================

    # Check 26: Staging workflow configured
    checks.append(FileContentCheck(
        name="staging_workflow_configured",
        file_path=".github/workflows/deploy-staging.yml",
        contains=["on:", "push:", "branches:", "staging", "wrangler deploy"],
        not_contains=[]
    ))

    # Check 27: Staging workflow has migrations
    checks.append(FileContentCheck(
        name="staging_workflow_has_migrations",
        file_path=".github/workflows/deploy-staging.yml",
        contains=["d1 migrations apply", "development-db"],
        not_contains=[]
    ))

    # Check 28: Staging workflow uses secrets
    checks.append(FileContentCheck(
        name="staging_workflow_has_secrets",
        file_path=".github/workflows/deploy-staging.yml",
        contains=["CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID"],
        not_contains=[]
    ))

    # Check 29: Production workflow configured
    checks.append(FileContentCheck(
        name="production_workflow_configured",
        file_path=".github/workflows/deploy-production.yml",
        contains=["on:", "push:", "branches:", "main", "wrangler deploy"],
        not_contains=[]
    ))

    # Check 30: Production workflow has migrations
    checks.append(FileContentCheck(
        name="production_workflow_has_migrations",
        file_path=".github/workflows/deploy-production.yml",
        contains=["d1 migrations apply", "production-db"],
        not_contains=[]
    ))

    # ========================================
    # Section 6: Documentation Validation (31-33)
    # ========================================

    # Check 31: Setup guide is comprehensive
    checks.append(FileContentCheck(
        name="setup_guide_complete",
        file_path="apps/server/CLOUDFLARE_SETUP.md",
        contains=["Prerequisites", "Wrangler", "D1 Databases", "Migrations", "GitHub Actions"],
        not_contains=[]
    ))

    # Check 32: Setup guide has required commands
    checks.append(FileContentCheck(
        name="setup_guide_has_commands",
        file_path="apps/server/CLOUDFLARE_SETUP.md",
        contains=["wrangler login", "d1 create", "wrangler deploy"],
        not_contains=[]
    ))

    # Check 33: Server README documents architecture
    checks.append(FileContentCheck(
        name="server_readme_has_architecture",
        file_path="apps/server/README.md",
        contains=["Architecture", "Worker", "D1", "Durable Objects"],
        not_contains=[]
    ))

    # ========================================
    # Section 7: Example Code Validation (34-35)
    # ========================================

    # Check 34: API example has CRUD operations
    checks.append(FileContentCheck(
        name="api_example_has_crud",
        file_path="apps/server/api/example.js",
        contains=["GET", "POST", "PUT", "DELETE"],
        not_contains=[]
    ))

    # Check 35: Durable Object example is valid
    checks.append(FileContentCheck(
        name="durable_object_example_valid",
        file_path="apps/server/durable-objects/example-counter.js",
        contains=["class", "fetch", "alarm"],
        not_contains=[]
    ))

    # ========================================
    # Section 8: Integration Checks (36-38)
    # ========================================

    # Check 36: Worker references API handlers
    checks.append(FileContentCheck(
        name="worker_references_api",
        file_path="apps/server/worker/index.js",
        contains=["api/", "handleApiRequest"],
        not_contains=[]
    ))

    # Check 37: Wrangler config matches worker location
    checks.append(FileContentCheck(
        name="wrangler_matches_worker",
        file_path="apps/server/wrangler.toml",
        contains=["main =", "worker/index.js"],
        not_contains=[]
    ))

    # Check 38: Package scripts use correct configs
    checks.append(FileContentCheck(
        name="package_scripts_match_configs",
        file_path="apps/server/package.json",
        contains=["wrangler", "deploy"],
        not_contains=[]
    ))

    # ========================================
    # Section 9: Git Integration (39-40)
    # ========================================

    # Check 39 & 40: Git branch check
    # Combined into a single check for the staging branch
    checks.append(GitBranchCheck(
        name="commit_on_staging",
        expected_branch="staging"
    ))

    # ========================================
    # Section 10: Composite Check (41)
    # ========================================

    # Check 41: Overall init-cloudflare completion
    init_cloudflare_complete = CompositeCheck(
        name="init_cloudflare_complete",
        checks=[
            FileExistsCheck("worker_check", "apps/server/worker/index.js"),
            FileExistsCheck("wrangler_check", "apps/server/wrangler.toml"),
            FileExistsCheck("migration_check", "apps/server/migrations/0001_initial_setup.sql"),
            FileExistsCheck("workflow_check", ".github/workflows/deploy-staging.yml"),
            FileExistsCheck("docs_check", "apps/server/CLOUDFLARE_SETUP.md"),
            GitBranchCheck("branch_check", "staging")
        ],
        require_all=True
    )
    checks.append(init_cloudflare_complete)

    # ========================================
    # Duration Check (with extended timeout)
    # ========================================

    # Extended timeout for init-cloudflare (10 minutes = 600 seconds)
    checks.append(DurationCheck(
        name="execution_time",
        max_duration=600  # 10 minutes max
    ))

    return checks


def run_init_cloudflare_test(config_path: str = None):
    """Run the init-cloudflare test.

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

    # Get checks
    checks = get_init_cloudflare_checks()

    # Run tests with both models
    print("Running init-cloudflare test...")
    run_ids = runner.run_multiple_tests(
        test_name="init-cloudflare",
        models=["sonnet", "haiku"],
        checks=checks
    )

    print(f"Completed test runs: {run_ids}")

    # Print results
    for run_id in run_ids:
        results = runner.get_run_results(run_id)
        if results:
            print(f"\nRun {run_id}:")
            print(f"  Model: {results['model']}")
            print(f"  Status: {results['status']}")

            for test_case in results['test_cases']:
                print(f"  Test: {test_case['name']}")
                for result in test_case['results']:
                    status = "✓" if result['passed'] else "✗"
                    print(f"    {status} {result['check_name']}")
                    if result['details'] and not result['passed']:
                        print(f"      Details: {result['details'][:100]}...")

    return run_ids


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run init-cloudflare test")
    parser.add_argument(
        "--config",
        help="Path to configuration file",
        default="config.yaml"
    )
    parser.add_argument(
        "--model",
        help="Specific model to test (sonnet or haiku)",
        choices=["sonnet", "haiku"],
        default=None
    )
    parser.add_argument(
        "--commit",
        help="Specific commit to test",
        default=None
    )
    parser.add_argument(
        "--branch",
        help="Specific branch to test",
        default=None
    )

    args = parser.parse_args()

    # Run test
    try:
        # Load configuration
        config = Config(args.config)

        # Initialize runner
        runner = TestRunner(config)

        # Get checks
        checks = get_init_cloudflare_checks()

        # Run test
        if args.model:
            # Run with specific model
            run_id = runner.run_test(
                test_name="init-cloudflare",
                model=args.model,
                commit=args.commit,
                branch=args.branch,
                checks=checks
            )
            print(f"Test run completed: {run_id}")

            # Show results
            results = runner.get_run_results(run_id)
            if results:
                print(f"\nResults for run {run_id}:")
                print(f"  Model: {results['model']}")
                print(f"  Status: {results['status']}")

                for test_case in results['test_cases']:
                    print(f"  Test: {test_case['name']}")
                    passed = 0
                    failed = 0
                    for result in test_case['results']:
                        if result['passed']:
                            passed += 1
                        else:
                            failed += 1
                        status = "✓" if result['passed'] else "✗"
                        print(f"    {status} {result['check_name']}")
                        if result['details'] and not result['passed']:
                            for line in result['details'].split('\n')[:3]:
                                if line.strip():
                                    print(f"      {line}")

                    print(f"  Summary: {passed} passed, {failed} failed")
        else:
            # Run with all models
            run_ids = runner.run_multiple_tests(
                test_name="init-cloudflare",
                commit=args.commit,
                branch=args.branch,
                checks=checks
            )
            print(f"Test runs completed: {run_ids}")

            # Show summary
            for run_id in run_ids:
                results = runner.get_run_results(run_id)
                if results:
                    print(f"\nRun {run_id} ({results['model']}): {results['status']}")

    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error running test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
