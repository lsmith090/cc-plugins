"""
Pytest configuration and fixtures for Brainworm Claude Code Analytics System.

This module provides shared fixtures, configuration, and utilities for testing
the brainworm analytics system across all test categories.
"""

import os
import sys
import json
import sqlite3
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Generator, Optional
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

import pytest


# Python path is configured in pyproject.toml via pythonpath setting
# brainworm package is available via hatchling build configuration


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Performance benchmarking is controlled by command line option
    # Do not force benchmark_only mode unless explicitly requested
    
    # Create test output directories
    test_dir = Path(__file__).parent
    (test_dir / "coverage").mkdir(exist_ok=True)
    (test_dir / "performance" / "benchmarks").mkdir(parents=True, exist_ok=True)
    (test_dir / "reports").mkdir(exist_ok=True)


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on location."""
    for item in items:
        # Add markers based on test file location
        test_path = Path(item.fspath)
        relative_path = test_path.relative_to(Path(__file__).parent)
        
        # Auto-mark tests based on directory
        if "unit" in relative_path.parts:
            item.add_marker(pytest.mark.unit)
            item.add_marker(pytest.mark.fast)
        elif "integration" in relative_path.parts:
            item.add_marker(pytest.mark.integration)
        elif "e2e" in relative_path.parts:
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)
        elif "performance" in relative_path.parts:
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
        elif "security" in relative_path.parts:
            item.add_marker(pytest.mark.security)
        elif "installation" in relative_path.parts:
            item.add_marker(pytest.mark.installation)
        elif "analytics" in relative_path.parts:
            item.add_marker(pytest.mark.analytics)
            item.add_marker(pytest.mark.database)
        elif "config" in relative_path.parts:
            item.add_marker(pytest.mark.config)


# ============================================================================
# DIRECTORY AND FILESYSTEM FIXTURES
# ============================================================================

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def brainworm_dir(project_root) -> Path:
    """Get the brainworm plugin directory."""
    return project_root / "brainworm"


@pytest.fixture
def fixtures_dir() -> Path:
    """Get the fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def mock_claude_project(temp_dir) -> Path:
    """Create a mock Claude Code project structure."""
    project_dir = temp_dir / "mock_project"
    project_dir.mkdir()
    
    # Create .claude directory structure
    claude_dir = project_dir / ".claude"
    claude_dir.mkdir()
    
    (claude_dir / "hooks").mkdir()
    (claude_dir / "analytics").mkdir()
    (claude_dir / "analytics" / "logs").mkdir()
    (claude_dir / "logs").mkdir()
    
    # Create basic project files
    (project_dir / "README.md").write_text("# Mock Project\n")
    (project_dir / "main.py").write_text("print('Hello World')\n")
    
    return project_dir


@pytest.fixture
def installed_hooks_project(mock_claude_project, brainworm_dir) -> Path:
    """Create a project with hooks already installed."""
    project_dir = mock_claude_project
    templates_dir = brainworm_dir / "hooks"
    hooks_dir = project_dir / ".claude" / "hooks"
    
    # Copy hook templates to project
    hook_files = [
        "stop.py", "pre_tool_use.py", "post_tool_use.py", 
        "session_start.py", "user_prompt_submit.py", "pre_compact.py",
        "notification.py", "subagent_stop.py", "analytics_processor.py",
        "view_analytics.py", "settings.json"
    ]
    
    for hook_file in hook_files:
        source = templates_dir / hook_file
        if source.exists():
            shutil.copy2(source, hooks_dir / hook_file)
    
    return project_dir


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture
def temp_db(temp_dir) -> Path:
    """Create a temporary SQLite database for testing."""
    db_path = temp_dir / "test.db"
    
    # Create basic analytics schema
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hook_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp_ns INTEGER NOT NULL,
            session_id TEXT NOT NULL,
            correlation_id TEXT,
            hook_name TEXT NOT NULL,
            event_data TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_session_id ON hook_events(session_id);
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_timestamp ON hook_events(timestamp_ns);
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_hook_name ON hook_events(hook_name);
    """)
    conn.close()
    
    return db_path


@pytest.fixture
def analytics_db_with_data(temp_db) -> Path:
    """Create a database with sample analytics data."""
    conn = sqlite3.connect(temp_db)
    
    # Insert sample data
    sample_events = [
        {
            "timestamp_ns": 1640995200000000000,  # 2022-01-01
            "session_id": "test-session-1",
            "correlation_id": "corr-1",
            "hook_name": "pre_tool_use",
            "event_data": json.dumps({
                "tool_name": "Read",
                "tool_input": {"file_path": "/test/file.py"}
            })
        },
        {
            "timestamp_ns": 1640995201000000000,
            "session_id": "test-session-1",
            "correlation_id": "corr-1",
            "hook_name": "post_tool_use",
            "event_data": json.dumps({
                "tool_name": "Read",
                "tool_result": "file contents"
            })
        }
    ]
    
    for event in sample_events:
        conn.execute(
            "INSERT INTO hook_events (timestamp_ns, session_id, correlation_id, hook_name, event_data) VALUES (?, ?, ?, ?, ?)",
            (event["timestamp_ns"], event["session_id"], event["correlation_id"], event["hook_name"], event["event_data"])
        )
    
    conn.commit()
    conn.close()
    return temp_db


# ============================================================================
# MOCK DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_hook_input() -> Dict[str, Any]:
    """Sample hook input data."""
    return {
        "session_id": "test-session-123",
        "tool_name": "Read",
        "tool_input": {
            "file_path": "/Users/test/project/main.py",
            "offset": 1,
            "limit": 100
        }
    }


@pytest.fixture
def sample_hook_output() -> Dict[str, Any]:
    """Sample hook output data."""
    return {
        "session_id": "test-session-123",
        "tool_name": "Read",
        "tool_result": "def main():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    main()",
        "timing": {
            "start_time": "1970-01-01T00:00:00.000Z",
            "end_time": "1970-01-01T00:00:00.050Z",
            "duration_ms": 50
        }
    }


@pytest.fixture
def sample_session_data() -> List[Dict[str, Any]]:
    """Sample session with multiple events."""
    session_id = "test-session-456"
    correlation_id = "test-correlation-456"
    
    return [
        {
            "hook_name": "session_start",
            "session_id": session_id,
            "timestamp_ns": 1640995200000000000,
            "event_data": {"started_at": "2022-01-01T00:00:00Z"}
        },
        {
            "hook_name": "pre_tool_use",
            "session_id": session_id,
            "correlation_id": correlation_id,
            "timestamp_ns": 1640995201000000000,
            "event_data": {
                "tool_name": "Grep",
                "tool_input": {"pattern": "def main", "path": "/project"}
            }
        },
        {
            "hook_name": "post_tool_use",
            "session_id": session_id,
            "correlation_id": correlation_id,
            "timestamp_ns": 1640995202000000000,
            "event_data": {
                "tool_name": "Grep",
                "tool_result": "Found 3 matches",
                "timing": {"duration_ms": 45}
            }
        },
        {
            "hook_name": "stop",
            "session_id": session_id,
            "timestamp_ns": 1640995300000000000,
            "event_data": {"stopped_at": "2022-01-01T00:01:40Z"}
        }
    ]


@pytest.fixture
def mock_config_data() -> Dict[str, Any]:
    """Mock configuration data."""
    return {
        "sources": [
            {
                "name": "test-project",
                "type": "local",
                "path": "/test/project",
                "enabled": True
            }
        ],
        "harvesting": {
            "schedule": "*/15 * * * *",
            "enabled": True
        },
        "analytics": {
            "retention_days": 30,
            "batch_size": 1000
        }
    }


# ============================================================================
# HOOK SYSTEM FIXTURES
# ============================================================================

@pytest.fixture
def mock_analytics_processor():
    """Mock analytics processor."""
    processor = Mock()
    processor.process_event.return_value = True
    processor.get_stats.return_value = {
        "total_events": 100,
        "sessions": 10,
        "avg_session_duration": 300
    }
    return processor


@pytest.fixture
def mock_hook_environment(monkeypatch, temp_dir):
    """Set up mock environment for hook testing."""
    # Mock environment variables
    monkeypatch.setenv("CLAUDE_PROJECT_ROOT", str(temp_dir))
    
    # Mock stdin for hook input
    mock_stdin = Mock()
    monkeypatch.setattr("sys.stdin", mock_stdin)
    
    # Mock datetime for consistent timestamps
    fixed_time = datetime(2024, 1, 1, 12, 0, 0)
    with patch("datetime.datetime") as mock_datetime:
        mock_datetime.now.return_value = fixed_time
        mock_datetime.utcnow.return_value = fixed_time
        yield {
            "project_root": temp_dir,
            "stdin": mock_stdin,
            "fixed_time": fixed_time
        }


# ============================================================================
# PERFORMANCE FIXTURES
# ============================================================================

@pytest.fixture
def performance_baseline():
    """Performance baseline expectations."""
    return {
        "max_hook_execution_ms": 100,
        "max_analytics_processing_ms": 50,
        "max_database_write_ms": 25,
        "max_memory_usage_mb": 50
    }


@pytest.fixture
def benchmark_data_sizes():
    """Different data sizes for performance testing."""
    return {
        "small": 10,
        "medium": 100,
        "large": 1000,
        "xlarge": 10000
    }


# ============================================================================
# INTEGRATION TEST FIXTURES
# ============================================================================

@pytest.fixture
def full_system_setup(installed_hooks_project, temp_db):
    """Full system setup for integration testing."""
    project_dir = installed_hooks_project
    
    # Configure analytics database path
    analytics_dir = project_dir / ".claude" / "analytics"
    db_path = analytics_dir / "hooks.db"
    
    # Copy test database
    shutil.copy2(temp_db, db_path)
    
    return {
        "project_dir": project_dir,
        "db_path": db_path,
        "hooks_dir": project_dir / ".claude" / "hooks",
        "analytics_dir": analytics_dir
    }


# ============================================================================
# UTILITIES
# ============================================================================

@pytest.fixture
def assert_hook_output():
    """Utility for asserting hook output format."""
    def _assert_hook_output(output: str, expected_fields: List[str] = None):
        """Assert that hook output has expected format."""
        if expected_fields is None:
            expected_fields = ["timestamp_ns", "session_id", "hook_name"]
        
        try:
            data = json.loads(output)
            for field in expected_fields:
                assert field in data, f"Missing required field: {field}"
            return data
        except json.JSONDecodeError as e:
            pytest.fail(f"Hook output is not valid JSON: {e}")
    
    return _assert_hook_output


@pytest.fixture
def create_test_session():
    """Utility for creating test session data."""
    def _create_session(session_id: str, num_events: int = 5) -> List[Dict]:
        """Create a test session with specified number of events."""
        events = []
        base_time = 1640995200000000000  # 2022-01-01
        
        for i in range(num_events):
            events.append({
                "timestamp_ns": base_time + (i * 1000000000),  # 1 second apart
                "session_id": session_id,
                "correlation_id": f"corr-{session_id}-{i}",
                "hook_name": f"test_hook_{i % 3}",  # Rotate through hook names
                "event_data": json.dumps({
                    "event_index": i,
                    "data": f"test data {i}"
                })
            })
        
        return events
    
    return _create_session


# ============================================================================
# CLEANUP
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Automatically cleanup test files after each test."""
    yield
    
    # Cleanup any temporary files in current directory
    test_files = [
        "test.db", "test.log", "test_output.json",
        ".test_cache", "pytest_cache"
    ]
    
    for filename in test_files:
        if os.path.exists(filename):
            if os.path.isdir(filename):
                shutil.rmtree(filename, ignore_errors=True)
            else:
                os.unlink(filename)


# ============================================================================
# PYTEST MARKERS REGISTRATION
# ============================================================================

# Note: pytest_benchmark and pytest_mock are optional dependencies
# Tests will run without them, but some performance benchmarking features may be unavailable


def pytest_runtest_setup(item):
    """Setup for individual test runs."""
    # Skip slow tests unless specifically requested
    if "slow" in item.keywords and not item.config.getoption("--runslow", default=False):
        pytest.skip("slow test skipped, use --runslow to run")


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--runslow", action="store_true", default=False,
        help="run slow tests"
    )
    parser.addoption(
        "--performance-only", action="store_true", default=False,
        help="run only performance tests"
    )
    parser.addoption(
        "--integration-db", action="store", default=None,
        help="path to integration test database"
    )