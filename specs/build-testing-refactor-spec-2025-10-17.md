# Build Testing Refactor Specification

**Document**: build-testing-refactor-spec-2025-10-17.md
**Author**: ADWS Testing Framework Team
**Date**: 2025-10-17
**Status**: Draft
**Version**: 1.0.0

## Executive Summary

This specification outlines the necessary changes to the ADWS Testing Framework to properly test the built/distributed version of standard-configuration after its refactoring to separate development tooling from distributable configurations.

## 1. Background and Context

### 1.1 Standard-Configuration Refactor

The standard-configuration repository has undergone a structural change:
- **Previous**: Configurations at root level (`.claude/`, `adws/`)
- **Current**:
  - Source files in `src/claude/` and `src/adws/` (no dots)
  - Build process generates `dist/.claude/` and `dist/.adws/` (with dots)
  - Development tools remain in root `.claude/` and `.adws/`

### 1.2 Testing Impact

Our testing framework must now:
1. Build the standard-configuration project before testing
2. Test the `dist/` output instead of root directories
3. Ensure we're validating distributable configurations, not development tools

## 2. Current Testing Approach

### 2.1 Existing Workflow
```python
# Current approach (simplified)
1. Clone/checkout standard-configuration
2. Create isolated workspace
3. Copy .claude/commands/project-init.md to workspace
4. Execute Claude with the command
5. Validate results
```

### 2.2 Problems with Current Approach
- Assumes configurations are at root level
- No build step before testing
- Tests development tools instead of distributable configs
- Commands like `project-init` may not exist at root anymore

## 3. Proposed Solution

### 3.1 New Testing Workflow

```python
# Proposed workflow
1. Clone/checkout standard-configuration
2. Execute build process (./scripts/build.sh)
3. Verify build output in dist/
4. Create isolated workspace
5. Copy dist/.claude/ and dist/.adws/ to workspace
6. Execute Claude with distributed commands
7. Validate results
```

### 3.2 Key Changes Required

#### 3.2.1 Build Integration
- Add build step to TestRunner
- Handle build failures gracefully
- Cache build outputs when possible
- Support different build environments

#### 3.2.2 Path Updates
- Update all paths from root to `dist/`
- Configure source vs. distribution paths
- Support both old and new structures during transition

#### 3.2.3 Validation Updates
- Verify build output structure
- Check for required files in `dist/`
- Validate that build process completes

## 4. Implementation Plan

### 4.1 Phase 1: Core Infrastructure Updates

#### 4.1.1 Config Updates (`src/core/config.py`)

Add new configuration options:
```yaml
standard_configuration:
  path: "~/ai/standard-configuration"
  build_required: true  # New field
  build_script: "./scripts/build.sh"  # New field
  source_path: "src/"  # New field
  dist_path: "dist/"  # New field
  legacy_mode: false  # Support old structure if needed
```

#### 4.1.2 Build Manager (`src/core/build_manager.py`) - NEW

Create new module to handle building:
```python
class BuildManager:
    def __init__(self, config: Config):
        self.config = config
        self.repo_path = config.standard_config_path

    def build(self, commit: Optional[str] = None) -> BuildResult:
        """Execute build process for standard-configuration"""
        # 1. Checkout specific commit if provided
        # 2. Run build script
        # 3. Verify dist/ output
        # 4. Return BuildResult with status and paths

    def verify_build_output(self) -> bool:
        """Check that dist/ contains expected structure"""
        # Check for dist/.claude/
        # Check for dist/.adws/
        # Verify command files exist

    def get_dist_path(self) -> Path:
        """Return path to dist directory"""
        return self.repo_path / "dist"
```

#### 4.1.3 TestRunner Updates (`src/core/runner.py`)

Modify TestRunner to incorporate build step:
```python
class TestRunner:
    def __init__(self, config: Config):
        # ... existing init ...
        self.build_manager = BuildManager(config)

    def run_test(self, test_name: str, **kwargs):
        # ... existing setup ...

        # NEW: Build step
        if self.config.build_required:
            build_result = self.build_manager.build(
                commit=kwargs.get('commit')
            )
            if not build_result.success:
                raise TestError(f"Build failed: {build_result.error}")

        # UPDATE: Use dist path for copying
        dist_path = self.build_manager.get_dist_path()
        self._copy_configurations(dist_path, workspace_path)

        # ... rest of test execution ...
```

### 4.2 Phase 2: Test Updates

#### 4.2.1 Update Existing Tests

Modify `tests/test_project_init.py`:
```python
def test_project_init():
    # Test should now expect:
    # - Command from dist/.claude/commands/project-init.md
    # - Not from .claude/commands/project-init.md

    # Update command path references
    command_path = "dist/.claude/commands/project-init.md"

    # Rest of test logic remains similar
```

#### 4.2.2 Add Build-Specific Tests

Create `tests/test_build_process.py`:
```python
def test_build_completes():
    """Verify build script executes successfully"""

def test_dist_structure():
    """Verify dist/ has correct structure"""

def test_command_migration():
    """Verify commands are correctly placed in dist/"""
```

### 4.3 Phase 3: Backward Compatibility

#### 4.3.1 Legacy Mode Support

Support testing repositories that haven't migrated yet:
```python
class TestRunner:
    def _determine_mode(self) -> str:
        """Auto-detect repository structure"""
        if (self.repo_path / "dist").exists():
            return "build"
        elif (self.repo_path / "src").exists():
            return "build_required"
        else:
            return "legacy"

    def _get_config_source(self) -> Path:
        """Return path to configurations based on mode"""
        mode = self._determine_mode()
        if mode == "build":
            return self.repo_path / "dist"
        elif mode == "legacy":
            return self.repo_path
        else:
            # Need to build first
            self.build_manager.build()
            return self.repo_path / "dist"
```

### 4.4 Phase 4: Enhanced Features

#### 4.4.1 Build Caching

Implement build caching to speed up repeated tests:
```python
class BuildCache:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir

    def get_cache_key(self, repo_path: Path, commit: str) -> str:
        """Generate cache key for build output"""

    def is_cached(self, key: str) -> bool:
        """Check if build output is cached"""

    def store(self, key: str, dist_path: Path):
        """Cache build output"""

    def retrieve(self, key: str, target_path: Path):
        """Retrieve cached build output"""
```

#### 4.4.2 Build Artifacts

Store build logs and outputs:
```python
class BuildArtifactManager:
    def store_build_log(self, run_id: str, log_content: str):
        """Store build process output"""

    def store_build_manifest(self, run_id: str, files: List[str]):
        """Store list of built files"""
```

## 5. Database Schema Updates

### 5.1 New Tables

```sql
-- Track build operations
CREATE TABLE builds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    commit_hash TEXT,
    build_script TEXT,
    status TEXT NOT NULL,  -- 'success', 'failed', 'skipped'
    duration_seconds REAL,
    output_path TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES runs(id)
);

-- Track build artifacts
CREATE TABLE build_artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    build_id INTEGER NOT NULL,
    artifact_type TEXT NOT NULL,  -- 'log', 'manifest', 'cache'
    file_path TEXT NOT NULL,
    file_size INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (build_id) REFERENCES builds(id)
);
```

### 5.2 Migration Script

Create Alembic migration:
```python
# migrations/versions/xxx_add_build_tracking.py
def upgrade():
    op.create_table('builds', ...)
    op.create_table('build_artifacts', ...)
    op.add_column('runs', sa.Column('build_required', sa.Boolean))

def downgrade():
    op.drop_table('build_artifacts')
    op.drop_table('builds')
    op.drop_column('runs', 'build_required')
```

## 6. CLI Updates

### 6.1 New Commands

Add build-specific CLI commands:
```bash
# Explicitly build before testing
adws-test build --repo ~/ai/standard-configuration

# Test with build step
adws-test test project-init --build

# Test without build (use existing dist/)
adws-test test project-init --no-build

# Clean build cache
adws-test clean-cache
```

### 6.2 Updated Help Text

```bash
adws-test test --help
Options:
  --build / --no-build    Build before testing (default: auto-detect)
  --cache / --no-cache    Use build cache if available (default: true)
  --legacy               Use legacy mode for old repo structure
```

## 7. Configuration Examples

### 7.1 Default Configuration
```yaml
# config.yaml
standard_configuration:
  path: "~/ai/standard-configuration"
  build_required: auto  # auto-detect based on structure
  build_script: "./scripts/build.sh"
  source_path: "src/"
  dist_path: "dist/"
  build_timeout: 60  # seconds
  cache_builds: true
  cache_dir: ".build-cache/"
```

### 7.2 Legacy Mode Configuration
```yaml
# For testing old structure
standard_configuration:
  path: "~/ai/standard-configuration"
  build_required: false
  legacy_mode: true
```

## 8. Testing the Refactor

### 8.1 Unit Tests

Create tests for new components:
- `test_build_manager.py` - Test BuildManager class
- `test_build_cache.py` - Test caching functionality
- `test_legacy_compatibility.py` - Test backward compatibility

### 8.2 Integration Tests

- Test full workflow with build step
- Test failure handling (build failures, missing dist/)
- Test cache hit/miss scenarios
- Test legacy mode detection

### 8.3 Performance Tests

- Measure build time impact
- Verify cache improves performance
- Test concurrent builds

## 9. Rollout Plan

### 9.1 Phase 1: Preparation (Week 1)
- [ ] Implement BuildManager
- [ ] Update configuration schema
- [ ] Create database migrations
- [ ] Write unit tests

### 9.2 Phase 2: Integration (Week 2)
- [ ] Integrate BuildManager with TestRunner
- [ ] Update existing tests
- [ ] Implement backward compatibility
- [ ] Test with both old and new structures

### 9.3 Phase 3: Enhancement (Week 3)
- [ ] Implement build caching
- [ ] Add CLI commands
- [ ] Performance optimization
- [ ] Documentation updates

### 9.4 Phase 4: Deployment (Week 4)
- [ ] Final testing
- [ ] Update documentation
- [ ] Release new version
- [ ] Monitor for issues

## 10. Risk Mitigation

### 10.1 Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Build script failures | Tests cannot run | Implement robust error handling, provide clear error messages |
| Performance degradation | Slower test execution | Implement caching, parallel builds |
| Breaking existing workflows | User disruption | Legacy mode support, gradual migration |
| Missing build dependencies | Build failures | Document requirements, auto-check dependencies |
| Disk space issues | Cache grows too large | Implement cache cleanup, size limits |

### 10.2 Rollback Plan

If issues occur:
1. Revert to previous version via git
2. Use `--legacy` flag to bypass build system
3. Disable build requirement in config
4. Document issues and fix incrementally

## 11. Success Criteria

The refactor will be considered successful when:

1. **Functionality**: All existing tests pass with new structure
2. **Performance**: Build step adds < 10 seconds to test time (with cache)
3. **Compatibility**: Both old and new structures are supported
4. **Reliability**: Build success rate > 99%
5. **Documentation**: All changes documented and examples updated
6. **User Experience**: No disruption to existing users

## 12. Future Enhancements

### 12.1 Potential Improvements
- Parallel build support for multiple configurations
- Incremental builds (only rebuild changed files)
- Build artifact versioning
- Remote build cache (shared across team)
- Build status webhooks/notifications
- Docker containerization of build environment

### 12.2 Long-term Vision
- Fully automated CI/CD pipeline
- Multi-version testing support
- A/B testing of configuration changes
- Performance benchmarking suite
- Configuration validation as a service

## 13. Documentation Updates Required

### 13.1 README.md
- Add build process explanation
- Update installation instructions
- Document new CLI commands
- Add troubleshooting section for build issues

### 13.2 CONTRIBUTING.md
- Explain build system
- Document testing with builds
- Add build debugging guide

### 13.3 API Documentation
- Document BuildManager class
- Document new configuration options
- Add build-related examples

## 14. Appendices

### Appendix A: Build Script Interface

Expected build script behavior:
```bash
#!/bin/bash
# scripts/build.sh

# Exit codes:
# 0 - Success
# 1 - Build failure
# 2 - Missing dependencies
# 3 - Invalid source structure

# Expected output:
# - Creates dist/ directory
# - Copies/processes files from src/
# - Outputs status messages to stdout
# - Errors to stderr
```

### Appendix B: File Structure Mapping

| Old Path | Build Source | Build Output | Test Uses |
|----------|--------------|--------------|-----------|
| `.claude/commands/project-init.md` | `src/claude/commands/project-init.md` | `dist/.claude/commands/project-init.md` | `dist/` |
| `adws/adw_init.py` | `src/adws/adw_init.py` | `dist/.adws/adw_init.py` | `dist/` |

### Appendix C: Sample Build Output

```
$ ./scripts/build.sh
Building standard configurations...
  ✓ Cleaned dist directory
  ✓ Copied src/claude to dist/.claude
  ✓ Copied src/adws to dist/.adws
  ✓ Processed templates
  ✓ Validated output structure
Build complete: dist/
  - dist/.claude/ (7 files)
  - dist/.adws/ (4 files)
```

## 15. Approval and Sign-off

- [ ] Technical Lead Review
- [ ] Testing Team Review
- [ ] Documentation Review
- [ ] Final Approval

---

*End of Specification*