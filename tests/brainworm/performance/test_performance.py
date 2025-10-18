"""
Performance Tests

Performance regression tests for token counting, JSON serialization,
and other performance-critical operations.

Tests measure execution time and establish baseline expectations to catch
performance regressions early.
"""

import pytest
import json
import time
import tempfile
from pathlib import Path

# Import modules to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "brainworm" / "hooks"))
from transcript_processor import get_token_count


class TestTokenCountingPerformance:
    """Performance tests for token counting operations"""

    def test_token_counting_small_text(self, benchmark_timer):
        """Test token counting performance on small text (< 1000 chars)"""
        small_text = "This is a small text sample. " * 30  # ~900 chars

        with benchmark_timer("token_count_small"):
            for _ in range(100):
                count = get_token_count(small_text)

        # Should complete 100 iterations in < 100ms
        assert benchmark_timer.elapsed < 0.1
        assert count > 0

    def test_token_counting_medium_text(self, benchmark_timer):
        """Test token counting performance on medium text (10KB)"""
        medium_text = "A" * 10000  # 10KB

        with benchmark_timer("token_count_medium"):
            for _ in range(10):
                count = get_token_count(medium_text)

        # Should complete 10 iterations in < 200ms
        assert benchmark_timer.elapsed < 0.2
        assert count > 0

    def test_token_counting_large_text(self, benchmark_timer):
        """Test token counting performance on large text (100KB)"""
        large_text = "This is sample text. " * 5000  # ~100KB

        with benchmark_timer("token_count_large"):
            count = get_token_count(large_text)

        # Should complete single large count in < 100ms
        assert benchmark_timer.elapsed < 0.1
        assert count > 0

    def test_token_counting_batch(self, benchmark_timer):
        """Test batch token counting performance"""
        texts = [f"Sample text number {i}. " * 100 for i in range(50)]

        with benchmark_timer("token_count_batch"):
            counts = [get_token_count(text) for text in texts]

        # Should complete 50 counts in < 500ms
        assert benchmark_timer.elapsed < 0.5
        assert len(counts) == 50
        assert all(c > 0 for c in counts)


class TestJSONSerializationPerformance:
    """Performance tests for JSON serialization/deserialization"""

    def test_small_object_serialization(self, benchmark_timer):
        """Test serialization performance for small objects"""
        small_obj = {"key": "value", "number": 42, "list": [1, 2, 3]}

        with benchmark_timer("json_serialize_small"):
            for _ in range(1000):
                json_str = json.dumps(small_obj)
                parsed = json.loads(json_str)

        # 1000 round-trips should complete in < 50ms
        assert benchmark_timer.elapsed < 0.05

    def test_medium_object_serialization(self, benchmark_timer):
        """Test serialization performance for medium objects"""
        medium_obj = {
            "messages": [
                {"role": "user", "content": f"Message {i}"}
                for i in range(100)
            ],
            "metadata": {"count": 100, "timestamp": "2024-01-01"}
        }

        with benchmark_timer("json_serialize_medium"):
            for _ in range(100):
                json_str = json.dumps(medium_obj)
                parsed = json.loads(json_str)

        # 100 round-trips should complete in < 200ms
        assert benchmark_timer.elapsed < 0.2

    def test_large_object_serialization(self, benchmark_timer):
        """Test serialization performance for large objects"""
        large_obj = {
            "transcripts": [
                {
                    "id": i,
                    "content": "A" * 1000,
                    "metadata": {"key": f"value-{i}"}
                }
                for i in range(100)
            ]
        }

        with benchmark_timer("json_serialize_large"):
            for _ in range(10):
                json_str = json.dumps(large_obj)
                parsed = json.loads(json_str)

        # 10 round-trips should complete in < 500ms
        assert benchmark_timer.elapsed < 0.5

    def test_json_pretty_printing_overhead(self, benchmark_timer):
        """Test overhead of pretty-printing JSON"""
        obj = {"data": [{"id": i, "value": f"item-{i}"} for i in range(100)]}

        # Measure compact serialization
        with benchmark_timer("json_compact"):
            for _ in range(100):
                json.dumps(obj)

        compact_time = benchmark_timer.elapsed

        # Measure pretty serialization
        with benchmark_timer("json_pretty"):
            for _ in range(100):
                json.dumps(obj, indent=2)

        pretty_time = benchmark_timer.elapsed

        # Pretty printing should be < 3x slower than compact
        assert pretty_time < compact_time * 3


class TestFileIOPerformance:
    """Performance tests for file I/O operations"""

    def test_small_file_write_performance(self, temp_dir, benchmark_timer):
        """Test performance of writing small files"""
        test_file = temp_dir / "test.json"
        data = {"key": "value", "number": 42}

        with benchmark_timer("file_write_small"):
            for i in range(100):
                test_file.write_text(json.dumps(data))

        # 100 small writes should complete in < 200ms
        assert benchmark_timer.elapsed < 0.2

    def test_medium_file_write_performance(self, temp_dir, benchmark_timer):
        """Test performance of writing medium files (10KB)"""
        test_file = temp_dir / "test.json"
        data = {"content": "A" * 10000}

        with benchmark_timer("file_write_medium"):
            for i in range(50):
                test_file.write_text(json.dumps(data))

        # 50 medium writes should complete in < 500ms
        assert benchmark_timer.elapsed < 0.5

    def test_file_read_performance(self, temp_dir, benchmark_timer):
        """Test performance of reading files"""
        test_file = temp_dir / "test.json"
        data = {"messages": [f"message-{i}" for i in range(100)]}
        test_file.write_text(json.dumps(data))

        with benchmark_timer("file_read"):
            for _ in range(100):
                content = test_file.read_text()
                parsed = json.loads(content)

        # 100 reads should complete in < 100ms
        assert benchmark_timer.elapsed < 0.1


class TestStateOperationPerformance:
    """Performance tests for state management operations"""

    def test_state_file_update_performance(self, temp_dir, benchmark_timer):
        """Test performance of state file updates"""
        state_file = temp_dir / "state.json"
        state_file.write_text(json.dumps({"mode": "discussion", "task": None}))

        with benchmark_timer("state_update"):
            for i in range(50):
                # Read-modify-write cycle
                state = json.loads(state_file.read_text())
                state["task"] = f"task-{i}"
                state["iteration"] = i
                state_file.write_text(json.dumps(state, indent=2))

        # 50 state updates should complete in < 300ms
        assert benchmark_timer.elapsed < 0.3

    def test_correlation_lookup_performance(self, temp_dir, benchmark_timer):
        """Test performance of correlation lookups"""
        correlation_file = temp_dir / ".correlation_state"
        correlations = {
            f"session-{i}": f"correlation-{i}"
            for i in range(100)
        }
        correlation_file.write_text(json.dumps(correlations))

        with benchmark_timer("correlation_lookup"):
            for i in range(100):
                data = json.loads(correlation_file.read_text())
                session_id = f"session-{i % 100}"
                correlation = data.get(session_id)

        # 100 lookups should complete in < 100ms
        assert benchmark_timer.elapsed < 0.1


class TestStringOperationPerformance:
    """Performance tests for string operations"""

    def test_large_string_concatenation(self, benchmark_timer):
        """Test performance of large string concatenation"""
        parts = [f"part-{i}" for i in range(1000)]

        with benchmark_timer("string_concat"):
            result = "".join(parts)

        # Should complete in < 5ms
        assert benchmark_timer.elapsed < 0.005
        assert len(result) > 0

    def test_string_formatting_performance(self, benchmark_timer):
        """Test performance of string formatting"""
        template = "Message {}: {}"

        with benchmark_timer("string_format"):
            for i in range(1000):
                message = template.format(i, f"content-{i}")

        # 1000 formats should complete in < 10ms
        assert benchmark_timer.elapsed < 0.01

    def test_regex_matching_performance(self, benchmark_timer):
        """Test performance of regex matching"""
        import re
        pattern = re.compile(r'session-\d+')
        texts = [f"This is session-{i} data" for i in range(100)]

        with benchmark_timer("regex_match"):
            for text in texts:
                matches = pattern.findall(text)

        # 100 regex matches should complete in < 10ms
        assert benchmark_timer.elapsed < 0.01


class TestBaselinePerformance:
    """Baseline performance tests to detect system-wide slowdowns"""

    def test_baseline_python_operations(self, benchmark_timer):
        """Baseline: basic Python operations"""
        with benchmark_timer("baseline_python"):
            total = 0
            for i in range(10000):
                total += i

        # Should complete in < 5ms
        assert benchmark_timer.elapsed < 0.005

    def test_baseline_list_operations(self, benchmark_timer):
        """Baseline: list operations"""
        with benchmark_timer("baseline_list"):
            data = list(range(10000))
            filtered = [x for x in data if x % 2 == 0]
            sorted_data = sorted(filtered)

        # Should complete in < 20ms
        assert benchmark_timer.elapsed < 0.02

    def test_baseline_dict_operations(self, benchmark_timer):
        """Baseline: dictionary operations"""
        with benchmark_timer("baseline_dict"):
            data = {f"key-{i}": f"value-{i}" for i in range(1000)}
            lookups = [data.get(f"key-{i}") for i in range(1000)]

        # Should complete in < 10ms
        assert benchmark_timer.elapsed < 0.01


# Fixtures

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def benchmark_timer():
    """Simple benchmark timer fixture"""
    class BenchmarkTimer:
        def __init__(self):
            self.start_time = None
            self.elapsed = None
            self.name = None

        def __enter__(self):
            self.start_time = time.perf_counter()
            return self

        def __exit__(self, *args):
            self.elapsed = time.perf_counter() - self.start_time
            if self.name:
                print(f"\n  {self.name}: {self.elapsed*1000:.2f}ms")

    timer = BenchmarkTimer()

    def _timer(name=None):
        timer.name = name
        return timer

    return _timer
