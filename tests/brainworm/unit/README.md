# Unit Tests for Brainworm Event Storage System

This directory contains comprehensive unit tests for the core components of the brainworm Claude Code event storage system.

## Test Structure

### Priority 1: Event Store Tests (`test_event_store.py`)

Comprehensive tests for the `HookEventStore` class covering:

#### Database Operations
- ✅ Database initialization and schema creation
- ✅ Event logging with proper metadata
- ✅ SQLite connection handling and cleanup
- ✅ Database locking and concurrency safety
- ✅ Concurrent database access validation

#### Configuration Management
- ✅ Loading configuration from `.claude/settings.json`
- ✅ Loading configuration from `brainworm-config.toml`
- ✅ Handling missing configuration gracefully
- ✅ Configuration validation and defaults
- ✅ TOML availability handling

#### Event Processing
- ✅ Event schema validation (version 2.0 format)
- ✅ Timestamp accuracy and formatting
- ✅ Metadata extraction and processing
- ✅ Error event handling
- ✅ JSONL backup logging

#### Performance Requirements
- ✅ Sub-100ms execution validation
- ✅ Memory usage monitoring (< 50MB)
- ✅ Database query optimization validation
- ✅ Concurrent access performance

**Test Methods:** 23 comprehensive test methods covering all functionality

### Priority 2: Correlation Manager Tests (`utils/test_correlation_manager.py`)

Comprehensive tests for correlation tracking functionality:

#### Correlation ID Management
- ✅ Correlation ID generation and consistency
- ✅ Session ID propagation across hooks
- ✅ Environment variable priority handling
- ✅ Cross-session correlation independence

#### Timing Analysis
- ✅ Pre/post tool execution correlation
- ✅ Duration calculation accuracy
- ✅ Workflow correlation chains
- ✅ Performance requirements (sub-10ms for 100 operations)

#### File-based Persistence
- ✅ Session correlation storage and retrieval
- ✅ Automatic cleanup of old entries (keep 50 most recent)
- ✅ Error handling for corrupted files
- ✅ Graceful degradation on OS errors

**Test Methods:** 20 comprehensive test methods covering all functionality

### Priority 3: Hook Component Tests

#### Stop Hook Tests (`hooks/test_stop.py`)
- ✅ Hook input parsing (Claude Code standard format)
- ✅ Analytics data capture
- ✅ Session completion tracking
- ✅ Performance requirements (sub-100ms)
- ✅ Error handling and graceful degradation
- ✅ Empty/invalid input handling

#### Pre-Tool Use Hook Tests (`hooks/test_pre_tool_use.py`)
- ✅ Security validation and categorization
- ✅ Dangerous command detection (rm -rf, sudo rm, etc.)
- ✅ Sensitive path validation (.env, secrets/, etc.)
- ✅ Performance prediction and resource analysis
- ✅ JSON response format compliance (continue/block decisions)
- ✅ Analytics integration with correlation tracking

#### Post-Tool Use Hook Tests (`hooks/test_post_tool_use.py`)
- ✅ Impact analysis and development categorization
- ✅ Timing analysis and duration calculation
- ✅ Tool result success/failure detection
- ✅ Correlation tracking between pre/post execution
- ✅ Performance requirements validation
- ✅ Comprehensive analytics integration

**Total Hook Test Methods:** 25+ test methods across all hooks

## Performance Requirements Validation

All tests include performance assertions to ensure:

- **Analytics Processor**: Sub-100ms event logging, sub-50ms statistics calculation
- **Correlation Manager**: Sub-10ms for 100 correlation operations
- **Hook Components**: Sub-100ms total execution time
- **Memory Usage**: Peak memory < 50MB for analytics operations

## Test Features

### Real Data Integration
- Uses actual hook I/O formats from the fixed hook system
- Tests with real Claude Code standard input/output formats
- Validates against actual database schemas and file structures

### Error Scenario Coverage
- Database connection failures
- Corrupted configuration files
- Invalid JSON input handling
- OS-level permission errors
- Concurrent access race conditions

### Mock Integration
- Proper mocking for file system operations
- Database operation mocking where appropriate
- Environment variable mocking
- Stdin/stdout redirection for hook testing

## Running the Tests

### Prerequisites
```bash
# Install test dependencies
uv sync --dev

# Or manually install requirements
pip install -r requirements-test.txt
```

### Run All Unit Tests
```bash
# Using pytest
uv run python -m pytest tests/unit/ -v

# Using the project test runner
./run_unit_tests.sh

# Run with coverage
uv run python -m pytest tests/unit/ --cov=src --cov-report=html
```

### Run Specific Test Suites
```bash
# Event store tests only
uv run python -m pytest tests/unit/test_event_store.py -v

# Correlation manager tests only
uv run python -m pytest tests/unit/utils/test_correlation_manager.py -v

# Hook component tests only
uv run python -m pytest tests/unit/hooks/ -v

# Performance tests only
uv run python -m pytest tests/unit/ -k "performance" -v
```

### Validation Script
```bash
# Quick validation that tests are properly structured
uv run python validate_unit_tests.py
```

## Test Isolation and Speed

- **Fast Execution**: All tests designed to run in < 5 seconds per file
- **Isolated**: No interdependencies between tests
- **Temporary Resources**: Uses tempfile/tempdir for all test data
- **Automatic Cleanup**: Test fixtures clean up resources automatically

## Coverage Goals

Current test coverage targets:

- **Event Store**: 95%+ line coverage
- **Correlation Manager**: 90%+ line coverage
- **Hook Components**: 85%+ line coverage
- **Critical Paths**: 100% coverage for error handling and performance paths

## Integration with CI/CD

These unit tests are designed to run in continuous integration environments:

- No external dependencies (self-contained)
- Deterministic results (no timing-dependent tests)
- Clear pass/fail criteria
- Comprehensive error reporting

## Future Enhancements

Planned improvements:

1. **Property-based testing** for correlation ID generation
2. **Stress testing** with large datasets (10k+ events)
3. **Integration testing** with actual Claude Code hook execution
4. **Performance benchmarking** with automated regression detection

## Contributing

When adding new unit tests:

1. Follow the existing test patterns and naming conventions
2. Include performance assertions for time-critical operations
3. Test both success and failure scenarios
4. Use the existing fixtures and utilities from `conftest.py`
5. Ensure tests are fast (< 1 second per test method)
6. Add comprehensive docstrings explaining what is being tested

## Test Utilities

The tests use several utilities from `tests/conftest.py`:

- `temp_dir`: Temporary directory fixture
- `mock_claude_project`: Claude Code project structure mock
- `temp_db`: SQLite database fixture
- `sample_hook_input/output`: Realistic hook data fixtures
- `performance_baseline`: Performance requirement constants

See `tests/conftest.py` for full documentation of available fixtures.
