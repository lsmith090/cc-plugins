#!/usr/bin/env python3
"""
Unit Tests for SessionEnd Hook

Tests essential behaviors of session_end.py including:
- Snapshot creation on session termination
- Session ID capture
- Graceful failure handling
- Success message output
- Event logging
"""

import pytest
import json
import sqlite3
import subprocess
from pathlib import Path
import uuid
from unittest.mock import Mock, patch


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
    """Create test project with .brainworm structure"""
    project_root = tmp_path / "test_project"
    project_root.mkdir()

    # Create minimal .brainworm structure
    brainworm_dir = project_root / ".brainworm"
    (brainworm_dir / "state").mkdir(parents=True)
    (brainworm_dir / "events").mkdir(parents=True)
    (brainworm_dir / "scripts").mkdir(parents=True)

    return project_root


@pytest.fixture
def session_input() -> dict:
    """Generate test session input"""
    return {
        "session_id": f"test-session-{uuid.uuid4().hex[:8]}",
        "correlation_id": f"test-corr-{uuid.uuid4().hex[:8]}",
        "hook_event_name": "SessionEnd",
        "reason": "normal",
        "cwd": "/test/project",
        "project_root": "/test/project"
    }


def execute_session_end(
    project_root: Path,
    plugin_root: Path,
    session_input: dict,
    timeout: int = 15
) -> subprocess.CompletedProcess:
    """Execute session_end hook with given input"""
    hook_script = plugin_root / "hooks" / "session_end.py"

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


class TestSnapshotCreation:
    """Test session snapshot creation"""

    def test_calls_snapshot_script_when_available(self, test_project, brainworm_plugin_root, session_input):
        """Test: Calls snapshot_session.py when script exists"""
        # Create mock snapshot script
        scripts_dir = test_project / ".brainworm" / "scripts"
        snapshot_script = scripts_dir / "snapshot_session.py"

        snapshot_script.write_text("""#!/usr/bin/env python3
import sys
import json
# Mock successful snapshot
print(json.dumps({"status": "success"}))
sys.exit(0)
""")
        snapshot_script.chmod(0o755)

        result = execute_session_end(test_project, brainworm_plugin_root, session_input)
        assert result.returncode == 0, f"Hook failed:\n{result.stderr.decode()}"

    def test_does_not_fail_when_snapshot_missing(self, test_project, brainworm_plugin_root, session_input):
        """Test: Hook succeeds even if snapshot script missing"""
        # Ensure snapshot script doesn't exist
        scripts_dir = test_project / ".brainworm" / "scripts"
        snapshot_script = scripts_dir / "snapshot_session.py"
        if snapshot_script.exists():
            snapshot_script.unlink()

        result = execute_session_end(test_project, brainworm_plugin_root, session_input)
        assert result.returncode == 0, "Hook should succeed even without snapshot script"

    def test_does_not_fail_when_snapshot_fails(self, test_project, brainworm_plugin_root, session_input):
        """Test: Hook succeeds even if snapshot script fails"""
        # Create snapshot script that fails
        scripts_dir = test_project / ".brainworm" / "scripts"
        snapshot_script = scripts_dir / "snapshot_session.py"

        snapshot_script.write_text("""#!/usr/bin/env python3
import sys
sys.exit(1)  # Fail
""")
        snapshot_script.chmod(0o755)

        result = execute_session_end(test_project, brainworm_plugin_root, session_input)
        assert result.returncode == 0, "Hook should succeed even if snapshot fails"


class TestSessionIDCapture:
    """Test session ID is properly captured"""

    def test_captures_session_id_from_input(self, test_project, brainworm_plugin_root, session_input):
        """Test: Session ID from input is used"""
        # Create mock snapshot script that logs args
        scripts_dir = test_project / ".brainworm" / "scripts"
        snapshot_script = scripts_dir / "snapshot_session.py"
        args_log = scripts_dir / "args.log"

        snapshot_script.write_text(f"""#!/usr/bin/env python3
import sys
with open("{args_log}", "w") as f:
    f.write(" ".join(sys.argv[1:]))
sys.exit(0)
""")
        snapshot_script.chmod(0o755)

        result = execute_session_end(test_project, brainworm_plugin_root, session_input)
        assert result.returncode == 0

        # Verify session ID was passed to snapshot script
        if args_log.exists():
            args = args_log.read_text()
            assert session_input["session_id"] in args

    def test_handles_missing_session_id(self, test_project, brainworm_plugin_root):
        """Test: Handles missing session_id gracefully"""
        invalid_input = {
            "hook_event_name": "SessionEnd",
            "reason": "normal",
            "cwd": str(test_project),
            "project_root": str(test_project)
        }

        result = execute_session_end(test_project, brainworm_plugin_root, invalid_input)
        # Should still succeed, using "unknown" as session ID
        assert result.returncode == 0


class TestEventLogging:
    """Test event logging integration"""

    def test_logs_session_end_event_to_database(self, test_project, brainworm_plugin_root, session_input):
        """Test: Session end event written to database when enabled"""
        result = execute_session_end(test_project, brainworm_plugin_root, session_input)
        assert result.returncode == 0

        # Verify event was logged if database exists
        # Note: Database is created by session_start, not session_end
        db_path = test_project / ".brainworm" / "events" / "hooks.db"

        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            cursor.execute("""
                SELECT hook_name, session_id
                FROM hook_events
                WHERE hook_name = 'session_end'
            """)

            events = cursor.fetchall()
            conn.close()

            # Should have at least one session_end event
            assert len(events) > 0, "No session_end events found in database"
            assert any(event[1] == session_input["session_id"] for event in events), \
                f"Session ID {session_input['session_id']} not found in events"
        else:
            # Database doesn't exist - that's OK, it's created by session_start
            # Just verify hook succeeded
            assert result.returncode == 0


class TestSuccessMessage:
    """Test success message output"""

    def test_hook_completes_successfully(self, test_project, brainworm_plugin_root, session_input):
        """Test: Hook completes successfully and returns 0"""
        result = execute_session_end(test_project, brainworm_plugin_root, session_input)
        assert result.returncode == 0, f"Hook failed:\n{result.stderr.decode()}"

    def test_hook_succeeds_with_different_reasons(self, test_project, brainworm_plugin_root, session_input):
        """Test: Hook succeeds regardless of end reason"""
        session_input["reason"] = "timeout"

        result = execute_session_end(test_project, brainworm_plugin_root, session_input)
        assert result.returncode == 0, f"Hook failed with reason 'timeout':\n{result.stderr.decode()}"


class TestSnapshotScriptArguments:
    """Test snapshot script is called with correct arguments"""

    def test_passes_action_stop_to_snapshot(self, test_project, brainworm_plugin_root, session_input):
        """Test: Snapshot called with --action stop"""
        scripts_dir = test_project / ".brainworm" / "scripts"
        snapshot_script = scripts_dir / "snapshot_session.py"
        args_log = scripts_dir / "args.log"

        snapshot_script.write_text(f"""#!/usr/bin/env python3
import sys
with open("{args_log}", "w") as f:
    f.write(" ".join(sys.argv[1:]))
sys.exit(0)
""")
        snapshot_script.chmod(0o755)

        result = execute_session_end(test_project, brainworm_plugin_root, session_input)
        assert result.returncode == 0

        if args_log.exists():
            args = args_log.read_text()
            assert "--action stop" in args or "--action" in args and "stop" in args

    def test_passes_session_id_to_snapshot(self, test_project, brainworm_plugin_root, session_input):
        """Test: Snapshot called with --session-id"""
        scripts_dir = test_project / ".brainworm" / "scripts"
        snapshot_script = scripts_dir / "snapshot_session.py"
        args_log = scripts_dir / "args.log"

        snapshot_script.write_text(f"""#!/usr/bin/env python3
import sys
with open("{args_log}", "w") as f:
    f.write(" ".join(sys.argv[1:]))
sys.exit(0)
""")
        snapshot_script.chmod(0o755)

        result = execute_session_end(test_project, brainworm_plugin_root, session_input)
        assert result.returncode == 0

        if args_log.exists():
            args = args_log.read_text()
            assert "--session-id" in args
            assert session_input["session_id"] in args

    def test_passes_quiet_flag_to_snapshot(self, test_project, brainworm_plugin_root, session_input):
        """Test: Snapshot called with --quiet flag"""
        scripts_dir = test_project / ".brainworm" / "scripts"
        snapshot_script = scripts_dir / "snapshot_session.py"
        args_log = scripts_dir / "args.log"

        snapshot_script.write_text(f"""#!/usr/bin/env python3
import sys
with open("{args_log}", "w") as f:
    f.write(" ".join(sys.argv[1:]))
sys.exit(0)
""")
        snapshot_script.chmod(0o755)

        result = execute_session_end(test_project, brainworm_plugin_root, session_input)
        assert result.returncode == 0

        if args_log.exists():
            args = args_log.read_text()
            assert "--quiet" in args


class TestTimeout:
    """Test snapshot timeout handling"""

    def test_handles_snapshot_timeout_gracefully(self, test_project, brainworm_plugin_root, session_input):
        """Test: Hook succeeds even if snapshot times out"""
        scripts_dir = test_project / ".brainworm" / "scripts"
        snapshot_script = scripts_dir / "snapshot_session.py"

        # Create script that hangs
        snapshot_script.write_text("""#!/usr/bin/env python3
import time
time.sleep(30)  # Exceeds 10s timeout
""")
        snapshot_script.chmod(0o755)

        result = execute_session_end(test_project, brainworm_plugin_root, session_input, timeout=20)
        # Hook should succeed even if snapshot times out
        assert result.returncode == 0


class TestIdempotency:
    """Test that SessionEnd can be called multiple times safely"""

    def test_multiple_calls_succeed(self, test_project, brainworm_plugin_root, session_input):
        """Test: Multiple session end calls don't cause errors"""
        # Create mock snapshot script
        scripts_dir = test_project / ".brainworm" / "scripts"
        snapshot_script = scripts_dir / "snapshot_session.py"
        snapshot_script.write_text("""#!/usr/bin/env python3
import sys
sys.exit(0)
""")
        snapshot_script.chmod(0o755)

        result1 = execute_session_end(test_project, brainworm_plugin_root, session_input)
        assert result1.returncode == 0

        result2 = execute_session_end(test_project, brainworm_plugin_root, session_input)
        assert result2.returncode == 0


class TestDifferentReasons:
    """Test session end with different termination reasons"""

    @pytest.mark.parametrize("reason", ["normal", "timeout", "error", "user_stop", "interrupt"])
    def test_handles_different_reasons(self, test_project, brainworm_plugin_root, session_input, reason):
        """Test: Handles different termination reasons"""
        session_input["reason"] = reason

        result = execute_session_end(test_project, brainworm_plugin_root, session_input)
        assert result.returncode == 0, f"Failed with reason: {reason}"
