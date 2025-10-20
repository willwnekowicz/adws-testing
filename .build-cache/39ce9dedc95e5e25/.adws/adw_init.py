#!/usr/bin/env -S uv run

# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "click>=8.0.0",
#     "rich>=10.0.0",
# ]
# ///

"""
adw_init.py - AI Developer Workflow for Project Initialization

This ADW script initializes a new project using the /project-init slash command
through the Claude Code CLI. It sets up standardized project configuration
including git setup, branch structure, .gitignore, and README.

When distributed to your project, this file will be in the .adws/ directory.

Usage (from your project root after distribution):
    uv run --python 3.13 .adws/adw_init.py PROJECT_NAME
    ./.adws/adw_init.py PROJECT_NAME

Examples:
    uv run --python 3.13 .adws/adw_init.py "my-web-app"
    uv run --python 3.13 .adws/adw_init.py "electron-todo-app"
"""

import click
import subprocess
import sys
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

@click.command()
@click.argument('project_name')
@click.option('--model', default='claude-sonnet-4-5-20250929',
              help='Claude model to use (default: claude-sonnet-4-5-20250929)')
@click.option('--dry-run', is_flag=True,
              help='Show what would be executed without running')
def init_project(project_name: str, model: str, dry_run: bool):
    """Initialize a new project using the /project-init slash command.

    PROJECT_NAME: Name of the project to initialize (e.g., "my-web-app")
    """

    console.print(Panel.fit(
        f"[bold cyan]ADW: Project Initialization[/bold cyan]\n"
        f"Project: [green]{project_name}[/green]\n"
        f"Model: [yellow]{model}[/yellow]",
        border_style="cyan"
    ))

    # Construct the Claude Code command
    # The /project-init command will handle all the project setup
    # Use --print flag for non-interactive mode (required for ADW background execution)
    claude_command = [
        "claude",
        "--print",
        "--dangerously-skip-permissions",
        "--model", model,
        "/project-init", project_name
    ]

    if dry_run:
        console.print("\n[yellow]Dry run mode - would execute:[/yellow]")
        console.print(f"[dim]{' '.join(claude_command)}[/dim]")
        return

    console.print(f"\n[dim]Executing: {' '.join(claude_command)}[/dim]\n")

    try:
        # Execute the Claude Code CLI command
        # We use subprocess.run to capture and stream the output
        process = subprocess.Popen(
            claude_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # Stream the output line by line
        if process.stdout:
            for line in process.stdout:
                # Print without adding extra newline since lines already have them
                print(line, end='')

        # Wait for the process to complete
        return_code = process.wait()

        if return_code == 0:
            console.print(Panel.fit(
                "[bold green]✓ Project initialization completed successfully![/bold green]\n"
                f"Project '{project_name}' has been initialized with standard configuration.",
                border_style="green"
            ))
        else:
            console.print(Panel.fit(
                f"[bold red]✗ Project initialization failed[/bold red]\n"
                f"Exit code: {return_code}",
                border_style="red"
            ))
            sys.exit(return_code)

    except FileNotFoundError:
        console.print(Panel.fit(
            "[bold red]Error: Claude Code CLI not found[/bold red]\n"
            "Please ensure 'claude' command is installed and in your PATH.\n"
            "Install from: https://github.com/anthropics/claude-code",
            border_style="red"
        ))
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(Panel.fit(
            f"[bold red]Unexpected error:[/bold red]\n{str(e)}",
            border_style="red"
        ))
        sys.exit(1)

if __name__ == "__main__":
    init_project()