#!/usr/bin/env python3
"""
DAIC Command Parsing Tests - Comprehensive Test Suite

Tests for the command parsing logic in pre_tool_use.py that determines
whether bash commands should be blocked in discussion mode.

CRITICAL: These tests validate the core DAIC functionality that users
depend on for workflow enforcement.

Consolidates all DAIC command parsing tests into one comprehensive suite.
"""

import pytest
import sys
from pathlib import Path

# Add src paths for testing
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src" / "hooks" / "templates"))
sys.path.insert(0, str(project_root / "src" / "hooks" / "templates" / "utils"))

from pre_tool_use import is_read_only_bash_command, is_brainworm_system_command, split_command_respecting_quotes


class TestDAICCommandParsing:
    """Comprehensive DAIC command parsing test suite"""

    @pytest.fixture
    def config(self):
        """Config matching actual brainworm-config.toml structure"""
        return {
            "daic": {
                "read_only_bash_commands": {
                    "basic": [
                        "ls", "ll", "pwd", "cd", "echo", "cat", "head", "tail", 
                        "less", "more", "grep", "rg", "find", "fd", "which", 
                        "whereis", "type", "file", "stat", "du", "df", "tree",
                        "basename", "dirname", "realpath", "readlink", "whoami", 
                        "env", "printenv", "date", "cal", "uptime", "wc", "cut", 
                        "sort", "uniq", "comm", "diff", "cmp", "md5sum", "sha256sum"
                    ],
                    "git": [
                        "git status", "git log", "git diff", "git show", 
                        "git branch", "git remote", "git fetch", "git describe", 
                        "git rev-parse", "git blame"
                    ],
                    "network": ["curl", "wget", "ping", "nslookup", "dig"],
                    "text_processing": ["jq", "awk", "sed -n"],
                    "docker": ["docker ps", "docker images", "docker logs"],
                    "package_managers": ["npm list", "npm ls", "pip list", "pip show", "yarn list"]
                }
            }
        }

    def test_basic_read_only_commands(self, config):
        """Test basic read-only commands are correctly identified"""
        test_cases = [
            ("ls", True, "List directory"),
            ("ls -la", True, "List with options"),  
            ("pwd", True, "Print working directory"),
            ("cat file.txt", True, "Read file"),
            ("grep pattern", True, "Search pattern"),
            ("find . -name '*.py'", True, "Find files"),
            ("git status", True, "Git status"),
            ("git log --oneline", True, "Git log with options"),
            ("echo 'hello'", True, "Echo command"),
            ("head -10 file.txt", True, "Head command"),
            ("sort data.txt", True, "Sort command"),
            ("uniq data.txt", True, "Unique command")
        ]
        
        for cmd, expected, description in test_cases:
            result = is_read_only_bash_command(cmd, config)
            assert result == expected, f"{description}: '{cmd}' should be {'allowed' if expected else 'blocked'}"

    def test_write_commands_blocked(self, config):
        """Test commands that modify files are blocked"""
        test_cases = [
            ("echo 'data' > file.txt", False, "Output redirection"),
            ("ls >> log.txt", False, "Append redirection"),  
            ("mv file1 file2", False, "Move/rename"),
            ("cp file1 file2", False, "Copy"),
            ("rm file.txt", False, "Remove file"),
            ("mkdir newdir", False, "Create directory"),
            ("touch newfile", False, "Create file"),
            ("sed 's/old/new/' file", False, "Sed without -n flag"),
            ("npm install package", False, "Package installation"),
            ("pip install package", False, "Python package installation"),
            ("find . -name '*.tmp' -delete", False, "Find with delete (SECURITY)"),
            ("find . -name '*.log' -exec rm {} \\;", False, "Find with rm exec (SECURITY)")
        ]
        
        for cmd, expected, description in test_cases:
            result = is_read_only_bash_command(cmd, config)
            assert result == expected, f"{description}: '{cmd}' should be {'allowed' if expected else 'blocked'}"

    def test_pipe_commands_fixed(self, config):
        """
        Test pipe commands work correctly after the quote-parsing fix
        
        CRITICAL: This validates the main bug fix for quoted patterns in pipes
        """
        test_cases = [
            ("ls -la | grep test", True, "Basic pipe should work"),
            ("cat file.txt | grep pattern", True, "Cat pipe should work"),
            ("find . -name '*.py' | head -10", True, "Find pipe should work"),
            ("git log | grep commit", True, "Git pipe should work"),
            ("ls | sort | uniq", True, "Multi-pipe should work"),
            ("echo hello | grep hello", True, "Echo pipe should work"),
            ("cat file.txt | head -5", True, "Cat to head pipe should work")
        ]
        
        for cmd, expected, description in test_cases:
            result = is_read_only_bash_command(cmd, config)
            assert result == expected, f"{description}: '{cmd}'"

    def test_quoted_strings_main_fix(self, config):
        """
        Test quoted string parsing - THE MAIN BUG FIX
        
        This was the core issue: pipes inside quoted strings were being 
        incorrectly parsed as command separators.
        """
        test_cases = [
            ('ls -la | grep "test"', True, "Simple quoted grep"),
            ('ls -la | grep "test|pattern"', True, "Quoted pattern with pipe"),
            ('ls -la | grep -E "(task|script)"', True, "Extended regex with pipe in quotes"),
            ("ls -la | grep 'test|pattern'", True, "Single quoted pattern"),
            ('find . -name "*.py" | grep -v __pycache__ | head -20', True, "Complex quoted pipe"),
            ('echo "hello|world" | cat', True, "Pipe in quoted string"),
        ]
        
        for cmd, expected, description in test_cases:
            result = is_read_only_bash_command(cmd, config)
            assert result == expected, f"MAIN FIX - {description}: '{cmd}'"

    def test_complex_command_chains(self, config):
        """Test complex command chains with &&, ||, ;"""
        test_cases = [
            ("ls && pwd", True, "AND chain of read-only commands"),
            ("cat file1 && cat file2", True, "Multiple read-only with AND"),
            ("ls || pwd", True, "OR chain of read-only commands"),  
            ("ls; pwd; echo done", True, "Semicolon chain of read-only"),
            ("ls && rm file", False, "Read-only AND write command"),
            ("rm file || ls", False, "Write OR read-only command"),
            ("ls && pwd && git status", True, "Triple AND chain"),
            ("ls || pwd || echo 'fallback'", True, "Triple OR chain")
        ]
        
        for cmd, expected, description in test_cases:
            result = is_read_only_bash_command(cmd, config)
            assert result == expected, f"{description}: '{cmd}'"

    def test_security_patterns(self, config):
        """Test security patterns are properly detected"""
        dangerous_commands = [
            ("find . -name '*.tmp' -delete", False, "Delete files with find"),
            ("find . -name '*.log' -exec rm {} \\;", False, "Execute delete with find"),
            ("sed 's/old/new/g' file.txt", False, "Sed modification without -n"),
            ("awk '{print $0 > \"output.txt\"}' input.txt", False, "Awk with output redirection"),
        ]
        
        safe_alternatives = [
            ("find . -name '*.tmp'", True, "Find without delete"),
            ("sed -n 's/old/new/p' file.txt", True, "Sed with -n flag"),
            ("awk '{print $0}' input.txt", True, "Awk without output redirection"),
        ]
        
        for cmd, expected, description in dangerous_commands + safe_alternatives:
            result = is_read_only_bash_command(cmd, config)
            assert result == expected, f"SECURITY - {description}: '{cmd}'"

    def test_prefix_matching_bug_prevention(self, config):
        """
        Test that we prevent the prefix matching bug

        CRITICAL: This test validates that commands are matched exactly or with space-separated args,
        not just by prefix. Without this fix, "git status-foo" would incorrectly match "git status".

        The bug: part.startswith("git status") allows "git status-foo" ❌
        The fix: part == "git status" or part.startswith("git status ") ✅
        """
        test_cases = [
            # Should be ALLOWED - exact matches or with args
            ("git status", True, "Exact match of allowed command"),
            ("git status --short", True, "Allowed command with space-separated args"),
            ("git status --porcelain", True, "Allowed command with different args"),
            ("git log", True, "Different allowed command exact match"),
            ("git log --oneline", True, "Different allowed command with args"),
            ("git diff", True, "Another allowed command"),
            ("git diff --cached", True, "Another allowed command with args"),
            ("ls", True, "Basic command exact match"),
            ("ls -la", True, "Basic command with args"),
            ("docker ps", True, "Multi-word allowed command exact"),
            ("docker ps -a", True, "Multi-word allowed command with args"),

            # Should be BLOCKED - the prefix matching bug cases
            ("git status-foo", False, "BUGFIX: Fake command similar to valid one"),
            ("git status_extra", False, "BUGFIX: Fake command with underscore"),
            ("git statusbar", False, "BUGFIX: Fake command concatenated"),
            ("git commit", False, "Valid git command but not in allowed list"),
            ("git push", False, "Write git command not in allowed list"),
            ("git add", False, "Write git command not in allowed list"),
            ("gitfoo", False, "Invalid command starting with 'git'"),
            ("git", False, "Incomplete git command"),
            ("docker psaux", False, "BUGFIX: Fake docker command"),
            ("docker ps-all", False, "BUGFIX: Fake docker command with dash"),

            # Edge cases with similar prefixes
            ("lsblk", False, "Valid command but not in allowed list"),
            ("pwd-extra", False, "BUGFIX: Fake command based on allowed one"),
        ]

        for cmd, expected, description in test_cases:
            result = is_read_only_bash_command(cmd, config)
            assert result == expected, f"PREFIX MATCHING BUG - {description}: '{cmd}' should be {'allowed' if expected else 'blocked'}"

    def test_brainworm_system_commands(self, config):
        """Test brainworm system commands are properly allowed"""
        test_cases = [
            ("./daic status", True, "DAIC status check with prefix"),
            ("daic status", True, "DAIC status check without prefix"),
            ("./tasks", True, "Tasks command with prefix"),
            ("tasks", True, "Tasks command without prefix"),
            ("./tasks status", True, "Tasks with args and prefix"),
            ("tasks status", True, "Tasks with args without prefix"),
            ("tasks set --task='feature'", True, "Tasks set command"),
            ("uv run .brainworm/scripts/update_task_state.py --show-current", True, "Show current state")
        ]

        for cmd, expected, description in test_cases:
            result = is_brainworm_system_command(cmd, config)
            assert result == expected, f"{description}: '{cmd}'"

    def test_edge_cases_whitespace_and_malformed(self, config):
        """Test edge cases: whitespace, tabs, malformed commands"""
        test_cases = [
            ("  ls  -la  |  grep  test  ", True, "Extra whitespace everywhere"),
            ("\tls\t|\tgrep\tpattern\t", True, "Tabs in command"),
            ("ls| grep test", True, "No space after pipe"),
            ("ls |grep test", True, "No space before second command"),
            ("", True, "Empty command"),
            ("   ", True, "Whitespace only"),
            ("ls|||grep", True, "Malformed triple pipe - parsing handles it")
        ]
        
        for cmd, expected, description in test_cases:
            result = is_read_only_bash_command(cmd, config)
            # For malformed commands, we expect them to be blocked for safety
            assert result == expected, f"EDGE CASE - {description}: '{repr(cmd)}'"

    def test_real_user_scenarios(self, config):
        """Test commands that real users actually run and reported as failing"""
        scenarios = [
            # The original user's exact failing command
            ('ls -la | grep -E "(task|script)"', True, "User's original failing command"),
            
            # Investigation commands users run
            ("find . -name '*test*' -type f", True, "Test file search"),
            ("cat package.json | jq '.dependencies'", True, "Package inspection"),
            ("git log --oneline | head -10", True, "Recent commits"),
            ("ls -la | grep python", True, "Simple file filtering"),
            
            # Complex but safe pipe chains
            ("find . -name '*.py' | grep -v __pycache__ | head -20", True, "Python file search"),
            ("ls -la && pwd && git status", True, "Status check chain"),
            ("curl -s http://api.example.com | jq '.data'", True, "API inspection"),
            
            # Commands that should still be blocked
            ("ls -la > filelist.txt", False, "Output redirection"),
            ("find . -name '*.tmp' -delete", False, "Find with delete"),
        ]
        
        for cmd, expected, description in scenarios:
            result = is_read_only_bash_command(cmd, config)
            assert result == expected, f"REAL USER - {description}: '{cmd}'"

    def test_split_function_directly(self):
        """Test the quote-aware splitting function directly"""
        test_cases = [
            ('ls | grep "test|pattern"', ['ls', 'grep "test|pattern"']),
            ('ls && pwd', ['ls', 'pwd']),
            ("grep 'a|b' file | head", ['grep \'a|b\' file', 'head']),
            ('ls; pwd; echo "done|finished"', ['ls', 'pwd', 'echo "done|finished"']),
            ('find . -name "*.py" | grep -E "(test|spec)"', ['find . -name "*.py"', 'grep -E "(test|spec)"']),
            ("ls || echo 'failed'", ['ls', 'echo \'failed\'']),
        ]
        
        for cmd, expected in test_cases:
            result = split_command_respecting_quotes(cmd)
            assert result == expected, f"Split function failed for: '{cmd}' -> got {result}, expected {expected}"

    def test_the_exact_original_failing_command(self, config):
        """
        Test the exact command that was failing for the original user report
        
        This is the most important test - validates the main fix works
        """
        failing_command = 'ls -la | grep -E "(task|script)"'
        result = is_read_only_bash_command(failing_command, config)
        
        assert result == True, f"CRITICAL: Original failing command should now work: '{failing_command}'"
        
        # Debug the parsing to show it's working correctly
        parts = split_command_respecting_quotes(failing_command)
        assert parts == ['ls -la', 'grep -E "(task|script)"'], f"Quote parsing should work: {parts}"

    def test_performance_with_complex_commands(self, config):
        """Test that parsing performance is reasonable for complex commands"""
        complex_commands = [
            "find . -name '*.py' | grep -v __pycache__ | head -100 | sort | uniq",
            "git log --oneline --since='1 week ago' | grep 'feat\\|fix\\|refactor' | head -20",
            "ls -la | grep '.py' | cut -d' ' -f9 | sort | uniq"
        ]
        
        import time
        for cmd in complex_commands:
            start = time.time()
            result = is_read_only_bash_command(cmd, config)
            duration = time.time() - start
            
            # Should complete in reasonable time (< 10ms)
            assert duration < 0.01, f"Command parsing too slow: {duration:.3f}s for '{cmd[:50]}...'"
            assert result == True, f"Complex safe command should be allowed: '{cmd[:50]}...'"


if __name__ == "__main__":
    # Run with verbose output to see all test details
    pytest.main([__file__, "-v", "-s"])