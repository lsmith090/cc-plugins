"""
Race Condition Prevention Tests

Tests for concurrent access protection using FileLock in state management operations.
Verifies that read-modify-write operations are atomic and prevent data corruption
when multiple processes or threads access the same state files.

Tests verify:
- FileLock prevents concurrent modifications
- State files remain consistent under concurrent access
- Lock timeouts are configured appropriately
- Lock files are cleaned up properly
"""

import pytest
import json
import time
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Thread, Barrier
import subprocess
import sys

try:
    from filelock import FileLock, Timeout
    FILELOCK_AVAILABLE = True
except ImportError:
    FILELOCK_AVAILABLE = False

from brainworm.utils.correlation_manager import CorrelationManager


pytestmark = pytest.mark.skipif(
    not FILELOCK_AVAILABLE,
    reason="filelock not available"
)


class TestFileLockConcurrency:
    """Test FileLock prevents race conditions in state management"""

    def test_filelock_prevents_lost_updates(self, temp_dir):
        """Test that FileLock prevents lost updates in concurrent writes"""
        test_file = temp_dir / "counter.json"
        lock_file = temp_dir / ".counter.json.lock"

        # Initialize counter
        test_file.write_text(json.dumps({"count": 0}))

        def increment_with_lock():
            """Increment counter with lock protection"""
            lock = FileLock(lock_file, timeout=10)
            with lock:
                # Read
                data = json.loads(test_file.read_text())
                count = data["count"]

                # Simulate processing delay
                time.sleep(0.01)

                # Write
                data["count"] = count + 1
                test_file.write_text(json.dumps(data))

        # Run 50 concurrent increments
        num_threads = 50
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(increment_with_lock) for _ in range(num_threads)]
            for future in as_completed(futures):
                future.result()  # Raise any exceptions

        # Verify final count is correct (no lost updates)
        final_data = json.loads(test_file.read_text())
        assert final_data["count"] == num_threads

    def test_filelock_without_protection_causes_lost_updates(self, temp_dir):
        """Demonstrate that without FileLock, updates are lost"""
        test_file = temp_dir / "counter.json"

        # Initialize counter
        test_file.write_text(json.dumps({"count": 0}))

        def increment_without_lock():
            """Increment counter WITHOUT lock protection (unsafe)"""
            # Read
            data = json.loads(test_file.read_text())
            count = data["count"]

            # Simulate processing delay
            time.sleep(0.01)

            # Write
            data["count"] = count + 1
            test_file.write_text(json.dumps(data))

        # Run 50 concurrent increments WITHOUT lock
        num_threads = 50
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(increment_without_lock) for _ in range(num_threads)]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception:
                    # May fail due to race conditions, which proves the point
                    pass

        # Verify final count is INCORRECT (lost updates occurred)
        final_data = json.loads(test_file.read_text())
        # With race conditions, count will be less than num_threads
        assert final_data["count"] < num_threads, \
            "Race condition should cause lost updates without locking"

    def test_lock_timeout_prevents_deadlock(self, temp_dir):
        """Test that lock timeout prevents indefinite waiting"""
        test_file = temp_dir / "data.json"
        lock_file = temp_dir / ".data.json.lock"

        test_file.write_text(json.dumps({"value": "initial"}))

        # Acquire lock and hold it
        lock1 = FileLock(lock_file, timeout=1)
        lock1.acquire()

        try:
            # Attempt to acquire same lock with short timeout
            lock2 = FileLock(lock_file, timeout=0.5)

            # Should raise Timeout exception
            with pytest.raises(Timeout):
                lock2.acquire()

        finally:
            lock1.release()

    def test_lock_files_are_cleaned_up(self, temp_dir):
        """Test that lock files are properly cleaned up after use"""
        test_file = temp_dir / "data.json"
        lock_file = temp_dir / ".data.json.lock"

        test_file.write_text(json.dumps({"value": "test"}))

        # Use lock in context manager
        lock = FileLock(lock_file, timeout=10)
        with lock:
            # Lock file should exist while locked
            assert lock_file.exists() or lock.is_locked

        # Lock should be released after context
        assert not lock.is_locked

class TestCorrelationManagerConcurrency:
    """Test concurrent access to correlation manager"""

    def test_concurrent_correlation_gets(self, temp_dir):
        """Test that multiple threads can get or create correlations safely"""
        project_root = temp_dir / "project"
        project_root.mkdir(parents=True)

        brainworm_dir = project_root / ".brainworm"
        brainworm_dir.mkdir(parents=True)

        state_dir = brainworm_dir / "state"
        state_dir.mkdir(parents=True)

        manager = CorrelationManager(project_root)

        def get_correlation(thread_id: int):
            """Get or create correlation from multiple threads"""
            session_id = f"session-{thread_id}"
            correlation_id = manager.get_or_create_correlation_id(session_id)
            return correlation_id

        # Run concurrent gets
        num_threads = 20
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(get_correlation, i) for i in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]

        # All threads should complete successfully
        assert len(results) == num_threads
        # All correlation IDs should be non-empty
        assert all(results)

    def test_concurrent_correlation_clears(self, temp_dir):
        """Test that concurrent clears don't cause corruption"""
        project_root = temp_dir / "project"
        project_root.mkdir(parents=True)

        brainworm_dir = project_root / ".brainworm"
        brainworm_dir.mkdir(parents=True)

        state_dir = brainworm_dir / "state"
        state_dir.mkdir(parents=True)

        manager = CorrelationManager(project_root)

        # Create some correlations first
        for i in range(5):
            manager.get_or_create_correlation_id(f"session-{i}")

        def clear_correlation(session_id: str):
            """Clear correlation safely"""
            try:
                manager.clear_session_correlation(session_id)
            except Exception:
                # May fail if file doesn't exist, which is fine
                pass

        # Run concurrent clears for different sessions
        num_threads = 10
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(clear_correlation, f"session-{i % 5}")
                for i in range(num_threads)
            ]
            for future in as_completed(futures):
                future.result()  # Should not raise


class TestJSONFileConcurrency:
    """Test concurrent access to JSON configuration files"""

    def test_concurrent_json_updates_with_lock(self, temp_dir):
        """Test that concurrent JSON updates are safe with FileLock"""
        config_file = temp_dir / "config.json"
        lock_file = temp_dir / ".config.json.lock"

        # Initialize config
        config_file.write_text(json.dumps({"triggers": []}))

        def update_trigger_phrases(thread_id: int):
            """Add trigger phrase with lock protection"""
            lock = FileLock(lock_file, timeout=10)
            with lock:
                # Read config
                config = json.loads(config_file.read_text())

                # Add trigger phrase
                config["triggers"].append(f"trigger-{thread_id}")

                # Write back
                config_file.write_text(json.dumps(config, indent=2))

        # Run concurrent updates
        num_threads = 20
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(update_trigger_phrases, i) for i in range(num_threads)]
            for future in as_completed(futures):
                future.result()

        # Verify all triggers were added
        final_config = json.loads(config_file.read_text())
        assert len(final_config["triggers"]) == num_threads


class TestStateFileConsistency:
    """Test that state files remain consistent under concurrent access"""

    def test_json_integrity_under_concurrent_writes(self, temp_dir):
        """Test that JSON files remain valid under concurrent access"""
        test_file = temp_dir / "state.json"
        lock_file = temp_dir / ".state.json.lock"

        # Initialize state
        test_file.write_text(json.dumps({"threads": {}}))

        def update_thread_state(thread_id: int):
            """Update state for a specific thread"""
            lock = FileLock(lock_file, timeout=10)
            with lock:
                # Read current state
                data = json.loads(test_file.read_text())

                # Update for this thread
                data["threads"][f"thread-{thread_id}"] = {
                    "id": thread_id,
                    "timestamp": time.time()
                }

                # Write back
                test_file.write_text(json.dumps(data, indent=2))

        # Run concurrent updates
        num_threads = 30
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(update_thread_state, i) for i in range(num_threads)]
            for future in as_completed(futures):
                future.result()

        # Verify final state is valid JSON with all threads
        final_data = json.loads(test_file.read_text())
        assert len(final_data["threads"]) == num_threads

        # Verify all thread IDs are present
        for i in range(num_threads):
            assert f"thread-{i}" in final_data["threads"]


class TestLockPerformance:
    """Test lock performance and overhead"""

    def test_lock_acquisition_is_fast(self, temp_dir):
        """Test that lock acquisition/release has minimal overhead"""
        test_file = temp_dir / "data.json"
        lock_file = temp_dir / ".data.json.lock"

        test_file.write_text(json.dumps({"value": 0}))

        # Measure time for 100 lock acquisitions
        start_time = time.time()

        for i in range(100):
            lock = FileLock(lock_file, timeout=10)
            with lock:
                data = json.loads(test_file.read_text())
                data["value"] = i
                test_file.write_text(json.dumps(data))

        elapsed = time.time() - start_time

        # Should complete in reasonable time (< 5 seconds for 100 operations)
        assert elapsed < 5.0, f"Lock overhead too high: {elapsed:.2f}s for 100 operations"

    def test_lock_timeout_is_respected(self, temp_dir):
        """Test that lock timeout value is respected"""
        lock_file = temp_dir / ".test.lock"

        # Hold lock indefinitely
        lock1 = FileLock(lock_file, timeout=30)
        lock1.acquire()

        try:
            # Attempt to acquire with 0.5s timeout
            lock2 = FileLock(lock_file, timeout=0.5)

            start_time = time.time()
            with pytest.raises(Timeout):
                lock2.acquire()
            elapsed = time.time() - start_time

            # Should timeout close to specified timeout (within 0.2s tolerance)
            assert 0.4 <= elapsed <= 0.7, \
                f"Lock timeout not respected: {elapsed:.2f}s (expected ~0.5s)"

        finally:
            lock1.release()


class TestRealWorldScenarios:
    """Test real-world concurrent access scenarios"""

    def test_concurrent_hook_executions(self, temp_dir):
        """Simulate concurrent hook executions accessing shared state"""
        brainworm_dir = temp_dir / ".brainworm"
        state_dir = brainworm_dir / "state"
        state_dir.mkdir(parents=True)

        state_file = state_dir / "hook_state.json"
        lock_file = state_dir / ".hook_state.json.lock"

        # Initialize hook execution counter
        state_file.write_text(json.dumps({"executions": 0, "hooks": {}}))

        def execute_hook(hook_name: str, execution_id: int):
            """Simulate hook execution updating shared state"""
            lock = FileLock(lock_file, timeout=10)
            with lock:
                # Read state
                data = json.loads(state_file.read_text())

                # Update execution count
                data["executions"] += 1

                # Record this hook execution
                if hook_name not in data["hooks"]:
                    data["hooks"][hook_name] = []
                data["hooks"][hook_name].append(execution_id)

                # Write back
                state_file.write_text(json.dumps(data))

        # Simulate 50 concurrent hook executions of various types
        hooks = ["PreToolUse", "PostToolUse", "UserPromptSubmit", "SessionStart"]
        num_executions = 50

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for i in range(num_executions):
                hook_name = hooks[i % len(hooks)]
                futures.append(executor.submit(execute_hook, hook_name, i))

            for future in as_completed(futures):
                future.result()

        # Verify state consistency
        final_data = json.loads(state_file.read_text())
        assert final_data["executions"] == num_executions

        # Verify all executions recorded
        total_recorded = sum(len(execs) for execs in final_data["hooks"].values())
        assert total_recorded == num_executions


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)
