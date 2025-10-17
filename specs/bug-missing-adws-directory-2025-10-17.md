# Bug: Missing .adws Directory in Test Workspace

## Bug Description

When running the project-init test, the `.adws/` directory is missing from the workspace after the test environment is set up. The expected behavior is that the workspace should contain both `.claude/` and `.adws/` directories from the built `dist/` directory of the standard-configuration project. However, only `.claude/` is present in the workspace at `runs/20251017_1747_cc676212/workspace`.

**Expected behavior**: The workspace should contain:
- `.claude/` directory (for slash commands)
- `.adws/` directory (for AI Developer Workflows)

**Actual behavior**: The workspace only contains:
- `.claude/` directory
- `.adws/` directory is missing

## Problem Statement

The `prepare_for_project_init()` method in `src/core/git_manager.py` removes the `.adws/` directory that was just copied from the `dist/` directory during workspace creation. This method only preserves `.claude/` while removing all other files and directories, including `.adws/`.

## Solution Statement

Modify the `prepare_for_project_init()` method to preserve both `.claude/` and `.adws/` directories when preparing the workspace for project-init tests. This ensures that the standard-configuration components are available in the test workspace.

## Steps to Reproduce

1. Build the standard-configuration project: `cd ~/ai/standard-configuration && ./scripts/build.sh`
2. Verify dist contains .adws: `ls -la ~/ai/standard-configuration/dist/.adws/`
3. Run the project-init test: `python cli.py test project-init --model sonnet`
4. Check the workspace: `ls -la runs/<run-id>/workspace`
5. Observe that `.adws/` directory is missing

## Root Cause Analysis

The issue occurs in the test execution flow:

1. **Line 142-143 in `src/core/runner.py`**: Sets `use_dist = True` to copy from the built `dist/` directory
2. **Line 104-108 in `src/core/git_manager.py`**: Calls `_copy_dist()` which copies all dist contents to workspace, including `.adws/`
3. **Line 164 in `src/core/runner.py`**: Calls `prepare_for_project_init()` AFTER workspace is created
4. **Line 157-179 in `src/core/git_manager.py`**: The `prepare_for_project_init()` method removes ALL files and directories **except `.claude`**

The root cause is at line 169 in `src/core/git_manager.py`:
```python
if item.name == '.claude':
    continue
```

This only preserves `.claude/` but removes everything else, including the `.adws/` directory that was just copied from the dist.

## Relevant Files

### Existing Files to Modify

- **src/core/git_manager.py** (lines 157-179)
  - Contains the `prepare_for_project_init()` method that needs to preserve `.adws/` directory
  - Currently only preserves `.claude/` at line 169
  - Need to add logic to also preserve `.adws/`

### Files Used for Testing

- **tests/test_project_init.py**
  - Test case that validates project-init command
  - Can be used to verify the fix works correctly

- **src/core/runner.py** (lines 138-165)
  - Orchestrates the workspace creation and preparation
  - No changes needed, but important for understanding the flow

- **src/core/build_manager.py**
  - Manages building the dist directory from source
  - No changes needed, but important for understanding what gets built

## Step by Step Tasks

### Fix the prepare_for_project_init method

Update `src/core/git_manager.py` to preserve both `.claude/` and `.adws/` directories:

- Modify line 169 to check for both `.claude` and `.adws` directory names
- Add a comment explaining why both directories need to be preserved
- Consider using a set or list of preserved directories for better maintainability

### Add validation test

Create or update a test to verify `.adws/` is present in the workspace:

- Add a check in `tests/test_project_init.py` or create a new test file
- Verify that `.adws/` directory exists after workspace preparation
- Verify that `.adws/adw_init.py` file exists

### Run validation commands

Execute the validation commands to ensure the fix works with zero regressions:

- Build the standard-configuration project
- Run the project-init test
- Verify the workspace contains `.adws/`
- Run the full test suite to ensure no regressions

## Validation Commands

Execute every command to validate the bug is fixed with zero regressions.

```bash
# 1. Build the standard-configuration project to ensure dist is up to date
cd ~/ai/standard-configuration && ./scripts/build.sh

# 2. Verify dist has .adws directory
ls -la ~/ai/standard-configuration/dist/.adws/
test -d ~/ai/standard-configuration/dist/.adws/ && echo "PASS: .adws exists in dist" || echo "FAIL: .adws missing in dist"

# 3. Return to testing framework
cd ~/ai/adws-testing

# 4. Run the project-init test
python cli.py test project-init --model sonnet

# 5. Get the most recent run ID
LATEST_RUN=$(ls -t runs/ | grep -E '^[0-9]{8}_[0-9]{4}_' | head -n 1)

# 6. Verify .adws directory exists in workspace (this should PASS after the fix)
test -d "runs/$LATEST_RUN/workspace/.adws" && echo "PASS: .adws exists in workspace" || echo "FAIL: .adws missing in workspace"

# 7. Verify .adws/adw_init.py exists in workspace
test -f "runs/$LATEST_RUN/workspace/.adws/adw_init.py" && echo "PASS: adw_init.py exists" || echo "FAIL: adw_init.py missing"

# 8. Verify .claude directory still exists (regression check)
test -d "runs/$LATEST_RUN/workspace/.claude" && echo "PASS: .claude still exists" || echo "FAIL: .claude missing"

# 9. List workspace contents to verify
ls -la "runs/$LATEST_RUN/workspace"

# 10. Run full test suite to ensure no regressions
python -m pytest tests/ -v
```

## Notes

- The fix is minimal and surgical - only one line needs to be modified in `src/core/git_manager.py`
- The `.adws/` directory is required for the standard-configuration to work properly in test workspaces
- This is a testing framework bug, not a bug in the standard-configuration project being tested
- After the fix, both `.claude/` and `.adws/` directories will be preserved when preparing workspaces for project-init tests
- Consider refactoring `prepare_for_project_init()` to accept a list of directories to preserve for better maintainability
