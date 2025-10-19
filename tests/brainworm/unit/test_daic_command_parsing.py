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

# Import from brainworm plugin package
from brainworm.hooks.pre_tool_use import is_read_only_bash_command, is_brainworm_system_command
from brainworm.utils.bash_validator import split_command_respecting_quotes


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
                    "package_managers": ["npm list", "npm ls", "pip list", "pip show", "yarn list"],
                    "testing": [
                        "pytest", "python -m pytest", "python -m unittest", "uv run pytest",
                        "npm test", "npm run test", "yarn test", "yarn run test",
                        "npx jest", "npx vitest", "pnpm test", "pnpm run test",
                        "cargo test", "go test", "mvn test", "gradle test",
                        "rake test", "mix test", "dotnet test", "rspec", "make test"
                    ]
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

    def test_daic_status_not_blocked_in_discussion_mode(self, config, tmp_path):
        """
        REGRESSION TEST: Ensure ./daic status is NOT blocked in discussion mode

        Bug: Lines 141-142 of pre_tool_use.py were blocking ALL ./daic commands
        in discussion mode, including read-only queries like ./daic status.

        Fix: Check for mode-switching subcommands (implementation, toggle) only,
        not all daic commands.

        This test validates the complete blocking logic, not just the
        is_brainworm_system_command check.
        """
        from brainworm.hooks.pre_tool_use import should_block_tool_daic
        from brainworm.utils.hook_types import DAICMode

        # Create a minimal project directory structure
        project_root = tmp_path / "test_project"
        state_dir = project_root / ".brainworm" / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        # DAIC state: discussion mode
        daic_state = {
            "mode": str(DAICMode.DISCUSSION),
            "timestamp": None,
            "previous_mode": None
        }

        # Test cases: (command, should_block, description)
        test_cases = [
            # Read-only daic commands - should be ALLOWED in discussion mode
            ("./daic status", False, "daic status should be allowed (read-only query)"),
            ("daic status", False, "daic status without ./ should be allowed"),
            (".brainworm/plugin-launcher daic_command.py status", False, "slash command status should be allowed"),

            # Mode-switching daic commands - should be BLOCKED in discussion mode
            ("./daic implementation", True, "daic implementation should be blocked"),
            ("daic implementation", True, "daic implementation without ./ should be blocked"),
            ("./daic toggle", True, "daic toggle should be blocked"),
            ("daic toggle", True, "daic toggle without ./ should be blocked"),
            (".brainworm/plugin-launcher daic_command.py implementation", True, "slash command implementation should be blocked"),
            (".brainworm/plugin-launcher daic_command.py toggle", True, "slash command toggle should be blocked"),

            # Discussion mode daic command - allowed (you're already there)
            ("./daic discussion", False, "daic discussion should be allowed (noop in discussion mode)"),
        ]

        for command, should_block, description in test_cases:
            raw_input_data = {
                "tool_name": "Bash",
                "tool_input": {"command": command}
            }

            result = should_block_tool_daic(raw_input_data, config, daic_state, project_root)

            assert result.should_block == should_block, \
                f"REGRESSION - {description}: '{command}' - expected block={should_block}, got block={result.should_block}, reason={result.reason}"

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

    def test_dev_null_redirections(self, config):
        """
        Test that redirections to /dev/null are allowed in discussion mode

        CRITICAL: Agents frequently use 2>/dev/null to suppress error messages
        in read-only commands. These should be allowed.
        """
        test_cases = [
            # Should be ALLOWED - redirections to /dev/null
            ("ls 2>/dev/null", True, "stderr to /dev/null"),
            ("cat file.txt 2>/dev/null", True, "cat stderr to /dev/null"),
            ("grep pattern file 2>/dev/null", True, "grep stderr to /dev/null"),
            ("ls -lt .brainworm/timing/*.jsonl 2>/dev/null", True, "ls with path stderr to /dev/null"),
            ("cat .brainworm/session_start_errors.log 2>/dev/null", True, "cat log file stderr to /dev/null"),
            ("find . -name '*.py' 2>/dev/null", True, "find stderr to /dev/null"),
            ("ls 1>/dev/null", True, "stdout to /dev/null"),
            ("echo test >/dev/null", True, "stdout redirection to /dev/null"),
            ("ls &>/dev/null", True, "both stdout and stderr to /dev/null"),
            ("ls 2>&1 >/dev/null", True, "complex redirection with /dev/null"),

            # Should be BLOCKED - actual file writes
            ("ls > output.txt", False, "stdout to file"),
            ("ls 2> errors.txt", False, "stderr to file"),
            ("echo test > file.txt", False, "echo to file"),
            ("cat file1 > file2", False, "cat to file"),
        ]

        for cmd, expected, description in test_cases:
            result = is_read_only_bash_command(cmd, config)
            assert result == expected, f"DEV_NULL - {description}: '{cmd}' should be {'allowed' if expected else 'blocked'}"

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

    def test_testing_commands_allowed(self, config):
        """
        Test that test execution commands are allowed in discussion mode

        CRITICAL: Tests are read-only exploration that inform planning decisions.
        They should be allowed in discussion mode for understanding codebase behavior.
        """
        test_cases = [
            # Python testing
            ("pytest", True, "Basic pytest"),
            ("pytest -v", True, "pytest with verbose flag"),
            ("pytest tests/", True, "pytest with path"),
            ("pytest tests/unit/test_foo.py", True, "pytest specific file"),
            ("pytest -v -s --cov=brainworm", True, "pytest with coverage"),
            ("python -m pytest", True, "pytest via python -m"),
            ("python -m pytest tests/", True, "pytest via python -m with path"),
            ("python -m unittest", True, "unittest via python -m"),
            ("python -m unittest discover", True, "unittest discover"),
            ("uv run pytest", True, "pytest via uv run"),
            ("uv run pytest tests/brainworm/", True, "pytest via uv run with path"),
            ("uv run pytest --cov=brainworm --cov-report=term-missing tests/", True, "pytest via uv with coverage"),

            # JavaScript/TypeScript testing
            ("npm test", True, "npm test"),
            ("npm run test", True, "npm run test"),
            ("npm test -- --verbose", True, "npm test with args"),
            ("yarn test", True, "yarn test"),
            ("yarn run test", True, "yarn run test"),
            ("yarn test --coverage", True, "yarn test with coverage"),
            ("npx jest", True, "jest via npx"),
            ("npx jest tests/", True, "jest with path"),
            ("npx jest --coverage", True, "jest with coverage"),
            ("npx vitest", True, "vitest via npx"),
            ("npx vitest run", True, "vitest run"),
            ("pnpm test", True, "pnpm test"),
            ("pnpm run test", True, "pnpm run test"),

            # Other language testing
            ("cargo test", True, "Rust cargo test"),
            ("cargo test --lib", True, "cargo test with flags"),
            ("go test", True, "Go test"),
            ("go test ./...", True, "Go test all packages"),
            ("go test -v", True, "Go test verbose"),
            ("mvn test", True, "Maven test"),
            ("mvn test -Dtest=FooTest", True, "Maven specific test"),
            ("gradle test", True, "Gradle test"),
            ("gradle test --tests FooTest", True, "Gradle specific test"),
            ("rake test", True, "Ruby rake test"),
            ("mix test", True, "Elixir mix test"),
            ("mix test --trace", True, "Elixir mix test with trace"),
            ("dotnet test", True, "dotnet test"),
            ("dotnet test --verbosity normal", True, "dotnet test with verbosity"),
            ("rspec", True, "RSpec"),
            ("rspec spec/", True, "RSpec with path"),
            ("rspec --format documentation", True, "RSpec with format"),
            ("make test", True, "Make test"),

            # Test commands with output redirection should be blocked
            ("pytest > test_output.txt", False, "pytest with output redirect"),
            ("npm test > results.txt", False, "npm test with output redirect"),
            ("cargo test >> log.txt", False, "cargo test with append redirect"),

            # Test commands in chains - only all-safe chains allowed
            ("pytest && echo 'done'", True, "pytest with echo chain"),
            ("npm test && npm run build", False, "test then build (build may write)"),
            ("pytest || echo 'failed'", True, "pytest with echo fallback"),

            # Edge cases
            ("pytest tests/ 2>/dev/null", True, "pytest with stderr to /dev/null"),
            ("npm test 2>&1", True, "npm test with stderr redirect to stdout"),
            ("uv run pytest tests/ --verbose", True, "uv pytest with multiple flags"),
        ]

        for cmd, expected, description in test_cases:
            result = is_read_only_bash_command(cmd, config)
            assert result == expected, f"TESTING COMMANDS - {description}: '{cmd}' should be {'allowed' if expected else 'blocked'}"

    def test_testing_commands_prefix_matching(self, config):
        """
        Test that test commands use exact matching, not prefix matching

        Validates that 'pytest-foo' doesn't match 'pytest'
        """
        test_cases = [
            # Should be ALLOWED - exact matches or with args
            ("pytest", True, "Exact pytest"),
            ("pytest tests/", True, "pytest with path"),
            ("pytest --verbose", True, "pytest with flag"),
            ("npm test", True, "Exact npm test"),
            ("npm test -- --coverage", True, "npm test with args"),
            ("cargo test", True, "Exact cargo test"),
            ("cargo test --lib", True, "cargo test with flag"),

            # Should be BLOCKED - fake commands
            ("pytest-foo", False, "Fake pytest command"),
            ("pytest_bar", False, "Fake pytest command with underscore"),
            ("pytestify", False, "Fake command starting with pytest"),
            ("npm testify", False, "npm with non-test command"),
            ("cargo testing", False, "cargo with non-test command"),
        ]

        for cmd, expected, description in test_cases:
            result = is_read_only_bash_command(cmd, config)
            assert result == expected, f"TEST PREFIX - {description}: '{cmd}' should be {'allowed' if expected else 'blocked'}"

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