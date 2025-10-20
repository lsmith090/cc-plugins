#!/usr/bin/env python3
"""
Unit Tests for SessionStart Hook

Tests essential behaviors of session_start.py including:
- Directory structure creation
- State initialization
- Wrapper script generation
- Database setup
- Session ID capture
"""

import pytest
import json
import sqlite3
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
    """Create empty test project directory"""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    return project_root


@pytest.fixture
def session_input() -> dict:
    """Generate test session input"""
    return {
        "session_id": f"test-session-{uuid.uuid4().hex[:8]}",
        "correlation_id": f"test-corr-{uuid.uuid4().hex[:8]}",
        "hook_event_name": "SessionStart",
        "cwd": "/test/project",
        "project_root": "/test/project"
    }


def execute_session_start(
    project_root: Path,
    plugin_root: Path,
    session_input: dict,
    timeout: int = 15
) -> subprocess.CompletedProcess:
    """Execute session_start hook with given input"""
    hook_script = plugin_root / "hooks" / "session_start.py"

    hook_input = session_input.copy()
    hook_input["cwd"] = str(project_root)
    hook_input["project_root"] = str(project_root)

    # Set environment to simulate plugin execution
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


class TestDirectoryStructure:
    """Test directory structure creation"""

    def test_creates_all_required_directories(self, test_project, brainworm_plugin_root, session_input):
        """Test: All required subdirectories are created"""
        result = execute_session_start(test_project, brainworm_plugin_root, session_input)
        assert result.returncode == 0, f"Hook failed:\n{result.stderr.decode()}"

        brainworm_dir = test_project / ".brainworm"
        required_dirs = ["state", "events", "tasks", "timing", "protocols"]

        for dir_name in required_dirs:
            dir_path = brainworm_dir / dir_name
            assert dir_path.exists(), f"{dir_name}/ directory not created"
            assert dir_path.is_dir()


class TestStateInitialization:
    """Test unified session state initialization"""

    def test_creates_state_with_required_fields(self, test_project, brainworm_plugin_root, session_input):
        """Test: State file created with all required fields"""
        result = execute_session_start(test_project, brainworm_plugin_root, session_input)
        assert result.returncode == 0

        state_file = test_project / ".brainworm" / "state" / "unified_session_state.json"
        assert state_file.exists(), "unified_session_state.json not created"

        with open(state_file) as f:
            state = json.load(f)

        required_fields = [
            "daic_mode", "session_id", "correlation_id", "plugin_root",
            "current_task", "current_branch", "developer"
        ]

        for field in required_fields:
            assert field in state, f"State missing field: {field}"

    def test_state_captures_session_id(self, test_project, brainworm_plugin_root, session_input):
        """Test: Session ID from input is captured"""
        result = execute_session_start(test_project, brainworm_plugin_root, session_input)
        assert result.returncode == 0

        state_file = test_project / ".brainworm" / "state" / "unified_session_state.json"
        with open(state_file) as f:
            state = json.load(f)

        assert state["session_id"] == session_input["session_id"]

    def test_default_daic_mode_is_discussion(self, test_project, brainworm_plugin_root, session_input):
        """Test: Default DAIC mode is discussion"""
        result = execute_session_start(test_project, brainworm_plugin_root, session_input)
        assert result.returncode == 0

        state_file = test_project / ".brainworm" / "state" / "unified_session_state.json"
        with open(state_file) as f:
            state = json.load(f)

        assert state["daic_mode"] == "discussion"


class TestWrapperScripts:
    """Test wrapper script generation"""

    def test_creates_executable_daic_wrapper(self, test_project, brainworm_plugin_root, session_input):
        """Test: ./daic wrapper created and executable"""
        result = execute_session_start(test_project, brainworm_plugin_root, session_input)
        assert result.returncode == 0

        daic_wrapper = test_project / "daic"
        assert daic_wrapper.exists(), "./daic not created"

        import os
        assert os.access(daic_wrapper, os.X_OK), "./daic not executable"

    def test_creates_executable_tasks_wrapper(self, test_project, brainworm_plugin_root, session_input):
        """Test: ./tasks wrapper created and executable"""
        result = execute_session_start(test_project, brainworm_plugin_root, session_input)
        assert result.returncode == 0

        tasks_wrapper = test_project / "tasks"
        assert tasks_wrapper.exists(), "./tasks not created"

        import os
        assert os.access(tasks_wrapper, os.X_OK), "./tasks not executable"

    def test_creates_executable_plugin_launcher(self, test_project, brainworm_plugin_root, session_input):
        """Test: plugin-launcher created and executable"""
        result = execute_session_start(test_project, brainworm_plugin_root, session_input)
        assert result.returncode == 0

        plugin_launcher = test_project / ".brainworm" / "plugin-launcher"
        assert plugin_launcher.exists(), "plugin-launcher not created"

        import os
        assert os.access(plugin_launcher, os.X_OK), "plugin-launcher not executable"

    def test_wrappers_reference_plugin_launcher(self, test_project, brainworm_plugin_root, session_input):
        """Test: Wrappers use plugin-launcher"""
        result = execute_session_start(test_project, brainworm_plugin_root, session_input)
        assert result.returncode == 0

        daic_wrapper = test_project / "daic"
        daic_content = daic_wrapper.read_text()

        assert ".brainworm/plugin-launcher" in daic_content
        assert "daic_command.py" in daic_content


class TestDatabaseInitialization:
    """Test event database setup"""

    def test_creates_database_with_schema(self, test_project, brainworm_plugin_root, session_input):
        """Test: Database created with hook_events table"""
        result = execute_session_start(test_project, brainworm_plugin_root, session_input)
        assert result.returncode == 0

        db_path = test_project / ".brainworm" / "events" / "hooks.db"
        assert db_path.exists(), "hooks.db not created"

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='hook_events'
        """)

        result = cursor.fetchone()
        conn.close()

        assert result is not None, "hook_events table not created"

    def test_database_has_required_columns(self, test_project, brainworm_plugin_root, session_input):
        """Test: hook_events table has required columns"""
        result = execute_session_start(test_project, brainworm_plugin_root, session_input)
        assert result.returncode == 0

        db_path = test_project / ".brainworm" / "events" / "hooks.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(hook_events)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        required = {"id", "hook_name", "correlation_id", "session_id", "timestamp", "event_data"}
        assert required.issubset(columns), f"Missing columns: {required - columns}"

    def test_database_has_indexes(self, test_project, brainworm_plugin_root, session_input):
        """Test: Database has performance indexes"""
        result = execute_session_start(test_project, brainworm_plugin_root, session_input)
        assert result.returncode == 0

        db_path = test_project / ".brainworm" / "events" / "hooks.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {row[0] for row in cursor.fetchall()}
        conn.close()

        expected = {
            "idx_hook_events_timestamp",
            "idx_hook_events_correlation",
            "idx_hook_events_session",
            "idx_hook_events_execution_id"
        }

        assert expected.issubset(indexes), f"Missing indexes: {expected - indexes}"


class TestClaudeSettings:
    """Test Claude Code settings configuration"""

    def test_configures_statusline(self, test_project, brainworm_plugin_root, session_input):
        """Test: StatusLine configured in settings.json"""
        result = execute_session_start(test_project, brainworm_plugin_root, session_input)
        assert result.returncode == 0

        settings_file = test_project / ".claude" / "settings.json"
        assert settings_file.exists()

        with open(settings_file) as f:
            settings = json.load(f)

        assert "statusLine" in settings
        assert settings["statusLine"]["type"] == "command"
        assert "plugin-launcher" in settings["statusLine"]["command"]

    def test_configures_daic_permissions(self, test_project, brainworm_plugin_root, session_input):
        """Test: DAIC mode-switching protected"""
        result = execute_session_start(test_project, brainworm_plugin_root, session_input)
        assert result.returncode == 0

        settings_local = test_project / ".claude" / "settings.local.json"
        assert settings_local.exists()

        with open(settings_local) as f:
            settings = json.load(f)

        assert "permissions" in settings
        deny_rules = settings["permissions"]["deny"]

        assert any("daic implementation" in rule for rule in deny_rules)
        assert any("daic toggle" in rule for rule in deny_rules)


class TestSessionFlagCleanup:
    """Test cleanup of session flags"""

    def test_cleans_context_warning_flags(self, test_project, brainworm_plugin_root, session_input):
        """Test: Context warning flags cleaned up"""
        state_dir = test_project / ".brainworm" / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        flag_75 = state_dir / "context-warning-75.flag"
        flag_90 = state_dir / "context-warning-90.flag"
        flag_75.touch()
        flag_90.touch()

        result = execute_session_start(test_project, brainworm_plugin_root, session_input)
        assert result.returncode == 0

        assert not flag_75.exists(), "75% flag not cleaned"
        assert not flag_90.exists(), "90% flag not cleaned"

    def test_cleans_subagent_context_flag(self, test_project, brainworm_plugin_root, session_input):
        """Test: Subagent context flag cleaned up"""
        state_dir = test_project / ".brainworm" / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        subagent_flag = state_dir / "in_subagent_context.flag"
        subagent_flag.touch()

        result = execute_session_start(test_project, brainworm_plugin_root, session_input)
        assert result.returncode == 0

        assert not subagent_flag.exists(), "Subagent flag not cleaned"


class TestIdempotency:
    """Test that SessionStart can run multiple times safely"""

    def test_second_run_updates_session_id(self, test_project, brainworm_plugin_root, session_input):
        """Test: Second run updates session_id"""
        result1 = execute_session_start(test_project, brainworm_plugin_root, session_input)
        assert result1.returncode == 0

        state_file = test_project / ".brainworm" / "state" / "unified_session_state.json"
        with open(state_file) as f:
            state1 = json.load(f)

        session_input2 = session_input.copy()
        session_input2["session_id"] = f"test-session-{uuid.uuid4().hex[:8]}"

        result2 = execute_session_start(test_project, brainworm_plugin_root, session_input2)
        assert result2.returncode == 0

        with open(state_file) as f:
            state2 = json.load(f)

        assert state2["session_id"] == session_input2["session_id"]
        assert state2["plugin_root"] == state1["plugin_root"]

    def test_regenerates_wrappers_each_run(self, test_project, brainworm_plugin_root, session_input):
        """Test: Wrappers regenerated on each run"""
        result1 = execute_session_start(test_project, brainworm_plugin_root, session_input)
        assert result1.returncode == 0

        daic_wrapper = test_project / "daic"
        first_mtime = daic_wrapper.stat().st_mtime

        import time
        time.sleep(0.1)

        result2 = execute_session_start(test_project, brainworm_plugin_root, session_input)
        assert result2.returncode == 0

        second_mtime = daic_wrapper.stat().st_mtime
        assert second_mtime >= first_mtime


class TestErrorHandling:
    """Test error handling"""

    def test_handles_missing_session_id(self, test_project, brainworm_plugin_root):
        """Test: Handles missing session_id gracefully"""
        invalid_input = {
            "hook_event_name": "SessionStart",
            "cwd": str(test_project),
            "project_root": str(test_project)
        }

        result = execute_session_start(test_project, brainworm_plugin_root, invalid_input)
        assert result.returncode == 0

    def test_core_functionality_always_succeeds(self, test_project, brainworm_plugin_root, session_input):
        """Test: Core setup always completes"""
        result = execute_session_start(test_project, brainworm_plugin_root, session_input)
        assert result.returncode == 0

        brainworm_dir = test_project / ".brainworm"
        assert brainworm_dir.exists()
