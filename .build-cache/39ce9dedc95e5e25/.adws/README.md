# AI Developer Workflows (ADWs) - Standard Configuration

## Overview

This directory contains standardized AI Developer Workflows (ADWs) that orchestrate complex development tasks using the Claude Code CLI. Upon distribution to your project, these files will be placed in the `.adws/` directory (hidden directory with dot prefix).

## Distribution Note

**Important**: This is the source directory (`src/adws/` without dot). When distributed to your project:
- Source location: `src/adws/` (development, no dot)
- Distribution location: `dist/.adws/` (packaged, with dot)
- Your project location: `.adws/` (installed, with dot)

## Current ADWs

### adw_init - Project Initialization

Initializes new projects with standardized configuration using the `/project-init` slash command.

## Quick Start

### Prerequisites

1. **uv** - Python package manager
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Claude Code CLI** - Must be installed and configured
   ```bash
   # Check if installed
   claude --version
   ```

### Usage in Your Project

After these configurations are distributed to your project's `.adws/` directory:

#### Basic Usage

```bash
# Initialize a new project (from your project root where .adws/ is located)
uv run --python 3.13 .adws/adw_init.py "my-project-name"

# Or if made executable
./.adws/adw_init.py "my-project-name"
```

#### Options

```bash
# Use a specific Claude model
uv run --python 3.13 .adws/adw_init.py "my-project" --model claude-sonnet-4-5-20250929

# Dry run to see what would be executed
uv run --python 3.13 .adws/adw_init.py "my-project" --dry-run
```

## What adw_init Does

The `adw_init.py` script executes the `/project-init` slash command, which:

1. **Git Setup**
   - Initializes git repository with 'main' as default branch
   - Creates 'staging' branch for development
   - Documents branch protection rules

2. **Project Structure**
   - Creates comprehensive `.gitignore` file
   - Sets up initial README.md with project template
   - Configures standard directory structure

3. **Project Type Detection**
   - Identifies project type (web app, electron, CLI tool, etc.)
   - Delegates to appropriate sub-agent for type-specific setup

## Examples

All examples assume the ADWs are installed in your project's `.adws/` directory:

### Initialize a Web Application

```bash
uv run --python 3.13 .adws/adw_init.py "todo-web-app"
```

### Initialize an Electron Desktop App

```bash
uv run --python 3.13 .adws/adw_init.py "electron-notes-app"
```

### Initialize a CLI Tool

```bash
uv run --python 3.13 .adws/adw_init.py "my-cli-tool"
```

## Script Architecture

The ADW follows patterns established in TAC projects:

- **Shebang**: `#!/usr/bin/env -S uv run` for direct execution
- **Dependencies**: Inline script dependencies using uv's script format
- **Output**: Streams Claude Code output in real-time
- **Error Handling**: Graceful handling of errors and interrupts

### Default Model

The default model is set to `claude-sonnet-4-5-20250929` (Sonnet 4.5), which provides:
- Latest capabilities and performance improvements
- Explicit version pinning for reproducibility
- Ability to override via `--model` flag if needed

### Non-Interactive Mode

**CRITICAL**: All ADW scripts MUST use the `--print` flag when invoking the Claude Code CLI. This is required because:

- **Background Execution**: ADWs run as background agents without interactive user sessions
- **No User Input**: Claude cannot prompt for confirmations, workspace trust dialogs, or any other interactive input
- **Automated Workflows**: The `--print` flag enables non-interactive mode, causing Claude to execute to completion and exit automatically
- **Output Capture**: Non-interactive mode allows proper output streaming and error handling

The `--print` (or `-p`) flag is designed specifically for this use case. According to the CLI documentation:
> Print response and exit (useful for pipes). Note: The workspace trust dialog is skipped when Claude is run with the -p mode.

**For Future ADW Development**: All new ADW scripts must include `--print` in the claude command construction to avoid execution hangs.

### Permissions Mode

ADWs run with the `--dangerously-skip-permissions` flag because:

- **Containerized Environment**: ADWs are designed for containerized execution where the security boundary is the container itself, not the permissions system
- **Functional Requirements**: The `/project-init` command requires file creation, directory manipulation, and git operations that would otherwise require repeated permission prompts
- **User Experience**: Automated workflows should run without interactive permission requests
- **Controlled Scope**: When used in the intended containerized environment, the risk surface is appropriately managed

This design choice prioritizes automation and workflow efficiency while relying on container boundaries for security isolation.

## Troubleshooting

### Claude Command Not Found

If you get an error about `claude` command not found:

1. Ensure Claude Code CLI is installed
2. Check that it's in your PATH: `which claude`
3. Try running with full path to claude executable

### Permission Denied

If you get a permission error when running directly:

```bash
chmod +x .adws/adw_init.py
```

### Python Version Issues

The scripts require Python 3.10 or later. If you encounter version issues:

```bash
# Explicitly specify Python version
uv run --python 3.13 .adws/adw_init.py "my-project"

# Check available Python versions
uv python list
```

### Project Type Not Detected

The `/project-init` command will ask for clarification if the project type is unclear from the name.

## Future Roadmap

This is a minimal implementation. Future ADWs may include:

- **adw_plan** - Planning phase for GitHub issues
- **adw_build** - Implementation phase
- **adw_test** - Testing phase
- **adw_review** - Code review phase
- **adw_sdlc** - Complete SDLC orchestrator

See the brainstorming documents for comprehensive roadmap details.

## Directory Structure When Distributed

When distributed to your project, the structure will be:

```
your-project/
├── .adws/                  # ADWs directory (hidden, with dot)
│   ├── adw_init.py        # Project initialization script
│   └── README.md          # This documentation
├── .claude/               # Claude configurations (if included)
└── [your project files]
```

## Contributing

This is part of the standard-configuration project. To contribute new ADWs or improvements:

1. Modify files in `src/adws/` (source directory, no dot)
2. Test your changes
3. Build distribution with build scripts
4. Submit pull request

## License

Part of the standard-configuration project.