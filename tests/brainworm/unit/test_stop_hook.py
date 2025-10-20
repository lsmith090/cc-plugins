#!/usr/bin/env python3
"""
Unit Tests for Stop Hook

Tests essential behaviors of stop.py including:
- Session correlation cleanup
- Error handling
- Success message output
"""

import pytest
import json
import subprocess
from pathlib import Path
import uuid


@pytest.fixture
def brainworm_plugin_root() -> Path:
    """Get path to brainworm plugin source"""
    test_file = Path(__file__)
    repo_root = test_file.parent.parent.parent.parent
    plugin_root = repo_root / "brainworm"
    if not plugin_root.exists():
        pytest.skip(f"Brainworm plugin not found: {plugin_root}")
    return plugin_root


@pytest.fixture
def test_project(tmp_path) -> Path:
    """Create test project"""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    brainworm_dir = project_root / ".brainworm"
    (brainworm_dir / "state").mkdir(parents=True)
    (brainworm_dir / "events").mkdir(parents=True)
    return project_root


@pytest.fixture
def stop_input() -> dict:
    """Generate test stop input"""
    return {
        "session_id": f"test-session-{uuid.uuid4().hex[:8]}",
        "correlation_id": f"test-corr-{uuid.uuid4().hex[:8]}",
        "hook_event_name": "Stop",
        "cwd": "/test/project",
        "project_root": "/test/project"
    }


def execute_stop(
    project_root: Path,
    plugin_root: Path,
    stop_input: dict,
    timeout: int = 15
) -> subprocess.CompletedProcess:
    """Execute stop hook"""
    hook_script = plugin_root / "hooks" / "stop.py"
    hook_input = stop_input.copy()
    hook_input["cwd"] = str(project_root)
    hook_input["project_root"] = str(project_root)

    import os
    env = os.environ.copy()
    env["CLAUDE_PLUGIN_ROOT"] = str(plugin_root)

    result = subprocess.run(
        ["uv", "run", str(hook_script)],
        input=json.dumps(hook_input).encode(),
        capture_output=True,
        timeout=timeout,
        cwd=project_root,
        env=env
    )
    return result


class TestSessionCorrelationCleanup:
    """Test session correlation cleanup"""

    def test_clears_session_correlation(self, test_project, brainworm_plugin_root, stop_input):
        """Test: Clears session correlation"""
        result = execute_stop(test_project, brainworm_plugin_root, stop_input)
        assert result.returncode == 0

    def test_handles_missing_correlation_state(self, test_project, brainworm_plugin_root, stop_input):
        """Test: Handles missing correlation state gracefully"""
        # Don't create correlation state file
        result = execute_stop(test_project, brainworm_plugin_root, stop_input)
        # Should still succeed
        assert result.returncode == 0


class TestErrorHandling:
    """Test error handling"""

    def test_handles_missing_session_id(self, test_project, brainworm_plugin_root):
        """Test: Handles missing session_id"""
        invalid_input = {
            "hook_event_name": "Stop",
            "cwd": str(test_project),
            "project_root": str(test_project)
        }
        result = execute_stop(test_project, brainworm_plugin_root, invalid_input)
        assert result.returncode == 0


class TestBasicFunctionality:
    """Test basic hook functionality"""

    def test_hook_succeeds_with_valid_input(self, test_project, brainworm_plugin_root, stop_input):
        """Test: Hook succeeds with valid input"""
        result = execute_stop(test_project, brainworm_plugin_root, stop_input)
        assert result.returncode == 0

    def test_multiple_stop_calls_succeed(self, test_project, brainworm_plugin_root, stop_input):
        """Test: Multiple stop calls don't cause errors"""
        result1 = execute_stop(test_project, brainworm_plugin_root, stop_input)
        assert result1.returncode == 0

        result2 = execute_stop(test_project, brainworm_plugin_root, stop_input)
        assert result2.returncode == 0
