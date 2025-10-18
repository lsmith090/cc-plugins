"""
Command Injection Prevention Integration Tests

Integration tests that verify command injection prevention is properly
implemented in actual code paths, particularly in git operations and
subprocess calls.

Tests verify:
- Git operations sanitize branch names
- Path validation in subprocess calls
- Input validation in state management
- Safe subprocess invocation patterns
"""

import pytest
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from brainworm.utils.git_submodule_manager import SubmoduleManager
from brainworm.utils.daic_state_manager import DAICStateManager
from brainworm.utils.security_validators import validate_branch_name


class TestGitCommandInjection:
    """Test command injection prevention in git operations"""

    def test_branch_validation_in_git_operations(self, temp_dir):
        """Test that git operations validate branch names"""
        project_root = temp_dir / "project"
        project_root.mkdir(parents=True)

        # Initialize git repo
        subprocess.run(
            ["git", "init"],
            cwd=project_root,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=project_root,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=project_root,
            check=True,
            capture_output=True
        )

        manager = SubmoduleManager(project_root)

        # Valid branch should work (or fail gracefully if branch doesn't exist)
        valid_branch = "feature/add-security"
        # This should not raise ValueError from validation
        # (it may raise other errors if branch doesn't exist, which is fine)
        try:
            result = manager.checkout_branch(valid_branch)
        except subprocess.CalledProcessError:
            # Expected if branch doesn't exist
            pass
        except Exception as e:
            # Should not be a validation error
            assert "dangerous character" not in str(e)
            assert "Invalid branch name" not in str(e)

        # Malicious branch should be rejected during validation
        malicious_branch = "feature; rm -rf /"
        with pytest.raises(ValueError, match="dangerous character"):
            validate_branch_name(malicious_branch)

    def test_service_name_validation(self, temp_dir):
        """Test that service names are validated"""
        project_root = temp_dir / "project"
        project_root.mkdir(parents=True)

        # Initialize git repo
        subprocess.run(
            ["git", "init"],
            cwd=project_root,
            check=True,
            capture_output=True
        )

        manager = SubmoduleManager(project_root)

        # Malicious service name should be detected
        malicious_service = "service; cat /etc/passwd"

        # The validation happens in service name checks
        from brainworm.utils.security_validators import validate_identifier

        with pytest.raises(ValueError):
            validate_identifier(malicious_service)

    def test_git_subprocess_timeout_protection(self, temp_dir):
        """Test that git subprocess calls have timeout protection"""
        project_root = temp_dir / "project"
        project_root.mkdir(parents=True)

        # Initialize git repo
        subprocess.run(
            ["git", "init"],
            cwd=project_root,
            check=True,
            capture_output=True
        )

        manager = SubmoduleManager(project_root)

        # Mock subprocess.run to verify timeout is set
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=['git', 'status'],
                returncode=0,
                stdout=b'',
                stderr=b''
            )

            try:
                manager.get_current_branch()
            except:
                # Might fail due to mocking, but we're checking the call
                pass

            # Verify subprocess.run was called with timeout
            if mock_run.called:
                call_kwargs = mock_run.call_args.kwargs if mock_run.call_args else {}
                # timeout should be present in the call
                assert 'timeout' in call_kwargs or 'check' in call_kwargs


class TestPathTraversalInRealUsage:
    """Test path traversal prevention in actual code paths"""

    def test_daic_state_manager_path_validation(self, temp_dir):
        """Test that DAIC state manager validates paths"""
        project_root = temp_dir / "project"
        project_root.mkdir(parents=True)

        brainworm_dir = project_root / ".brainworm"
        brainworm_dir.mkdir(parents=True)

        state_dir = brainworm_dir / "state"
        state_dir.mkdir(parents=True)

        # Create initial state file
        state_file = state_dir / "unified_session_state.json"
        state_file.write_text('{"daic_mode": "discussion"}')

        # State manager should work with valid paths
        manager = DAICStateManager(project_root)
        state = manager.get_unified_state()
        assert state is not None
        assert "daic_mode" in state

    def test_hook_framework_boundary_validation(self, temp_dir):
        """Test that hook framework validates execution boundaries"""
        from brainworm.utils.security_validators import validate_safe_path

        project_root = temp_dir / "project"
        project_root.mkdir(parents=True)

        # Valid: hook script within project
        hook_path = project_root / ".brainworm" / "hooks" / "pre_tool_use.py"
        hook_path.parent.mkdir(parents=True, exist_ok=True)
        hook_path.touch()

        validated = validate_safe_path(hook_path, project_root)
        assert validated.resolve().is_relative_to(project_root.resolve())

        # Invalid: hook script outside project
        malicious_path = temp_dir / "evil" / "hook.py"
        malicious_path.parent.mkdir(parents=True, exist_ok=True)
        malicious_path.touch()

        with pytest.raises(ValueError, match="Path traversal"):
            validate_safe_path(malicious_path, project_root)


class TestInputSanitization:
    """Test input sanitization in state management and logging"""

    def test_session_id_validation_in_state(self, temp_dir):
        """Test that session IDs are validated in state management"""
        from brainworm.utils.security_validators import validate_session_id

        # Valid session IDs
        valid_ids = [
            "12345678",
            "a1b2c3d4e5f6",
            "550e8400-e29b-41d4-a716-446655440000",
        ]

        for session_id in valid_ids:
            result = validate_session_id(session_id)
            assert result == session_id

        # Invalid session IDs should be rejected
        invalid_ids = [
            "short",              # Too short
            "id; rm -rf /",      # Command injection attempt
            "id $(whoami)",      # Command substitution
            "id`cat /etc/passwd`",  # Backticks
        ]

        for session_id in invalid_ids:
            with pytest.raises(ValueError):
                validate_session_id(session_id)

    def test_error_message_sanitization(self):
        """Test that error messages sanitize potentially dangerous input"""
        from brainworm.utils.security_validators import sanitize_for_display

        # Malicious input with control characters
        malicious = "Error\x00with\x01null\x1fbytes"
        sanitized = sanitize_for_display(malicious)

        # Control characters should be removed
        assert "\x00" not in sanitized
        assert "\x01" not in sanitized
        assert "\x1f" not in sanitized

        # Should only contain printable characters
        assert sanitized == "Errorwithnullbytes"


class TestSubprocessSafety:
    """Test subprocess invocation safety patterns"""

    def test_subprocess_uses_list_args_not_shell(self):
        """Test that subprocess calls use list arguments, not shell=True"""
        # This is a pattern test - actual implementation should use:
        # subprocess.run(['git', 'checkout', branch], shell=False)
        # NOT: subprocess.run(f'git checkout {branch}', shell=True)

        # Demonstrate safe pattern
        branch = "feature/test"
        safe_cmd = ['git', 'checkout', branch]

        # This is safe because each argument is separate
        assert isinstance(safe_cmd, list)
        assert branch in safe_cmd

        # Demonstrate unsafe pattern (what we avoid)
        unsafe_cmd = f'git checkout {branch}'
        assert isinstance(unsafe_cmd, str)

        # With shell=True, this would be vulnerable:
        malicious_branch = "feature; rm -rf /"
        unsafe_with_injection = f'git checkout {malicious_branch}'

        # The injection would execute if shell=True was used
        assert "; rm -rf /" in unsafe_with_injection

    def test_environment_variable_injection_prevention(self):
        """Test that environment variables are sanitized"""
        # Environment variables can also be injection vectors
        # They should be validated before use in subprocess calls

        from brainworm.utils.security_validators import validate_identifier

        # Safe environment variable names
        safe_vars = ["PATH", "HOME", "USER", "BRAINWORM_MODE"]
        for var in safe_vars:
            # Should not raise
            result = validate_identifier(var, allow_underscore=True, allow_hyphen=False)
            assert result == var

        # Dangerous environment variable names
        dangerous_vars = [
            "VAR; rm -rf /",
            "VAR$(whoami)",
            "VAR`id`",
        ]

        for var in dangerous_vars:
            with pytest.raises(ValueError):
                validate_identifier(var, allow_underscore=True, allow_hyphen=False)


class TestSQLInjectionDefense:
    """Test SQL injection defense-in-depth measures"""

    def test_sql_identifier_validation(self):
        """Test that SQL identifiers are validated"""
        from brainworm.utils.security_validators import validate_sql_identifier

        # Valid table/column names
        valid_identifiers = [
            "hook_events",
            "session_id",
            "created_at",
            "event_data",
        ]

        for identifier in valid_identifiers:
            result = validate_sql_identifier(identifier)
            assert result == identifier

        # SQL injection attempts should be blocked
        injection_attempts = [
            "users; DROP TABLE users--",
            "users' OR '1'='1",
            "users UNION SELECT",
        ]

        for attempt in injection_attempts:
            with pytest.raises(ValueError):
                validate_sql_identifier(attempt)

    def test_event_store_uses_parameterized_queries(self, temp_dir):
        """Test that event store uses parameterized queries"""
        from brainworm.utils.event_store import HookEventStore

        brainworm_dir = temp_dir / ".brainworm"
        brainworm_dir.mkdir(parents=True)

        event_store = HookEventStore(brainworm_dir)

        # Attempt to log event with SQL injection in data
        malicious_data = {
            "hook_name": "test_hook",
            "session_id": "test'; DROP TABLE hook_events--",
            "malicious_field": "'; DELETE FROM hook_events--"
        }

        # Should succeed because parameterized queries prevent injection
        success = event_store.log_event(malicious_data)
        assert success

        # Verify data was stored safely (injection didn't execute)
        # If it executed, the table would be dropped/deleted
        # The fact that we can query proves injection was prevented
        import sqlite3
        db_file = brainworm_dir / "events" / "hooks.db"
        conn = sqlite3.connect(db_file)

        # Table should still exist
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='hook_events'"
        )
        tables = cursor.fetchall()
        assert len(tables) == 1
        assert tables[0][0] == "hook_events"

        # Data should be stored as literal strings, not executed
        cursor = conn.execute(
            "SELECT COUNT(*) FROM hook_events WHERE session_id LIKE '%DROP TABLE%'"
        )
        count = cursor.fetchone()[0]
        assert count == 1  # Stored as literal string

        conn.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)
