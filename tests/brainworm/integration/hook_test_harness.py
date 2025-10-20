#!/usr/bin/env python3
"""
Hook Test Harness - E2E Testing Framework for Brainworm Hooks

Provides comprehensive testing infrastructure for hook execution sequences,
state validation, and event verification.

Usage:
    harness = HookTestHarness(project_root, plugin_root)
    harness.execute_hook("pre_tool_use", "Read", {"file_path": "/test.py"})
    events = harness.get_events_written()
"""

import json
import subprocess
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import time


@dataclass
class HookEvent:
    """Represents a single hook event in a test sequence"""
    hook_name: str
    tool_name: Optional[str]
    tool_input: Dict[str, Any]
    expected_output: Optional[Dict[str, Any]] = None
    expected_block: Optional[bool] = None
    expected_files_created: Optional[List[Path]] = None


class HookTestHarness:
    """
    Test harness for simulating Claude Code hook execution sequences.

    Provides:
    - Hook invocation with stdin/stdout JSON
    - State file validation
    - Database content assertions
    - JSONL event log verification
    - Session and correlation ID management

    Example:
        harness = HookTestHarness(tmp_path / "project", plugin_root)

        # Execute single hook
        result = harness.execute_hook("pre_tool_use", "Read", {"file_path": "/test.py"})

        # Execute sequence
        events = [
            HookEvent("session_start", None, {}),
            HookEvent("pre_tool_use", "Read", {"file_path": "/test.py"}),
            HookEvent("post_tool_use", "Read", {"file_path": "/test.py"}),
        ]
        results = harness.execute_sequence(events)

        # Validate results
        db_events = harness.get_database_events()
        jsonl_events = harness.get_events_written()
    """

    def __init__(
        self,
        project_root: Path,
        brainworm_plugin_root: Path,
        session_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        """
        Initialize hook test harness.

        Args:
            project_root: Path to test project directory
            brainworm_plugin_root: Path to brainworm plugin source
            session_id: Optional session ID (generated if not provided)
            correlation_id: Optional correlation ID (generated if not provided)
        """
        self.project_root = Path(project_root)
        self.plugin_root = Path(brainworm_plugin_root)
        self.brainworm_dir = self.project_root / ".brainworm"

        # Generate IDs if not provided
        import uuid
        self.session_id = session_id or f"test-session-{uuid.uuid4().hex[:8]}"
        self.correlation_id = correlation_id or f"test-corr-{uuid.uuid4().hex[:8]}"

        self._setup_project_structure()

    def _setup_project_structure(self):
        """Create realistic .brainworm directory structure for testing"""
        # Create directory structure
        self.brainworm_dir.mkdir(parents=True, exist_ok=True)
        (self.brainworm_dir / "state").mkdir(exist_ok=True)
        (self.brainworm_dir / "events").mkdir(exist_ok=True)
        (self.brainworm_dir / "logs").mkdir(exist_ok=True)

        # Create minimal config
        config_content = """[daic]
enabled = true
default_mode = "discussion"
blocked_tools = ["Write", "Edit", "MultiEdit", "NotebookEdit"]
trigger_phrases = ["make it so", "go ahead", "ship it", "let's do it", "execute", "implement it"]

[debug]
enabled = false
level = "INFO"
format = "text"

[debug.outputs]
stderr = false
file = false
framework = false
"""
        (self.brainworm_dir / "config.toml").write_text(config_content)

        # Create initial unified session state
        self._write_state({
            "daic_mode": "discussion",
            "session_id": self.session_id,
            "correlation_id": self.correlation_id,
            "plugin_root": str(self.plugin_root),
            "current_task": None,
            "current_branch": "main"
        })

    def _write_state(self, state: Dict[str, Any]):
        """Write unified session state"""
        state_file = self.brainworm_dir / "state" / "unified_session_state.json"
        state_file.write_text(json.dumps(state, indent=2))

    def _read_state(self) -> Dict[str, Any]:
        """Read current session state"""
        state_file = self.brainworm_dir / "state" / "unified_session_state.json"
        if not state_file.exists():
            return {}
        return json.loads(state_file.read_text())

    def set_daic_mode(self, mode: str):
        """
        Set DAIC mode for testing.

        Args:
            mode: "discussion" or "implementation"
        """
        state = self._read_state()
        state["daic_mode"] = mode
        self._write_state(state)

    def enable_debug_logging(self, format: str = "json", outputs: Dict[str, bool] = None):
        """
        Enable debug logging for testing.

        Args:
            format: "json" or "text"
            outputs: Dict with keys stderr, file, framework (defaults to file=True)
        """
        if outputs is None:
            outputs = {"stderr": False, "file": True, "framework": False}

        config_file = self.brainworm_dir / "config.toml"
        config_content = config_file.read_text()

        # Update debug section
        config_content = config_content.replace("enabled = false", "enabled = true", 1)
        config_content = config_content.replace(f'format = "text"', f'format = "{format}"')

        # Update outputs
        for key, value in outputs.items():
            config_content = config_content.replace(
                f'{key} = {str(not value).lower()}',
                f'{key} = {str(value).lower()}'
            )

        config_file.write_text(config_content)

    def execute_hook(
        self,
        hook_name: str,
        tool_name: Optional[str],
        tool_input: Dict[str, Any],
        timeout: int = 10,
        expect_success: bool = True
    ) -> subprocess.CompletedProcess:
        """
        Execute a single hook with given input.

        Args:
            hook_name: Name of hook (e.g., "pre_tool_use", "session_start")
            tool_name: Tool being used (e.g., "Read", "Write") or None
            tool_input: Tool input parameters
            timeout: Execution timeout in seconds
            expect_success: Whether to expect successful execution

        Returns:
            CompletedProcess with stdout/stderr

        Raises:
            subprocess.TimeoutExpired: If hook execution times out
            AssertionError: If expect_success=True but hook fails
        """
        hook_script = self.plugin_root / "hooks" / f"{hook_name}.py"

        if not hook_script.exists():
            raise FileNotFoundError(f"Hook script not found: {hook_script}")

        # Build hook input matching Claude Code's format
        hook_input = {
            "session_id": self.session_id,
            "correlation_id": self.correlation_id,
            "cwd": str(self.project_root),
            "project_root": str(self.project_root),
            "hook_event_name": self._hook_name_to_event(hook_name),
        }

        # Add tool-specific fields
        if tool_name:
            hook_input["tool_name"] = tool_name
            hook_input["tool_input"] = tool_input

        # Execute hook via subprocess
        result = subprocess.run(
            ["uv", "run", str(hook_script)],
            input=json.dumps(hook_input).encode(),
            capture_output=True,
            timeout=timeout,
            cwd=self.project_root
        )

        # Check for expected success/failure
        if expect_success and result.returncode != 0:
            raise AssertionError(
                f"Hook {hook_name} failed unexpectedly:\n"
                f"returncode: {result.returncode}\n"
                f"stdout: {result.stdout.decode()}\n"
                f"stderr: {result.stderr.decode()}"
            )

        return result

    def _hook_name_to_event(self, hook_name: str) -> str:
        """Convert hook filename to hook event name"""
        # Map hook filenames to event names
        mapping = {
            "session_start": "SessionStart",
            "session_end": "SessionEnd",
            "user_prompt_submit": "UserPromptSubmit",
            "pre_tool_use": "PreToolUse",
            "post_tool_use": "PostToolUse",
            "stop": "Stop",
            "notification": "Notification"
        }
        return mapping.get(hook_name, hook_name)

    def execute_sequence(self, events: List[HookEvent]) -> List[subprocess.CompletedProcess]:
        """
        Execute a sequence of hook events.

        Args:
            events: List of HookEvent objects defining the sequence

        Returns:
            List of CompletedProcess results for each event

        Example:
            events = [
                HookEvent("session_start", None, {}),
                HookEvent("pre_tool_use", "Read", {"file_path": "/test.py"}),
                HookEvent("post_tool_use", "Read", {"file_path": "/test.py"}),
            ]
            results = harness.execute_sequence(events)
        """
        results = []

        for event in events:
            result = self.execute_hook(
                event.hook_name,
                event.tool_name,
                event.tool_input
            )
            results.append(result)

            # Validate expected output if specified
            if event.expected_output and result.stdout:
                try:
                    output = json.loads(result.stdout.decode())
                    assert output == event.expected_output, (
                        f"Output mismatch for {event.hook_name}:\n"
                        f"Expected: {event.expected_output}\n"
                        f"Got: {output}"
                    )
                except json.JSONDecodeError:
                    # Some hooks don't produce JSON output
                    pass

            # Validate blocking decision if specified
            if event.expected_block is not None and result.stdout:
                try:
                    output = json.loads(result.stdout.decode())
                    actual_block = output.get("block", False)
                    assert actual_block == event.expected_block, (
                        f"Block decision mismatch for {event.hook_name}:\n"
                        f"Expected block={event.expected_block}, got block={actual_block}"
                    )
                except json.JSONDecodeError:
                    pass

            # Validate files created if specified
            if event.expected_files_created:
                for expected_file in event.expected_files_created:
                    assert expected_file.exists(), (
                        f"Expected file {expected_file} to be created by {event.hook_name}"
                    )

        return results

    def get_debug_logs(self, format: str = "json") -> List[Dict[str, Any]]:
        """
        Read debug logs from .brainworm/logs/debug.{jsonl,log}

        Args:
            format: "json" for JSONL or "text" for text logs

        Returns:
            List of log entries (dicts for json, strings for text)
        """
        logs = []

        if format == "json":
            debug_file = self.brainworm_dir / "logs" / "debug.jsonl"
            if debug_file.exists():
                with open(debug_file) as f:
                    for line in f:
                        if line.strip():
                            try:
                                logs.append(json.loads(line))
                            except json.JSONDecodeError:
                                pass
        else:
            debug_file = self.brainworm_dir / "logs" / "debug.log"
            if debug_file.exists():
                with open(debug_file) as f:
                    logs = [line.strip() for line in f if line.strip()]

        return logs

    def get_database_events(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Query events from SQLite database.

        Args:
            session_id: Filter by session_id, or None for current session

        Returns:
            List of event dictionaries
        """
        db_path = self.brainworm_dir / "events" / "hooks.db"
        if not db_path.exists():
            return []

        if session_id is None:
            session_id = self.session_id

        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.execute("""
                SELECT
                    session_id,
                    correlation_id,
                    hook_name,
                    timestamp,
                    execution_id,
                    event_data
                FROM hook_events
                WHERE session_id = ?
                ORDER BY timestamp
            """, (session_id,))

            return [
                {
                    "session_id": row[0],
                    "correlation_id": row[1],
                    "hook_name": row[2],
                    "timestamp": row[3],
                    "execution_id": row[4],
                    "event_data": json.loads(row[5]) if row[5] else {}
                }
                for row in cursor.fetchall()
            ]

    def validate_database_events(self) -> Dict[str, Any]:
        """
        Validate database events for completeness and consistency.

        Returns:
            Dictionary with validation results:
            - event_count: int
            - has_session_id: bool
            - has_correlation_id: bool
            - unique_hooks: List[str]
        """
        db_events = self.get_database_events()

        has_session_id = all(e.get("session_id") == self.session_id for e in db_events)
        has_correlation_id = all(e.get("correlation_id") is not None for e in db_events)
        unique_hooks = list(set(e.get("hook_name") for e in db_events if e.get("hook_name")))

        return {
            "event_count": len(db_events),
            "has_session_id": has_session_id,
            "has_correlation_id": has_correlation_id,
            "unique_hooks": unique_hooks
        }

    def assert_events_written(self, expected_count: int):
        """
        Assert that expected number of events were written to database.

        Args:
            expected_count: Expected number of events

        Raises:
            AssertionError: If event counts don't match
        """
        validation = self.validate_database_events()

        assert validation["event_count"] == expected_count, (
            f"Expected {expected_count} events in database, got {validation['event_count']}"
        )

        assert validation["has_session_id"], (
            "Not all events have correct session_id"
        )

        assert validation["has_correlation_id"], (
            "Not all events have correlation_id"
        )

    def cleanup(self):
        """Clean up test project directory"""
        import shutil
        if self.project_root.exists():
            shutil.rmtree(self.project_root)
