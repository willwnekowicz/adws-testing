# Chore: Update Tests for init-git Refactoring

## Chore Description

The `project-init` slash command has been refactored into two smaller, more composable commands:
1. `/init-git` - Handles git repository initialization, branches, .gitignore, and README
2. `/init-structure` - Handles directory structure creation (documentation, scripts, apps)

The `adw_init.py` ADW script now orchestrates both commands in sequence, but our testing framework still references the old `project-init` command name. This chore updates all test files, function names, and CLI references to reflect the new `/init-git` command name while maintaining the existing validation logic.

Previously, tests were failing because the `project-init` command was asking for user input despite running in non-interactive mode. The refactoring to `/init-git` has resolved this issue, and now we need to update our tests accordingly and verify they all pass.

## Relevant Files

Use these files to resolve the chore:

**tests/test_project_init.py** (RENAME & MODIFY)
- Currently tests the `/project-init` slash command
- Should be renamed to `tests/test_init_git.py` to match the new command name
- Function `get_project_init_checks()` should be renamed to `get_init_git_checks()`
- Function `run_project_init_test()` should be renamed to `run_init_git_test()`
- All references to "project-init" in docstrings, comments, and variable names should be updated to "init-git"
- Test validation logic remains the same (README, git branches, .gitignore, etc.)
- This test validates git initialization only, not directory structure

**tests/test_adw_init.py** (MODIFY)
- Currently imports `get_project_init_checks` from `tests.test_project_init`
- Should be updated to import `get_init_git_checks` from `tests.test_init_git`
- Line 34: Update import statement
- Line 88: Update function call from `get_project_init_checks()` to `get_init_git_checks()`
- Line 289: Update function call from `get_project_init_checks()` to `get_init_git_checks()`
- Comments referencing "project-init" should be updated to "init-git" where they refer to Phase 1
- Maintains existing directory structure validation checks for Phase 2 (`/init-structure`)

**cli.py** (MODIFY)
- Line 16: Update import from `tests.test_project_init` to `tests.test_init_git`
- Line 16: Update import from `get_project_init_checks` to `get_init_git_checks`
- Line 38: Update test choice from `'project-init'` to `'init-git'`
- Line 67-68: Update test name handling to use `'init-git'` instead of `'project-init'`
- Line 76: Update checks assignment to use `get_init_git_checks()` instead of `get_project_init_checks()`
- Line 99: Update test name reference from `'project-init'` to `'init-git'`
- Line 240: Update help text from "project-init" to "init-git"
- All user-facing messages and documentation strings referencing "project-init" should be updated

**README.md** (MODIFY)
- Multiple references to "project-init" test throughout the documentation
- Line 143-156: Update test examples to use `init-git` instead of `project-init`
- Line 212-229: Update "Project-Init Test" section header and description
- Section should be renamed to "Init-Git Test"
- Update description to clarify it validates `/init-git` command (git setup only)
- Update all example commands showing test execution
- Line 240-253: Update ADW-Init Test section to clarify Phase 1 is `/init-git`
- Line 269-291: Update "Creating Slash Command Tests" example

### New Files

No new files need to be created. One file will be renamed (`test_project_init.py` → `test_init_git.py`).

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Rename and Update Core Test File

- Rename `tests/test_project_init.py` to `tests/test_init_git.py` using `git mv` to preserve history
- Update the module docstring to reference `/init-git` instead of `/project-init`
- Rename function `get_project_init_checks()` to `get_init_git_checks()`
- Rename function `run_project_init_test()` to `run_init_git_test()`
- Update all docstrings in both functions to reference "init-git" instead of "project-init"
- Update variable `project_init_complete` composite check name to `init_git_complete`
- Update all string literals in the file from "project-init" to "init-git"
- Update all comments referencing "project-init" to "init-git"
- Keep all validation logic unchanged (checks for README, git branches, .gitignore, etc.)

### Step 2: Update ADW Test File Imports and References

- Open `tests/test_adw_init.py`
- Update line 34 import statement from:
  ```python
  from tests.test_project_init import get_project_init_checks
  ```
  to:
  ```python
  from tests.test_init_git import get_init_git_checks
  ```
- Update line 88 function call from `get_project_init_checks()` to `get_init_git_checks()`
- Update line 289 function call from `get_project_init_checks()` to `get_init_git_checks()`
- Update docstring on line 40-42 to reference Phase 1 as `/init-git` instead of `/project-init`
- Update comment on line 84-86 section header to reference "init-git checks"
- Keep all directory structure validation logic unchanged (Phase 2 validation)

### Step 3: Update CLI Integration

- Open `cli.py`
- Update line 16 import from:
  ```python
  from tests.test_project_init import get_project_init_checks
  ```
  to:
  ```python
  from tests.test_init_git import get_init_git_checks
  ```
- Update line 38 test choice from `'project-init'` to `'init-git'`
- Update line 67 conditional from `if test_name == 'project-init':` to `if test_name == 'init-git':`
- Update line 68 assignment to use `get_init_git_checks()` instead of `get_project_init_checks()`
- Update line 76 fallback to use `get_init_git_checks()` instead of `get_project_init_checks()`
- Update line 99 conditional from `'project-init'` to `'init-git'`
- Update line 240 help text from "project-init" to "init-git"
- Keep all test execution logic unchanged

### Step 4: Update Documentation

- Open `README.md`
- Update all command examples using `project-init` to use `init-git`:
  - Line 143: `python cli.py test project-init` → `python cli.py test init-git`
  - Line 149-150: Both examples using `project-init` → `init-git`
  - Line 154-157: All examples using `project-init` → `init-git`
- Update section header on line 212 from "### Project-Init Test" to "### Init-Git Test"
- Update description on lines 213-220 to clarify this validates `/init-git` command (git initialization only)
- Update line 230 section header from "### ADW-Init Test" to clarify it references `/init-git` in Phase 1
- Update line 233 to reference `/init-git` instead of `/project-init`
- Update example code on line 269-291 to use `init-git` test name
- Ensure consistency across all documentation

### Step 5: Run Validation Commands

Execute the validation commands to ensure all tests pass and there are no regressions.

## Validation Commands

Execute every command to validate the chore is complete with zero regressions.

```bash
# Verify the file was renamed correctly
ls -la tests/test_init_git.py

# Verify old file no longer exists
test ! -f tests/test_project_init.py && echo "✓ Old file removed" || echo "✗ Old file still exists"

# Verify imports work correctly
python -c "from tests.test_init_git import get_init_git_checks; print('✓ Import successful')"

# Verify ADW test imports work
python -c "from tests.test_adw_init import get_adw_init_checks; print('✓ ADW imports successful')"

# Verify CLI imports work
python -c "from cli import cli; print('✓ CLI imports successful')"

# Run the init-git test with sonnet model
python cli.py test init-git --model sonnet

# Run the adw-init test with sonnet model
python cli.py test adw-init --model sonnet

# Verify test results show passing checks
python cli.py list --limit 5

# Check for any remaining references to "project-init" in test files
grep -r "project-init" tests/ || echo "✓ No remaining project-init references in tests/"

# Check for any remaining references to "project_init" function names
grep -r "get_project_init_checks\|run_project_init_test" . --include="*.py" || echo "✓ No remaining old function names"
```

## Notes

- The refactoring keeps the validation logic completely unchanged - we're only updating names and references
- The `/init-git` command focuses solely on git initialization (repository, branches, .gitignore, README)
- The `/init-structure` command creates the directory structure and is validated separately in the ADW test
- The `adw_init.py` ADW orchestrates both commands in sequence, which is why the ADW test validates both phases
- Previous test failures were due to interactive prompts; the refactored commands run non-interactively
- After this chore, we should have two distinct slash command tests:
  1. `test_init_git.py` - Tests `/init-git` command (git setup)
  2. A future `test_init_structure.py` could test `/init-structure` independently if needed
- The ADW test validates the complete two-phase workflow end-to-end
