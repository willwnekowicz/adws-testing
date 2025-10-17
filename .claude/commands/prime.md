# Prime
> Execute the following sections to understand the ADWS Testing Framework codebase then summarize your understanding.

## List project structure
```bash
git ls-files | head -30
```

## Core documentation
README.md

## Configuration
config.yaml
requirements.txt
setup.py
alembic.ini

## Test implementation
tests/test_project_init.py

## Core modules overview
src/core/runner.py
src/core/process_manager.py
src/core/config.py

## Check system
src/checks/base.py
src/checks/simple.py
src/checks/llm_judge.py

## Database schema
src/models/database.py

## CLI interface
cli.py

## Understand project structure
```bash
# Show Python module structure
find . -type f -name "*.py" | grep -E "^./src/|^./tests/" | sort

# Show configuration files
ls -la *.yaml *.ini *.txt *.md 2>/dev/null

# Check for test runs directory
ls -la runs/ 2>/dev/null || echo "No test runs yet"

# Check database
ls -la *.db 2>/dev/null || echo "Database not initialized yet"
```

## Summary
After reviewing the above files, provide a concise summary of:
1. The purpose and architecture of the ADWS Testing Framework
2. How tests are structured and executed
3. The check system (simple vs LLM-based)
4. Key components and their responsibilities
5. How to run tests and view results