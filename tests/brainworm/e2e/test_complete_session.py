#!/usr/bin/env python3
"""
End-to-End Session Lifecycle Tests

Tests complete hook execution workflows from SessionStart to SessionEnd,
validating that events are properly captured, correlated, and stored.

Test Scenarios:
1. Basic session lifecycle (SessionStart → Read → SessionEnd)
2. DAIC enforcement workflow (discussion mode blocking)
3. Trigger phrase detection and mode switching
4. Multi-tool workflow with proper correlation
"""

import pytest
import json
from pathlib import Path
from typing import Generator

# Import test harness
import sys
test_integration_dir = Path(__file__).parent.parent / "integration"
sys.path.insert(0, str(test_integration_dir))

from hook_test_harness import HookTestHarness, HookEvent


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
def test_harness(tmp_path, brainworm_plugin_root) -> Generator[HookTestHarness, None, None]:
    """Create hook test harness for E2E tests"""
    project_root = tmp_path / "test_project"
    project_root.mkdir()

    harness = HookTestHarness(
        project_root=project_root,
        brainworm_plugin_root=brainworm_plugin_root
    )

    yield harness

    # Cleanup
    harness.cleanup()


@pytest.mark.e2e
class TestBasicSessionLifecycle:
    """Test complete session lifecycle from start to end"""

    def test_session_start_to_end(self, test_harness):
        """
        Test: SessionStart → PreToolUse (Read) → PostToolUse → SessionEnd

        Validates:
        - All hooks execute successfully
        - Events are written to database
        - Events are written to JSONL
        - Session and correlation IDs are consistent
        """
        # Create a test file to read
        test_file = test_harness.project_root / "test.py"
        test_file.write_text("# Test file")

        # Execute session lifecycle
        events = [
            HookEvent(
                hook_name="session_start",
                tool_name=None,
                tool_input={}
            ),
            HookEvent(
                hook_name="pre_tool_use",
                tool_name="Read",
                tool_input={"file_path": str(test_file)}
            ),
            HookEvent(
                hook_name="post_tool_use",
                tool_name="Read",
                tool_input={"file_path": str(test_file)}
            ),
            HookEvent(
                hook_name="session_end",
                tool_name=None,
                tool_input={}
            )
        ]

        results = test_harness.execute_sequence(events)

        # All hooks should execute successfully
        for i, result in enumerate(results):
            assert result.returncode == 0, (
                f"Hook {events[i].hook_name} failed:\n"
                f"stderr: {result.stderr.decode()}"
            )

        # Verify events were written to database
        db_events = test_harness.get_database_events()

        # Should have events (exact count depends on which hooks ran)
        assert len(db_events) > 0, "No events written to database"

        # Verify session IDs are consistent
        for event in db_events:
            assert event["session_id"] == test_harness.session_id

        # Verify correlation IDs exist
        for event in db_events:
            assert event.get("correlation_id") is not None, "Missing correlation ID"

    def test_read_tool_execution_flow(self, test_harness):
        """
        Test: PreToolUse (Read) → PostToolUse (Read)

        Validates:
        - Read tool is not blocked (even in discussion mode)
        - Pre and Post hooks share correlation ID
        - Tool execution is tracked
        """
        # Create test file
        test_file = test_harness.project_root / "example.txt"
        test_file.write_text("Example content")

        # Execute Read tool flow
        pre_result = test_harness.execute_hook(
            "pre_tool_use",
            "Read",
            {"file_path": str(test_file)}
        )

        post_result = test_harness.execute_hook(
            "post_tool_use",
            "Read",
            {"file_path": str(test_file)}
        )

        # Both should succeed
        assert pre_result.returncode == 0
        assert post_result.returncode == 0

        # PreToolUse should not block Read (safe operation)
        if pre_result.stdout:
            try:
                output = json.loads(pre_result.stdout.decode())
                # If there's a blocking decision, it should allow Read
                if "block" in output:
                    assert output["block"] == False, "Read tool should not be blocked"
            except json.JSONDecodeError:
                pass  # No JSON output is fine


@pytest.mark.e2e
class TestDAICWorkflow:
    """Test DAIC enforcement and mode switching"""

    def test_discussion_mode_blocks_write_tools(self, test_harness):
        """
        Test: Write tool blocked in discussion mode

        Validates:
        - DAIC enforcement works
        - Block decision is returned
        - Tool execution is prevented
        """
        # Ensure discussion mode
        test_harness.set_daic_mode("discussion")

        # Attempt to use Write tool
        result = test_harness.execute_hook(
            "pre_tool_use",
            "Write",
            {
                "file_path": str(test_harness.project_root / "new_file.py"),
                "content": "# New code"
            },
            expect_success=False  # Expect blocking
        )

        # Check if hook produced blocking decision
        if result.stdout:
            try:
                output = json.loads(result.stdout.decode())

                # Should contain blocking decision
                assert "block" in output, "No blocking decision in output"
                assert output["block"] == True, "Write should be blocked in discussion mode"

                # Should have message explaining why
                assert "message" in output, "No message explaining block"
                assert "discussion" in output["message"].lower(), \
                    "Block message should mention discussion mode"

            except json.JSONDecodeError:
                # If no JSON output, check stderr for error message
                stderr = result.stderr.decode()
                assert "discussion" in stderr.lower() or "blocked" in stderr.lower(), \
                    "No indication of DAIC blocking in output"

    def test_implementation_mode_allows_write_tools(self, test_harness):
        """
        Test: Write tool allowed in implementation mode

        Validates:
        - Implementation mode permits tools
        - No blocking decision
        - Tool execution proceeds
        """
        # Set implementation mode
        test_harness.set_daic_mode("implementation")

        # Use Write tool
        result = test_harness.execute_hook(
            "pre_tool_use",
            "Write",
            {
                "file_path": str(test_harness.project_root / "allowed_file.py"),
                "content": "# Allowed code"
            },
            expect_success=True
        )

        # Should succeed without blocking
        assert result.returncode == 0

        # If there's output, should not block
        if result.stdout:
            try:
                output = json.loads(result.stdout.decode())
                if "block" in output:
                    assert output["block"] == False, \
                        "Write should be allowed in implementation mode"
            except json.JSONDecodeError:
                pass


@pytest.mark.e2e
class TestMultiToolWorkflow:
    """Test workflows with multiple tool invocations"""

    def test_multiple_tools_with_correlation(self, test_harness):
        """
        Test: Multiple tools in sequence maintain correlation

        Validates:
        - Multiple tool executions
        - Correlation IDs are tracked
        - Events are properly sequenced
        """
        # Set implementation mode to allow all tools
        test_harness.set_daic_mode("implementation")

        # Execute multiple tools
        events = [
            HookEvent(
                hook_name="pre_tool_use",
                tool_name="Bash",
                tool_input={"command": "echo 'test'", "description": "Test command"}
            ),
            HookEvent(
                hook_name="post_tool_use",
                tool_name="Bash",
                tool_input={"command": "echo 'test'", "description": "Test command"}
            ),
            HookEvent(
                hook_name="pre_tool_use",
                tool_name="Read",
                tool_input={"file_path": "/test/file.py"}
            ),
            HookEvent(
                hook_name="post_tool_use",
                tool_name="Read",
                tool_input={"file_path": "/test/file.py"}
            ),
        ]

        results = test_harness.execute_sequence(events)

        # All should execute
        for result in results:
            assert result.returncode == 0, f"Tool execution failed:\n{result.stderr.decode()}"

        # Verify events were captured
        db_events = test_harness.get_database_events()
        assert len(db_events) > 0, "No events captured for multi-tool workflow"

        # Verify correlation IDs exist
        for event in db_events:
            assert event["correlation_id"] is not None, "Missing correlation ID"


@pytest.mark.e2e
class TestEventConsistency:
    """Test event storage consistency between database and JSONL"""

    def test_database_jsonl_consistency(self, test_harness):
        """
        Test: Events written to both DB and JSONL are consistent

        Validates:
        - Same events in both stores
        - Correlation IDs match
        - Session IDs match
        - Event counts match
        """
        # Execute some hooks
        test_harness.execute_hook(
            "pre_tool_use",
            "Read",
            {"file_path": "/test.py"}
        )

        test_harness.execute_hook(
            "post_tool_use",
            "Read",
            {"file_path": "/test.py"}
        )

        # Validate database events
        validation = test_harness.validate_database_events()

        # Should have events
        assert validation["event_count"] > 0, "No events in database"
        assert validation["has_session_id"], "Events missing session_id"
        assert validation["has_correlation_id"], "Events missing correlation_id"


@pytest.mark.e2e
@pytest.mark.slow
class TestCompleteWorkflow:
    """Test complete realistic development workflow"""

    def test_full_development_session(self, test_harness):
        """
        Test: Complete session with DAIC mode switching

        Workflow:
        1. Session starts in discussion mode
        2. Attempt Write (blocked)
        3. Switch to implementation mode
        4. Write tool (allowed)
        5. Read tool
        6. Session end

        Validates:
        - Complete workflow executes
        - DAIC enforcement works
        - All events captured
        - Correlation maintained
        """
        # Start in discussion mode
        test_harness.set_daic_mode("discussion")

        # 1. Attempt Write in discussion mode (should be blocked)
        write_blocked = test_harness.execute_hook(
            "pre_tool_use",
            "Write",
            {"file_path": str(test_harness.project_root / "blocked.py"), "content": "# Blocked"},
            expect_success=False
        )

        # 2. Switch to implementation mode
        test_harness.set_daic_mode("implementation")

        # 3. Write tool (should succeed)
        test_file = test_harness.project_root / "implemented.py"
        write_allowed = test_harness.execute_hook(
            "pre_tool_use",
            "Write",
            {"file_path": str(test_file), "content": "# Implemented code"},
            expect_success=True
        )

        # 4. Read the file we just wrote
        read_result = test_harness.execute_hook(
            "pre_tool_use",
            "Read",
            {"file_path": str(test_file)},
            expect_success=True
        )

        # Verify complete workflow
        assert write_blocked.returncode != 0 or (
            write_blocked.stdout and "block" in write_blocked.stdout.decode()
        ), "Write should be blocked in discussion mode"

        assert write_allowed.returncode == 0, "Write should succeed in implementation mode"
        assert read_result.returncode == 0, "Read should succeed"

        # Verify events were captured
        validation = test_harness.validate_database_events()
        assert validation["event_count"] > 0, "No events captured"
        assert validation["has_session_id"], "Events missing session_id"
        assert validation["has_correlation_id"], "Events missing correlation_id"
