# Testing Slash Commands

## Overview

This document explains the proper approach to testing slash commands in the standard-configuration repository.

## Testing Philosophy

**Slash commands should be tested as part of ADW (AI Developer Workflow) integration tests, not as isolated unit tests.**

### Why?

1. **Real-world usage**: Slash commands are typically used as part of larger workflows, not in isolation
2. **Dependencies**: Many slash commands have prerequisites (e.g., `/init-frontend` requires `/init-git` and `/init-structure`)
3. **Integration testing**: ADW tests validate the complete workflow from script execution through to final state
4. **Maintainability**: Fewer, more comprehensive tests are easier to maintain than many isolated tests

## Test Structure

### ADW Tests (Recommended)

ADW tests execute complete workflows using ADW Python scripts like `adw_init.py`:

```
tests/
├── test_adw_init.py          # Tests adw_init.py (init-git → init-structure → init-frontend → init-cloudflare)
├── base_adw_test.py          # Base class for ADW tests
└── test_init_cloudflare.py   # Specific test for init-cloudflare only
```

**Example: `test_adw_init.py`**
- Executes `adw_init.py` which runs multiple slash commands in sequence
- Validates complete project initialization
- Tests `/init-git`, `/init-structure`, `/init-frontend`, and `/init-cloudflare` together

### Isolated Slash Command Tests (Use Sparingly)

Only create isolated tests for:
- Slash commands with NO prerequisites
- Debugging specific issues
- Commands that can run independently

**Example: `test_init_git.py`**
- Tests `/init-git` in isolation
- Valid because it has no prerequisites

## How to Test a New Slash Command

### Step 1: Determine if it's part of an ADW workflow

Check if the command is called by any ADW script:

```bash
grep -r "your-command" ~/ai/standard-configuration/dist/.adws/
```

### Step 2a: If it's part of an ADW - Update existing ADW test

Add checks to the existing ADW test file (e.g., `test_adw_init.py`):

```python
def get_adw_init_checks(adw_result=None, script_path=None):
    checks = []

    # Add checks for your command's expected outputs
    checks.append(FileExistsCheck(
        name="your_file_exists",
        file_path="path/to/expected/file"
    ))

    return checks
```

### Step 2b: If it's standalone - Create minimal test

Only if the command truly stands alone:

```python
# tests/test_your_command.py
def get_your_command_checks():
    checks = []
    # Add checks
    return checks
```

And add it to `src/core/runner.py`:

```python
elif test_name == "your-command":
    command = self.config.get_claude_command(
        model=model,
        additional_args=["--", "/your-command"]
    )
```

## Example: Why init-frontend Shouldn't Be Tested in Isolation

The `/init-frontend` command:

1. **Requires `/init-git`**: Checks for `.git/` directory
2. **Requires `/init-structure`**: Needs `apps/client/` directory
3. **Is part of `adw_init.py`**: Always used in sequence with other commands

Therefore:
- ❌ Don't create `test_init_frontend.py`
- ✅ Test it via `test_adw_init.py` which runs the complete workflow

## Running Tests

### Run ADW integration test
```bash
python tests/test_adw_init.py --model sonnet
```

### Run specific isolated test
```bash
python tests/test_init_git.py --model sonnet
```

## Test Artifacts

All test runs create artifacts in `runs/`:

```
runs/
└── YYYYMMDD_HHMM_uuid/
    ├── workspace/          # Isolated test workspace
    ├── stdout.log          # Command output
    ├── stderr.log          # Command errors
    ├── checks/             # Check results
    ├── logs/               # Test logs
    └── summary.json        # Test summary
```

## Best Practices

1. **Test workflows, not units**: Focus on ADW integration tests
2. **Reuse check functions**: Import checks from other test files when appropriate
3. **Keep tests maintainable**: Fewer, comprehensive tests > many fragmented tests
4. **Document prerequisites**: Clearly state what a command needs to run
5. **Follow the testing framework scope**: Only modify code in `adws-testing`, never in `standard-configuration`

## Current Test Coverage

| Command | Test File | Type | Notes |
|---------|-----------|------|-------|
| `/init-git` | `test_init_git.py` | Isolated | Standalone command |
| `/init-structure` | `test_adw_init.py` | ADW | Part of init workflow |
| `/init-frontend` | `test_adw_init.py` | ADW | Part of init workflow |
| `/init-cloudflare` | `test_adw_init.py` | ADW | Part of init workflow (may hit Opus API limits) |
| `adw_init.py` | `test_adw_init.py` | ADW | Complete 4-phase init workflow |

### Known Limitations

**Phase 4 Model**: The `adw_init.py` script uses `claude-opus-4-1` for Phase 4 (`/init-cloudflare`), which may hit API rate limits during testing. This is expected behavior. The test framework focuses on validating Phases 1-3, which cover the core initialization including frontend setup. Phase 4 testing requires API availability and cannot be overridden from the test runner (by design - we don't modify code under test).

## References

- ADW Test Base Class: `tests/base_adw_test.py`
- Test Runner: `src/core/runner.py`
- Testing Framework Boundaries: `.claude/CLAUDE.md`
