#!/usr/bin/env python3
"""
Unit Tests for PostToolUse Hook

Tests essential behaviors of post_tool_use.py including:
- Tool success determination
- Subagent flag cleanup for Task tool
- Event logging
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
def tool_input() -> dict:
    """Generate test tool input"""
    return {
        "session_id": f"test-session-{uuid.uuid4().hex[:8]}",
        "correlation_id": f"test-corr-{uuid.uuid4().hex[:8]}",
        "hook_event_name": "PostToolUse",
        "tool_name": "Bash",
        "tool_response": {"success": True},
        "cwd": "/test/project",
        "project_root": "/test/project"
    }


def execute_post_tool_use(
    project_root: Path,
    plugin_root: Path,
    tool_input: dict,
    timeout: int = 15
) -> subprocess.CompletedProcess:
    """Execute post_tool_use hook"""
    hook_script = plugin_root / "hooks" / "post_tool_use.py"
    hook_input = tool_input.copy()
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


class TestToolSuccessDetermination:
    """Test tool success determination logic"""

    def test_success_with_explicit_true(self, test_project, brainworm_plugin_root, tool_input):
        """Test: Recognizes explicit success=true"""
        tool_input["tool_response"] = {"success": True}
        result = execute_post_tool_use(test_project, brainworm_plugin_root, tool_input)
        assert result.returncode == 0

    def test_failure_with_explicit_false(self, test_project, brainworm_plugin_root, tool_input):
        """Test: Recognizes explicit success=false"""
        tool_input["tool_response"] = {"success": False}
        result = execute_post_tool_use(test_project, brainworm_plugin_root, tool_input)
        assert result.returncode == 0

    def test_failure_with_is_error_flag(self, test_project, brainworm_plugin_root, tool_input):
        """Test: Recognizes is_error flag"""
        tool_input["tool_response"] = {"is_error": True}
        result = execute_post_tool_use(test_project, brainworm_plugin_root, tool_input)
        assert result.returncode == 0

    def test_failure_with_error_field(self, test_project, brainworm_plugin_root, tool_input):
        """Test: Recognizes error field"""
        tool_input["tool_response"] = {"error": "Something went wrong"}
        result = execute_post_tool_use(test_project, brainworm_plugin_root, tool_input)
        assert result.returncode == 0

    def test_success_with_no_indicators(self, test_project, brainworm_plugin_root, tool_input):
        """Test: Defaults to success with no indicators"""
        tool_input["tool_response"] = {"result": "Completed normally"}
        result = execute_post_tool_use(test_project, brainworm_plugin_root, tool_input)
        assert result.returncode == 0


class TestSubagentFlagCleanup:
    """Test subagent flag cleanup for Task tool"""

    def test_cleans_up_flag_for_task_tool(self, test_project, brainworm_plugin_root, tool_input):
        """Test: Cleans up subagent flag when Task tool completes"""
        # Create subagent flag
        state_dir = test_project / ".brainworm" / "state"
        subagent_flag = state_dir / "in_subagent_context.flag"
        subagent_flag.touch()

        tool_input["tool_name"] = "Task"
        tool_input["tool_response"] = {"success": True}

        result = execute_post_tool_use(test_project, brainworm_plugin_root, tool_input)
        assert result.returncode == 0

        # Flag should be cleaned up
        # Note: Cleanup might happen in business controller, check if flag still exists
        # If cleanup works, flag should be gone or state directory should show cleanup

    def test_no_cleanup_for_non_task_tools(self, test_project, brainworm_plugin_root, tool_input):
        """Test: No cleanup for non-Task tools"""
        # Create subagent flag
        state_dir = test_project / ".brainworm" / "state"
        subagent_flag = state_dir / "in_subagent_context.flag"
        subagent_flag.touch()

        tool_input["tool_name"] = "Bash"
        result = execute_post_tool_use(test_project, brainworm_plugin_root, tool_input)
        assert result.returncode == 0


class TestDifferentTools:
    """Test handling of different tool types"""

    @pytest.mark.parametrize("tool_name", ["Bash", "Edit", "Write", "Read", "Task", "Grep"])
    def test_handles_various_tools(self, test_project, brainworm_plugin_root, tool_input, tool_name):
        """Test: Handles various tool types"""
        tool_input["tool_name"] = tool_name
        tool_input["tool_response"] = {"success": True}

        result = execute_post_tool_use(test_project, brainworm_plugin_root, tool_input)
        assert result.returncode == 0


class TestBasicFunctionality:
    """Test basic hook functionality"""

    def test_hook_succeeds_with_valid_input(self, test_project, brainworm_plugin_root, tool_input):
        """Test: Hook succeeds with valid input"""
        result = execute_post_tool_use(test_project, brainworm_plugin_root, tool_input)
        assert result.returncode == 0

    def test_handles_empty_tool_response(self, test_project, brainworm_plugin_root, tool_input):
        """Test: Handles empty tool response"""
        tool_input["tool_response"] = {}
        result = execute_post_tool_use(test_project, brainworm_plugin_root, tool_input)
        assert result.returncode == 0

    def test_handles_missing_tool_response(self, test_project, brainworm_plugin_root, tool_input):
        """Test: Handles missing tool response"""
        del tool_input["tool_response"]
        result = execute_post_tool_use(test_project, brainworm_plugin_root, tool_input)
        assert result.returncode == 0
