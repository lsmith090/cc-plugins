#!/usr/bin/env python3
"""
Bash Command Validator - Shared utility for DAIC bash command checking

Provides centralized logic for determining if bash commands are read-only and safe
to execute in discussion mode. Fixes the prefix matching bug where commands like
"git status-foo" would incorrectly match "git status".

Key Features:
- Exact command matching or space-separated argument matching
- Quote-aware command splitting (preserves quoted strings with special chars)
- Comprehensive write pattern detection
- Security pattern detection (find -delete, -exec rm, etc.)
- Consistent behavior across all DAIC enforcement points

Usage:
    from utils.bash_validator import is_read_only_bash_command

    config = load_config()
    if is_read_only_bash_command("git status", config):
        # Command is safe in discussion mode
        pass
"""

import re
from typing import Dict, Any, List


def split_command_respecting_quotes(command: str) -> List[str]:
    """
    Split command on operators (&&, ||, ;, |) while respecting quoted strings.

    This ensures that pipes and operators inside quoted strings are not treated
    as command separators.

    Examples:
        'ls | grep "test"' → ['ls', 'grep "test"']
        'ls | grep "test|pattern"' → ['ls', 'grep "test|pattern"']  # Pipe in quotes preserved
        'ls && pwd' → ['ls', 'pwd']
        'ls; pwd; echo "done"' → ['ls', 'pwd', 'echo "done"']

    Args:
        command: Full bash command string potentially with operators

    Returns:
        List of command parts split by operators, with quotes preserved
    """
    parts = []
    current_part = []
    in_single_quote = False
    in_double_quote = False
    i = 0

    while i < len(command):
        char = command[i]

        # Handle quotes - toggle state and preserve in output
        if char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            current_part.append(char)
        elif char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            current_part.append(char)
        # Handle operators only when not in quotes
        elif not in_single_quote and not in_double_quote:
            # Check for multi-character operators (&&, ||, >>)
            if i < len(command) - 1:
                two_char = command[i:i+2]
                if two_char in ['&&', '||', '>>']:
                    # End current part and skip both characters
                    if current_part:
                        parts.append(''.join(current_part))
                        current_part = []
                    i += 2
                    continue

            # Check for single-character operators (;, |)
            if char in [';', '|']:
                # End current part
                if current_part:
                    parts.append(''.join(current_part))
                    current_part = []
            else:
                current_part.append(char)
        else:
            # Inside quotes - preserve everything
            current_part.append(char)

        i += 1

    # Add final part
    if current_part:
        parts.append(''.join(current_part))

    return [part.strip() for part in parts if part.strip()]


def is_read_only_bash_command(command: str, config: Dict[str, Any]) -> bool:
    """
    Check if a bash command is read-only and safe to execute in discussion mode.

    This function implements the core DAIC bash command filtering logic with
    the fixed prefix matching behavior.

    Matching Logic (THE FIX):
        - Exact match: "git status" == "git status" ✅
        - With args: "git status --short".startswith("git status ") ✅
        - Fake command: "git status-foo".startswith("git status ") ❌ BLOCKED

    Security Checks:
        1. Write patterns: Detects output redirection, file modifications, etc.
        2. Security patterns: Detects dangerous flags like -delete, -exec rm
        3. Command matching: Ensures ALL parts of chained commands are allowed

    Args:
        command: Full bash command string to validate
        config: Configuration dictionary with daic.read_only_bash_commands section

    Returns:
        True if command is read-only and safe, False otherwise

    Examples:
        >>> config = {"daic": {"read_only_bash_commands": {"git": ["git status"]}}}
        >>> is_read_only_bash_command("git status", config)
        True
        >>> is_read_only_bash_command("git status --short", config)
        True
        >>> is_read_only_bash_command("git status-foo", config)  # BUGFIX!
        False
        >>> is_read_only_bash_command("git commit", config)
        False
    """
    daic_config = config.get("daic", {})
    read_only_commands = daic_config.get("read_only_bash_commands", {})

    # Flatten all read-only command categories into single list
    all_read_only = []
    for category_commands in read_only_commands.values():
        if isinstance(category_commands, list):
            all_read_only.extend(category_commands)

    # PHASE 1: Check for write patterns (output redirection, file modifications)
    write_patterns = [
        # Output redirection patterns (improved security)
        # Match > but exclude specific safe patterns: >&1, >&2, > /dev/null, > /dev/zero
        r'>(?!&[12]\b)(?!\s*/dev/null\b)(?!\s*/dev/zero\b)',  # Output redirection
        r'>>',                      # Append redirection always blocked
        r'\btee\b',           # tee command (writes to files)
        r'\bmv\b',            # move/rename
        r'\bcp\b',            # copy
        r'\brm\b',            # remove
        r'\bmkdir\b',         # make directory
        r'\btouch\b',         # create/update file
        r'\bsed\s+(?!-n)',    # sed without -n flag (modifies in place)
        r'\bnpm\s+install',   # npm install
        r'\bpip\s+install',   # pip install
        r'-delete\b',         # find -delete flag (SECURITY)
        r'-exec\s+.*rm\b',    # find -exec with rm (SECURITY)
        r'\bdd\b',            # dd command (can write to disk)
        r'<\(',               # Process substitution write
        r'>\(',               # Process substitution write
    ]

    # If command has any write patterns, it's not read-only
    if any(re.search(pattern, command) for pattern in write_patterns):
        return False

    # PHASE 2: Check if ALL commands in chain are read-only
    # Use quote-aware splitting to handle pipes inside quoted strings correctly
    command_parts = split_command_respecting_quotes(command)

    for part in command_parts:
        part = part.strip()
        if not part:
            continue

        # THE FIX: Check for exact match OR command with space-separated args
        # This prevents "git status-foo" from matching "git status"
        is_part_read_only = any(
            part == allowed_cmd or part.startswith(allowed_cmd + " ")
            for allowed_cmd in all_read_only
        )

        # If any part is not read-only, reject entire command chain
        if not is_part_read_only:
            return False

    return True


def get_read_only_commands_flattened(config: Dict[str, Any]) -> List[str]:
    """
    Get flattened list of all read-only commands from config.

    Utility function for other components that need access to the allowed
    command list.

    Args:
        config: Configuration dictionary

    Returns:
        Flattened list of all allowed read-only commands
    """
    daic_config = config.get("daic", {})
    read_only_commands = daic_config.get("read_only_bash_commands", {})

    all_read_only = []
    for category_commands in read_only_commands.values():
        if isinstance(category_commands, list):
            all_read_only.extend(category_commands)

    return all_read_only
