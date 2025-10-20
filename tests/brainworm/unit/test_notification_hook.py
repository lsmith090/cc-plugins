#!/usr/bin/env python3
"""
Unit Tests for Notification Hook

Tests essential behaviors of notification.py including:
- Notification message extraction
- Logging
- Basic functionality
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
def notification_input() -> dict:
    """Generate test notification input"""
    return {
        "session_id": f"test-session-{uuid.uuid4().hex[:8]}",
        "correlation_id": f"test-corr-{uuid.uuid4().hex[:8]}",
        "hook_event_name": "Notification",
        "message": "Test notification message",
        "cwd": "/test/project",
        "project_root": "/test/project"
    }


def execute_notification(
    project_root: Path,
    plugin_root: Path,
    notification_input: dict,
    timeout: int = 15
) -> subprocess.CompletedProcess:
    """Execute notification hook"""
    hook_script = plugin_root / "hooks" / "notification.py"
    hook_input = notification_input.copy()
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


class TestNotificationProcessing:
    """Test notification message processing"""

    def test_processes_notification_message(self, test_project, brainworm_plugin_root, notification_input):
        """Test: Processes notification message"""
        notification_input["message"] = "Important notification"
        result = execute_notification(test_project, brainworm_plugin_root, notification_input)
        assert result.returncode == 0

    def test_handles_empty_message(self, test_project, brainworm_plugin_root, notification_input):
        """Test: Handles empty message"""
        notification_input["message"] = ""
        result = execute_notification(test_project, brainworm_plugin_root, notification_input)
        assert result.returncode == 0

    def test_handles_missing_message(self, test_project, brainworm_plugin_root, notification_input):
        """Test: Handles missing message field"""
        del notification_input["message"]
        result = execute_notification(test_project, brainworm_plugin_root, notification_input)
        assert result.returncode == 0


class TestVariousMessages:
    """Test various notification message types"""

    @pytest.mark.parametrize("message", [
        "Simple message",
        "Message with special chars: @#$%",
        "Very long message " * 50,
        "Multi\nline\nmessage",
    ])
    def test_handles_various_messages(self, test_project, brainworm_plugin_root, notification_input, message):
        """Test: Handles various message formats"""
        notification_input["message"] = message
        result = execute_notification(test_project, brainworm_plugin_root, notification_input)
        assert result.returncode == 0


class TestBasicFunctionality:
    """Test basic hook functionality"""

    def test_hook_succeeds_with_valid_input(self, test_project, brainworm_plugin_root, notification_input):
        """Test: Hook succeeds with valid input"""
        result = execute_notification(test_project, brainworm_plugin_root, notification_input)
        assert result.returncode == 0

    def test_multiple_notifications_succeed(self, test_project, brainworm_plugin_root, notification_input):
        """Test: Multiple notifications can be processed"""
        result1 = execute_notification(test_project, brainworm_plugin_root, notification_input)
        assert result1.returncode == 0

        notification_input["message"] = "Second notification"
        result2 = execute_notification(test_project, brainworm_plugin_root, notification_input)
        assert result2.returncode == 0
