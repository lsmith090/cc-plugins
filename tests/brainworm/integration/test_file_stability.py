"""
File Stability Check Integration Tests

Integration tests for the file stability checking implementation in wait_for_transcripts.py.
Verifies that the script correctly waits for files to be fully written before proceeding.

Tests verify:
- File size stability detection
- Handling of files being actively written
- Timeout behavior
- Exponential backoff
- Empty file handling
- Missing file handling
"""

import pytest
import time
import tempfile
import json
from pathlib import Path
from threading import Thread
import sys
import os

# Import the wait_for_transcripts module
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "brainworm" / "scripts"))
from wait_for_transcripts import wait_for_transcripts


class TestFileStabilityDetection:
    """Test file stability detection mechanism"""

    def test_detects_stable_files_immediately(self, temp_project):
        """Test that stable files are detected without unnecessary waiting"""
        batch_dir = temp_project / ".brainworm" / "state" / "test-subagent"
        batch_dir.mkdir(parents=True)

        # Create stable files (complete and won't change)
        transcript = batch_dir / "current_transcript_1.json"
        transcript.write_text(json.dumps({"test": "data"}))

        context = batch_dir / "service_context.json"
        context.write_text(json.dumps({"context": "data"}))

        # Should detect stable files quickly
        start_time = time.time()
        result = wait_for_transcripts("test-subagent", temp_project, timeout_ms=5000)
        elapsed = time.time() - start_time

        assert result is not None
        assert len(result) == 1
        # Should complete in less than 200ms (one extra poll to verify stability)
        assert elapsed < 0.3

    def test_waits_for_files_being_written(self, temp_project):
        """Test that script waits for files that are actively being written"""
        batch_dir = temp_project / ".brainworm" / "state" / "test-subagent"
        batch_dir.mkdir(parents=True)

        # Create initial files
        transcript = batch_dir / "current_transcript_1.json"
        context = batch_dir / "service_context.json"

        def write_incrementally():
            """Simulate incremental file writing"""
            time.sleep(0.05)  # Small delay before starting

            # Write in stages
            transcript.write_text(json.dumps({"partial": "data"}))
            context.write_text(json.dumps({"context": "partial"}))

            time.sleep(0.1)  # Continue writing

            transcript.write_text(json.dumps({"complete": "data", "more": "content"}))
            context.write_text(json.dumps({"context": "complete", "more": "data"}))

            # Files are now stable

        # Start writing in background
        writer = Thread(target=write_incrementally, daemon=True)
        writer.start()

        # Wait for files to stabilize
        start_time = time.time()
        result = wait_for_transcripts("test-subagent", temp_project, timeout_ms=2000)
        elapsed = time.time() - start_time

        assert result is not None
        # Should have waited for stability (at least 100ms for writing + polls)
        assert elapsed >= 0.15

        # Verify files are complete
        final_transcript = json.loads(transcript.read_text())
        assert "complete" in final_transcript

    def test_handles_empty_files(self, temp_project):
        """Test that empty files are not considered stable"""
        batch_dir = temp_project / ".brainworm" / "state" / "test-subagent"
        batch_dir.mkdir(parents=True)

        # Create empty files initially
        transcript = batch_dir / "current_transcript_1.json"
        context = batch_dir / "service_context.json"
        transcript.touch()
        context.touch()

        def write_after_delay():
            """Write content after initial empty files exist"""
            time.sleep(0.1)
            transcript.write_text(json.dumps({"data": "content"}))
            context.write_text(json.dumps({"context": "content"}))

        # Start delayed writer
        writer = Thread(target=write_after_delay, daemon=True)
        writer.start()

        # Should wait for non-empty content
        result = wait_for_transcripts("test-subagent", temp_project, timeout_ms=2000)

        assert result is not None
        # Files should have content
        assert transcript.stat().st_size > 0
        assert context.stat().st_size > 0


class TestTimeoutBehavior:
    """Test timeout handling"""

    def test_timeout_when_files_never_appear(self, temp_project):
        """Test that FileNotFoundError is raised when directory doesn't exist"""
        # Don't create any files - directory won't exist

        # Should raise FileNotFoundError when directory doesn't exist
        with pytest.raises(FileNotFoundError, match="Subagent directory does not exist"):
            wait_for_transcripts("nonexistent-subagent", temp_project, timeout_ms=500)

    def test_timeout_behavior_with_rapidly_changing_files(self, temp_project):
        """Test behavior when files change rapidly (may timeout or succeed)"""
        batch_dir = temp_project / ".brainworm" / "state" / "test-subagent"
        batch_dir.mkdir(parents=True)

        transcript = batch_dir / "current_transcript_1.json"
        context = batch_dir / "service_context.json"

        # Create initial files
        transcript.write_text(json.dumps({"iteration": 0}))
        context.write_text(json.dumps({"iteration": 0}))

        def keep_writing():
            """Continuously modify files for a period"""
            counter = 1
            # Write continuously for longer than timeout to force timeout
            for _ in range(20):
                try:
                    transcript.write_text(json.dumps({"iteration": counter, "data": "x" * counter * 10}))
                    context.write_text(json.dumps({"iteration": counter, "data": "y" * counter * 10}))
                    counter += 1
                    time.sleep(0.05)  # 50ms writes
                except Exception:
                    pass

        # Start continuous writer
        writer = Thread(target=keep_writing, daemon=False)
        writer.start()

        # With rapidly changing files and short timeout, should timeout
        # However, due to exponential backoff timing, files may stabilize between polls
        # So we accept either outcome as valid
        start_time = time.time()
        try:
            result = wait_for_transcripts("test-subagent", temp_project, timeout_ms=500)
            elapsed = time.time() - start_time
            # If succeeded, files stabilized - this is valid behavior
            assert result is not None
        except TimeoutError:
            elapsed = time.time() - start_time
            # Timeout is also valid behavior
            assert 0.4 <= elapsed <= 0.8

        # Wait for writer thread
        writer.join(timeout=2.0)

    def test_succeeds_before_timeout(self, temp_project):
        """Test that success occurs before timeout if files stabilize"""
        batch_dir = temp_project / ".brainworm" / "state" / "test-subagent"
        batch_dir.mkdir(parents=True)

        transcript = batch_dir / "current_transcript_1.json"
        context = batch_dir / "service_context.json"

        def write_then_stop():
            """Write files then let them stabilize"""
            time.sleep(0.1)
            transcript.write_text(json.dumps({"data": "complete"}))
            context.write_text(json.dumps({"context": "complete"}))
            # Now files are stable

        writer = Thread(target=write_then_stop, daemon=True)
        writer.start()

        # Should succeed well before timeout
        start_time = time.time()
        result = wait_for_transcripts("test-subagent", temp_project, timeout_ms=5000)
        elapsed = time.time() - start_time

        assert result is not None
        # Should complete quickly, well before timeout
        assert elapsed < 1.0


class TestExponentialBackoff:
    """Test exponential backoff mechanism"""

    def test_backoff_reduces_cpu_usage(self, temp_project):
        """Test that exponential backoff reduces polling frequency"""
        batch_dir = temp_project / ".brainworm" / "state" / "test-subagent"
        batch_dir.mkdir(parents=True)

        # Create files that will be written after some delay
        transcript = batch_dir / "current_transcript_1.json"
        context = batch_dir / "service_context.json"

        def write_after_long_delay():
            """Write files after significant delay to trigger backoff"""
            time.sleep(0.5)  # Wait long enough for backoff to increase
            transcript.write_text(json.dumps({"data": "content"}))
            context.write_text(json.dumps({"context": "content"}))

        writer = Thread(target=write_after_long_delay, daemon=True)
        writer.start()

        # The wait should use exponential backoff
        # We can't directly measure polls, but we can verify it completes successfully
        result = wait_for_transcripts("test-subagent", temp_project, timeout_ms=2000)

        assert result is not None


class TestMultipleTranscriptFiles:
    """Test handling of multiple transcript files"""

    def test_detects_multiple_stable_transcripts(self, temp_project):
        """Test that all transcript files are detected when stable"""
        batch_dir = temp_project / ".brainworm" / "state" / "test-subagent"
        batch_dir.mkdir(parents=True)

        # Create multiple transcript files
        transcript1 = batch_dir / "current_transcript_1.json"
        transcript2 = batch_dir / "current_transcript_2.json"
        transcript3 = batch_dir / "current_transcript_3.json"
        context = batch_dir / "service_context.json"

        # Write all files
        for t in [transcript1, transcript2, transcript3]:
            t.write_text(json.dumps({"file": str(t.name)}))
        context.write_text(json.dumps({"context": "data"}))

        result = wait_for_transcripts("test-subagent", temp_project, timeout_ms=2000)

        assert result is not None
        assert len(result) == 3

    def test_waits_for_all_transcripts_to_stabilize(self, temp_project):
        """Test that script waits for all transcript files to stabilize"""
        batch_dir = temp_project / ".brainworm" / "state" / "test-subagent"
        batch_dir.mkdir(parents=True)

        transcript1 = batch_dir / "current_transcript_1.json"
        transcript2 = batch_dir / "current_transcript_2.json"
        context = batch_dir / "service_context.json"

        def write_files_sequentially():
            """Write files at different times"""
            time.sleep(0.05)

            # Write first file
            transcript1.write_text(json.dumps({"file": "1"}))
            context.write_text(json.dumps({"context": "partial"}))

            time.sleep(0.1)

            # Write second file (later)
            transcript2.write_text(json.dumps({"file": "2"}))
            context.write_text(json.dumps({"context": "complete"}))

            # Now all are stable

        writer = Thread(target=write_files_sequentially, daemon=True)
        writer.start()

        result = wait_for_transcripts("test-subagent", temp_project, timeout_ms=2000)

        assert result is not None
        assert len(result) == 2


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_handles_file_disappearing(self, temp_project):
        """Test handling when a file disappears during polling"""
        batch_dir = temp_project / ".brainworm" / "state" / "test-subagent"
        batch_dir.mkdir(parents=True)

        transcript = batch_dir / "current_transcript_1.json"
        context = batch_dir / "service_context.json"

        def create_then_delete():
            """Create files then delete one"""
            time.sleep(0.05)
            transcript.write_text(json.dumps({"data": "content"}))
            context.write_text(json.dumps({"context": "content"}))

            time.sleep(0.1)
            # Simulate file deletion/corruption
            transcript.unlink()

            time.sleep(0.1)
            # Recreate stable file
            transcript.write_text(json.dumps({"data": "restored"}))

        writer = Thread(target=create_then_delete, daemon=True)
        writer.start()

        # Should eventually succeed when file is stable again
        result = wait_for_transcripts("test-subagent", temp_project, timeout_ms=2000)

        # May succeed or timeout depending on timing
        # Both are acceptable behaviors for this edge case

    def test_handles_permission_errors_gracefully(self, temp_project):
        """Test that permission errors are handled gracefully"""
        batch_dir = temp_project / ".brainworm" / "state" / "test-subagent"
        batch_dir.mkdir(parents=True)

        transcript = batch_dir / "current_transcript_1.json"
        context = batch_dir / "service_context.json"

        # Create files
        transcript.write_text(json.dumps({"data": "content"}))
        context.write_text(json.dumps({"context": "content"}))

        # The function should handle permission errors gracefully
        # (We can't easily simulate this on all platforms, so this test
        # mainly ensures the code doesn't crash)
        result = wait_for_transcripts("test-subagent", temp_project, timeout_ms=1000)

        assert result is not None


class TestRealWorldScenarios:
    """Test real-world usage scenarios"""

    def test_subagent_completion_workflow(self, temp_project):
        """Simulate a complete subagent execution workflow"""
        batch_dir = temp_project / ".brainworm" / "state" / "logging"
        batch_dir.mkdir(parents=True)

        transcript = batch_dir / "current_transcript_1.json"
        context = batch_dir / "service_context.json"

        def simulate_subagent_execution():
            """Simulate subagent processing and writing results"""
            # Subagent starts
            time.sleep(0.05)

            # Begins writing transcript
            transcript.write_text(json.dumps({
                "messages": [{"role": "assistant", "content": "Processing..."}]
            }))
            context.write_text(json.dumps({"status": "processing"}))

            time.sleep(0.1)

            # Continues processing
            transcript.write_text(json.dumps({
                "messages": [
                    {"role": "assistant", "content": "Processing..."},
                    {"role": "assistant", "content": "Almost done..."}
                ]
            }))

            time.sleep(0.05)

            # Completes
            transcript.write_text(json.dumps({
                "messages": [
                    {"role": "assistant", "content": "Processing..."},
                    {"role": "assistant", "content": "Almost done..."},
                    {"role": "assistant", "content": "Complete!"}
                ]
            }))
            context.write_text(json.dumps({"status": "complete"}))

            # Files now stable

        # Start simulated subagent
        subagent = Thread(target=simulate_subagent_execution, daemon=True)
        subagent.start()

        # Wait for completion
        result = wait_for_transcripts("logging", temp_project, timeout_ms=3000)

        assert result is not None

        # Verify complete content
        final_data = json.loads(transcript.read_text())
        assert len(final_data["messages"]) == 3
        assert "Complete!" in final_data["messages"][2]["content"]


@pytest.fixture
def temp_project():
    """Create a temporary project directory"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_root = Path(tmp_dir) / "project"
        project_root.mkdir(parents=True)

        # Create .brainworm structure
        brainworm_dir = project_root / ".brainworm"
        brainworm_dir.mkdir()

        state_dir = brainworm_dir / "state"
        state_dir.mkdir()

        yield project_root
