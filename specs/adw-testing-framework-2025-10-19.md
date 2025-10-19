# Feature: ADW Integration Testing Framework

## Feature Description

This feature adds comprehensive integration testing capabilities for AI Developer Workflows (ADWs) to the ADWS Testing Framework. ADWs are Python-based workflow orchestrators that execute one or more slash commands through the Claude Code CLI to accomplish higher-level development tasks. Unlike our existing slash command tests (which function as unit tests), ADW tests are integration tests that validate complete workflows from start to finish.

The first ADW to be tested is `adw_init.py`, which orchestrates the `/project-init` slash command to set up new projects with standardized configurations, git setup, and project structure.

This framework will establish patterns for testing future ADWs like `adw_plan`, `adw_build`, `adw_test`, and `adw_sdlc`, which will orchestrate multiple slash commands in sequence.

## User Story

As a testing framework developer
I want to test ADW workflow scripts that orchestrate slash commands
So that I can validate complete development workflows work correctly and ensure the distributed ADW configurations function as expected in real-world usage

## Problem Statement

The ADWS Testing Framework currently only tests individual slash commands (like `/project-init`) directly through the Claude CLI. However, the standard-configuration project now includes ADWs - Python scripts that wrap and orchestrate these slash commands into higher-level workflows.

Current gaps:
1. **No ADW execution testing**: Cannot validate that ADW scripts execute correctly
2. **No workflow validation**: Cannot test multi-command workflows that future ADWs will implement
3. **No integration layer testing**: Cannot verify the Python wrapper layer works correctly
4. **Missing test organization**: No distinction between unit tests (slash commands) and integration tests (ADWs)
5. **Incomplete coverage**: Cannot validate the distributed `.adws/` directory structure and executability

## Solution Statement

Create a dedicated ADW testing subsystem within the ADWS Testing Framework that:

1. **Executes ADW Python scripts** directly (not just slash commands)
2. **Validates workflow orchestration** from Python script through to Claude execution
3. **Reuses existing check infrastructure** to verify outcomes
4. **Organizes tests hierarchically** as unit (slash commands) vs integration (ADWs)
5. **Tests the distributed form** of ADWs to ensure they work as users will encounter them

The implementation will:
- Add an `AdwRunner` class to execute ADW Python scripts
- Create a base `AdwTestCase` class for ADW-specific testing patterns
- Implement `test_adw_init.py` to validate the first ADW
- Extend the CLI to support ADW tests alongside slash command tests
- Reuse existing workspace isolation, checks, and artifact management

## Relevant Files

### Existing Files to Modify

- **`src/core/runner.py`** - Main test runner that orchestrates test execution
  - Will be extended to support ADW test execution mode
  - Currently only executes Claude CLI directly
  - Needs ability to delegate to AdwRunner for ADW tests

- **`src/core/config.py`** - Configuration management
  - Add ADW-specific configuration options (Python version, uv settings)
  - Configure paths to ADW directories in dist
  - Add ADW execution parameters

- **`src/models/database.py`** - Database schema and models
  - Add ADW-specific tracking (script name, Python version used)
  - Track workflow steps within an ADW test
  - Distinguish slash command tests from ADW tests in schema

- **`cli.py`** - Command-line interface
  - Add `adw-init` test option alongside `project-init`
  - Support ADW-specific options (--python-version, --uv-run)
  - Display ADW test results with workflow step information

- **`tests/test_project_init.py`** - Existing slash command test
  - Reference implementation for check patterns
  - Some checks may be reusable for ADW tests

### New Files

- **`src/core/adw_runner.py`** - NEW
  - Core class for executing ADW Python scripts
  - Handles `uv run` execution with proper Python version
  - Streams output and captures results
  - Validates ADW script structure and dependencies

- **`src/checks/adw.py`** - NEW
  - ADW-specific check classes
  - `AdwExecutionCheck` - Verify ADW script executes successfully
  - `AdwOutputCheck` - Validate ADW output format and content
  - `PythonScriptCheck` - Verify ADW Python script is valid
  - `UvDependencyCheck` - Check inline dependencies are correct

- **`tests/test_adw_init.py`** - NEW
  - Complete test for adw_init.py workflow
  - Validates ADW script execution
  - Verifies `/project-init` slash command is executed correctly
  - Checks final project state matches expectations
  - Tests both dry-run and actual execution modes

- **`tests/base_adw_test.py`** - NEW
  - Base class for all ADW tests
  - Common patterns for ADW testing (setup, teardown, validation)
  - Reusable helper methods for workflow verification
  - Template for future ADW tests

## Implementation Plan

### Phase 1: Foundation - Core ADW Execution Infrastructure

This phase establishes the fundamental infrastructure for executing and monitoring ADW Python scripts. We need to be able to run ADW scripts in the same isolated, monitored way we run slash commands.

**Key Deliverables:**
- AdwRunner class that can execute Python scripts via uv
- Configuration support for ADW testing parameters
- Database schema updates to track ADW tests

**Why this comes first:**
Without the ability to execute ADW scripts, we cannot test them. This foundation enables all subsequent work.

### Phase 2: Core Implementation - ADW-Specific Testing Capabilities

This phase builds the ADW-specific testing logic on top of the execution foundation. We create specialized checks, base test classes, and the actual adw_init test.

**Key Deliverables:**
- ADW-specific check classes
- Base ADW test class for code reuse
- Complete test_adw_init.py implementation
- Integration with existing TestRunner

**Why this comes second:**
With execution capability in place, we can now build the testing logic that validates ADW behavior and outcomes.

### Phase 3: Integration - CLI and User-Facing Features

This phase exposes ADW testing to users through the CLI and completes the integration with existing framework features.

**Key Deliverables:**
- CLI commands for running ADW tests
- Enhanced result display for workflows
- Documentation and examples
- End-to-end validation

**Why this comes last:**
User-facing features depend on the core functionality being complete and tested.

## Step by Step Tasks

### Step 1: Configuration Schema Updates

- Add `adws` section to `config.yaml` schema in `src/core/config.py`
- Define ADW execution parameters:
  - `adw_directory`: Path to ADWs in dist (default: "dist/.adws")
  - `python_version`: Python version for uv run (default: "3.13")
  - `uv_command`: Command to run uv (default: "uv")
  - `adw_timeout`: Max execution time for ADWs (default: 600s)
- Add validation for new configuration fields
- Update `config.yaml` with example ADW configuration

### Step 2: Database Schema Updates

- Create Alembic migration for ADW tracking
- Add `test_type` column to `test_cases` table (values: "slash_command", "adw")
- Add `adw_tests` table with columns:
  - `id` (primary key)
  - `test_case_id` (foreign key to test_cases)
  - `adw_script_name` (e.g., "adw_init.py")
  - `python_version` (version used for execution)
  - `script_execution_status` (success/failed)
  - `claude_execution_status` (did Claude command execute)
  - `dry_run` (boolean, was this a dry run)
- Add `workflow_steps` table for tracking multi-step workflows:
  - `id` (primary key)
  - `adw_test_id` (foreign key)
  - `step_number` (integer)
  - `step_name` (e.g., "/project-init")
  - `status` (pending/running/completed/failed)
  - `duration` (seconds)
- Update database models in `src/models/database.py`
- Run migrations with `alembic upgrade head`

### Step 3: Core AdwRunner Implementation

- Create `src/core/adw_runner.py` with `AdwRunner` class
- Implement `__init__(self, config: Config)` to initialize from configuration
- Implement `get_adw_path(self, adw_name: str) -> Path` to locate ADW scripts in dist
- Implement `validate_adw_script(self, script_path: Path) -> bool` to check:
  - File exists and is executable
  - Has proper shebang line
  - Contains uv script dependencies block
  - Python syntax is valid
- Implement `execute_adw(self, script_path: Path, args: List[str], workspace: Path) -> AdwResult`:
  - Build uv run command with Python version
  - Execute in isolated workspace
  - Stream stdout/stderr to logs
  - Capture exit code
  - Return AdwResult dataclass
- Create `AdwResult` dataclass to encapsulate execution results:
  - `success: bool`
  - `exit_code: int`
  - `stdout: str`
  - `stderr: str`
  - `duration: float`
  - `claude_executed: bool` (detected from output)
- Add comprehensive error handling and logging

### Step 4: ADW-Specific Checks

- Create `src/checks/adw.py` with ADW-specific check classes
- Implement `AdwExecutionCheck(BaseCheck)`:
  - Validates ADW script executed successfully (exit code 0)
  - Checks execution time is within reasonable bounds
  - Verifies no critical errors in output
- Implement `AdwOutputCheck(BaseCheck)`:
  - Validates ADW output contains expected patterns
  - Checks for Claude CLI execution indicators
  - Verifies rich console output formatting (if applicable)
- Implement `PythonScriptValidityCheck(BaseCheck)`:
  - Runs Python syntax validation on ADW script
  - Checks shebang is correct
  - Validates uv dependencies block format
- Implement `UvDependencyCheck(BaseCheck)`:
  - Validates inline dependencies are specified correctly
  - Checks Python version requirement
- All checks should extend BaseCheck and follow existing patterns

### Step 5: Base ADW Test Class

- Create `tests/base_adw_test.py` with `BaseAdwTest` class
- Implement common ADW test setup:
  - `setup_adw_workspace(self) -> Path`: Create isolated workspace
  - `copy_adw_dist(self, workspace: Path)`: Copy .adws/ from dist
  - `get_adw_checks(self) -> List[BaseCheck]`: Return standard checks
- Implement common validation methods:
  - `validate_adw_execution(self, result: AdwResult)`: Check script ran
  - `validate_claude_execution(self, result: AdwResult)`: Check Claude was called
  - `validate_project_outcome(self, workspace: Path)`: Check final state
- Provide template methods for subclasses to override:
  - `get_adw_name(self) -> str`: Return ADW script name
  - `get_adw_args(self) -> List[str]`: Return arguments for ADW
  - `get_specific_checks(self) -> List[BaseCheck]`: Add test-specific checks
- Add helper for dry-run testing
- Include comprehensive docstrings as reference for future ADW tests

### Step 6: Implement test_adw_init.py

- Create `tests/test_adw_init.py` extending `BaseAdwTest`
- Implement `get_adw_init_checks()` function returning check list:
  - `AdwExecutionCheck` - Script executes successfully
  - `PythonScriptValidityCheck` - Script is valid Python
  - All checks from `get_project_init_checks()` - Project created correctly
  - `AdwOutputCheck` - Output indicates success
- Implement `AdwInitTest` class:
  - Override `get_adw_name()` to return "adw_init.py"
  - Override `get_adw_args()` to return test project name
  - Override `get_specific_checks()` with adw_init-specific validations
- Implement test execution:
  - Test with default model
  - Test with --dry-run flag
  - Test with different project names
  - Verify final project structure matches `/project-init` expectations
- Add command-line interface for standalone execution:
  - `--model` option
  - `--config` option
  - `--dry-run` option
- Ensure test can run both standalone and via CLI

### Step 7: Integrate AdwRunner with TestRunner

- Update `src/core/runner.py` to support ADW tests
- Add `adw_runner: AdwRunner` to `TestRunner.__init__`
- Implement test type detection in `run_test()`:
  - Detect if test_name is ADW (e.g., "adw-init") vs slash command (e.g., "project-init")
  - Route to appropriate execution path
- Implement `_run_adw_test()` method:
  - Use AdwRunner to execute ADW script
  - Track in database as ADW test type
  - Run checks against workspace and output
  - Save artifacts (ADW output, logs, workspace state)
- Update `_build_command()` to handle ADW vs slash command distinction
- Ensure workspace isolation works for both test types
- Preserve all existing functionality for slash command tests

### Step 8: Update CLI for ADW Tests

- Update `cli.py` to add ADW test support
- Add "adw-init" to test name choices in `@cli.command('test')`
- Update test command to handle ADW test types:
  - Detect ADW tests by naming convention ("adw-*")
  - Route to appropriate test module
  - Pass ADW-specific options
- Add `--dry-run` flag for ADW tests
- Add `--python-version` option for ADW tests
- Implement `get_adw_test_checks()` helper to load correct checks
- Update `_display_results()` to show ADW-specific information:
  - ADW script name
  - Python version used
  - Workflow steps (if multi-step)
  - Claude execution status
- Import `test_adw_init` module and integrate with CLI

### Step 9: Enhanced Artifact Management for ADWs

- Update `src/utils/artifacts.py` to handle ADW artifacts
- Create ADW-specific subdirectory structure:
  - `runs/{run_id}/adw/` - ADW-specific artifacts
  - `runs/{run_id}/adw/script_output.log` - ADW script output
  - `runs/{run_id}/adw/uv_output.log` - uv command output
  - `runs/{run_id}/adw/workflow_steps.json` - Workflow step tracking
- Implement `save_adw_output()` method
- Implement `save_workflow_steps()` method for multi-step ADWs
- Ensure ADW artifacts are preserved alongside existing artifacts
- Update `save_run_summary()` to include ADW metadata

### Step 10: Documentation

- Update `README.md` with ADW testing section:
  - Explain difference between slash command tests (unit) and ADW tests (integration)
  - Document how to run ADW tests
  - Provide examples of running adw-init test
  - Show how to create new ADW tests
- Add "Creating ADW Tests" section:
  - Reference `BaseAdwTest` class
  - Explain check patterns
  - Show example test structure
  - Document naming conventions
- Update "Test Structure" section to distinguish test types
- Add ADW testing to "Troubleshooting" section
- Document ADW-specific configuration options
- Add examples to configuration section

### Step 11: End-to-End Validation

- Run complete test suite to ensure no regressions:
  - `python cli.py test project-init` - Existing slash command test still works
  - `python cli.py test adw-init` - New ADW test executes successfully
  - `python cli.py test adw-init --dry-run` - Dry run mode works
- Test with both Sonnet and Haiku models
- Verify database tracking works correctly:
  - Check `test_cases` table has correct test_type
  - Verify `adw_tests` table is populated
  - Confirm workflow_steps are tracked
- Validate artifact storage:
  - Check ADW artifacts are saved correctly
  - Verify logs are comprehensive
  - Ensure workspace is preserved
- Test CLI output and formatting
- Verify results display correctly
- Run `python cli.py list` to ensure ADW tests appear
- Run `python cli.py results <run-id>` for an ADW test

## Testing Strategy

### Unit Tests

**AdwRunner Tests** (`tests/test_adw_runner.py`):
- Test ADW script path resolution
- Test script validation (syntax, shebang, dependencies)
- Test uv command building
- Test execution with mocked subprocess
- Test error handling for missing scripts
- Test timeout handling
- Test output streaming and capture

**ADW Check Tests** (`tests/test_adw_checks.py`):
- Test `AdwExecutionCheck` with success and failure cases
- Test `AdwOutputCheck` pattern matching
- Test `PythonScriptValidityCheck` syntax validation
- Test `UvDependencyCheck` dependency parsing
- Verify all checks follow BaseCheck interface
- Test check context setting

**Configuration Tests** (`tests/test_adw_config.py`):
- Test ADW configuration parsing
- Test default values
- Test validation of ADW paths
- Test Python version validation
- Test uv command detection

### Integration Tests

**adw_init Workflow Test** (`tests/test_adw_init.py`):
- Execute full adw_init.py workflow
- Verify ADW script runs successfully
- Confirm `/project-init` slash command is executed
- Validate project structure is created
- Check all git branches are configured
- Verify README content is present
- Test with multiple project names
- Test dry-run mode
- Test with different models

**TestRunner Integration** (`tests/test_runner_adw_integration.py`):
- Test TestRunner routes ADW tests correctly
- Verify database tracking for ADW tests
- Confirm artifact storage for ADWs
- Test ADW test alongside slash command test
- Verify workspace isolation for ADWs

**CLI Integration** (`tests/test_cli_adw.py`):
- Test `cli test adw-init` command
- Verify CLI options are passed correctly
- Test results display formatting
- Verify ADW tests appear in `cli list`
- Test error handling and messages

### Edge Cases

1. **Missing ADW Script**
   - ADW file doesn't exist in dist/.adws/
   - Should fail gracefully with clear error message

2. **Invalid Python Syntax**
   - ADW script has syntax errors
   - PythonScriptValidityCheck should fail
   - Should not attempt execution

3. **Missing Dependencies**
   - ADW script missing uv dependency block
   - Should warn or fail depending on configuration

4. **uv Not Installed**
   - uv command not available on system
   - Should fail with helpful installation message

5. **Python Version Mismatch**
   - Requested Python version not available
   - Should use fallback or fail with clear message

6. **ADW Timeout**
   - ADW execution exceeds timeout
   - Should terminate gracefully and mark as failed

7. **Workspace Permission Issues**
   - Cannot write to workspace directory
   - Should fail with permission error

8. **Claude CLI Failure**
   - Claude command fails within ADW
   - Should capture and report Claude errors
   - Should still validate what was accomplished

9. **Dry-Run Edge Cases**
   - Dry-run should not modify anything
   - Should still validate syntax and setup

10. **Multi-Model Testing**
    - ADW with different Claude models
    - Should respect model parameter
    - Should track model used per test

## Acceptance Criteria

1. **ADW Execution**
   - ✅ AdwRunner successfully executes adw_init.py via uv
   - ✅ Python version is configurable and respected
   - ✅ ADW script output is captured and logged
   - ✅ Exit codes are properly detected

2. **Test Organization**
   - ✅ ADW tests are clearly distinguished from slash command tests in database
   - ✅ Test type is tracked in database schema
   - ✅ CLI supports both test types with appropriate commands

3. **Check System**
   - ✅ ADW-specific checks validate script execution
   - ✅ Existing project-init checks work with ADW tests
   - ✅ Checks reuse BaseCheck infrastructure
   - ✅ Check results are properly stored and displayed

4. **Workflow Validation**
   - ✅ test_adw_init.py validates complete initialization workflow
   - ✅ Both ADW script execution AND final project state are verified
   - ✅ Dry-run mode is supported and tested

5. **Database Tracking**
   - ✅ ADW tests are stored with test_type = "adw"
   - ✅ ADW-specific metadata is tracked (script name, Python version)
   - ✅ Workflow steps table is ready for future multi-step ADWs

6. **Artifact Management**
   - ✅ ADW output is saved in dedicated subdirectory
   - ✅ uv command output is preserved
   - ✅ Workspace state is accessible for debugging

7. **CLI Integration**
   - ✅ `python cli.py test adw-init` executes ADW test
   - ✅ `--dry-run` flag works correctly
   - ✅ Results display shows ADW-specific information
   - ✅ ADW tests appear in `list` command

8. **Documentation**
   - ✅ README explains ADW testing concepts
   - ✅ Creating new ADW tests is documented
   - ✅ Examples are provided for running tests

9. **No Regressions**
   - ✅ Existing slash command tests still work
   - ✅ All current CLI commands function correctly
   - ✅ Database schema migrations apply cleanly

10. **Extensibility**
    - ✅ BaseAdwTest class makes creating new ADW tests straightforward
    - ✅ Workflow steps tracking supports future multi-command ADWs
    - ✅ Check system easily extends to new ADW-specific validations

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

- `cd /Users/william/ai/adws-testing && python -m pytest tests/test_adw_runner.py -v` - Run AdwRunner unit tests
- `cd /Users/william/ai/adws-testing && python -m pytest tests/test_adw_checks.py -v` - Run ADW check unit tests
- `cd /Users/william/ai/adws-testing && alembic upgrade head` - Apply database migrations for ADW tracking
- `cd /Users/william/ai/adws-testing && python cli.py validate` - Validate configuration includes ADW settings
- `cd /Users/william/ai/adws-testing && python cli.py test project-init --model sonnet` - Verify existing slash command test still works
- `cd /Users/william/ai/adws-testing && python cli.py test adw-init --model sonnet` - Run new ADW integration test
- `cd /Users/william/ai/adws-testing && python cli.py test adw-init --dry-run` - Test dry-run mode
- `cd /Users/william/ai/adws-testing && python tests/test_adw_init.py --model sonnet` - Run ADW test standalone
- `cd /Users/william/ai/adws-testing && python cli.py list` - Verify ADW tests appear in run list
- `cd /Users/william/ai/adws-testing && python cli.py results --latest` - View latest ADW test results
- `cd /Users/william/ai/adws-testing && python -m pytest tests/ -v` - Run complete test suite for regressions

## Notes

### Why This Architecture

1. **Separation of Concerns**: AdwRunner handles execution, BaseAdwTest handles test patterns, checks handle validation
2. **Reusability**: Existing checks, workspace isolation, and artifact management all work with ADWs
3. **Extensibility**: Adding new ADW tests only requires extending BaseAdwTest and defining checks
4. **Future-Proof**: Workflow steps table and multi-step support ready for complex ADWs

### Future ADW Tests

This framework enables testing of future ADWs that orchestrate multiple slash commands:

- **adw_plan.py**: Test planning workflow (issues → specs → tasks)
- **adw_build.py**: Test implementation workflow (multiple slash commands in sequence)
- **adw_test.py**: Test testing workflow
- **adw_sdlc.py**: Test complete SDLC orchestration

The workflow_steps tracking table will capture each step in these multi-command workflows.

### Python and uv Considerations

- ADWs use uv's inline script dependencies (PEP 723)
- Tests execute via `uv run --python 3.13 <script>` matching real usage
- Python version is configurable per test if needed
- uv installation is a prerequisite documented in README

### Test Hierarchy

```
Unit Tests (Slash Commands)
├── test_project_init.py
└── [future slash command tests]

Integration Tests (ADWs)
├── test_adw_init.py
├── test_adw_plan.py (future)
├── test_adw_build.py (future)
└── test_adw_sdlc.py (future)
```

### Performance Considerations

ADW tests will be slower than slash command tests because they:
1. Execute Python script wrapper layer
2. Go through uv dependency resolution
3. Include full workflow orchestration

This is acceptable because they test real-world usage patterns.

### Dependencies

No new external libraries required. All dependencies already in requirements.txt:
- subprocess (standard library) for executing uv
- pathlib (standard library) for path handling
- Existing test framework infrastructure

### Relationship to Existing Features

- **Build Manager**: ADW tests use the build system to test dist/.adws/ (already implemented)
- **Workspace Isolation**: Reuses existing workspace creation and cleanup
- **Check System**: Extends existing BaseCheck patterns
- **Database**: Extends existing schema with new tables
- **Artifacts**: Extends existing artifact management
