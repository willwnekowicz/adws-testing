# Test Specification: init-cloudflare

**Date**: 2025-10-20
**Test Type**: Slash Command Test (Unit Test)
**Command**: `/init-cloudflare`
**Purpose**: Validate that the init-cloudflare slash command creates complete Cloudflare Workers infrastructure

## Summary

The `/init-cloudflare` command creates a comprehensive Cloudflare Workers setup including:
- Worker code with security features
- Wrangler configurations for production and development
- D1 database migrations and seeds
- API endpoint templates
- Durable Objects examples
- GitHub Actions deployment workflows
- Complete documentation

## Test Run Results

**Run ID**: 20251020_1251_565c7852
**Model**: claude-sonnet-4-5
**Duration**: 342.5 seconds (~5.7 minutes)
**Status**: PASSED (all functional checks, exceeded time limit)

## Files Created by init-cloudflare

### Worker Code
1. **`apps/server/worker/index.js`** - Main worker entry point
   - Request ID generation for tracing
   - Security path blocking (50+ patterns)
   - CORS handling
   - API routing with D1 integration
   - Static asset serving with SPA fallback
   - Comprehensive error handling and logging

### Configuration Files
2. **`apps/server/wrangler.toml`** - Production configuration
   - Worker name and main entry point
   - D1 database binding (placeholder database_id)
   - Durable Objects configuration (commented)
   - Observability settings
   - Build and asset configuration

3. **`apps/server/wrangler-dev.toml`** - Development configuration
   - Similar structure to production config
   - Separate development database binding

4. **`apps/server/package.json`** - NPM package configuration
   - Dependencies: `@cloudflare/kv-asset-handler`
   - DevDependencies: `wrangler`
   - Scripts:
     - `dev` - Local development
     - `deploy:staging` - Deploy to staging
     - `deploy:production` - Deploy to production
     - `migrate:dev` / `migrate:prod` - Database migrations
     - `seed:dev` - Seed development database
     - `tail` - View logs
     - `db:query:dev` / `db:query:prod` - Query databases

### Database Files
5. **`apps/server/migrations/0001_initial_setup.sql`** - Initial database schema
   - `example_table` with proper indexing
   - `example_categories` lookup table
   - `example_table_categories` junction table (many-to-many)
   - Best practices comments
   - Foreign key constraints

6. **`apps/server/seeds/example-seed.sql`** - Example seed data
   - Sample data for testing

### Example Code
7. **`apps/server/api/example.js`** - API endpoint template
   - CRUD operation examples
   - D1 database query patterns

8. **`apps/server/durable-objects/example-counter.js`** - Durable Object example
   - Counter implementation with alarms

### CI/CD Workflows
9. **`.github/workflows/deploy-staging.yml`** - Staging deployment
   - Triggers on push to `staging` branch
   - Node.js 20 setup
   - Dependency installation
   - D1 migrations
   - Worker deployment
   - Uses secrets: CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID

10. **`.github/workflows/deploy-production.yml`** - Production deployment
    - Triggers on push to `main` branch
    - Similar structure to staging
    - Uses production database and config

### Documentation
11. **`apps/server/CLOUDFLARE_SETUP.md`** - Complete setup guide
    - Prerequisites list
    - Wrangler CLI installation
    - Authentication steps
    - D1 database creation
    - Configuration updates
    - Migration instructions
    - GitHub Actions setup
    - Local development guide

12. **`apps/server/README.md`** - Server documentation
    - Architecture overview
    - File structure explanation
    - Development instructions
    - Deployment guide

## Proposed Test Checks

### Section 1: File Existence Checks
These validate that all expected files are created:

1. **`worker_exists`** - Check `apps/server/worker/index.js` exists
2. **`wrangler_prod_exists`** - Check `apps/server/wrangler.toml` exists
3. **`wrangler_dev_exists`** - Check `apps/server/wrangler-dev.toml` exists
4. **`package_json_exists`** - Check `apps/server/package.json` exists
5. **`migration_exists`** - Check `apps/server/migrations/0001_initial_setup.sql` exists
6. **`seed_exists`** - Check `apps/server/seeds/example-seed.sql` exists
7. **`api_example_exists`** - Check `apps/server/api/example.js` exists
8. **`durable_object_exists`** - Check `apps/server/durable-objects/example-counter.js` exists
9. **`gh_workflow_staging_exists`** - Check `.github/workflows/deploy-staging.yml` exists
10. **`gh_workflow_prod_exists`** - Check `.github/workflows/deploy-production.yml` exists
11. **`setup_guide_exists`** - Check `apps/server/CLOUDFLARE_SETUP.md` exists
12. **`server_readme_exists`** - Check `apps/server/README.md` exists

### Section 2: Worker Code Validation
These validate the worker implementation has key features:

13. **`worker_has_security`** - Check worker contains security features
    - Contains: `shouldBlockPath`, `blockedPatterns`, `.env`, `.git`

14. **`worker_has_cors`** - Check worker has CORS handling
    - Contains: `handleOptions`, `Access-Control-Allow-Origin`

15. **`worker_has_request_id`** - Check worker has request ID tracking
    - Contains: `generateRequestId`, `X-Request-Id`, `crypto.randomUUID`

16. **`worker_has_api_routing`** - Check worker has API routing
    - Contains: `handleApiRequest`, `/api/`, `env.DB`

17. **`worker_has_static_assets`** - Check worker serves static assets
    - Contains: `getAssetFromKV`, `handleStaticAsset`

### Section 3: Configuration Validation
These validate configuration files are properly structured:

18. **`wrangler_prod_configured`** - Check production wrangler config
    - Contains: `name =`, `main =`, `d1_databases`, `database_id`

19. **`wrangler_dev_configured`** - Check development wrangler config
    - Contains: `name =`, `main =`, `d1_databases`, `development-db`

20. **`package_json_has_scripts`** - Check package.json has required scripts
    - Contains: `"dev"`, `"deploy:staging"`, `"deploy:production"`, `"migrate:dev"`, `"migrate:prod"`

21. **`package_json_has_dependencies`** - Check package.json dependencies
    - Contains: `@cloudflare/kv-asset-handler`, `wrangler`

### Section 4: Database Schema Validation
These validate database files are complete:

22. **`migration_has_tables`** - Check migration creates tables
    - Contains: `CREATE TABLE`, `example_table`, `example_categories`

23. **`migration_has_indexes`** - Check migration creates indexes
    - Contains: `CREATE INDEX`, `idx_example_status`, `idx_example_created`

24. **`migration_has_foreign_keys`** - Check migration has foreign keys
    - Contains: `FOREIGN KEY`, `REFERENCES`, `ON DELETE CASCADE`

25. **`migration_best_practices`** - Check migration follows best practices
    - Contains: `IF NOT EXISTS`, `created_at`, `updated_at`, `unixepoch()`

### Section 5: CI/CD Workflow Validation
These validate GitHub Actions workflows are properly configured:

26. **`staging_workflow_configured`** - Check staging workflow
    - Contains: `on:`, `push:`, `branches:`, `staging`, `wrangler deploy`

27. **`staging_workflow_has_migrations`** - Check staging runs migrations
    - Contains: `d1 migrations apply`, `development-db`

28. **`staging_workflow_has_secrets`** - Check staging uses secrets
    - Contains: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`

29. **`production_workflow_configured`** - Check production workflow
    - Contains: `on:`, `push:`, `branches:`, `main`, `wrangler deploy`

30. **`production_workflow_has_migrations`** - Check production runs migrations
    - Contains: `d1 migrations apply`, `production-db`

### Section 6: Documentation Validation
These validate documentation is comprehensive:

31. **`setup_guide_complete`** - Check setup guide is comprehensive
    - Contains: `Prerequisites`, `Wrangler`, `D1 Databases`, `Migrations`, `GitHub Actions`

32. **`setup_guide_has_commands`** - Check setup guide has required commands
    - Contains: `wrangler login`, `d1 create`, `wrangler deploy`

33. **`server_readme_has_architecture`** - Check server README documents architecture
    - Contains: `Architecture`, `Worker`, `D1`, `Durable Objects`

### Section 7: Example Code Validation
These validate example code is included:

34. **`api_example_has_crud`** - Check API example has CRUD operations
    - Contains: `GET`, `POST`, `PUT`, `DELETE`, or equivalent patterns

35. **`durable_object_example_valid`** - Check Durable Object example
    - Contains: `class`, `fetch`, `alarm`, or similar patterns

### Section 8: Integration Checks
These validate that components work together:

36. **`worker_references_api`** - Check worker references API handlers
    - Worker imports or references API modules

37. **`wrangler_matches_worker`** - Check wrangler config matches worker location
    - Wrangler `main` path points to correct worker file

38. **`package_scripts_match_configs`** - Check package scripts use correct configs
    - Deploy scripts reference correct wrangler config files

### Section 9: Git Integration
These validate changes are committed:

39. **`changes_committed`** - Check all files are committed to git
    - No untracked files in `apps/server/` or `.github/workflows/`

40. **`commit_on_staging`** - Check changes are on staging branch
    - Current branch is `staging`
    - Latest commit includes cloudflare changes

### Section 10: Composite Check
This validates overall success:

41. **`init_cloudflare_complete`** - Composite check combining:
    - Worker exists and has security features
    - Configuration files exist and are valid
    - Database migrations exist
    - GitHub workflows exist
    - Documentation exists
    - All changes committed to staging branch

## Expected Outcomes

### Success Criteria
All checks should pass, validating that:
- ✅ Complete Cloudflare Worker infrastructure is created
- ✅ Security-first worker with path blocking and CORS
- ✅ Production and development configurations
- ✅ Database migrations with best practices
- ✅ CI/CD workflows for automated deployment
- ✅ Comprehensive documentation
- ✅ Example code for API and Durable Objects
- ✅ All changes committed to staging branch

### Known Issues
- **Execution Time**: Command takes ~5.7 minutes (exceeds 2-minute limit)
  - This is expected as it involves multiple Claude commands
  - May need separate time limit for init-cloudflare

## Test Implementation Notes

1. **Create Test File**: `tests/test_init_cloudflare.py`
2. **Use Existing Patterns**: Follow structure from `test_init_git.py`
3. **Check Factory Function**: Create `get_init_cloudflare_checks()`
4. **Register in CLI**: Add to `cli.py` test choices
5. **Time Limit**: Consider 10-minute timeout for this command

## Next Steps

1. Create `tests/test_init_cloudflare.py` with all 41 checks
2. Add check implementations using existing check classes:
   - `FileExistsCheck` for file existence
   - `FileContentCheck` for content validation
   - `GitBranchCheck` for git state
   - `CompositeCheck` for overall validation
3. Register test in `cli.py`
4. Run test: `python cli.py test init-cloudflare --model sonnet`
5. Validate all checks pass

## Reference Files

- Test workspace: `runs/20251020_1251_565c7852/workspace/`
- Test output: `runs/20251020_1251_565c7852/outputs/adw-init/stdout.txt`
- ADW script: `.adws/adw_init.py` (Phase 3 executes init-cloudflare)
