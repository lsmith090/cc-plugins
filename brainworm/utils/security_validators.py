#!/usr/bin/env python3
"""
Security Validators - Input validation and sanitization utilities

Provides centralized security validation functions to prevent:
- Path traversal attacks
- Command injection
- SQL injection
- Other input validation vulnerabilities

Usage:
    from utils.security_validators import validate_safe_path, validate_branch_name

    safe_path = validate_safe_path(user_path, project_root)
    safe_branch = validate_branch_name(branch_name)
"""

import re
from pathlib import Path


def validate_safe_path(path: Path, base_dir: Path, allow_symlinks: bool = False) -> Path:
    """
    Validate that a path is safe and within expected boundaries.

    Prevents path traversal attacks by ensuring the resolved path
    stays within the base directory.

    Args:
        path: Path to validate
        base_dir: Base directory that path must be within
        allow_symlinks: Whether to allow symlinks (default: False for security)

    Returns:
        Validated, resolved path

    Raises:
        ValueError: If path escapes base_dir or is a symlink when not allowed

    Examples:
        >>> validate_safe_path(Path("subdir/file.txt"), Path("/project"))
        Path("/project/subdir/file.txt")

        >>> validate_safe_path(Path("../../etc/passwd"), Path("/project"))
        ValueError: Path traversal attempt detected
    """
    try:
        # Resolve both paths to absolute, normalized forms
        resolved_path = path.resolve()
        resolved_base = base_dir.resolve()

        # Check for symlink if not allowed
        if not allow_symlinks and path.is_symlink():
            raise ValueError(f"Symlinks not allowed: {path}")

        # Ensure resolved path is within base directory
        try:
            resolved_path.relative_to(resolved_base)
        except ValueError:
            raise ValueError(
                f"Path traversal attempt detected: {path} escapes {base_dir}"
            )

        return resolved_path

    except Exception as e:
        raise ValueError(f"Path validation failed: {e}")


def validate_branch_name(branch_name: str, max_length: int = 255) -> str:
    """
    Validate and sanitize git branch name to prevent command injection.

    Ensures branch names are safe to use in shell commands by checking
    against git's branch naming rules and blocking shell metacharacters.

    Args:
        branch_name: Branch name to validate
        max_length: Maximum allowed length (default: 255)

    Returns:
        Validated branch name

    Raises:
        ValueError: If branch name is invalid or contains dangerous characters

    Examples:
        >>> validate_branch_name("feature/add-auth")
        "feature/add-auth"

        >>> validate_branch_name("feature; rm -rf /")
        ValueError: Invalid branch name
    """
    if not branch_name or not branch_name.strip():
        raise ValueError("Branch name cannot be empty")

    if len(branch_name) > max_length:
        raise ValueError(f"Branch name too long (max {max_length} characters)")

    # Check for shell metacharacters that could enable command injection
    dangerous_chars = [';', '&', '|', '$', '`', '(', ')', '<', '>', '\n', '\r', '\\', '"', "'"]
    for char in dangerous_chars:
        if char in branch_name:
            raise ValueError(
                f"Invalid branch name: contains dangerous character '{char}'"
            )

    # Git branch name rules
    # See: https://git-scm.com/docs/git-check-ref-format
    invalid_patterns = [
        r'^/',              # Cannot start with /
        r'/$',              # Cannot end with /
        r'//',              # Cannot contain //
        r'@{',              # Cannot contain @{
        r'\.\.',            # Cannot contain ..
        r'\.lock$',         # Cannot end with .lock
        r'^\.',             # Cannot start with .
        r'\.$',             # Cannot end with .
        r'[\x00-\x1f\x7f]', # No control characters
        r'[ \t]',           # No spaces or tabs (stricter than git, but safer)
    ]

    for pattern in invalid_patterns:
        if re.search(pattern, branch_name):
            raise ValueError(f"Invalid branch name format: {branch_name}")

    return branch_name


def validate_identifier(identifier: str, max_length: int = 100,
                       allow_hyphen: bool = True, allow_underscore: bool = True) -> str:
    """
    Validate an identifier (service name, task name, etc.) for safe use.

    Args:
        identifier: String to validate
        max_length: Maximum allowed length
        allow_hyphen: Whether to allow hyphens
        allow_underscore: Whether to allow underscores

    Returns:
        Validated identifier

    Raises:
        ValueError: If identifier contains invalid characters
    """
    if not identifier or not identifier.strip():
        raise ValueError("Identifier cannot be empty")

    if len(identifier) > max_length:
        raise ValueError(f"Identifier too long (max {max_length} characters)")

    # Build allowed character pattern
    pattern = r'^[a-zA-Z0-9'
    if allow_hyphen:
        pattern += r'\-'
    if allow_underscore:
        pattern += r'_'
    pattern += r']+$'

    if not re.match(pattern, identifier):
        raise ValueError(
            "Invalid identifier: must contain only alphanumeric characters"
            + (" and hyphens" if allow_hyphen else "")
            + (" and underscores" if allow_underscore else "")
        )

    return identifier


def sanitize_for_display(text: str, max_length: int = 500) -> str:
    """
    Sanitize text for safe display in error messages and logs.

    Prevents information disclosure and log injection attacks by:
    - Truncating long strings
    - Removing control characters
    - Escaping special characters

    Args:
        text: Text to sanitize
        max_length: Maximum length before truncation

    Returns:
        Sanitized text safe for display
    """
    if not text:
        return ""

    # Remove control characters except newline and tab
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "... (truncated)"

    return sanitized


def validate_file_extension(path: Path, allowed_extensions: list[str]) -> Path:
    """
    Validate that a file has an allowed extension.

    Args:
        path: File path to validate
        allowed_extensions: List of allowed extensions (e.g., ['.json', '.txt'])

    Returns:
        Validated path

    Raises:
        ValueError: If extension is not in allowed list
    """
    extension = path.suffix.lower()
    allowed_lower = [ext.lower() for ext in allowed_extensions]

    if extension not in allowed_lower:
        raise ValueError(
            f"Invalid file extension: {extension}. "
            f"Allowed: {', '.join(allowed_extensions)}"
        )

    return path


def validate_session_id(session_id: str) -> str:
    """
    Validate session ID format to prevent injection attacks.

    Args:
        session_id: Session ID to validate

    Returns:
        Validated session ID

    Raises:
        ValueError: If session ID format is invalid
    """
    # Session IDs should be UUID format or alphanumeric with hyphens
    if not re.match(r'^[a-zA-Z0-9\-]{8,64}$', session_id):
        raise ValueError("Invalid session ID format")

    return session_id


def validate_sql_identifier(identifier: str) -> str:
    """
    Validate SQL table/column identifier to prevent SQL injection.

    Note: This should be used alongside parameterized queries, not as a replacement.

    Args:
        identifier: SQL identifier to validate

    Returns:
        Validated identifier

    Raises:
        ValueError: If identifier contains dangerous characters
    """
    # SQL identifiers should only contain alphanumeric and underscores
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
        raise ValueError(f"Invalid SQL identifier: {identifier}")

    if len(identifier) > 64:
        raise ValueError("SQL identifier too long")

    # Block SQL keywords
    sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE',
                    'ALTER', 'EXEC', 'EXECUTE', 'UNION', 'WHERE']
    if identifier.upper() in sql_keywords:
        raise ValueError(f"SQL keyword not allowed as identifier: {identifier}")

    return identifier
