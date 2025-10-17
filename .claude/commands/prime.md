# Prime
> Execute the following sections to understand the codebase then summarize your understanding.

## Read
README.md
config.yaml
requirements.txt

## Read & Execute
tests/test_project_init.py
src/core/runner.py
src/core/process_manager.py
src/checks/base.py
cli.py

## Run
```bash
# List all project files
git ls-files

# Show project structure
find . -type f -name "*.py" | grep -E "^./src/|^./tests/" | sort

# Count lines of code
find . -name "*.py" -type f -exec wc -l {} + | tail -1

# Show available CLI commands
python cli.py --help 2>/dev/null || echo "Not installed yet - run install command first"

# Check test runs directory
ls -la runs/ 2>/dev/null || echo "No test runs yet"

# Check database
ls -la *.db 2>/dev/null || echo "Database not initialized yet"
```

## Report
Summarize:
1. Purpose and architecture of the ADWS Testing Framework
2. How tests are structured and executed
3. The check system (simple vs LLM-based)
4. Key components (runner, process manager, checks, database)
5. How to run tests and view results