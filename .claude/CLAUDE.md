## ⚠️ IMPORTANT: Testing Framework Scope and Boundaries

### Two Distinct Codebases

This project involves TWO separate codebases with different rules:

#### 1. **adws-testing** (THIS repository: `~/ai/adws-testing`)

**Location:** `/Users/william/ai/adws-testing`

**Purpose:** Testing framework for validating ADWs (AI Developer Workflows) and slash commands

**Modification Policy:** ✅ **FREELY MODIFIABLE**

You CAN and SHOULD:
- ✅ **FIX** bugs in the testing framework
- ✅ **BUILD** new test cases and checks
- ✅ **UPDATE** test runners and utilities
- ✅ **IMPROVE** test coverage and validation logic
- ✅ **ADD** new features to the testing framework
- ✅ **REFACTOR** testing code for better maintainability
- ✅ **MODIFY** configuration, checks, and test specifications

This is OUR code - we maintain it, improve it, and fix it as needed.

---

#### 2. **standard-configuration** (Code Under Test: `~/ai/standard-configuration`)

**Location:** `/Users/william/ai/standard-configuration`

**Purpose:** The actual ADWs, slash commands, and agent definitions being tested

**Modification Policy:** ❌ **READ-ONLY FOR TESTING**

You must NOT:
- ❌ **FIX** bugs in ADWs or slash commands
- ❌ **MODIFY** any files in standard-configuration
- ❌ **UPDATE** slash command definitions
- ❌ **CHANGE** agent configurations
- ❌ **ADD** missing slash commands
- ❌ **IMPLEMENT** features in the code being tested

You CAN:
- ✅ **READ** files for testing purposes
- ✅ **EXECUTE** commands in isolated test workspaces
- ✅ **ANALYZE** behavior and outputs
- ✅ **REPORT** bugs and issues found

---

### Reporting Issues in Code Under Test

When tests fail due to bugs in **standard-configuration**, the framework should:

1. Document the failure clearly in test results
2. Provide detailed error messages and logs
3. Create reproducible test cases
4. Report issues to maintainers (do NOT fix them)

**Example:**
- ❌ Test finds `/init-frontend` command missing → Report it, don't create it
- ✅ Test framework bug in `runner.py` → Fix it immediately

---

### Quick Reference

| What | Location | Can Modify? |
|------|----------|-------------|
| Test framework code | `~/ai/adws-testing/src/` | ✅ YES |
| Test cases | `~/ai/adws-testing/tests/` | ✅ YES |
| Check definitions | `~/ai/adws-testing/src/checks/` | ✅ YES |
| Test specs | `~/ai/adws-testing/specs/` | ✅ YES |
| Configuration | `~/ai/adws-testing/config.yaml` | ✅ YES |
| ADWs (scripts) | `~/ai/standard-configuration/.adws/` | ❌ NO |
| Slash commands | `~/ai/standard-configuration/.claude/commands/` | ❌ NO |
| Agents | `~/ai/standard-configuration/.claude/agents/` | ❌ NO |
| Build output | `~/ai/standard-configuration/dist/` | ❌ NO (read-only) |

---

### The Rule

**If it's in `~/ai/adws-testing` → FIX IT**

**If it's in `~/ai/standard-configuration` → REPORT IT**
