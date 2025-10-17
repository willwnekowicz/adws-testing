#!/usr/bin/env python3
"""Command-line interface for ADWS Testing framework."""

import sys
import json
from pathlib import Path
import click
from tabulate import tabulate

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config import Config
from src.core.runner import TestRunner
from src.core.build_manager import BuildManager
from tests.test_project_init import get_project_init_checks


@click.group()
@click.option('--config', default='config.yaml', help='Path to configuration file')
@click.pass_context
def cli(ctx, config):
    """ADWS Testing Framework - Test harness for standard-configuration."""
    ctx.ensure_object(dict)
    ctx.obj['config'] = Config(config)

    # Validate configuration
    errors = ctx.obj['config'].validate()
    if errors:
        click.echo(click.style("Configuration errors:", fg='red'))
        for error in errors:
            click.echo(f"  • {error}")
        ctx.exit(1)


@cli.command()
@click.argument('test_name', type=click.Choice(['project-init', 'all']))
@click.option('--model', type=click.Choice(['sonnet', 'haiku']), help='Specific model to test')
@click.option('--models', help='Comma-separated list of models to test')
@click.option('--commit', help='Specific commit to test')
@click.option('--branch', help='Specific branch to test')
@click.option('--build/--no-build', default=None, help='Build before testing (default: auto-detect)')
@click.option('--json', 'output_json', is_flag=True, help='Output results as JSON')
@click.pass_context
def test(ctx, test_name, model, models, commit, branch, build, output_json):
    """Run a test case."""
    config = ctx.obj['config']
    runner = TestRunner(config)

    # Determine which models to use
    if model:
        models_to_test = [model]
    elif models:
        models_to_test = models.split(',')
    else:
        models_to_test = list(config.claude.models.keys())

    # Get checks based on test name
    if test_name == 'project-init':
        checks = get_project_init_checks()
    elif test_name == 'all':
        # Run all tests
        click.echo("Running all tests...")
        checks = get_project_init_checks()  # Add more as implemented
    else:
        click.echo(f"Unknown test: {test_name}")
        ctx.exit(1)

    # Run tests
    click.echo(f"Running test: {test_name}")
    click.echo(f"Models: {', '.join(models_to_test)}")
    if commit:
        click.echo(f"Commit: {commit}")
    if branch:
        click.echo(f"Branch: {branch}")
    click.echo("")

    run_ids = []
    for model_name in models_to_test:
        click.echo(f"Testing with {model_name}...")
        try:
            run_id = runner.run_test(
                test_name=test_name if test_name != 'all' else 'project-init',
                model=model_name,
                commit=commit,
                branch=branch,
                checks=checks,
                build=build
            )
            run_ids.append(run_id)

            # Get results
            results = runner.get_run_results(run_id)
            if results:
                if output_json:
                    click.echo(json.dumps(results, indent=2))
                else:
                    _display_results(results)
        except Exception as e:
            click.echo(click.style(f"Error: {e}", fg='red'))
            import traceback
            traceback.print_exc()

    # Summary
    if not output_json:
        click.echo("\n" + "="*60)
        click.echo(f"Completed {len(run_ids)} test run(s)")
        for run_id in run_ids:
            results = runner.get_run_results(run_id)
            if results:
                status_color = 'green' if results['status'] == 'completed' else 'red'
                click.echo(f"  • {run_id[:8]} ({results['model']}): " +
                          click.style(results['status'], fg=status_color))


@cli.command()
@click.argument('run_id', required=False)
@click.option('--latest', is_flag=True, help='Show latest run results')
@click.option('--json', 'output_json', is_flag=True, help='Output results as JSON')
@click.pass_context
def results(ctx, run_id, latest, output_json):
    """View test results."""
    config = ctx.obj['config']
    runner = TestRunner(config)

    if latest or not run_id:
        # Get latest run
        runs = runner.list_runs(limit=1)
        if not runs:
            click.echo("No test runs found")
            ctx.exit(1)
        run_id = runs[0]['run_id']

    # Get results
    results = runner.get_run_results(run_id)

    if not results:
        click.echo(f"No results found for run: {run_id}")
        ctx.exit(1)

    if output_json:
        click.echo(json.dumps(results, indent=2))
    else:
        _display_results(results, detailed=True)


@cli.command()
@click.option('--limit', default=10, help='Number of runs to list')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.pass_context
def list(ctx, limit, output_json):
    """List recent test runs."""
    config = ctx.obj['config']
    runner = TestRunner(config)

    runs = runner.list_runs(limit=limit)

    if not runs:
        click.echo("No test runs found")
        return

    if output_json:
        click.echo(json.dumps(runs, indent=2))
    else:
        # Format as table
        table_data = []
        for run in runs:
            table_data.append([
                run['run_id'][:8],
                run['model'],
                run['branch'],
                run['commit'][:8] if run['commit'] else 'N/A',
                run['status'],
                run['start_time']
            ])

        headers = ['Run ID', 'Model', 'Branch', 'Commit', 'Status', 'Start Time']
        click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize the database and create necessary directories."""
    config = ctx.obj['config']

    click.echo("Initializing ADWS Testing Framework...")

    # Create directories
    directories = [
        Path(config.artifacts.base_path),
        Path('logs'),
        Path('migrations')
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        click.echo(f"  ✓ Created directory: {directory}")

    # Initialize database
    from src.models.database import DatabaseManager
    db_manager = DatabaseManager(config.database.url)
    db_manager.create_tables()
    click.echo(f"  ✓ Initialized database: {config.database.url}")

    # Run Alembic migrations
    import subprocess
    try:
        result = subprocess.run(
            ['alembic', 'upgrade', 'head'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            click.echo("  ✓ Applied database migrations")
        else:
            click.echo("  ⚠ Migrations may need to be created first")
    except FileNotFoundError:
        click.echo("  ⚠ Alembic not found, skipping migrations")

    click.echo("\nInitialization complete!")
    click.echo("Run 'adws-test test project-init' to run your first test.")


@cli.command()
@click.pass_context
def validate(ctx):
    """Validate configuration and environment."""
    config = ctx.obj['config']

    click.echo("Validating configuration...")

    # Check configuration
    errors = config.validate()
    if errors:
        click.echo(click.style("Configuration errors:", fg='red'))
        for error in errors:
            click.echo(f"  ✗ {error}")
        ctx.exit(1)
    else:
        click.echo("  ✓ Configuration is valid")

    # Check standard-configuration path
    sc_path = config.get_standard_config_path()
    if sc_path.exists():
        click.echo(f"  ✓ Standard configuration found: {sc_path}")

        # Check if it's a git repo
        if (sc_path / ".git").exists():
            click.echo("  ✓ Standard configuration is a git repository")
        else:
            click.echo(click.style("  ✗ Standard configuration is not a git repository", fg='red'))
    else:
        click.echo(click.style(f"  ✗ Standard configuration not found: {sc_path}", fg='red'))

    # Check OpenAI API key
    if config.openai.api_key:
        click.echo("  ✓ OpenAI API key configured")
    else:
        click.echo(click.style("  ⚠ OpenAI API key not configured (required for LLM judge)", fg='yellow'))

    # Check Claude command
    import shutil
    if shutil.which(config.claude.command):
        click.echo(f"  ✓ Claude command available: {config.claude.command}")
    else:
        click.echo(click.style(f"  ✗ Claude command not found: {config.claude.command}", fg='red'))

    click.echo("\nValidation complete!")


@cli.command()
@click.option('--commit', help='Specific commit to build')
@click.option('--force', is_flag=True, help='Force rebuild even if cached')
@click.option('--clean', is_flag=True, help='Clean dist directory before building')
@click.pass_context
def build(ctx, commit, force, clean):
    """Build the standard-configuration project."""
    config = ctx.obj['config']
    build_manager = BuildManager(config)

    click.echo("Building standard-configuration...")

    # Clean if requested
    if clean:
        click.echo("Cleaning dist directory...")
        if build_manager.clean_dist():
            click.echo("  ✓ Cleaned dist directory")
        else:
            click.echo(click.style("  ✗ Failed to clean dist directory", fg='red'))

    # Execute build
    result = build_manager.build(commit=commit, force_rebuild=force)

    if result.success:
        click.echo(click.style("✓ Build completed successfully", fg='green'))
        click.echo(f"  Duration: {result.duration:.2f} seconds")
        click.echo(f"  Files built: {result.files_built}")
        if result.cache_hit:
            click.echo(f"  Cache: Retrieved from cache")
        if result.dist_path:
            click.echo(f"  Output: {result.dist_path}")
    else:
        click.echo(click.style("✗ Build failed", fg='red'))
        click.echo(f"  Error: {result.error}")
        ctx.exit(1)


@cli.command()
@click.option('--max-age', default=7, help='Maximum age in days for cache entries')
@click.pass_context
def clean_cache(ctx, max_age):
    """Clean old build cache entries."""
    config = ctx.obj['config']
    build_manager = BuildManager(config)

    if build_manager.cache:
        click.echo(f"Cleaning cache entries older than {max_age} days...")
        build_manager.cache.clean(max_age_days=max_age)
        click.echo("  ✓ Cache cleaned")
    else:
        click.echo("Build caching is not enabled")


def _display_results(results, detailed=False):
    """Display test results in a formatted way."""
    click.echo("\n" + "="*60)
    click.echo(f"Run ID: {results['run_id']}")
    click.echo(f"Model: {results['model']}")
    click.echo(f"Branch: {results['branch']}")
    click.echo(f"Commit: {results['commit'][:8] if results['commit'] else 'N/A'}")

    status_color = 'green' if results['status'] == 'completed' else 'red'
    click.echo(f"Status: " + click.style(results['status'].upper(), fg=status_color))

    if results['start_time'] and results['end_time']:
        from datetime import datetime
        start = datetime.fromisoformat(results['start_time'])
        end = datetime.fromisoformat(results['end_time'])
        duration = (end - start).total_seconds()
        click.echo(f"Duration: {duration:.2f} seconds")

    click.echo("="*60)

    # Display test cases
    for test_case in results['test_cases']:
        click.echo(f"\nTest: {test_case['name']}")

        if test_case['results']:
            passed = sum(1 for r in test_case['results'] if r['passed'])
            failed = len(test_case['results']) - passed

            click.echo(f"Results: {passed} passed, {failed} failed")

            if detailed:
                for result in test_case['results']:
                    status = click.style("✓", fg='green') if result['passed'] else click.style("✗", fg='red')
                    click.echo(f"  {status} {result['check_name']}")

                    if result['details'] and (not result['passed'] or detailed):
                        # Show first few lines of details
                        lines = result['details'].split('\n')[:3]
                        for line in lines:
                            if line.strip():
                                click.echo(f"    {line}")


if __name__ == '__main__':
    # Add tabulate to requirements if not present
    try:
        import tabulate
    except ImportError:
        click.echo("Installing tabulate...")
        import subprocess
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'tabulate'])

    cli()