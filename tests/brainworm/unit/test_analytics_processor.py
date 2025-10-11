#!/usr/bin/env python3
"""
Comprehensive unit tests for ClaudeAnalyticsProcessor.

Tests the core analytics processing functionality including:
- Database operations and schema management
- Configuration loading and validation
- Event processing and logging
- Performance requirements (sub-100ms execution)
- Error handling and graceful degradation
"""

import json
import os
import sqlite3
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from typing import Dict, Any

import pytest

# Import the analytics processor from brainworm plugin package
from brainworm.utils.analytics_processor import ClaudeAnalyticsProcessor


class TestClaudeAnalyticsProcessor:
    """Test suite for ClaudeAnalyticsProcessor class."""

    def test_init_creates_required_directories(self, temp_dir):
        """Test that initialization creates required directory structure."""
        claude_dir = temp_dir / ".claude"
        
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        # Verify directory structure
        assert claude_dir.exists()
        assert (claude_dir / "analytics").exists()
        assert (claude_dir / "analytics" / "logs").exists()
        assert processor.db_path == claude_dir / "analytics" / "hooks.db"

    def test_init_creates_database_schema(self, temp_dir):
        """Test that database is initialized with correct schema."""
        claude_dir = temp_dir / ".claude"
        
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        # Verify database exists and has correct schema
        assert processor.db_path.exists()
        
        with sqlite3.connect(processor.db_path) as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='hook_events'
            """)
            assert cursor.fetchone() is not None
            
            # Check table schema
            cursor = conn.execute("PRAGMA table_info(hook_events)")
            columns = [row[1] for row in cursor.fetchall()]
            expected_columns = [
                'id', 'timestamp', 'hook_name', 'event_type', 
                'correlation_id', 'session_id', 'success', 
                'duration_ms', 'data', 'created_at'
            ]
            assert all(col in columns for col in expected_columns)
            
            # Check indexes exist
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND sql IS NOT NULL
            """)
            index_names = [row[0] for row in cursor.fetchall()]
            assert 'idx_hook_events_timestamp' in index_names
            assert 'idx_hook_events_correlation' in index_names

    def test_database_init_failure_graceful(self, temp_dir):
        """Test that database initialization failures are handled gracefully."""
        claude_dir = temp_dir / ".claude"
        
        # Create a file where the database should be (to cause conflict)
        analytics_dir = claude_dir / "analytics"
        analytics_dir.mkdir(parents=True)
        db_path = analytics_dir / "hooks.db"
        db_path.touch()
        db_path.chmod(0o000)  # Remove all permissions
        
        try:
            # Should not raise exception despite database issues
            processor = ClaudeAnalyticsProcessor(claude_dir)
            assert processor.db_path == db_path
        finally:
            # Restore permissions for cleanup
            db_path.chmod(0o644)

    def test_default_configuration(self, temp_dir):
        """Test default configuration values."""
        claude_dir = temp_dir / ".claude"
        
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        expected_config = {
            'real_time_processing': True,
            'correlation_timeout_minutes': 60,
            'success_rate_window_hours': 24,
            'max_processing_time_ms': 50,
            'retention_days': 30,
            'max_db_size_mb': 100
        }
        
        assert processor.config == expected_config

    def test_load_config_from_toml_file(self, temp_dir):
        """Test loading configuration from brainworm-config.toml."""
        claude_dir = temp_dir / ".claude"
        project_root = claude_dir.parent
        
        # Create config file with analytics section
        config_content = """
[analytics]
real_time_processing = false
correlation_timeout_minutes = 30
max_processing_time_ms = 25
retention_days = 60
"""
        config_path = project_root / "brainworm-config.toml"
        config_path.write_text(config_content)
        
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        assert processor.config['real_time_processing'] is False
        assert processor.config['correlation_timeout_minutes'] == 30
        assert processor.config['max_processing_time_ms'] == 25
        assert processor.config['retention_days'] == 60
        # Should keep defaults for unspecified values
        assert processor.config['success_rate_window_hours'] == 24

    def test_load_config_toml_not_available(self, temp_dir):
        """Test behavior when TOML library is not available."""
        claude_dir = temp_dir / ".claude"
        
        with patch('analytics_processor.TOML_AVAILABLE', False):
            processor = ClaudeAnalyticsProcessor(claude_dir)
            
            # Should use default config
            assert processor.config['real_time_processing'] is True
            assert processor.config['max_processing_time_ms'] == 50

    def test_load_config_file_not_found(self, temp_dir):
        """Test behavior when config file doesn't exist."""
        claude_dir = temp_dir / ".claude"
        
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        # Should use default config
        assert processor.config['real_time_processing'] is True
        assert processor.config['correlation_timeout_minutes'] == 60

    def test_load_config_invalid_toml(self, temp_dir):
        """Test behavior with invalid TOML file."""
        claude_dir = temp_dir / ".claude"
        project_root = claude_dir.parent
        
        # Create invalid TOML file
        config_path = project_root / "brainworm-config.toml"
        config_path.write_text("invalid toml content [[[")
        
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        # Should fallback to default config
        assert processor.config['real_time_processing'] is True

    def test_log_event_success(self, temp_dir):
        """Test successful event logging."""
        claude_dir = temp_dir / ".claude"
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        event_data = {
            'hook_name': 'test_hook',
            'event_type': 'test_event',
            'correlation_id': 'test-corr-123',
            'session_id': 'test-session-456',
            'success': True,
            'duration_ms': 25.5,
            'custom_field': 'custom_value'
        }
        
        result = processor.log_event(event_data)
        assert result is True
        
        # Verify data in database
        with sqlite3.connect(processor.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM hook_events 
                WHERE hook_name = ? AND correlation_id = ?
            """, ('test_hook', 'test-corr-123'))
            
            row = cursor.fetchone()
            assert row is not None
            assert row['hook_name'] == 'test_hook'
            assert row['event_type'] == 'test_event'
            assert row['correlation_id'] == 'test-corr-123'
            assert row['session_id'] == 'test-session-456'
            assert row['success'] == 1  # SQLite stores boolean as integer
            assert row['duration_ms'] == 25.5
            
            # Verify stored JSON data contains custom fields
            stored_data = json.loads(row['data'])
            assert stored_data['custom_field'] == 'custom_value'

    def test_log_event_jsonl_backup(self, temp_dir):
        """Test that events are also logged to JSONL backup files."""
        claude_dir = temp_dir / ".claude"
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        event_data = {
            'hook_name': 'backup_test',
            'event_type': 'test_event',
            'session_id': 'backup-session'
        }
        
        with patch('analytics_processor.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, 12, 30, 45)
            result = processor.log_event(event_data)
        
        assert result is True
        
        # Check JSONL file was created
        log_file = processor.logs_dir / "2024-01-15_hooks.jsonl"
        assert log_file.exists()
        
        # Verify content
        content = log_file.read_text().strip()
        logged_event = json.loads(content)
        assert logged_event['hook_name'] == 'backup_test'
        assert logged_event['session_id'] == 'backup-session'

    def test_log_event_with_defaults(self, temp_dir):
        """Test event logging with missing fields uses defaults."""
        claude_dir = temp_dir / ".claude"
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        # Minimal event data
        event_data = {}
        
        result = processor.log_event(event_data)
        assert result is True
        
        # Verify defaults were applied
        with sqlite3.connect(processor.db_path) as conn:
            cursor = conn.execute("SELECT * FROM hook_events ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            
            assert row[2] == 'unknown'  # hook_name
            assert row[3] == 'hook_execution'  # event_type
            assert row[6] == 1  # success (True)
            assert row[7] == 0  # duration_ms

    def test_log_event_performance_requirement(self, temp_dir):
        """Test that event logging meets sub-100ms performance requirement."""
        claude_dir = temp_dir / ".claude"
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        event_data = {
            'hook_name': 'performance_test',
            'event_type': 'timing_test',
            'session_id': 'perf-test-session',
            'large_data': 'x' * 10000  # Large data to test performance
        }
        
        # Measure execution time
        start_time = time.perf_counter()
        result = processor.log_event(event_data)
        execution_time_ms = (time.perf_counter() - start_time) * 1000
        
        assert result is True
        assert execution_time_ms < 100, f"Event logging took {execution_time_ms}ms, should be < 100ms"

    def test_log_event_database_failure_graceful(self, temp_dir):
        """Test graceful handling of database failures during event logging."""
        claude_dir = temp_dir / ".claude"
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        # Remove database directory to cause failure
        import shutil
        if processor.db_path.parent.exists():
            shutil.rmtree(processor.db_path.parent)
        
        event_data = {'hook_name': 'failure_test'}
        
        # Should not raise exception
        result = processor.log_event(event_data)
        assert result is False

    def test_process_hook_event_alias(self, temp_dir):
        """Test that process_hook_event is an alias for log_event."""
        claude_dir = temp_dir / ".claude"
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        event_data = {
            'hook_name': 'alias_test',
            'session_id': 'alias-session'
        }
        
        result = processor.process_hook_event(event_data)
        assert result is True
        
        # Verify event was logged
        with sqlite3.connect(processor.db_path) as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) FROM hook_events WHERE hook_name = ?
            """, ('alias_test',))
            count = cursor.fetchone()[0]
            assert count == 1

    def test_get_recent_events(self, temp_dir):
        """Test retrieving recent events."""
        claude_dir = temp_dir / ".claude"
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        # Insert test events
        events = [
            {
                'hook_name': f'test_hook_{i}',
                'session_id': 'recent-test',
                'timestamp': time.time() - i  # Different timestamps
            }
            for i in range(5)
        ]
        
        for event in events:
            processor.log_event(event)
        
        # Get recent events
        recent = processor.get_recent_events(limit=3)
        
        assert len(recent) == 3
        # Should be ordered by timestamp DESC (most recent first)
        assert recent[0]['hook_name'] == 'test_hook_0'
        assert recent[1]['hook_name'] == 'test_hook_1'
        assert recent[2]['hook_name'] == 'test_hook_2'

    def test_get_recent_events_empty_database(self, temp_dir):
        """Test get_recent_events with empty database."""
        claude_dir = temp_dir / ".claude"
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        recent = processor.get_recent_events()
        assert recent == []

    def test_get_recent_events_database_error(self, temp_dir):
        """Test get_recent_events handles database errors gracefully."""
        claude_dir = temp_dir / ".claude"
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        # Corrupt the database
        processor.db_path.write_text("invalid database content")
        
        recent = processor.get_recent_events()
        assert recent == []

    def test_get_statistics_with_data(self, temp_dir):
        """Test statistics calculation with sample data."""
        claude_dir = temp_dir / ".claude"
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        # Insert test events (within last 24 hours)
        current_time = time.time()
        events = [
            {
                'hook_name': 'stats_test',
                'session_id': f'session_{i}',
                'correlation_id': f'corr_{i}',
                'success': i % 2 == 0,  # Alternate success/failure
                'duration_ms': 10 + i * 5,
                'timestamp': current_time - (i * 3600)  # Spread over hours
            }
            for i in range(4)
        ]
        
        for event in events:
            processor.log_event(event)
        
        stats = processor.get_statistics()
        
        assert stats['total_events'] == 4
        assert stats['success_rate'] == 50.0  # 2 out of 4 successful
        assert stats['avg_duration_ms'] == 17.5  # (10+15+20+25)/4
        assert stats['unique_sessions'] == 4
        assert stats['unique_correlations'] == 4
        assert stats['period'] == '24h'

    def test_get_statistics_empty_database(self, temp_dir):
        """Test statistics with empty database."""
        claude_dir = temp_dir / ".claude"
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        stats = processor.get_statistics()
        
        expected_stats = {
            'total_events': 0,
            'avg_duration_ms': 0,
            'success_rate': 0,
            'unique_sessions': 0,
            'unique_correlations': 0,
            'period': '24h'
        }
        
        assert stats == expected_stats

    def test_get_statistics_database_error(self, temp_dir):
        """Test statistics calculation handles database errors."""
        claude_dir = temp_dir / ".claude"
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        # Corrupt database
        processor.db_path.write_text("invalid database")
        
        stats = processor.get_statistics()
        
        expected_stats = {
            'total_events': 0,
            'avg_duration_ms': 0,
            'success_rate': 0,
            'unique_sessions': 0,
            'unique_correlations': 0,
            'period': '24h'
        }
        
        assert stats == expected_stats

    def test_get_statistics_performance_requirement(self, temp_dir):
        """Test that statistics calculation meets performance requirements."""
        claude_dir = temp_dir / ".claude"
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        # Insert many events to test performance
        events = [
            {
                'hook_name': f'perf_test_{i}',
                'session_id': f'session_{i}',
                'timestamp': time.time() - (i * 60)  # Spread over minutes
            }
            for i in range(100)
        ]
        
        for event in events:
            processor.log_event(event)
        
        # Measure statistics performance
        start_time = time.perf_counter()
        stats = processor.get_statistics()
        execution_time_ms = (time.perf_counter() - start_time) * 1000
        
        assert stats['total_events'] == 100
        assert execution_time_ms < 50, f"Statistics calculation took {execution_time_ms}ms, should be < 50ms"

    def test_concurrent_database_access(self, temp_dir):
        """Test that database operations handle concurrent access safely."""
        claude_dir = temp_dir / ".claude"
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        import threading
        import concurrent.futures
        
        results = []
        
        def log_event_worker(worker_id):
            """Worker function to log events concurrently."""
            event_data = {
                'hook_name': f'concurrent_test_{worker_id}',
                'session_id': f'session_{worker_id}',
                'timestamp': time.time()
            }
            return processor.log_event(event_data)
        
        # Run multiple concurrent log operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(log_event_worker, i) for i in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All operations should succeed
        assert all(results)
        
        # Verify all events were logged
        with sqlite3.connect(processor.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM hook_events WHERE hook_name LIKE 'concurrent_test_%'")
            count = cursor.fetchone()[0]
            assert count == 10

    def test_database_locking_timeout(self, temp_dir):
        """Test database operations respect timeout settings."""
        claude_dir = temp_dir / ".claude"
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        # Create a long-running transaction to test timeout
        def blocking_transaction():
            conn = sqlite3.connect(processor.db_path)
            conn.execute("BEGIN EXCLUSIVE")
            time.sleep(2)  # Hold lock for 2 seconds
            conn.close()
        
        import threading
        thread = threading.Thread(target=blocking_transaction)
        thread.start()
        
        # Wait a bit for the blocking transaction to start
        time.sleep(0.1)
        
        # This should timeout quickly due to the 1.0 second timeout in log_event
        start_time = time.time()
        result = processor.log_event({'hook_name': 'timeout_test'})
        elapsed = time.time() - start_time
        
        # Should fail quickly (within timeout + small buffer)
        assert result is False
        assert elapsed < 2.0, f"Database timeout took {elapsed}s, should be < 2s"
        
        thread.join()

    def test_event_schema_version_compatibility(self, temp_dir):
        """Test handling of different event schema versions."""
        claude_dir = temp_dir / ".claude"
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        # Test with schema version 2.0 event (current format)
        v2_event = {
            'schema_version': '2.0',
            'hook_name': 'schema_test',
            'session_id': 'v2-session',
            'correlation_id': 'v2-corr',
            'workflow_phase': 'tool_preparation'
        }
        
        result = processor.log_event(v2_event)
        assert result is True
        
        # Verify stored data preserves schema fields
        with sqlite3.connect(processor.db_path) as conn:
            cursor = conn.execute("SELECT data FROM hook_events WHERE hook_name = 'schema_test'")
            stored_data = json.loads(cursor.fetchone()[0])
            assert stored_data['schema_version'] == '2.0'
            assert stored_data['workflow_phase'] == 'tool_preparation'

    def test_memory_usage_optimization(self, temp_dir):
        """Test that processor maintains reasonable memory usage."""
        claude_dir = temp_dir / ".claude"
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        import tracemalloc
        
        tracemalloc.start()
        
        # Log many events to test memory usage
        for i in range(1000):
            processor.log_event({
                'hook_name': f'memory_test_{i}',
                'session_id': f'session_{i}',
                'data': 'x' * 100  # Some data
            })
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Peak memory should be reasonable (less than 50MB as per config)
        peak_mb = peak / (1024 * 1024)
        assert peak_mb < 50, f"Peak memory usage was {peak_mb}MB, should be < 50MB"

    def test_configuration_validation(self, temp_dir):
        """Test that configuration values are properly validated."""
        claude_dir = temp_dir / ".claude"
        project_root = claude_dir.parent
        
        # Create config with extreme values
        config_content = """
[analytics]
max_processing_time_ms = 0
retention_days = -1
max_db_size_mb = 99999
"""
        config_path = project_root / "brainworm-config.toml"
        config_path.write_text(config_content)
        
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        # Values should be loaded as-is (validation happens at usage time)
        assert processor.config['max_processing_time_ms'] == 0
        assert processor.config['retention_days'] == -1
        assert processor.config['max_db_size_mb'] == 99999

    def test_extract_file_path_bash_commands(self, temp_dir):
        """Test file_path extraction from Bash commands with various patterns."""
        claude_dir = temp_dir / ".claude"
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        # Test cases: (command, expected_file_path)
        test_cases = [
            # Problematic cases that should be fixed
            ("head -20 file.txt", "file.txt"),
            ("head -10", None),
            ("cat <<'EOF'", None),
            ("find . -name '*.py'", None),
            ("ls > /dev/null", None),
            ("git commit -m \"$(cat <<'EOF'\nCommit message\nEOF\n)\"", None),
            
            # Valid cases that should work
            ("cat /path/to/file.py", "/path/to/file.py"),
            ("vim src/test.py", "src/test.py"),
            ("less README.md", "README.md"),
            ("touch newfile.txt", "newfile.txt"),
            ("rm oldfile.py", "oldfile.py"),
            ("head -20 /Users/test/file.log", "/Users/test/file.log"),
            ("tail -f server.log", "server.log"),
            
            # Edge cases
            ("echo 'test' > output.txt", "output.txt"),
            ("cat input.txt | grep pattern", "input.txt"),
            ("head -20 'file with spaces.txt'", "'file with spaces.txt'"),
            ("vim \"quoted/path.py\"", "\"quoted/path.py\""),
        ]
        
        for command, expected in test_cases:
            # Create test event data
            event_data = {
                'tool_name': 'Bash',
                'tool_input': {
                    'command': command
                }
            }
            
            result = processor._extract_file_path(event_data)
            
            # Strip quotes for comparison if both are strings
            if result and expected and isinstance(result, str) and isinstance(expected, str):
                result_clean = result.strip('"\'')
                expected_clean = expected.strip('"\'')
                assert result_clean == expected_clean, f"Command: '{command}' | Expected: {expected} | Got: {result}"
            else:
                assert result == expected, f"Command: '{command}' | Expected: {expected} | Got: {result}"

    def test_extract_file_path_edit_tools(self, temp_dir):
        """Test file_path extraction from Edit/Write/Read tools."""
        claude_dir = temp_dir / ".claude"
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        # Test Edit tool
        event_data = {
            'tool_name': 'Edit',
            'tool_input': {
                'file_path': '/path/to/test.py',
                'old_string': 'old',
                'new_string': 'new'
            }
        }
        
        result = processor._extract_file_path(event_data)
        assert result == '/path/to/test.py'
        
        # Test Write tool  
        event_data = {
            'tool_name': 'Write',
            'tool_input': {
                'file_path': 'src/new_file.py',
                'content': 'print("hello")'
            }
        }
        
        result = processor._extract_file_path(event_data)
        assert result == 'src/new_file.py'

    def test_is_valid_file_path(self, temp_dir):
        """Test the _is_valid_file_path validation function."""
        claude_dir = temp_dir / ".claude"
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        # Test cases: (path, should_be_valid)
        validation_cases = [
            # Invalid paths
            ("-20", False),
            ("-name", False),
            ("<<'EOF'", False),
            ("EOF", False),
            ("/dev/null", False),
            ("", False),
            ("20", False),
            
            # Valid paths
            ("file.txt", True),
            ("/path/to/file.py", True),
            ("src/test.py", True),
            ("README.md", True),
            ("file with spaces.txt", True),
            ("test123", True),
            (".hidden", True),
            ("../parent.py", True),
        ]
        
        for path, should_be_valid in validation_cases:
            result = processor._is_valid_file_path(path)
            assert result == should_be_valid, f"Path: '{path}' | Expected: {should_be_valid} | Got: {result}"

    def test_extract_file_path_complex_bash_commands(self, temp_dir):
        """Test file_path extraction from complex Bash commands with multiple flags."""
        claude_dir = temp_dir / ".claude" 
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        complex_test_cases = [
            # Multiple flags before filename
            ("head -n 20 -v file.log", "file.log"),
            ("tail -f --retry server.log", "server.log"),
            ("grep -r -n pattern src/main.py", "src/main.py"),
            
            # Commands with piping that should stop at pipe
            ("cat file.txt | head -20", "file.txt"),
            ("less data.json | jq '.field'", "data.json"),
            
            # Commands that shouldn't match anything
            ("ls -la", None),
            ("ps aux", None),
            ("git status", None),
            
            # Redirection with valid files
            ("sort < input.txt", "input.txt"),
            ("python script.py > results.txt", "results.txt"),
        ]
        
        for command, expected in complex_test_cases:
            event_data = {
                'tool_name': 'Bash',
                'tool_input': {'command': command}
            }
            
            result = processor._extract_file_path(event_data)
            assert result == expected, f"Command: '{command}' | Expected: {expected} | Got: {result}"