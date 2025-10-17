# ADWS Testing Framework

A comprehensive testing harness for the standard-configuration project. This framework enables automated testing of Claude-based agents with support for multiple models, process monitoring, and both simple and LLM-based evaluations.

## Features

- **Multi-Model Testing**: Test with Claude 4.5 Sonnet and Haiku models
- **Process Monitoring**: Track and monitor all spawned background processes using psutil
- **Flexible Checks**: Extensible check system supporting:
  - Simple checks (file existence, content validation, git state)
  - LLM-based evaluations using OpenAI GPT for complex assessments
- **Database Tracking**: SQLite database with Alembic migrations for complete audit trail
- **Artifact Management**: Organized storage of test outputs and logs
- **CI/CD Integration**: JSON and JUnit XML output formats for integration
- **CLI Interface**: User-friendly command-line interface with Click

## Installation

### Prerequisites

- Python 3.8 or higher
- Git
- Claude CLI (`claude` command available in PATH)
- OpenAI API key (optional, for LLM judge features)

### Quick Setup

Run the installation script which handles everything:
```bash
python install.py
```

This will:
- Create a Python virtual environment
- Install all required dependencies
- Run database migrations
- Validate your configuration

### Manual Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd adws-testing
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run database migrations:
```bash
alembic upgrade head
```

## Configuration

Edit `config.yaml` to configure the framework:

```yaml
database:
  url: "sqlite:///test_runs.db"

standard_configuration:
  path: "~/ai/standard-configuration"

claude:
  command: "claude"
  models:
    sonnet: "sonnet"  # Use model aliases
    haiku: "haiku"
  default_model: "sonnet"
  default_args:
    - "--output-format"
    - "stream-json"
    - "--verbose"
    - "-p"
    - "--dangerously-skip-permissions"  # Required for automated testing

openai:
  api_key: "${OPENAI_API_KEY}"  # Set via environment variable (optional)
  judge_model: "gpt-4o-mini"

process:
  max_wait_time: 300  # seconds
  poll_interval: 1     # seconds

artifacts:
  base_path: "./runs"
```

### Environment Variables

Set the following environment variables:

```bash
export OPENAI_API_KEY="your-api-key-here"
export STANDARD_CONFIG_PATH="~/ai/standard-configuration"  # Optional override
```

## Usage

### Running Tests

Run the project-init test with both models:
```bash
python cli.py test project-init
```

Run with a specific model:
```bash
python cli.py test project-init --model sonnet
python cli.py test project-init --model haiku
```

Test a specific commit or branch:
```bash
python cli.py test project-init --commit abc123
python cli.py test project-init --branch feature-branch
```

### Viewing Results

List recent runs:
```bash
python cli.py list
```

View specific run results:
```bash
python cli.py show <run-id>
```

### Checking Test Artifacts

Each test run creates a directory in `runs/` with:
- `stdout.log` - Claude's complete output
- `stderr.log` - Error output
- `summary.json` - Test run summary
- `process_info.json` - Process tracking information
- `checks/` - Individual check results
- `workspace/` - Symlink to the isolated test workspace

## Test Structure

### Workspace Isolation

Tests run in completely isolated environments:
- Temporary directories in system temp folder prevent git repository conflicts
- Parent repository details are stripped for clean initialization
- Symlinks in `runs/` directory provide easy access to workspaces
- Each test gets a fresh, uncontaminated workspace

### Project-Init Test

The included `project-init` test validates that the `/project-init` slash command correctly:

1. Creates a README.md file with project structure
2. Initializes a git repository
3. Creates both main and staging branches
4. Sets up comprehensive .gitignore file
5. Leaves the repository on the staging branch
6. Creates initial commit

Checks performed:
- `readme_exists` - Verifies README.md creation
- `readme_has_content` - Ensures README has markdown content
- `git_initialized` - Checks .git directory exists
- `git_branches_configured` - Validates both main and staging branches exist
- `on_staging_branch` - Confirms current branch is staging
- `execution_time` - Ensures completion within 2 minutes
- `project_init_complete` - Composite check for overall success

### Creating New Tests

1. Create a new test file in `tests/`:
```python
from src.checks.simple import FileExistsCheck, FileContentCheck

def get_my_test_checks():
    return [
        FileExistsCheck("check_name", "path/to/file"),
        FileContentCheck("content_check", "file.txt", contains=["expected"])
    ]
```

2. Register the test in the CLI or runner.

## Architecture

### Core Components

- **TestRunner**: Orchestrates test execution
- **GitManager**: Handles repository operations
- **ProcessManager**: Tracks background processes
- **Config**: Configuration management
- **DatabaseManager**: SQLAlchemy-based persistence

### Check System

- **BaseCheck**: Abstract base for all checks
- **SimpleCheck**: File, git, and content validations
- **LLMJudge**: OpenAI-powered evaluations
- **CompositeCheck**: Combine multiple checks

### Database Schema

- **runs**: Test run metadata
- **test_cases**: Individual test cases
- **test_results**: Check results
- **process_logs**: Process tracking

## Development

### Running Tests Directly

```bash
python tests/test_project_init.py --model sonnet
```

### Database Migrations

Create a new migration:
```bash
alembic revision -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

### Adding New Check Types

1. Create check class inheriting from `BaseCheck`
2. Implement the `execute()` method
3. Return a `CheckResult` instance

Example:
```python
from src.checks.base import BaseCheck, CheckResult, CheckType

class MyCustomCheck(BaseCheck):
    def __init__(self, name: str):
        super().__init__(name, CheckType.SIMPLE)

    def execute(self, **kwargs) -> CheckResult:
        # Perform check logic
        passed = True  # Your logic here
        return self._create_result(
            passed=passed,
            details="Check details"
        )
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -e .

      - name: Run tests
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          adws-test init
          adws-test test project-init --json > results.json

      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: results.json
```

## Key Features

### Permission Bypass for Testing

The framework uses `--dangerously-skip-permissions` flag to enable automated testing without user prompts. This is essential for CI/CD integration and unattended test execution.

### Timestamp-based Run IDs

Run IDs follow the format `YYYYMMDD_HHMM_shortUUID` for easy chronological sorting and identification.

### Process Monitoring

Uses psutil to track all spawned processes, ensuring cleanup and preventing orphaned processes.

## Troubleshooting

### Common Issues

1. **Test fails with "permission denied" or Claude asks for permissions**
   - Ensure `--dangerously-skip-permissions` is in the `default_args` in config.yaml
   - This flag is required for automated testing

2. **Git branch tests fail (missing main branch)**
   - Fixed in latest version - ensure project-init.md includes initial commit
   - The framework now creates an empty commit to establish branches properly

3. **Workspace conflicts with parent repository**
   - Framework uses temp directories for complete isolation
   - Check that symlinks are created properly in runs/ directory

4. **Model not found errors**
   - Use model aliases: `"sonnet"` and `"haiku"` instead of full model names
   - Check config.yaml for proper model configuration

5. **Database errors**
   - Run migrations: `alembic upgrade head`
   - Check SQLite database permissions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: [https://github.com/yourusername/adws-testing/issues](https://github.com/yourusername/adws-testing/issues)
- Documentation: [https://github.com/yourusername/adws-testing/wiki](https://github.com/yourusername/adws-testing/wiki)