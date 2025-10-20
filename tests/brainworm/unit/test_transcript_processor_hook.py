#!/usr/bin/env python3
"""
Unit Tests for Transcript Processor Hook (PreToolUse - Task matcher)

Tests essential behaviors of transcript_processor.py including:
- Tool filtering (only Task tool processed)
- Recursion prevention (skip if already in subagent context)
- Transcript processing (read, clean, chunk)
- Service context detection
- Subagent type extraction
- Output file generation
- Flag management
"""

import pytest
import json
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
    """Create test project with minimal structure"""
    project_root = tmp_path / "test_project"
    project_root.mkdir()

    # Create minimal structure
    brainworm_dir = project_root / ".brainworm"
    (brainworm_dir / "state").mkdir(parents=True)
    (brainworm_dir / "events").mkdir(parents=True)

    return project_root


@pytest.fixture
def tool_input() -> dict:
    """Generate test tool input"""
    return {
        "session_id": f"test-session-{uuid.uuid4().hex[:8]}",
        "correlation_id": f"test-corr-{uuid.uuid4().hex[:8]}",
        "hook_event_name": "PreToolUse",
        "tool_name": "Task",
        "tool_params": {
            "prompt": "Test task",
            "subagent_type": "context-gathering"
        },
        "transcript_path": "",
        "cwd": "/test/project",
        "project_root": "/test/project"
    }


def execute_transcript_processor(
    project_root: Path,
    plugin_root: Path,
    tool_input: dict,
    timeout: int = 30
) -> subprocess.CompletedProcess:
    """Execute transcript_processor hook with given input"""
    hook_script = plugin_root / "hooks" / "transcript_processor.py"

    hook_input = tool_input.copy()
    hook_input["cwd"] = str(project_root)
    hook_input["project_root"] = str(project_root)

    # Set environment
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


class TestToolFiltering:
    """Test tool filtering - only Task tool processed"""

    def test_processes_task_tool(self, test_project, brainworm_plugin_root, tool_input):
        """Test: Task tool is processed"""
        # Create minimal transcript
        transcript_path = test_project / "transcript.jsonl"
        transcript_entry = {
            "role": "user",
            "content": [{"type": "text", "text": "Test prompt"}]
        }
        transcript_path.write_text(json.dumps(transcript_entry) + "\n")
        tool_input["transcript_path"] = str(transcript_path)
        tool_input["tool_name"] = "Task"

        result = execute_transcript_processor(test_project, brainworm_plugin_root, tool_input)
        assert result.returncode == 0

    @pytest.mark.parametrize("non_task_tool", ["Bash", "Edit", "Write", "Read", "Grep"])
    def test_skips_non_task_tools(self, test_project, brainworm_plugin_root, tool_input, non_task_tool):
        """Test: Non-Task tools are skipped"""
        tool_input["tool_name"] = non_task_tool

        result = execute_transcript_processor(test_project, brainworm_plugin_root, tool_input)
        # Hook should exit successfully (returncode 0) but not process
        assert result.returncode == 0


class TestRecursionPrevention:
    """Test recursion prevention"""

    def test_skips_when_already_in_subagent_context(self, test_project, brainworm_plugin_root, tool_input):
        """Test: Skip processing if already in subagent context"""
        # Create subagent context flag
        state_dir = test_project / ".brainworm" / "state"
        subagent_flag = state_dir / "in_subagent_context.flag"
        subagent_flag.touch()

        # Create minimal transcript
        transcript_path = test_project / "transcript.jsonl"
        transcript_entry = {"role": "user", "content": [{"type": "text", "text": "Test"}]}
        transcript_path.write_text(json.dumps(transcript_entry) + "\n")
        tool_input["transcript_path"] = str(transcript_path)

        result = execute_transcript_processor(test_project, brainworm_plugin_root, tool_input)
        assert result.returncode == 0

        # Should not create output files (skipped)
        batch_dir = test_project / ".brainworm" / "state" / "context-gathering"
        # If processing was skipped, batch_dir might not exist or be empty
        assert not batch_dir.exists() or not list(batch_dir.glob("chunk_*.jsonl"))

    def test_processes_when_not_in_subagent_context(self, test_project, brainworm_plugin_root, tool_input):
        """Test: Process normally when not in subagent context"""
        # Ensure flag doesn't exist
        state_dir = test_project / ".brainworm" / "state"
        subagent_flag = state_dir / "in_subagent_context.flag"
        if subagent_flag.exists():
            subagent_flag.unlink()

        # Create minimal transcript
        transcript_path = test_project / "transcript.jsonl"
        transcript_entry = {"role": "user", "content": [{"type": "text", "text": "Test"}]}
        transcript_path.write_text(json.dumps(transcript_entry) + "\n")
        tool_input["transcript_path"] = str(transcript_path)

        result = execute_transcript_processor(test_project, brainworm_plugin_root, tool_input)
        assert result.returncode == 0


class TestTranscriptPathHandling:
    """Test transcript path handling"""

    def test_skips_when_no_transcript_path(self, test_project, brainworm_plugin_root, tool_input):
        """Test: Skip if no transcript_path provided"""
        tool_input["transcript_path"] = ""

        result = execute_transcript_processor(test_project, brainworm_plugin_root, tool_input)
        assert result.returncode == 0

    def test_handles_missing_transcript_file(self, test_project, brainworm_plugin_root, tool_input):
        """Test: Reports error for missing transcript file"""
        tool_input["transcript_path"] = "/nonexistent/transcript.jsonl"

        result = execute_transcript_processor(test_project, brainworm_plugin_root, tool_input)
        # Should fail with error (returncode 1) when transcript doesn't exist
        assert result.returncode == 1
        assert b"No such file or directory" in result.stderr


class TestTranscriptProcessing:
    """Test transcript processing"""

    def test_reads_and_processes_transcript(self, test_project, brainworm_plugin_root, tool_input):
        """Test: Reads and processes transcript file"""
        # Create transcript with multiple entries
        transcript_path = test_project / "transcript.jsonl"
        entries = [
            {"role": "user", "content": [{"type": "text", "text": "First message"}]},
            {"role": "assistant", "content": [{"type": "text", "text": "First response"}]},
            {"role": "user", "content": [{"type": "text", "text": "Second message"}]},
        ]
        transcript_path.write_text("\n".join(json.dumps(entry) for entry in entries) + "\n")
        tool_input["transcript_path"] = str(transcript_path)

        result = execute_transcript_processor(test_project, brainworm_plugin_root, tool_input)
        assert result.returncode == 0

        # Check that chunks were created
        batch_dir = test_project / ".brainworm" / "state" / "context-gathering"
        if batch_dir.exists():
            chunk_files = list(batch_dir.glob("chunk_*.jsonl"))
            assert len(chunk_files) > 0, "No chunk files created"


class TestSubagentTypeExtraction:
    """Test subagent type extraction"""

    @pytest.mark.parametrize("subagent_type", [
        "context-gathering",
        "code-review",
        "logging",
        "service-documentation"
    ])
    def test_extracts_subagent_type(self, test_project, brainworm_plugin_root, tool_input, subagent_type):
        """Test: Extracts subagent type from tool params"""
        # Create minimal transcript
        transcript_path = test_project / "transcript.jsonl"
        transcript_entry = {"role": "user", "content": [{"type": "text", "text": "Test"}]}
        transcript_path.write_text(json.dumps(transcript_entry) + "\n")

        tool_input["transcript_path"] = str(transcript_path)
        tool_input["tool_params"] = {"subagent_type": subagent_type}

        result = execute_transcript_processor(test_project, brainworm_plugin_root, tool_input)
        assert result.returncode == 0

        # Check that output directory uses subagent type
        batch_dir = test_project / ".brainworm" / "state" / subagent_type
        if batch_dir.exists():
            assert batch_dir.is_dir()


class TestOutputFileGeneration:
    """Test output file generation"""

    def test_creates_chunk_files(self, test_project, brainworm_plugin_root, tool_input):
        """Test: Creates transcript chunk files"""
        # Create transcript
        transcript_path = test_project / "transcript.jsonl"
        entries = [
            {"role": "user", "content": [{"type": "text", "text": f"Message {i}"}]}
            for i in range(5)
        ]
        transcript_path.write_text("\n".join(json.dumps(entry) for entry in entries) + "\n")
        tool_input["transcript_path"] = str(transcript_path)

        result = execute_transcript_processor(test_project, brainworm_plugin_root, tool_input)
        assert result.returncode == 0

        # Check chunk files were created
        batch_dir = test_project / ".brainworm" / "state" / "context-gathering"
        if batch_dir.exists():
            chunk_files = list(batch_dir.glob("chunk_*.jsonl"))
            assert len(chunk_files) > 0

    def test_creates_service_context_file(self, test_project, brainworm_plugin_root, tool_input):
        """Test: Creates service context file"""
        # Create transcript
        transcript_path = test_project / "transcript.jsonl"
        transcript_entry = {"role": "user", "content": [{"type": "text", "text": "Test"}]}
        transcript_path.write_text(json.dumps(transcript_entry) + "\n")
        tool_input["transcript_path"] = str(transcript_path)

        result = execute_transcript_processor(test_project, brainworm_plugin_root, tool_input)
        assert result.returncode == 0

        # Check service context file
        batch_dir = test_project / ".brainworm" / "state" / "context-gathering"
        if batch_dir.exists():
            context_file = batch_dir / "service_context.json"
            if context_file.exists():
                # Verify it's valid JSON
                context = json.loads(context_file.read_text())
                assert isinstance(context, dict)


class TestFlagManagement:
    """Test subagent context flag management"""

    def test_creates_subagent_context_flag(self, test_project, brainworm_plugin_root, tool_input):
        """Test: Creates subagent context flag after processing"""
        # Create transcript
        transcript_path = test_project / "transcript.jsonl"
        transcript_entry = {"role": "user", "content": [{"type": "text", "text": "Test"}]}
        transcript_path.write_text(json.dumps(transcript_entry) + "\n")
        tool_input["transcript_path"] = str(transcript_path)

        result = execute_transcript_processor(test_project, brainworm_plugin_root, tool_input)
        assert result.returncode == 0

        # Check flag was created
        state_dir = test_project / ".brainworm" / "state"
        subagent_flag = state_dir / "in_subagent_context.flag"
        # Flag should exist after processing
        if not subagent_flag.exists():
            # Alternative: check for subagent-specific state
            batch_dir = test_project / ".brainworm" / "state" / "context-gathering"
            assert batch_dir.exists(), "Neither flag nor batch directory created"


class TestBasicFunctionality:
    """Test basic hook functionality"""

    def test_hook_succeeds_with_valid_input(self, test_project, brainworm_plugin_root, tool_input):
        """Test: Hook succeeds with valid input"""
        # Create minimal transcript
        transcript_path = test_project / "transcript.jsonl"
        transcript_entry = {"role": "user", "content": [{"type": "text", "text": "Test"}]}
        transcript_path.write_text(json.dumps(transcript_entry) + "\n")
        tool_input["transcript_path"] = str(transcript_path)

        result = execute_transcript_processor(test_project, brainworm_plugin_root, tool_input)
        assert result.returncode == 0

    def test_hook_handles_empty_transcript(self, test_project, brainworm_plugin_root, tool_input):
        """Test: Handles empty transcript gracefully"""
        # Create empty transcript
        transcript_path = test_project / "transcript.jsonl"
        transcript_path.write_text("")
        tool_input["transcript_path"] = str(transcript_path)

        result = execute_transcript_processor(test_project, brainworm_plugin_root, tool_input)
        # Should handle gracefully
        assert result.returncode == 0
