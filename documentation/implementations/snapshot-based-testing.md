# Snapshot-Based Testing Architecture

**Date:** 2025-11-05
**Status:** Implemented
**Version:** 1.0

## Overview

Implemented a comprehensive snapshot-based testing architecture that enables efficient testing of SDLC workflows and other features without re-running the lengthy initialization process for each test.

## Problem Statement

The init process (adw_init.py) takes ~8 minutes to complete all phases:
- Phase 1: Git setup and configuration
- Phase 2: GitHub repository creation
- Phase 3: Folder structure creation
- Phase 4: Conditional documentation system
- Phase 5: Frontend setup (Next.js, TypeScript, TailwindCSS)
- Phase 6: Cloudflare Workers and D1 database
- Phase 7: Prefect deployment setup
- Phase 8: Configuration and cleanup

Running init for every SDLC test would be extremely inefficient. We needed a way to:
1. Run init once and capture the result
2. Reuse the initialized workspace for multiple tests
3. Overlay latest standard-configuration files when needed
4. Maintain test isolation

## Solution Architecture

### Core Components

#### 1. Snapshot Manager (`src/core/snapshot.py`)

Core class that handles all snapshot operations:

```python
class SnapshotManager:
    - create_snapshot()    # Create snapshot from workspace
    - restore_snapshot()   # Restore with optional overlays
    - list_snapshots()     # List all available snapshots
    - delete_snapshot()    # Remove snapshots
    - set_default_snapshot() # Set default for tests
    - get_snapshot_info()  # Get detailed metadata
```

**Key Features:**
- Metadata tracking (creation time, size, file counts, tags)
- Default snapshot designation
- Overlay system for updating .adws and .claude directories
- JSON-based metadata storage

#### 2. Snapshot Runner (`src/core/snapshot_runner.py`)

Test runner that leverages snapshots:

```python
class SnapshotTestRunner(TestRunner):
    - run_with_snapshot()      # Run tests using snapshots
    - run_sdlc_test()          # SDLC-specific test runner
    - run_slash_command_test() # Slash command test runner
    - cleanup_old_runs()       # Manage test artifacts
```

**Automatic Overlays:**
- By default, overlays latest `.adws` and `.claude` from `~/ai/standard-configuration`
- Ensures tests use current workflow definitions
- Maintains initialized project structure

#### 3. SDLC Checks (`src/checks/sdlc.py`)

Validation checks for SDLC workflows:

- `SDLCPlanCheck` - Validates plan file creation with required sections
- `SDLCImplementationCheck` - Verifies code changes via git status
- `SDLCTestsCheck` - Ensures test files exist and were updated
- `SDLCDocumentationCheck` - Checks for documentation updates
- `SDLCCommitCheck` - Validates commit message patterns (feat:, fix:, chore:)
- `SDLCPullRequestCheck` - Verifies feature branch creation

### Management Scripts

#### Create Snapshot (`scripts/create_init_snapshot.py`)

Creates snapshots from successful init runs:

```bash
python scripts/create_init_snapshot.py <workspace_path> \
    --name init-complete \
    --description "Full init with all phases"
```

**Validation:**
- Checks for required directories (.git, apps, documentation, scripts)
- Warns if workspace appears incomplete
- Automatically sets as default

#### Manage Snapshots (`scripts/manage_snapshots.py`)

Complete CLI for snapshot management:

```bash
# List all snapshots
python scripts/manage_snapshots.py list

# Show snapshot details
python scripts/manage_snapshots.py info [name]

# Restore a snapshot
python scripts/manage_snapshots.py restore <name> [--target <path>]

# Delete a snapshot
python scripts/manage_snapshots.py delete <name>

# Set default snapshot
python scripts/manage_snapshots.py set-default <name>
```

### Test Integration

#### SDLC Test Runner (`tests/test_sdlc_with_snapshot.py`)

Comprehensive test runner for SDLC workflows:

```bash
# Test all workflow types
python tests/test_sdlc_with_snapshot.py --workflow all

# Test specific workflow
python tests/test_sdlc_with_snapshot.py --workflow feature

# Use specific snapshot and model
python tests/test_sdlc_with_snapshot.py \
    --snapshot init-complete-frontend \
    --model sonnet
```

**Workflow Types Supported:**
- `feature` - New functionality implementation
- `bug` - Bug fix workflows
- `chore` - Maintenance and configuration tasks

## Implementation Details

### Snapshot Storage Structure

```
adws-testing/
├── snapshots/
│   ├── metadata.json              # Central metadata file
│   └── init-complete-frontend/    # Snapshot directory
│       ├── .git/
│       ├── .adws/                 # Will be overlaid
│       ├── .claude/               # Will be overlaid
│       ├── apps/
│       │   ├── client/            # Frontend with node_modules
│       │   └── server/            # Cloudflare worker
│       ├── documentation/
│       └── scripts/
```

### Metadata Format

```json
{
  "snapshots": {
    "init-complete-frontend": {
      "created_at": "2025-11-05T13:22:08",
      "source_workspace": "runs/20251026_2217_80f39d66/workspace",
      "description": "Complete initialized project...",
      "tags": ["init", "complete", "all-phases"],
      "files_count": 27325,
      "dirs_count": 3642,
      "size_bytes": 382567424
    }
  },
  "default": "init-complete-frontend"
}
```

### Overlay Mechanism

When restoring a snapshot:

1. **Copy snapshot** to target workspace
2. **Remove existing** `.adws` and `.claude` directories
3. **Copy latest** from `~/ai/standard-configuration`
4. **Result:** Initialized project with current workflow definitions

This ensures:
- Tests use latest ADWs, slash commands, and agents
- No need to re-initialize when standard-configuration updates
- Isolation between test runs

## Current State

### Available Snapshots

**init-complete-frontend** (DEFAULT)
- Created: 2025-11-05 13:22:08
- Size: 364.84 MB
- Files: 27,325
- Directories: 3,642
- Tags: init, complete, all-phases
- Source: runs/20251026_2217_80f39d66/workspace

### Test Results from Source Run

Run: 20251026_2217_80f39d66
- Duration: 471 seconds (~8 minutes)
- Status: 7/12 checks passed
- Model: Sonnet

**Passing Checks:**
- ✓ Git initialized
- ✓ Git branches configured (main, staging)
- ✓ On staging branch
- ✓ README exists with content
- ✓ Init git phase complete
- ✓ Directory structure created (all 9 directories)

**Failed Checks:**
- ✗ Execution time (471s > 120s limit) - Expected for full init
- ✗ Missing README files in apps/, documentation/, scripts/ subdirectories
- ✗ Main README doesn't document project structure

**Note:** Failed checks are documentation-related and don't impact SDLC testing functionality.

## Usage Examples

### Creating a Snapshot from Latest Init

```bash
# Run init test
python tests/test_adw_init.py --model sonnet --project-name test-project

# Create snapshot from successful run
python scripts/create_init_snapshot.py \
    runs/<run_id>/workspace \
    --name init-v2 \
    --description "Init with updated frontend"
```

### Running SDLC Tests

```bash
# Test feature workflow
python tests/test_sdlc_with_snapshot.py \
    --workflow feature \
    --model sonnet

# Test all workflows
python tests/test_sdlc_with_snapshot.py --workflow all
```

### Managing Snapshots

```bash
# List available snapshots
python scripts/manage_snapshots.py list

# View detailed info
python scripts/manage_snapshots.py info

# Create a test workspace from snapshot
python scripts/manage_snapshots.py restore init-complete-frontend \
    --target /tmp/test-workspace
```

## Performance Benefits

### Before (Without Snapshots)
- Each SDLC test: ~8 minutes (init) + test time
- 3 workflow tests: ~24 minutes minimum
- Wasted compute on identical init processes

### After (With Snapshots)
- Initial snapshot creation: ~8 minutes (one-time)
- Snapshot restore: ~5-10 seconds
- Each SDLC test: ~10 seconds + test time
- 3 workflow tests: ~30-60 seconds total

**Speed Improvement: ~24x faster** for multi-test scenarios

## Future Enhancements

### Planned Features

1. **Snapshot Versioning**
   - Track standard-configuration version used
   - Automatic snapshot updates when configs change
   - Version compatibility checks

2. **Differential Snapshots**
   - Store only changes from base snapshot
   - Reduce storage requirements
   - Faster snapshot creation

3. **Snapshot Validation**
   - Automated health checks on snapshots
   - Verify critical files and structure
   - Flag corrupted or incomplete snapshots

4. **Multiple Snapshot Types**
   - `init-minimal` - Just git and structure
   - `init-frontend` - Frontend only
   - `init-backend` - Backend/Cloudflare only
   - `init-complete` - All phases

5. **Parallel Test Execution**
   - Multiple tests using same snapshot
   - Isolated workspaces from one snapshot
   - Better CI/CD integration

6. **Snapshot Compression**
   - Compress snapshots at rest (tar.gz)
   - Decompress on restore
   - Save ~70% disk space

## Testing Strategy

### Test Pyramid with Snapshots

```
        /\
       /  \
      / E2E \          <- Full init tests (rare)
     /--------\
    / SDLC    \        <- Snapshot-based workflow tests
   /   Tests   \
  /--------------\
 /   Unit Tests  \    <- Component checks
/------------------\
```

**Layers:**
1. **Unit Tests** - Individual checks and components
2. **SDLC Tests** - Workflow tests using snapshots (frequent)
3. **E2E Tests** - Full init tests (nightly/weekly)

### When to Use Snapshots

**Use Snapshots For:**
- SDLC workflow testing (feature, bug, chore)
- Slash command validation
- Agent behavior testing
- Multiple test iterations
- Regression testing

**Don't Use Snapshots For:**
- Testing init process itself
- Validating init phase outputs
- Testing first-time setup flows

## Dependencies

### Required Packages
- Python 3.13+
- shutil (standard library)
- json (standard library)
- pathlib (standard library)

### External Dependencies
- Git (for workspace operations)
- Standard-configuration repository (for overlays)

## File Locations

### Core Implementation
- `src/core/snapshot.py` - SnapshotManager class
- `src/core/snapshot_runner.py` - SnapshotTestRunner class
- `src/checks/sdlc.py` - SDLC validation checks

### Scripts
- `scripts/create_init_snapshot.py` - Create snapshots
- `scripts/manage_snapshots.py` - Manage snapshots CLI

### Tests
- `tests/test_sdlc_with_snapshot.py` - SDLC workflow tests
- `tests/test_adw_init.py` - Init process tests (creates snapshots)

### Data Storage
- `snapshots/` - Snapshot storage directory
- `snapshots/metadata.json` - Snapshot metadata
- `runs/` - Test run artifacts

## Maintenance

### Regular Tasks

**Weekly:**
- Review snapshot usage and cleanup unused
- Verify default snapshot is current
- Check for snapshot corruption

**Monthly:**
- Update snapshots with latest standard-configuration
- Archive old snapshots
- Review storage usage

**After Config Updates:**
- Overlays handle most updates automatically
- Create new snapshot if init process changes
- Update snapshot descriptions and tags

### Troubleshooting

**Snapshot restore fails:**
- Check snapshot exists: `python scripts/manage_snapshots.py info`
- Verify disk space available
- Check permissions on target directory

**Tests fail with snapshot:**
- Verify overlay directories exist in standard-configuration
- Check git status is clean in snapshot
- Try restoring snapshot manually to inspect

**Snapshot too large:**
- Check for node_modules bloat
- Remove build artifacts before creating snapshot
- Consider differential snapshots (future feature)

## Conclusion

The snapshot-based testing architecture provides a robust, efficient way to test SDLC workflows and other features without the overhead of repeated initialization. With 24x speed improvements and flexible overlay mechanisms, this system enables rapid iteration and comprehensive testing of the standard-configuration workflows.

## References

- Init Process: `tests/test_adw_init.py`
- Test Framework: `src/core/runner.py`
- Configuration: `config.yaml`
- Standard Configuration: `~/ai/standard-configuration`
