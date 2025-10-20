# Standard Configuration Distribution

This directory contains the built standard configurations ready for use in your projects.

## Installation

Copy the directories to your project root:

```bash
cp -r .claude/ /path/to/your/project/
cp -r .adws/ /path/to/your/project/
```

## Contents

- `.claude/` - Claude Code CLI configurations
  - `commands/` - Custom slash commands
  - `settings.template.json` - Settings template (customize as needed)

- `.adws/` - AI Developer Workflows
  - `adw_init.py` - Project initialization workflow
  - `templates/` - Project templates

## Customization

After copying to your project, you can customize the configurations:

1. Rename `settings.template.json` to `settings.json` and adjust as needed
2. Add project-specific commands to `.claude/commands/`
3. Modify ADW scripts for your workflow

## Documentation

For full documentation, see the main repository:
https://github.com/your-org/standard-configuration
