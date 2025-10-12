"""
Unit tests for wait_for_transcripts.py script.

Tests the exponential backoff retry logic for waiting on transcript files
to solve the race condition between hook execution and file writing.
"""

import pytest
import time
from pathlib import Path
from unittest.mock import Mock, patch
import sys
import tempfile
import shutil

# Import the script's functions
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "brainworm" / "scripts"))
from wait_for_transcripts import wait_for_transcripts, find_project_root


class TestFindProjectRoot:
    """Test project root discovery logic."""

    def test_finds_project_root_with_brainworm_dir(self, tmp_path):
        """Should find project root when .brainworm directory exists."""
        # Create .brainworm directory
        brainworm_dir = tmp_path / ".brainworm"
        brainworm_dir.mkdir()

        # Create a subdirectory and cd into it
        subdir = tmp_path / "some" / "nested" / "path"
        subdir.mkdir(parents=True)

        with patch('pathlib.Path.cwd', return_value=subdir):
            root = find_project_root()
            assert root == tmp_path

    def test_fallback_to_current_directory(self, tmp_path):
        """Should fallback to current directory if no .brainworm found."""
        with patch('pathlib.Path.cwd', return_value=tmp_path):
            root = find_project_root()
            assert root == tmp_path


class TestWaitForTranscripts:
    """Test wait_for_transcripts retry logic."""

    def test_success_when_files_exist(self, tmp_path):
        """Should return immediately when transcript files exist."""
        # Setup: Create brainworm state directory with transcript files
        state_dir = tmp_path / ".brainworm" / "state" / "logging"
        state_dir.mkdir(parents=True)

        # Create transcript files
        transcript1 = state_dir / "current_transcript_001.json"
        transcript2 = state_dir / "current_transcript_002.json"
        transcript1.write_text('{"test": "data1"}')
        transcript2.write_text('{"test": "data2"}')

        # Create service context file
        service_context = state_dir / "service_context.json"
        service_context.write_text('{"project_type": "single"}')

        # Execute
        start_time = time.time()
        result = wait_for_transcripts("logging", tmp_path, timeout_ms=5000)
        elapsed_ms = (time.time() - start_time) * 1000

        # Verify
        assert len(result) == 2
        assert transcript1 in result
        assert transcript2 in result
        # Should complete quickly (within 200ms including two polls for stability)
        assert elapsed_ms < 200

    def test_handles_plugin_namespace_prefix(self, tmp_path):
        """Should strip plugin namespace prefix from subagent type."""
        # Setup with brainworm:logging format
        state_dir = tmp_path / ".brainworm" / "state" / "logging"
        state_dir.mkdir(parents=True)

        transcript = state_dir / "current_transcript_001.json"
        transcript.write_text('{"test": "data"}')

        service_context = state_dir / "service_context.json"
        service_context.write_text('{}')

        # Execute with plugin-prefixed subagent type
        result = wait_for_transcripts("brainworm:logging", tmp_path, timeout_ms=1000)

        # Verify it found files in the 'logging' directory
        assert len(result) == 1
        assert result[0] == transcript

    def test_timeout_when_files_never_appear(self, tmp_path):
        """Should raise TimeoutError when files don't appear within timeout."""
        # Setup: Create empty directory
        state_dir = tmp_path / ".brainworm" / "state" / "logging"
        state_dir.mkdir(parents=True)

        # Execute with short timeout
        with pytest.raises(TimeoutError) as exc_info:
            wait_for_transcripts("logging", tmp_path, timeout_ms=200)

        # Verify error message contains key information
        error_msg = str(exc_info.value)
        assert "Timeout waiting for transcripts" in error_msg
        assert "Waited" in error_msg
        assert "ms" in error_msg
        assert "attempts" in error_msg

    def test_raises_filenotfound_when_directory_missing(self, tmp_path):
        """Should raise FileNotFoundError when state directory doesn't exist."""
        # No setup - directory doesn't exist

        # Execute
        with pytest.raises(FileNotFoundError) as exc_info:
            wait_for_transcripts("logging", tmp_path, timeout_ms=1000)

        # Verify error message mentions hook failure
        assert "directory does not exist" in str(exc_info.value)
        assert "transcript_processor hook never ran" in str(exc_info.value)

    def test_exponential_backoff_timing(self, tmp_path):
        """Should implement exponential backoff with correct timing."""
        # Setup: Directory exists but no files
        state_dir = tmp_path / ".brainworm" / "state" / "logging"
        state_dir.mkdir(parents=True)

        # Track poll attempts
        poll_times = []
        original_exists = Path.exists

        def track_polls(self):
            poll_times.append(time.time())
            return original_exists(self)

        with patch.object(Path, 'exists', track_polls):
            try:
                wait_for_transcripts("logging", tmp_path, timeout_ms=500, initial_delay_ms=50)
            except TimeoutError:
                pass  # Expected

        # Verify exponential backoff: 50ms, 100ms, 200ms, 400ms
        # We should see roughly these delays between polls
        if len(poll_times) >= 3:
            delay1 = (poll_times[1] - poll_times[0]) * 1000
            delay2 = (poll_times[2] - poll_times[1]) * 1000

            # Allow 20ms tolerance for system timing
            assert 40 < delay1 < 70, f"First delay should be ~50ms, got {delay1:.0f}ms"
            assert 90 < delay2 < 130, f"Second delay should be ~100ms, got {delay2:.0f}ms"

    def test_waits_for_file_stability(self, tmp_path):
        """Should wait for files to be stable (non-empty) before returning."""
        # Setup: Create directory
        state_dir = tmp_path / ".brainworm" / "state" / "logging"
        state_dir.mkdir(parents=True)

        transcript = state_dir / "current_transcript_001.json"
        service_context = state_dir / "service_context.json"

        # Start with empty files (simulating incomplete write)
        transcript.write_text("")
        service_context.write_text("")

        # After a delay, write actual content (simulating hook finishing)
        def write_content_after_delay():
            time.sleep(0.1)
            transcript.write_text('{"test": "data"}')
            service_context.write_text('{"project": "test"}')

        from threading import Thread
        writer = Thread(target=write_content_after_delay)
        writer.start()

        # Execute - should wait for content
        start_time = time.time()
        result = wait_for_transcripts("logging", tmp_path, timeout_ms=1000, initial_delay_ms=25)
        elapsed_ms = (time.time() - start_time) * 1000

        writer.join()

        # Verify it waited for content
        assert len(result) == 1
        # Should have taken at least 100ms (the delay)
        assert elapsed_ms >= 90
        # But should complete reasonably quickly
        assert elapsed_ms < 500

    def test_requires_both_transcript_and_service_context(self, tmp_path):
        """Should require both transcript and service_context.json files."""
        # Setup: Create only transcript, no service context
        state_dir = tmp_path / ".brainworm" / "state" / "logging"
        state_dir.mkdir(parents=True)

        transcript = state_dir / "current_transcript_001.json"
        transcript.write_text('{"test": "data"}')

        # Execute - should timeout waiting for service_context.json
        with pytest.raises(TimeoutError):
            wait_for_transcripts("logging", tmp_path, timeout_ms=200)

    def test_returns_sorted_transcript_list(self, tmp_path):
        """Should return transcript files in sorted order."""
        # Setup: Create multiple transcript files out of order
        state_dir = tmp_path / ".brainworm" / "state" / "logging"
        state_dir.mkdir(parents=True)

        transcript3 = state_dir / "current_transcript_003.json"
        transcript1 = state_dir / "current_transcript_001.json"
        transcript2 = state_dir / "current_transcript_002.json"

        # Write in random order
        transcript3.write_text('{"order": 3}')
        transcript1.write_text('{"order": 1}')
        transcript2.write_text('{"order": 2}')

        service_context = state_dir / "service_context.json"
        service_context.write_text('{}')

        # Execute
        result = wait_for_transcripts("logging", tmp_path, timeout_ms=1000)

        # Verify sorted order
        assert len(result) == 3
        assert result[0].name == "current_transcript_001.json"
        assert result[1].name == "current_transcript_002.json"
        assert result[2].name == "current_transcript_003.json"


class TestMainFunction:
    """Test the main() entry point."""

    def test_main_success_prints_file_paths(self, tmp_path, capsys):
        """Should print transcript file paths on success."""
        # Setup
        state_dir = tmp_path / ".brainworm" / "state" / "logging"
        state_dir.mkdir(parents=True)

        transcript1 = state_dir / "current_transcript_001.json"
        transcript2 = state_dir / "current_transcript_002.json"
        transcript1.write_text('{}')
        transcript2.write_text('{}')

        service_context = state_dir / "service_context.json"
        service_context.write_text('{}')

        # Mock sys.argv and project root
        with patch('sys.argv', ['wait_for_transcripts.py', 'logging']):
            with patch('wait_for_transcripts.find_project_root', return_value=tmp_path):
                with pytest.raises(SystemExit) as exc_info:
                    from wait_for_transcripts import main
                    main()

        # Verify exit code 0
        assert exc_info.value.code == 0

        # Verify stdout contains file paths
        captured = capsys.readouterr()
        assert str(transcript1) in captured.out
        assert str(transcript2) in captured.out

    def test_main_exits_with_code_2_on_directory_missing(self, tmp_path, capsys):
        """Should exit with code 2 when directory doesn't exist."""
        # Mock sys.argv
        with patch('sys.argv', ['wait_for_transcripts.py', 'logging']):
            with patch('wait_for_transcripts.find_project_root', return_value=tmp_path):
                with pytest.raises(SystemExit) as exc_info:
                    from wait_for_transcripts import main
                    main()

        # Verify exit code 2
        assert exc_info.value.code == 2

        # Verify error message
        captured = capsys.readouterr()
        assert "does not exist" in captured.err

    def test_main_exits_with_code_3_on_timeout(self, tmp_path, capsys):
        """Should exit with code 3 on timeout."""
        # Setup: Empty directory
        state_dir = tmp_path / ".brainworm" / "state" / "logging"
        state_dir.mkdir(parents=True)

        # Mock sys.argv with short timeout
        with patch('sys.argv', ['wait_for_transcripts.py', 'logging', '100']):
            with patch('wait_for_transcripts.find_project_root', return_value=tmp_path):
                with pytest.raises(SystemExit) as exc_info:
                    from wait_for_transcripts import main
                    main()

        # Verify exit code 3
        assert exc_info.value.code == 3

        # Verify error message
        captured = capsys.readouterr()
        assert "Timeout" in captured.err

    def test_main_requires_subagent_type_argument(self, capsys):
        """Should exit with error if no subagent type provided."""
        with patch('sys.argv', ['wait_for_transcripts.py']):
            with pytest.raises(SystemExit) as exc_info:
                from wait_for_transcripts import main
                main()

        # Verify exit code 1
        assert exc_info.value.code == 1

        # Verify usage message
        captured = capsys.readouterr()
        assert "Subagent type required" in captured.err
        assert "Usage:" in captured.err
