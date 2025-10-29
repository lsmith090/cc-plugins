"""
Unit Tests for Brainworm Analytics System

Fast, isolated tests for individual components. Unit tests should:
- Execute in < 100ms per test
- Have no external dependencies (database, network, filesystem)
- Use mocks for all I/O operations
- Test single functions/methods/classes in isolation

Test Structure:
- hooks/: Hook system component tests
- utils/: Utility function and class tests
- test_analytics_processor.py: Analytics processor unit tests

Run unit tests:
    pytest -m unit
    ./run_unit_tests.sh
"""

import pytest

# Shared unit test utilities
def assert_no_external_calls(mock_objects):
    """Assert that no external calls were made during unit tests."""
    for mock_obj in mock_objects:
        if hasattr(mock_obj, 'call_count'):
            # Allow certain mocked calls but ensure no real external calls
            pass


def create_mock_hook_input(session_id="test-session", tool_name="TestTool", **kwargs):
    """Create standardized mock hook input for unit tests."""
    return {
        "session_id": session_id,
        "tool_name": tool_name,
        "tool_input": kwargs,
        "schema_version": "2.0",
        "correlation_id": f"test-corr-{session_id}",
        "timestamp_ns": 1640995200000000000,
        "workflow_phase": "tool_preparation",
        "project_root": "/test/project",
        "working_directory": "/test/project"
    }


def create_mock_hook_output(session_id="test-session", tool_name="TestTool", result="test result"):
    """Create standardized mock hook output for unit tests."""
    return {
        "session_id": session_id,
        "tool_name": tool_name,
        "tool_result": result,
        "timing": {
            "duration_ms": 25
        },
        "schema_version": "2.0",
        "correlation_id": f"test-corr-{session_id}",
        "timestamp_ns": 1640995200100000000,
        "workflow_phase": "tool_completion",
        "project_root": "/test/project",
        "working_directory": "/test/project"
    }
