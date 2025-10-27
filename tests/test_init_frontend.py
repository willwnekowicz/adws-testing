"""Test case for the /init-frontend slash command."""

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


def get_init_frontend_checks():
    """Get checks for init-frontend test.

    Returns:
        List of check instances
    """
    checks = []

    # ========================================
    # Section 1: File Existence Checks (1-27)
    # ========================================

    # Configuration Files
    checks.append(FileExistsCheck(
        name="package_json_exists",
        file_path="apps/client/package.json"
    ))

    checks.append(FileExistsCheck(
        name="next_config_exists",
        file_path="apps/client/next.config.js"
    ))

    checks.append(FileExistsCheck(
        name="tsconfig_exists",
        file_path="apps/client/tsconfig.json"
    ))

    checks.append(FileExistsCheck(
        name="tailwind_config_exists",
        file_path="apps/client/tailwind.config.js"
    ))

    checks.append(FileExistsCheck(
        name="postcss_config_exists",
        file_path="apps/client/postcss.config.js"
    ))

    # ESLint and Prettier
    checks.append(FileExistsCheck(
        name="eslintrc_exists",
        file_path="apps/client/.eslintrc.json"
    ))

    checks.append(FileExistsCheck(
        name="prettierrc_exists",
        file_path="apps/client/.prettierrc"
    ))

    checks.append(FileExistsCheck(
        name="prettierignore_exists",
        file_path="apps/client/.prettierignore"
    ))

    # Testing
    checks.append(FileExistsCheck(
        name="jest_config_exists",
        file_path="apps/client/jest.config.js"
    ))

    checks.append(FileExistsCheck(
        name="jest_setup_exists",
        file_path="apps/client/jest.setup.js"
    ))

    # App Directory Files
    checks.append(FileExistsCheck(
        name="globals_css_exists",
        file_path="apps/client/app/globals.css"
    ))

    checks.append(FileExistsCheck(
        name="layout_exists",
        file_path="apps/client/app/layout.tsx"
    ))

    checks.append(FileExistsCheck(
        name="page_exists",
        file_path="apps/client/app/page.tsx"
    ))

    checks.append(FileExistsCheck(
        name="about_page_exists",
        file_path="apps/client/app/about/page.tsx"
    ))

    # Source Directory Files
    checks.append(FileExistsCheck(
        name="button_component_exists",
        file_path="apps/client/src/components/Button.tsx"
    ))

    checks.append(FileExistsCheck(
        name="use_local_storage_hook_exists",
        file_path="apps/client/src/hooks/useLocalStorage.ts"
    ))

    checks.append(FileExistsCheck(
        name="cn_util_exists",
        file_path="apps/client/src/utils/cn.ts"
    ))

    checks.append(FileExistsCheck(
        name="types_index_exists",
        file_path="apps/client/src/types/index.ts"
    ))

    # Test Files
    checks.append(FileExistsCheck(
        name="button_test_exists",
        file_path="apps/client/src/components/__tests__/Button.test.tsx"
    ))

    # API Routes
    checks.append(FileExistsCheck(
        name="health_route_exists",
        file_path="apps/client/app/api/health/route.ts"
    ))

    # Middleware
    checks.append(FileExistsCheck(
        name="middleware_exists",
        file_path="apps/client/middleware.ts"
    ))

    # Environment Files
    checks.append(FileExistsCheck(
        name="env_example_exists",
        file_path="apps/client/.env.example"
    ))

    checks.append(FileExistsCheck(
        name="env_local_exists",
        file_path="apps/client/.env.local"
    ))

    # Documentation
    checks.append(FileExistsCheck(
        name="client_readme_exists",
        file_path="apps/client/README.md"
    ))

    # Gitignore (either root or client-specific)
    checks.append(FileExistsCheck(
        name="gitignore_exists",
        file_path="apps/client/.gitignore"
    ))

    # ========================================
    # Section 2: Configuration Validation (26-37)
    # ========================================

    # Package.json dependencies
    checks.append(FileContentCheck(
        name="package_json_has_dependencies",
        file_path="apps/client/package.json",
        contains=['"next"', '"react"', '"react-dom"', '"clsx"', '"tailwind-merge"'],
        not_contains=[]
    ))

    checks.append(FileContentCheck(
        name="package_json_has_dev_dependencies",
        file_path="apps/client/package.json",
        contains=['"typescript"', '"eslint"', '"prettier"', '"jest"', '"tailwindcss"', '"autoprefixer"', '"postcss"'],
        not_contains=[]
    ))

    checks.append(FileContentCheck(
        name="package_json_has_scripts",
        file_path="apps/client/package.json",
        contains=['"dev"', '"build"', '"start"', '"lint"', '"type-check"', '"test"', '"format"'],
        not_contains=[]
    ))

    checks.append(FileContentCheck(
        name="package_json_has_engines",
        file_path="apps/client/package.json",
        contains=['"engines"', '"node"', '"bun"'],
        not_contains=[]
    ))

    # Next.js configuration
    checks.append(FileContentCheck(
        name="next_config_has_output",
        file_path="apps/client/next.config.js",
        contains=["output: 'export'", "distDir: 'dist'"],
        not_contains=[]
    ))

    checks.append(FileContentCheck(
        name="next_config_has_settings",
        file_path="apps/client/next.config.js",
        contains=["reactStrictMode", "swcMinify"],
        not_contains=[]
    ))

    # TypeScript configuration
    checks.append(FileContentCheck(
        name="tsconfig_has_strict",
        file_path="apps/client/tsconfig.json",
        contains=['"strict": true'],
        not_contains=[]
    ))

    checks.append(FileContentCheck(
        name="tsconfig_has_target",
        file_path="apps/client/tsconfig.json",
        contains=['"target": "ES2020"'],
        not_contains=[]
    ))

    checks.append(FileContentCheck(
        name="tsconfig_has_module_settings",
        file_path="apps/client/tsconfig.json",
        contains=['"module": "esnext"', '"moduleResolution": "bundler"'],
        not_contains=[]
    ))

    checks.append(FileContentCheck(
        name="tsconfig_has_path_mappings",
        file_path="apps/client/tsconfig.json",
        contains=['"@/*": ["./src/*"]', '"@/components/*": ["./src/components/*"]', '"@/hooks/*": ["./src/hooks/*"]'],
        not_contains=[]
    ))

    # TailwindCSS configuration
    checks.append(FileContentCheck(
        name="tailwind_has_content_paths",
        file_path="apps/client/tailwind.config.js",
        contains=["'./app/**/*.{js,ts,jsx,tsx,mdx}'", "'./src/**/*.{js,ts,jsx,tsx,mdx}'"],
        not_contains=[]
    ))

    # PostCSS configuration
    checks.append(FileContentCheck(
        name="postcss_has_plugins",
        file_path="apps/client/postcss.config.js",
        contains=["tailwindcss", "autoprefixer"],
        not_contains=[]
    ))

    # ========================================
    # Section 3: Source Code Validation (38-47)
    # ========================================

    # Button component
    checks.append(FileContentCheck(
        name="button_uses_clsx_and_twmerge",
        file_path="apps/client/src/components/Button.tsx",
        contains=["import { clsx }", "import { twMerge }", "twMerge(clsx("],
        not_contains=[]
    ))

    checks.append(FileContentCheck(
        name="button_has_variant_props",
        file_path="apps/client/src/components/Button.tsx",
        contains=["variant?: 'primary' | 'secondary' | 'outline' | 'ghost'"],
        not_contains=[]
    ))

    checks.append(FileContentCheck(
        name="button_has_size_props",
        file_path="apps/client/src/components/Button.tsx",
        contains=["size?: 'sm' | 'md' | 'lg'"],
        not_contains=[]
    ))

    checks.append(FileContentCheck(
        name="button_has_loading_prop",
        file_path="apps/client/src/components/Button.tsx",
        contains=["isLoading?:", "isLoading"],
        not_contains=[]
    ))

    # useLocalStorage hook
    checks.append(FileContentCheck(
        name="use_local_storage_hook_valid",
        file_path="apps/client/src/hooks/useLocalStorage.ts",
        contains=["useState", "window.localStorage", "getItem", "setItem"],
        not_contains=[]
    ))

    # cn utility
    checks.append(FileContentCheck(
        name="cn_util_valid",
        file_path="apps/client/src/utils/cn.ts",
        contains=["clsx", "twMerge", "export function cn"],
        not_contains=[]
    ))

    # Types
    checks.append(FileContentCheck(
        name="types_has_user_interface",
        file_path="apps/client/src/types/index.ts",
        contains=["export interface User", "id:", "email:", "name:"],
        not_contains=[]
    ))

    checks.append(FileContentCheck(
        name="types_has_api_response",
        file_path="apps/client/src/types/index.ts",
        contains=["export interface ApiResponse", "data?:", "error?:", "status:"],
        not_contains=[]
    ))

    checks.append(FileContentCheck(
        name="types_has_paginated_response",
        file_path="apps/client/src/types/index.ts",
        contains=["export interface PaginatedResponse", "items:", "total:", "page:"],
        not_contains=[]
    ))

    # ========================================
    # Section 4: Testing Configuration (48-52)
    # ========================================

    # Jest configuration
    checks.append(FileContentCheck(
        name="jest_uses_next_jest",
        file_path="apps/client/jest.config.js",
        contains=["require('next/jest')", "createJestConfig"],
        not_contains=[]
    ))

    checks.append(FileContentCheck(
        name="jest_has_module_mapper",
        file_path="apps/client/jest.config.js",
        contains=["moduleNameMapper", "'^@/(.*)$'", "'<rootDir>/src/$1'"],
        not_contains=[]
    ))

    checks.append(FileContentCheck(
        name="jest_has_test_environment",
        file_path="apps/client/jest.config.js",
        contains=["testEnvironment: 'jest-environment-jsdom'"],
        not_contains=[]
    ))

    # Jest setup
    checks.append(FileContentCheck(
        name="jest_setup_imports_dom",
        file_path="apps/client/jest.setup.js",
        contains=["@testing-library/jest-dom"],
        not_contains=[]
    ))

    # Button test
    checks.append(FileContentCheck(
        name="button_test_has_cases",
        file_path="apps/client/src/components/__tests__/Button.test.tsx",
        contains=["render", "screen", "fireEvent", "describe", "it", "expect"],
        not_contains=[]
    ))

    # ========================================
    # Section 5: Styling Validation (53-55)
    # ========================================

    # Global CSS
    checks.append(FileContentCheck(
        name="globals_has_tailwind_directives",
        file_path="apps/client/app/globals.css",
        contains=["@tailwind base", "@tailwind components", "@tailwind utilities"],
        not_contains=[]
    ))

    checks.append(FileContentCheck(
        name="globals_has_css_variables",
        file_path="apps/client/app/globals.css",
        contains=[":root", "--foreground-rgb", "--background-start-rgb"],
        not_contains=[]
    ))

    checks.append(FileContentCheck(
        name="globals_has_custom_components",
        file_path="apps/client/app/globals.css",
        contains=["@layer components", ".btn-primary", ".card"],
        not_contains=[]
    ))

    # ========================================
    # Section 6: App Structure Validation (56-60)
    # ========================================

    # Layout
    checks.append(FileContentCheck(
        name="layout_imports_globals",
        file_path="apps/client/app/layout.tsx",
        contains=["import './globals.css'", "import { Inter }", "export const metadata"],
        not_contains=[]
    ))

    # Home page
    checks.append(FileContentCheck(
        name="page_has_welcome_content",
        file_path="apps/client/app/page.tsx",
        contains=["Welcome to Your App", "grid", "card"],
        not_contains=[]
    ))

    # About page
    checks.append(FileContentCheck(
        name="about_has_tech_stack",
        file_path="apps/client/app/about/page.tsx",
        contains=["Technology Stack", "Next.js", "React", "TypeScript", "TailwindCSS"],
        not_contains=[]
    ))

    # API health route
    checks.append(FileContentCheck(
        name="health_route_valid",
        file_path="apps/client/app/api/health/route.ts",
        contains=["NextResponse", "export async function GET", "status", "timestamp", "environment"],
        not_contains=[]
    ))

    # ========================================
    # Section 7: Development Tools (61-63)
    # ========================================

    # ESLint
    checks.append(FileContentCheck(
        name="eslint_extends_next",
        file_path="apps/client/.eslintrc.json",
        contains=['"next/core-web-vitals"', '"@typescript-eslint/recommended"'],
        not_contains=[]
    ))

    # Prettier
    checks.append(FileContentCheck(
        name="prettier_has_config",
        file_path="apps/client/.prettierrc",
        contains=['"semi"', '"singleQuote"', '"printWidth"'],
        not_contains=[]
    ))

    # Middleware
    checks.append(FileContentCheck(
        name="middleware_has_security_headers",
        file_path="apps/client/middleware.ts",
        contains=["X-Frame-Options", "X-Content-Type-Options", "X-Request-Id"],
        not_contains=[]
    ))

    # ========================================
    # Section 8: Documentation Validation (64-68)
    # ========================================

    # README sections
    checks.append(FileContentCheck(
        name="readme_has_tech_stack_section",
        file_path="apps/client/README.md",
        contains=["## Technology Stack", "Next.js", "React", "TypeScript", "TailwindCSS"],
        not_contains=[]
    ))

    checks.append(FileContentCheck(
        name="readme_has_getting_started",
        file_path="apps/client/README.md",
        contains=["## Getting Started", "Prerequisites", "Installation"],
        not_contains=[]
    ))

    checks.append(FileContentCheck(
        name="readme_has_scripts_section",
        file_path="apps/client/README.md",
        contains=["## Available Scripts", "bun run dev", "bun run build", "bun run test"],
        not_contains=[]
    ))

    checks.append(FileContentCheck(
        name="readme_has_project_structure",
        file_path="apps/client/README.md",
        contains=["## Project Structure", "app/", "src/"],
        not_contains=[]
    ))

    checks.append(FileContentCheck(
        name="readme_has_env_vars_section",
        file_path="apps/client/README.md",
        contains=["## Environment Variables", "NEXT_PUBLIC_API_URL"],
        not_contains=[]
    ))

    # ========================================
    # Section 9: Git Integration (69)
    # ========================================

    # Git branch check
    checks.append(GitBranchCheck(
        name="commit_on_staging",
        expected_branch="staging"
    ))

    # ========================================
    # Section 10: Composite Check (70)
    # ========================================

    # Overall init-frontend completion check
    init_frontend_complete = CompositeCheck(
        name="init_frontend_complete",
        checks=[
            FileExistsCheck("package_check", "apps/client/package.json"),
            FileExistsCheck("next_check", "apps/client/next.config.js"),
            FileExistsCheck("tsconfig_check", "apps/client/tsconfig.json"),
            FileExistsCheck("tailwind_check", "apps/client/tailwind.config.js"),
            FileExistsCheck("button_check", "apps/client/src/components/Button.tsx"),
            FileExistsCheck("layout_check", "apps/client/app/layout.tsx"),
            FileExistsCheck("readme_check", "apps/client/README.md"),
            GitBranchCheck("branch_check", "staging")
        ],
        require_all=True
    )
    checks.append(init_frontend_complete)

    # ========================================
    # Duration Check
    # ========================================

    # Extended timeout for init-frontend (10 minutes = 600 seconds)
    checks.append(DurationCheck(
        name="execution_time",
        max_duration=600  # 10 minutes max
    ))

    return checks


def run_init_frontend_test(config_path: str = None):
    """Run the init-frontend test.

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
    checks = get_init_frontend_checks()

    # Run tests with both models
    print("Running init-frontend test...")
    run_ids = runner.run_multiple_tests(
        test_name="init-frontend",
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

    parser = argparse.ArgumentParser(description="Run init-frontend test")
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
        checks = get_init_frontend_checks()

        # Run test
        if args.model:
            # Run with specific model
            run_id = runner.run_test(
                test_name="init-frontend",
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
                test_name="init-frontend",
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
