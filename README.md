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
- OpenAI API key (for LLM judge features)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/adws-testing.git
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

4. Install the package:
```bash
pip install -e .
```

5. Initialize the framework:
```bash
adws-test init
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
    sonnet: "claude-3-5-sonnet-latest"
    haiku: "claude-3-5-haiku-latest"
  default_model: "claude-3-5-sonnet-latest"
  default_args:
    - "--stream-json"
    - "--verbose"
    - "-p"

openai:
  api_key: "${OPENAI_API_KEY}"  # Set via environment variable
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
adws-test test project-init
```

Run with a specific model:
```bash
adws-test test project-init --model sonnet
adws-test test project-init --model haiku
```

Test a specific commit or branch:
```bash
adws-test test project-init --commit abc123
adws-test test project-init --branch feature-branch
```

### Viewing Results

View latest test results:
```bash
adws-test results --latest
```

View specific run results:
```bash
adws-test results <run-id>
```

List recent runs:
```bash
adws-test list --limit 20
```

Get JSON output for CI/CD:
```bash
adws-test results --latest --json > results.json
```

### Validation

Validate your configuration:
```bash
adws-test validate
```

## Test Structure

### Project-Init Test

The included `project-init` test validates that the `/project-init` slash command correctly:

1. Creates a README.md file
2. Initializes a git repository
3. Creates main and staging branches
4. Leaves the repository on the staging branch

Checks performed:
- File existence checks
- File content validation
- Git branch verification
- Execution time limits
- Process completion monitoring

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

## Troubleshooting

### Common Issues

1. **Claude command not found**
   - Ensure `claude` is installed and in your PATH
   - Check configuration: `adws-test validate`

2. **OpenAI API key not working**
   - Verify the key is set: `echo $OPENAI_API_KEY`
   - Check API key validity with OpenAI

3. **Process tracking issues**
   - Ensure psutil is installed: `pip install psutil`
   - Check process permissions

4. **Database errors**
   - Run migrations: `alembic upgrade head`
   - Reinitialize: `adws-test init`

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