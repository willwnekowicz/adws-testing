## ⚠️ IMPORTANT: Testing Framework Scope

**This is a TESTING framework only. It must NOT modify the code it is testing.**

### Strict Boundaries

This framework has READ access to the standard-configuration repository for testing purposes, but it must:

- ✅ **TEST** the code and report results
- ✅ **VALIDATE** that commands work as expected
- ✅ **REPORT** failures and issues found
- ✅ **DOCUMENT** test results and findings

It must NOT:

- ❌ **FIX** bugs in the code being tested
- ❌ **MODIFY** the standard-configuration repository
- ❌ **UPDATE** slash commands or agent definitions
- ❌ **CHANGE** any code outside the testing framework itself

### Reporting Issues

When tests fail, the framework should:
1. Document the failure clearly in test results
2. Provide detailed error messages and logs
3. Create reproducible test cases
4. Report issues to maintainers (do NOT fix them)

If you discover a bug in the code being tested, report it - don't fix it. The testing framework's job is to find problems, not solve them.
