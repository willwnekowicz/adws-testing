# Feature: Enhanced ADW Init Tests for Directory Structure Validation

## Feature Description

This feature enhances the `adw-init` test suite to validate the new two-phase initialization workflow. The `adw_init.py` ADW script now executes two slash commands sequentially: `/project-init` (for git setup) and `/init-structure` (for directory structure creation). This feature adds comprehensive test checks to validate that the enhanced workflow creates the complete expected project structure, including the new standardized folder hierarchy for documentation, scripts, and application code.

The testing framework will validate not only that both commands execute successfully, but that the resulting directory structure matches specifications with proper README files, git commits, and integration between the two phases.

## User Story

As a testing framework maintainer
I want to validate that `adw_init` correctly executes both `/project-init` and `/init-structure` commands
So that we can ensure the complete project initialization workflow creates all expected directories, files, and git configuration with zero regressions

## Problem Statement

The `adw_init` workflow has been enhanced to run two slash commands instead of one, creating a more comprehensive project initialization that includes:

1. **Git initialization** via `/project-init` (existing)
2. **Directory structure creation** via `/init-structure` (new)

However, the current test suite for `adw-init` only validates the `/project-init` outcomes. It does not check for:

- The new directory structure (`documentation/`, `scripts/`, `apps/` with subdirectories)
- README files within the created directories
- The second git commit for folder structure
- Proper integration between the two commands
- Error handling when either command fails

Without comprehensive tests, we cannot confidently validate that:
- Both commands execute in the correct sequence
- The complete folder structure is created properly
- Git history shows both initialization phases
- The workflow fails gracefully if either command encounters errors

## Solution Statement

Extend the `adw-init` test to include comprehensive checks for the enhanced two-phase initialization:

1. **Add directory structure validation checks** using the existing `DirectoryStructureCheck` class to verify all new folders are created
2. **Add file existence checks** for README.md files in major directories (`documentation/`, `scripts/`, `apps/`)
3. **Add git commit validation** to ensure a second commit exists with message "Add standard folder structure"
4. **Add integration checks** to validate the main project README was updated to document the structure
5. **Update `get_adw_init_checks()`** function to include all new validation checks
6. **Maintain backwards compatibility** with existing checks to ensure no regressions in `/project-init` validation

This approach reuses existing check classes from the framework while adding new instances specifically configured for the enhanced workflow validation.

## Relevant Files

Use these files to implement the feature:

**tests/test_adw_init.py** (MODIFY)
- Contains the `AdwInitTest` class and `get_adw_init_checks()` function
- Currently only validates `/project-init` outcomes (README, git, branches)
- Needs additional checks for directory structure validation
- Must be extended to check for README files in subdirectories
- Should validate the second git commit for folder structure
- Already imports `DirectoryStructureCheck` but doesn't use it for the new directories

**src/checks/simple.py** (REFERENCE)
- Contains all the check classes needed: `DirectoryStructureCheck`, `FileExistsCheck`, `FileContentCheck`, `GitConfigCheck`
- Provides patterns for creating validation checks
- Will be referenced to understand how to properly configure checks
- No modifications needed - existing classes are sufficient

**tests/base_adw_test.py** (REFERENCE)
- Provides the `BaseAdwTest` pattern that `AdwInitTest` extends
- Shows how ADW tests integrate with the framework
- No modifications needed - existing structure supports the enhancement

**cli.py** (REFERENCE)
- Shows how `adw-init` test is invoked via CLI
- Line 69-72: Calls `get_adw_init_checks()` to get validation checks
- No modifications needed - just need to ensure enhanced checks are returned from the function

### New Files

No new files are required. All implementation can be done by extending the existing `tests/test_adw_init.py` file with additional check instances.

## Implementation Plan

### Phase 1: Foundation

Understand the existing test structure and new requirements:
- Review the current `get_adw_init_checks()` implementation to understand existing patterns
- Analyze the directory structure specification from the feature description
- Identify which check classes from `src/checks/simple.py` are needed
- Verify the expected folder hierarchy matches the specification exactly
- Understand the git commit strategy (two commits: initial setup + folder structure)

### Phase 2: Core Implementation

Add comprehensive directory structure validation:
- Create `DirectoryStructureCheck` instances for the new folder hierarchy
- Add `FileExistsCheck` instances for README files in subdirectories
- Add `FileContentCheck` instances to validate README content where appropriate
- Add git commit validation to ensure the second commit exists
- Verify the main project README documents the structure
- Ensure check names are descriptive and follow existing naming conventions

### Phase 3: Integration

Integrate new checks into the test workflow:
- Update `get_adw_init_checks()` to include all new validation checks
- Organize checks logically (ADW checks, project-init checks, structure checks, git checks)
- Add docstring comments explaining each category of checks
- Test the enhanced validation with the CLI
- Verify all checks pass with a successful `adw_init` execution
- Ensure proper error messages when checks fail

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Add Directory Structure Validation Checks

- Open `tests/test_adw_init.py` for modification
- In the `get_adw_init_checks()` function, after the existing checks, add a comprehensive `DirectoryStructureCheck`
- Configure it to validate all required directories:
  - `documentation/` (parent)
  - `documentation/research/`
  - `documentation/brainstorming/`
  - `documentation/specs/`
  - `documentation/implementations/`
  - `scripts/`
  - `apps/` (parent)
  - `apps/client/`
  - `apps/server/`
- Name the check `"directory_structure_created"` for clarity
- Add a comment explaining this validates the `/init-structure` command output

### 2. Add README File Existence Checks

- Add `FileExistsCheck` instances to validate README.md files in key directories
- Create check for `documentation/README.md` named `"documentation_readme_exists"`
- Create check for `scripts/README.md` named `"scripts_readme_exists"`
- Create check for `apps/README.md` named `"apps_readme_exists"`
- Group these checks together with a comment explaining they validate directory documentation
- Place these checks after the directory structure check for logical flow

### 3. Add Main Project README Structure Documentation Check

- Add a `FileContentCheck` for the main `README.md` to verify it documents the structure
- Name the check `"main_readme_documents_structure"`
- Configure it to check for the presence of "Project Structure" or similar section header
- Use the `contains` parameter with patterns like `["Project Structure", "documentation/", "scripts/", "apps/"]`
- This validates that `/init-structure` updated the main README as expected
- Add comment explaining this validates integration between the two commands

### 4. Add Git Commit Validation for Folder Structure

- Add a new check to validate the second git commit exists
- This requires creating a custom validation approach since we need to check git history
- Use `FileContentCheck` as a pattern, or create a lambda-based validation if needed
- Alternatively, add a note in the check comments that git commit validation is done via the existing `GitConfigCheck`
- Add a comment noting that two commits should exist: "Initial project setup" and "Add standard folder structure"
- This check may need to be implemented as part of the validation process rather than a discrete check class

### 5. Update get_adw_init_checks() Function Organization

- Reorganize the function to group checks logically:
  - **Section 1**: ADW-specific checks (script validity, execution, Claude execution, output)
  - **Section 2**: Project-init checks (from `get_project_init_checks()`)
  - **Section 3**: Directory structure checks (new - the 9 directories)
  - **Section 4**: README file checks (new - documentation, scripts, apps READMEs)
  - **Section 5**: Integration checks (new - main README structure documentation)
- Add section comments to make the organization clear
- Update the function docstring to mention it validates both `/project-init` and `/init-structure` outcomes

### 6. Update AdwInitTest Class Documentation

- Update the class docstring in `AdwInitTest` to mention the two-phase initialization
- Update comments in the `get_specific_checks()` method to note that additional structure checks are in `get_adw_init_checks()`
- Add a comment in `validate_project_outcome()` noting it should check for directory structure as well
- Consider adding basic structure validation in `validate_project_outcome()` for early failure detection

### 7. Enhance validate_project_outcome() Method

- In the `AdwInitTest` class, enhance the `validate_project_outcome()` method
- Add checks for the new directory structure (at least the top-level directories)
- Check for existence of `documentation/`, `scripts/`, and `apps/` directories
- This provides early validation before checks run
- Return `False` if any critical directories are missing
- Add logging statements to indicate what's being validated

### 8. Test the Enhanced Checks with CLI

- Run the test using the CLI: `python cli.py test adw-init --model sonnet`
- Verify all new checks are executed
- Verify check output shows clear pass/fail status for each validation
- Check that error messages are descriptive when checks fail
- Validate that the test run completes successfully with all checks passing

### 9. Test Failure Scenarios

- Create a test scenario where `/init-structure` hasn't been implemented yet (directory structure missing)
- Run the test and verify the new checks fail with clear error messages
- Verify the error messages explain what's missing (e.g., "✗ Directory missing: documentation/research")
- Ensure check failures don't crash the test framework
- Validate that partial success is properly reported (e.g., project-init passed, structure checks failed)

### 10. Add Edge Case Validation

- Consider edge cases in the test checks:
  - What if directories exist but are empty?
  - What if README files exist but have no content?
  - What if only some directories are created?
  - What if the main README wasn't updated?
- Add appropriate checks or update existing checks to handle these cases
- Document any assumptions or limitations in comments

### 11. Update Test Documentation in README

- Update `/Users/william/ai/adws-testing/README.md` section on "ADW-Init Test"
- Add details about the new two-phase validation (lines 230-240)
- Document the complete list of checks performed
- List all directories and README files that are validated
- Update the "Checks performed" list to include structure validation checks
- Add example output showing the enhanced check results

### 12. Run All Validation Commands

Execute all validation commands listed below to ensure zero regressions and complete functionality

## Testing Strategy

### Unit Tests

Since this enhances existing test infrastructure, validation focuses on:

- **Check configuration**: Verify all `DirectoryStructureCheck` instances have correct paths
- **Check completeness**: Ensure all 9 expected directories are included in validation
- **Check naming**: Verify check names are descriptive and follow conventions
- **Function return**: Ensure `get_adw_init_checks()` returns a complete list of checks

### Integration Tests

- **CLI integration**: Test via `python cli.py test adw-init` to ensure checks are executed
- **End-to-end workflow**: Run complete `adw_init.py` workflow and verify all checks pass
- **Error propagation**: Verify that check failures are reported correctly through the CLI
- **Results display**: Ensure check results are displayed clearly to users
- **Database persistence**: Verify check results are stored correctly in the test database

### Edge Cases

1. **Partial directory structure**: Only some directories created - checks should fail for missing ones
2. **Missing README files**: Directories exist but README files missing - specific checks should fail
3. **Existing structure**: Running test on a project that already has the structure - should pass
4. **Git not initialized**: If `/project-init` fails, structure checks may be irrelevant - should handle gracefully
5. **Empty directories**: Directories created but empty - checks should still pass (existence check only)
6. **Permission issues**: Cannot read directories - checks should error gracefully with clear messages
7. **Symlinks**: Directories are symlinks - checks should handle appropriately
8. **Case sensitivity**: Directory names with different casing - checks should be case-sensitive
9. **README content variation**: README files have different content than expected - should validate presence not exact content

## Acceptance Criteria

1. **Enhanced test function**: `get_adw_init_checks()` returns checks for both `/project-init` and `/init-structure` outcomes
2. **Directory structure validation**: Test validates all 9 required directories are created
3. **README file validation**: Test validates README.md files exist in `documentation/`, `scripts/`, and `apps/`
4. **Main README integration**: Test validates main README.md documents the project structure
5. **Clear organization**: Checks are organized in logical sections with clear comments
6. **Backwards compatible**: Existing `/project-init` checks continue to work without modification
7. **Descriptive naming**: All new checks have clear, descriptive names following existing patterns
8. **CLI integration**: Enhanced tests work seamlessly with existing CLI commands
9. **Error messages**: Failed checks provide clear, actionable error messages
10. **Documentation updated**: README.md documents the enhanced validation
11. **Zero regressions**: All existing functionality continues to work correctly
12. **Complete coverage**: All aspects of the two-phase initialization are validated

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

```bash
# 1. Verify the test file can be imported without errors
cd /Users/william/ai/adws-testing
python -c "from tests.test_adw_init import get_adw_init_checks; print('✓ Import successful')"

# 2. Verify get_adw_init_checks returns checks
python -c "from tests.test_adw_init import get_adw_init_checks; checks = get_adw_init_checks(); print(f'✓ Returns {len(checks)} checks')"

# 3. Verify check types are correct
python -c "from tests.test_adw_init import get_adw_init_checks; from src.checks.base import BaseCheck; checks = get_adw_init_checks(); assert all(isinstance(c, BaseCheck) for c in checks), 'Not all checks are BaseCheck instances'; print('✓ All checks are valid BaseCheck instances')"

# 4. Verify directory structure check is included
python -c "from tests.test_adw_init import get_adw_init_checks; checks = get_adw_init_checks(); names = [c.name for c in checks]; assert 'directory_structure_created' in names, 'Missing directory_structure_created check'; print('✓ Directory structure check included')"

# 5. Verify README checks are included
python -c "from tests.test_adw_init import get_adw_init_checks; checks = get_adw_init_checks(); names = [c.name for c in checks]; assert 'documentation_readme_exists' in names, 'Missing documentation README check'; assert 'scripts_readme_exists' in names, 'Missing scripts README check'; assert 'apps_readme_exists' in names, 'Missing apps README check'; print('✓ All README existence checks included')"

# 6. Verify main README structure check is included
python -c "from tests.test_adw_init import get_adw_init_checks; checks = get_adw_init_checks(); names = [c.name for c in checks]; assert 'main_readme_documents_structure' in names, 'Missing main README structure check'; print('✓ Main README structure check included')"

# 7. Run syntax check on the test file
python -m py_compile tests/test_adw_init.py && echo "✓ Test file has valid Python syntax" || echo "✗ Syntax error in test file"

# 8. Test the CLI can load the test
python cli.py test adw-init --help && echo "✓ CLI can load adw-init test" || echo "✗ CLI failed to load test"

# 9. Run a dry-run test to verify test execution (if adw_init supports it)
# Note: This requires the enhanced adw_init.py to be in place
# python cli.py test adw-init --model sonnet --dry-run

# 10. Verify test database integration
python -c "from src.core.config import Config; from src.core.runner import TestRunner; config = Config('config.yaml'); runner = TestRunner(config); print('✓ Test runner can be initialized')"

# 11. Check that existing project-init checks are still included
python -c "from tests.test_adw_init import get_adw_init_checks; from tests.test_project_init import get_project_init_checks; adw_checks = get_adw_init_checks(); project_checks = get_project_init_checks(); project_check_names = [c.name for c in project_checks]; adw_check_names = [c.name for c in adw_checks]; included = sum(1 for name in project_check_names if name in adw_check_names); print(f'✓ {included}/{len(project_checks)} project-init checks included in adw-init checks')"

# 12. Verify DirectoryStructureCheck is configured correctly
python -c "from tests.test_adw_init import get_adw_init_checks; from src.checks.simple import DirectoryStructureCheck; checks = get_adw_init_checks(); structure_checks = [c for c in checks if isinstance(c, DirectoryStructureCheck) and c.name == 'directory_structure_created']; assert len(structure_checks) > 0, 'No directory_structure_created check found'; check = structure_checks[0]; expected_dirs = ['documentation', 'documentation/research', 'documentation/brainstorming', 'documentation/specs', 'documentation/implementations', 'scripts', 'apps', 'apps/client', 'apps/server']; actual_dirs = check.required_dirs; missing = [d for d in expected_dirs if d not in actual_dirs]; assert not missing, f'Missing directories in check: {missing}'; print(f'✓ DirectoryStructureCheck configured with all {len(expected_dirs)} expected directories')"

# 13. Verify FileExistsCheck instances for READMEs
python -c "from tests.test_adw_init import get_adw_init_checks; from src.checks.simple import FileExistsCheck; checks = get_adw_init_checks(); readme_checks = [c for c in checks if isinstance(c, FileExistsCheck) and 'readme' in c.name.lower()]; expected_readmes = ['documentation_readme_exists', 'scripts_readme_exists', 'apps_readme_exists']; actual_names = [c.name for c in readme_checks]; for name in expected_readmes: assert name in actual_names, f'Missing README check: {name}'; print(f'✓ All {len(expected_readmes)} README existence checks configured correctly')"

# 14. Test check execution in isolation (create a mock workspace)
python -c "
from pathlib import Path
import tempfile
from tests.test_adw_init import get_adw_init_checks
from src.checks.simple import DirectoryStructureCheck

# Create temp workspace with expected structure
with tempfile.TemporaryDirectory() as tmpdir:
    workspace = Path(tmpdir)

    # Create expected directories
    (workspace / 'documentation' / 'research').mkdir(parents=True)
    (workspace / 'documentation' / 'brainstorming').mkdir(parents=True)
    (workspace / 'documentation' / 'specs').mkdir(parents=True)
    (workspace / 'documentation' / 'implementations').mkdir(parents=True)
    (workspace / 'scripts').mkdir(parents=True)
    (workspace / 'apps' / 'client').mkdir(parents=True)
    (workspace / 'apps' / 'server').mkdir(parents=True)

    # Get checks
    checks = get_adw_init_checks()
    structure_check = next((c for c in checks if c.name == 'directory_structure_created'), None)

    if structure_check:
        structure_check.set_context(workspace, workspace / 'artifacts')
        result = structure_check.execute()
        assert result.passed, f'Structure check failed: {result.details}'
        print('✓ Directory structure check executes correctly on valid structure')
    else:
        print('✗ Could not find directory_structure_created check')
"

# 15. Test check execution with missing directories
python -c "
from pathlib import Path
import tempfile
from tests.test_adw_init import get_adw_init_checks

# Create temp workspace WITHOUT expected structure
with tempfile.TemporaryDirectory() as tmpdir:
    workspace = Path(tmpdir)

    # Get checks
    checks = get_adw_init_checks()
    structure_check = next((c for c in checks if c.name == 'directory_structure_created'), None)

    if structure_check:
        structure_check.set_context(workspace, workspace / 'artifacts')
        result = structure_check.execute()
        assert not result.passed, 'Structure check should fail when directories are missing'
        assert 'missing' in result.details.lower() or 'not exist' in result.details.lower(), 'Error message should indicate missing directories'
        print('✓ Directory structure check correctly fails when directories are missing')
    else:
        print('✗ Could not find directory_structure_created check')
"

# 16. Verify check count increased
python -c "
from tests.test_adw_init import get_adw_init_checks
from tests.test_project_init import get_project_init_checks

# Get current check count
adw_checks = get_adw_init_checks()
project_checks = get_project_init_checks()

print(f'Project-init checks: {len(project_checks)}')
print(f'ADW-init checks (total): {len(adw_checks)}')
print(f'New structure checks: {len(adw_checks) - len(project_checks)}')

# Should have at least 4 additional checks:
# 1. directory_structure_created
# 2. documentation_readme_exists
# 3. scripts_readme_exists
# 4. apps_readme_exists
# 5. main_readme_documents_structure (maybe)

expected_minimum_increase = 4
actual_increase = len(adw_checks) - len(project_checks)
assert actual_increase >= expected_minimum_increase, f'Expected at least {expected_minimum_increase} new checks, got {actual_increase}'
print(f'✓ Check count increased appropriately (added {actual_increase} checks)')
"

# 17. Validate test can be run end-to-end (requires valid environment)
# Note: This test requires the enhanced adw_init.py to be implemented
# Uncomment when ready to test end-to-end:
# python cli.py test adw-init --model sonnet && echo "✓ End-to-end test passed" || echo "⚠ End-to-end test failed (may be expected if adw_init not yet enhanced)"

# 18. Verify no import errors from changes
python -c "import sys; sys.path.insert(0, '.'); from tests import test_adw_init; print('✓ No import errors in test_adw_init module')"

# 19. Verify check organization (checks are returned in correct order)
python -c "
from tests.test_adw_init import get_adw_init_checks

checks = get_adw_init_checks()
check_names = [c.name for c in checks]

print('Check execution order:')
for i, name in enumerate(check_names, 1):
    print(f'  {i}. {name}')

print('✓ Check order verified')
"

# 20. Final validation - run linting if available
# python -m pylint tests/test_adw_init.py 2>/dev/null && echo "✓ Linting passed" || echo "⚠ Linting not available or failed (non-critical)"

echo ""
echo "================================"
echo "All validation commands complete"
echo "================================"
echo ""
echo "Note: Commands 9 and 17 are commented out as they require"
echo "the enhanced adw_init.py implementation to be in place."
echo "Uncomment and run them after implementing the adw_init changes."
```

## Notes

### Design Decisions

**Reuse Existing Check Classes**
- Chose to use existing `DirectoryStructureCheck`, `FileExistsCheck`, and `FileContentCheck` classes
- Rationale: These classes already provide the exact functionality needed for validation
- Trade-off: No trade-offs - this is the most efficient approach

**Check Organization Strategy**
- Organized checks into logical sections within `get_adw_init_checks()`
- Rationale: Makes the function easier to understand and maintain
- Sections: ADW checks → project-init checks → structure checks → README checks → integration checks

**Check Granularity**
- Created separate checks for each README file rather than one composite check
- Rationale: Better error reporting - users can see exactly which README is missing
- Trade-off: More checks to maintain, but clearer failure messages

**Git Commit Validation Approach**
- Did not create a separate check class for git commit validation
- Rationale: Git history validation is complex and may be better suited to manual verification or LLM judge
- Future consideration: Could add a `GitHistoryCheck` class if needed

**Main README Content Validation**
- Used `FileContentCheck` with basic string matching rather than complex parsing
- Rationale: Simple presence checks are sufficient to validate integration
- Trade-off: Won't catch if structure documentation is incomplete, but confirms basic integration

### Implementation Considerations

**No New Dependencies**
- All implementation uses existing check classes from `src/checks/simple.py`
- No new Python packages required
- No modifications to core framework classes needed

**Backwards Compatibility**
- All existing checks continue to work unchanged
- The `get_adw_init_checks()` function signature remains the same
- Test database schema doesn't need updates

**Error Message Quality**
- Leveraging built-in error messages from check classes
- `DirectoryStructureCheck` provides clear messages like "✗ Directory missing: documentation/research"
- `FileExistsCheck` shows "File does not exist: documentation/README.md"

### Testing Approach

**Validation Strategy**
- Comprehensive validation commands that don't require the enhanced `adw_init.py` to be implemented
- Can verify check configuration and execution in isolation
- Commands 9 and 17 require the actual enhanced workflow and can be run after implementation

**Mock Testing**
- Validation commands 14 and 15 create temporary workspaces to test check execution
- This allows validation of check logic without running the full ADW workflow
- Provides confidence that checks will work correctly when integrated

### Future Enhancements

**Git History Validation**
- Could add a `GitHistoryCheck` class to validate commit messages and sequence
- Would check for specific commits: "Initial project setup" and "Add standard folder structure"
- Would validate commits are in correct chronological order

**README Content Validation**
- Could enhance README checks to validate specific content sections
- Could use `FileContentCheck` with regex patterns to validate structure documentation
- Could use LLM judge to validate README quality and completeness

**Composite Checks**
- Could create composite checks grouping related validations
- Example: `structure_complete` = directories + READMEs + git commit
- Would provide higher-level pass/fail status

**Performance Optimization**
- If check count grows significantly, consider parallel execution
- Could cache directory existence checks to avoid repeated filesystem calls
- Could optimize check order to fail fast on critical checks

### Relationship to Other Components

**Dependencies on standard-configuration**
- Tests depend on the enhanced `adw_init.py` in standard-configuration repo
- Tests assume `/init-structure` command exists and works correctly
- Must maintain read-only boundary - tests should never modify standard-configuration

**Integration with CLI**
- CLI already supports `adw-init` test via `cli.py test adw-init`
- No CLI changes needed - enhanced checks are returned from `get_adw_init_checks()`
- Results display automatically includes new checks

**Database Integration**
- Test results are automatically persisted to database
- Each check result is stored as a separate row in `test_results` table
- No schema changes needed - existing structure supports arbitrary checks

### Documentation Updates

After implementation, consider updating:
1. **README.md**: Add details about structure validation in ADW-Init Test section
2. **Test output examples**: Show what successful validation looks like
3. **Troubleshooting section**: Add common issues with directory structure checks
4. **Contributing guide**: Document how to add new validation checks
