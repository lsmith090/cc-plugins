"""
Brainworm Claude Code Analytics Testing Infrastructure

This package contains comprehensive tests for the Brainworm analytics system,
organized by test category for efficient testing workflows.

Test Categories:
- unit: Fast, isolated component tests
- integration: Cross-component interaction tests
- e2e: End-to-end workflow tests
- performance: Benchmarking and performance validation
- security: Security vulnerability testing
- installation: Hook installation and deployment tests
- analytics: Analytics system functionality tests
- config: Configuration system tests

Quick Start:
    # Run all standard tests (unit + integration + e2e)
    ./run_tests.sh

    # Fast development testing
    ./run_unit_tests.sh

    # Performance benchmarking
    ./run_performance_tests.sh

For detailed usage instructions, see tests/README.md
"""

__version__ = "1.1.0"
__author__ = "Brainworm Analytics Team"

# Test configuration constants
TEST_TIMEOUT_SECONDS = 300
PERFORMANCE_BASELINE_PATH = "tests/performance/benchmarks"
FIXTURES_PATH = "tests/fixtures"

# Test markers for categorization
UNIT_MARKER = "unit"
INTEGRATION_MARKER = "integration"
E2E_MARKER = "e2e"
PERFORMANCE_MARKER = "performance"
SECURITY_MARKER = "security"
INSTALLATION_MARKER = "installation"
ANALYTICS_MARKER = "analytics"
CONFIG_MARKER = "config"

# Quick access to common test markers
FAST_MARKERS = [UNIT_MARKER]
SLOW_MARKERS = [E2E_MARKER, PERFORMANCE_MARKER]
DATABASE_MARKERS = [INTEGRATION_MARKER, ANALYTICS_MARKER]
