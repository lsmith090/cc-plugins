# Brainworm Claude Code Analytics Testing Infrastructure

Comprehensive testing framework for the Brainworm Claude Code analytics system. This infrastructure supports multiple test categories including unit, integration, end-to-end, performance, and security testing.

## Quick Start

### Run All Tests
```bash
./run_tests.sh all
```

### Run Unit Tests Only (Fast Development Loop)
```bash
./run_tests.sh unit
```

### Run Performance Tests  
```bash
./run_tests.sh performance
```

### Run Integration Tests
```bash
./run_tests.sh integration
```

### Run with Coverage Report
```bash
./run_tests.sh all --coverage
```

## Test Categories

### Unit Tests (`tests/unit/`)
Fast, isolated tests for individual components.

- **Location**: `tests/unit/`
- **Markers**: `@pytest.mark.unit`, `@pytest.mark.fast`
- **Characteristics**: No external dependencies, mocked I/O, < 100ms per test
- **Coverage**: Individual functions, classes, and modules

**Examples**:
```bash
# Run all unit tests
pytest -m unit

# Run specific unit test category
pytest tests/unit/hooks/
pytest tests/unit/utils/

# Run with coverage
pytest -m unit --cov=src --cov-report=html
```

### Integration Tests (`tests/integration/`)
Tests for component interactions and system integration.

- **Location**: `tests/integration/`
- **Markers**: `@pytest.mark.integration`
- **Characteristics**: Real databases, filesystem, cross-component testing
- **Coverage**: Hook system integration, analytics pipeline, database operations

**Examples**:
```bash
# Run integration tests
pytest -m integration

# Run with verbose output
pytest -m integration -v
```

### End-to-End Tests (`tests/e2e/`)
Full system workflow tests simulating real usage scenarios.

- **Location**: `tests/e2e/`
- **Markers**: `@pytest.mark.e2e`, `@pytest.mark.slow`
- **Characteristics**: Complete workflows, real project structures, actual hook execution
- **Coverage**: Complete user journeys, system behavior validation

**Examples**:
```bash
# Run E2E tests (requires --runslow flag)
pytest -m e2e --runslow

# Run specific E2E workflow
pytest tests/e2e/test_complete_analytics_workflow.py
```

### Performance Tests (`tests/performance/`)
Benchmarking and performance validation tests.

- **Location**: `tests/performance/`
- **Markers**: `@pytest.mark.performance`, `@pytest.mark.slow`
- **Characteristics**: Benchmarking, load testing, performance regression detection
- **Tools**: `pytest-benchmark`, memory profiling, timing analysis

**Examples**:
```bash
# Run performance tests with benchmarking
./run_performance_tests.sh

# Compare against baseline
./run_performance_tests.sh --compare-baseline

# Generate performance reports
./run_performance_tests.sh --output-html
```

### Security Tests (`tests/security/`)
Security validation and vulnerability testing.

- **Location**: `tests/security/`
- **Markers**: `@pytest.mark.security`
- **Characteristics**: Input validation, path traversal, injection testing
- **Tools**: `bandit`, `safety`, custom security scanners

### Installation Tests (`tests/installation/`)
Hook installation and deployment validation.

- **Location**: `tests/installation/`
- **Markers**: `@pytest.mark.installation`
- **Characteristics**: Installation process validation, deployment testing
- **Coverage**: Hook installation, configuration validation, system setup

### Analytics Tests (`tests/analytics/`)
Analytics system functionality and data processing tests.

- **Location**: `tests/analytics/`
- **Markers**: `@pytest.mark.analytics`, `@pytest.mark.database`
- **Characteristics**: Data processing, analytics algorithms, reporting
- **Coverage**: Analytics processor, correlation tracking, data harvesting

### Configuration Tests (`tests/config/`)
Configuration system and settings validation.

- **Location**: `tests/config/`
- **Markers**: `@pytest.mark.config`
- **Characteristics**: Configuration parsing, validation, defaults
- **Coverage**: TOML parsing, configuration inheritance, validation rules

## Test Execution Scripts

### `./run_tests.sh` - Complete Test Suite Runner
Comprehensive test runner with extensive configuration options.

**Options**:
- `--unit-only` - Run only unit tests (fast)
- `--integration-only` - Run only integration tests  
- `--e2e-only` - Run only end-to-end tests
- `--performance` - Include performance tests (slow)
- `--security` - Include security tests
- `--no-coverage` - Disable code coverage reporting
- `--no-parallel` - Disable parallel test execution
- `--verbose` - Enable verbose output
- `--fail-fast` - Stop on first failure
- `--clean` - Clean test artifacts before running
- `--install-deps` - Install test dependencies first
- `--report-xml` - Generate XML coverage report
- `--report-json` - Generate JSON test report

**Examples**:
```bash
# Standard test run (unit + integration + e2e)
./run_tests.sh

# Fast development testing
./run_tests.sh --unit-only

# Comprehensive testing including performance
./run_tests.sh --performance

# Debug failing tests
./run_tests.sh --unit-only --no-parallel --verbose --fail-fast

# CI/CD pipeline
./run_tests.sh --clean --install-deps --report-xml
```

### `./run_unit_tests.sh` - Fast Unit Test Runner
Optimized for development workflow with watch mode support.

**Options**:
- `--no-coverage` - Disable code coverage reporting
- `--no-parallel` - Run sequentially for debugging
- `--verbose` - Enable verbose output  
- `--fail-fast` - Stop on first failure
- `--watch` - Continuous testing mode (file watching)
- `--clean` - Clean test artifacts before running

**Examples**:
```bash
# Quick unit test run
./run_unit_tests.sh

# Continuous testing during development
./run_unit_tests.sh --watch

# Debug specific failures
./run_unit_tests.sh --no-parallel --verbose --fail-fast
```

### `./run_performance_tests.sh` - Performance Test Runner
Specialized performance testing with benchmarking and profiling.

**Options**:
- `--verbose` - Enable verbose output with detailed timing
- `--profile` - Enable detailed profiling (memory, CPU)
- `--no-save` - Don't save benchmark results  
- `--compare-baseline` - Compare results against baseline
- `--baseline FILE` - Specify baseline file for comparison
- `--output-json` - Output results in JSON format
- `--output-html` - Generate HTML performance report

**Examples**:
```bash
# Basic performance testing
./run_performance_tests.sh

# Detailed profiling and analysis
./run_performance_tests.sh --verbose --profile

# Performance regression testing
./run_performance_tests.sh --compare-baseline

# Generate performance reports
./run_performance_tests.sh --output-html
```

## Test Configuration

### `pytest.ini`
Main pytest configuration with test discovery, markers, coverage, and logging settings.

**Key Settings**:
- Test discovery patterns
- Marker definitions for categorization
- Coverage reporting configuration
- Parallel execution settings
- Warning filters
- Logging configuration

### `conftest.py`
Shared fixtures and pytest configuration for all test categories.

**Key Fixtures**:
- `temp_dir` - Temporary directory for testing
- `mock_claude_project` - Mock Claude Code project structure
- `installed_hooks_project` - Project with hooks pre-installed
- `temp_db` - Temporary SQLite database
- `analytics_db_with_data` - Database with sample data
- `sample_hook_input/output` - Hook I/O data samples
- `mock_event_store` - Mocked event store
- `performance_baseline` - Performance expectations
- `full_system_setup` - Complete system for integration testing

### `requirements-test.txt`
Complete testing dependency specification including:

**Core Testing**:
- `pytest` and plugins (`pytest-xdist`, `pytest-cov`, `pytest-html`)
- `pytest-mock` for enhanced mocking
- `pytest-asyncio` for async test support

**Performance Testing**:
- `pytest-benchmark` for benchmarking
- `memory-profiler` for memory analysis
- `psutil` for system resource monitoring

**Security Testing**:
- `bandit` for security static analysis
- `safety` for dependency vulnerability scanning
- `semgrep` for advanced static analysis

**Development Tools**:
- Code quality tools (`flake8`, `black`, `isort`, `mypy`)
- Interactive debugging (`ipdb`, `pdbpp`)
- Rich console output (`rich`)

## Test Data and Fixtures

### `tests/fixtures/`
Organized test data and fixtures for comprehensive testing.

**Structure**:
```
fixtures/
├── sample_sessions/          # Real session data samples
│   ├── basic_session.json    # Simple Read/Grep workflow
│   └── complex_session.json  # Multi-tool, compaction workflow
├── test_projects/            # Mock project structures  
│   └── simple_python_project/ # Basic Python project
├── mock_data/               # Mock hook events and data
│   └── hook_events.json     # Sample hook event data
└── configurations/          # Test configuration files
    └── test_brainworm_config.toml # Test configuration
```

**Sample Session Data Format**:
```json
{
  "description": "Basic Claude Code session with file reading",
  "session_id": "sample-session-001",
  "events": [
    {
      "hook_name": "pre_tool_use",
      "tool_name": "Read",
      "tool_input": {"file_path": "/path/to/file.py"},
      "session_id": "sample-session-001",
      "schema_version": "2.0",
      "correlation_id": "corr-001-1",
      "timestamp_ns": 1640995202000000000,
      "workflow_phase": "tool_preparation",
      "project_root": "/project/root",
      "logged_at": "2022-01-01T00:00:02.000000",
      "working_directory": "/working/dir"
    }
  ]
}
```

## Performance Testing

### Benchmarking
Performance tests use `pytest-benchmark` for accurate benchmarking:

```python
def test_hook_execution_performance(benchmark):
    result = benchmark(hook_function, test_input)
    assert result is not None
```

### Performance Baselines
Expected performance characteristics:

- **Hook Execution**: < 100ms per hook
- **Analytics Processing**: < 50ms per event
- **Database Operations**: < 25ms per write
- **Memory Usage**: < 50MB total system impact

### Performance Reports
Generated performance artifacts:

- **Console Output**: Real-time benchmark results
- **JSON Reports**: `tests/performance/reports/benchmark_*.json`
- **HTML Histograms**: `tests/performance/reports/histogram_*.svg`
- **Saved Baselines**: `tests/performance/benchmarks/*.json`

## Continuous Integration

### GitHub Actions Integration
The testing infrastructure supports GitHub Actions with:

- `pytest-github-actions-annotate-failures` for inline annotations
- XML coverage reports for integration
- Parallel test execution across environments
- Performance regression detection

### Test Execution Strategy

**Pull Request Testing**:
```bash
./run_tests.sh --unit-only --integration-only --report-xml
```

**Nightly Testing**:
```bash
./run_tests.sh --performance --security --report-json
```

**Release Testing**:
```bash
./run_tests.sh --clean --install-deps --performance --security
```

## Development Workflow

### TDD Workflow
1. **Write failing test**: Create test for new functionality
2. **Run unit tests**: `./run_unit_tests.sh --fail-fast`
3. **Implement code**: Write minimal implementation
4. **Run tests continuously**: `./run_unit_tests.sh --watch`
5. **Integration testing**: `./run_tests.sh --integration-only`
6. **Performance validation**: `./run_performance_tests.sh`

### Debugging Tests
```bash
# Debug specific test with verbose output
pytest tests/unit/test_specific.py::test_function -v -s

# Drop into debugger on failure
pytest tests/unit/test_specific.py --pdb

# Run single test without parallelization
pytest tests/unit/test_specific.py -n 0 -v -s
```

### Coverage Analysis
```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html

# View coverage report
open tests/coverage/index.html

# Terminal coverage report
pytest --cov=src --cov-report=term-missing
```

## Troubleshooting

### Common Issues

**Import Errors**:
```bash
# Ensure test dependencies are installed
pip install -r requirements-test.txt

# Check Python path in tests
pytest --collect-only
```

**Database Issues**:
```bash
# Clean test artifacts
rm -rf tests/.pytest_cache tests/coverage

# Reset temporary databases
find tests -name "*.db" -delete
```

**Performance Test Failures**:
```bash
# Check system load before running
./run_performance_tests.sh --verbose

# Compare with baseline
./run_performance_tests.sh --compare-baseline --verbose
```

**Parallel Execution Issues**:
```bash
# Run tests sequentially for debugging
pytest -n 0

# Or disable parallel execution
./run_tests.sh --no-parallel
```

### Test Data Issues

**Fixture Loading Problems**:
- Verify fixture files exist in `tests/fixtures/`
- Check JSON syntax in fixture files
- Ensure fixture permissions are correct

**Mock Data Inconsistencies**:
- Update fixtures to match actual hook output format
- Validate sample data against real system behavior
- Check schema versions in mock data

### Environment Issues

**Python Version Compatibility**:
- Tests require Python 3.8+
- Check virtual environment activation
- Verify dependency compatibility

**System Dependencies**:
- SQLite3 for database testing
- Git for repository operations
- System tools for performance monitoring

## Contributing

### Adding New Tests

1. **Choose appropriate category** (unit/integration/e2e/performance)
2. **Use existing fixtures** where possible
3. **Add appropriate markers** (`@pytest.mark.unit`, etc.)
4. **Follow naming conventions** (`test_*.py`, `test_*()`)
5. **Include docstrings** with test purpose and expectations
6. **Update fixtures** if new test data patterns are needed

### Test Quality Guidelines

- **Fast feedback**: Unit tests should run in < 1 second
- **Isolated tests**: No dependencies between test cases
- **Clear assertions**: Descriptive assertion messages
- **Proper cleanup**: Use fixtures for setup/teardown
- **Performance awareness**: Monitor test execution time

### Documentation Updates

When adding new test categories or significant functionality:

1. Update this README.md
2. Add examples to test docstrings
3. Update script help messages
4. Consider adding new fixtures for common patterns
5. Update CI/CD configuration if needed

## Advanced Usage

### Custom Markers
```python
# Add custom markers for specific testing needs
@pytest.mark.regression
@pytest.mark.slow
@pytest.mark.database
def test_complex_scenario():
    pass
```

### Parametrized Testing
```python
@pytest.mark.parametrize("input,expected", [
    ("test1", "result1"),
    ("test2", "result2"),
])
def test_multiple_cases(input, expected):
    assert process(input) == expected
```

### Async Testing
```python
@pytest.mark.asyncio
async def test_async_operation():
    result = await async_function()
    assert result is not None
```

---

**For more information**: See individual test files and the main project documentation in `/CLAUDE.md`.