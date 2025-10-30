---
allowed-tools: Bash(uv:*,cd:*)
description: Execute plugin test suites with proper uv configuration
argument-hint: "[plugin-name] [suite]"
---

# Test Plugin

Executes test suites for plugins using uv for dependency management.

**Usage:**
```bash
/test-plugin                          # Test all plugins
/test-plugin <plugin-name>            # Test specific plugin
/test-plugin <plugin-name> unit       # Test specific suite
/test-plugin <plugin-name> --cov      # With coverage report
```

**Test Suites:**

- **unit** - Fast, isolated component tests (< 100ms per test)
- **integration** - Component interaction tests with real databases/filesystem
- **e2e** - End-to-end workflow validation (requires --runslow)
- **security** - Security validation tests
- **performance** - Performance regression checks

**Examples:**

Test all brainworm tests:
```bash
/test-plugin brainworm
```

Test specific suite:
```bash
/test-plugin brainworm unit
/test-plugin brainworm integration
```

Run E2E tests (slow):
```bash
/test-plugin brainworm e2e --runslow
```

With coverage report:
```bash
/test-plugin brainworm --cov
```

Verbose output:
```bash
/test-plugin brainworm -v
```

**What it does:**

1. **Detects plugin** - Finds test directory at tests/<plugin-name>/
2. **Validates structure** - Checks for conftest.py and test files
3. **Runs with uv** - Uses `uv run pytest` for dependency management
4. **Reports results** - Shows test outcomes, failures, coverage
5. **Explains failures** - Provides context for test failures

**Test Organization:**

Tests live at repository root (NOT in plugin directory):
```
tests/
  <plugin-name>/
    unit/           # Fast unit tests
    integration/    # Integration tests
    e2e/            # End-to-end tests
    conftest.py     # Shared fixtures
```

**Coverage Reports:**

With `--cov` flag:
- Shows line coverage by module
- Identifies untested code
- Reports missing coverage

**Common Commands:**

```bash
# Quick validation
/test-plugin brainworm unit

# Full test run
/test-plugin brainworm

# Coverage analysis
/test-plugin brainworm --cov --cov-report=term-missing

# Specific test file
uv run pytest tests/brainworm/unit/test_specific.py

# Debug single test
uv run pytest tests/brainworm/unit/test_specific.py::test_name -v
```

**Why uv run?**

Using `uv run pytest` ensures:
- Correct dependencies from pyproject.toml
- Plugin package is built correctly
- Isolated test environment
- Consistent behavior across machines

**Test Markers:**

Tests use pytest markers for organization:
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Slow tests (require --runslow)

**Interpreting Results:**

- **PASSED** - Test succeeded
- **FAILED** - Test failed (shows assertion details)
- **SKIPPED** - Test skipped (conditional or marked)
- **ERROR** - Test setup/teardown error

**Next Steps After Failures:**

1. Read failure output carefully
2. Check test file for expected behavior
3. Run single test with `-v` for details
4. Check relevant plugin code
5. Fix issue and re-run tests
