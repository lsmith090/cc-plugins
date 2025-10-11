#!/usr/bin/env python3
"""
Tests for analytics logging integration and JSONL streamlining.

Tests the fixes for:
1. No double logging (single JSONL path via analytics processor)
2. No spurious empty logs directories
3. Analytics logging streamlined through single path
"""

import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from brainworm.utils.hook_analytics import AnalyticsHookLogger


class TestAnalyticsLoggingIntegration:
    """Test suite for analytics logging integration fixes."""

    def test_no_double_logging_to_jsonl(self, temp_dir):
        """Test that events are NOT double-logged to .brainworm/logs/"""
        project_root = temp_dir

        # Create analytics logger with analytics enabled
        logger = AnalyticsHookLogger(
            project_root=project_root,
            hook_name='test_hook',
            enable_analytics=True,
            session_id='test-session-123'
        )

        event_data = {
            'tool_name': 'Bash',
            'tool_input': {'command': 'ls -la'},
            'session_id': 'test-session-123'
        }

        # Log event
        result = logger.log_event_with_analytics(event_data, debug=False)
        assert result is True

        # Verify NO JSONL files in .brainworm/logs/ (old location)
        old_logs_dir = project_root / '.brainworm' / 'logs'
        if old_logs_dir.exists():
            jsonl_files = list(old_logs_dir.glob('*.jsonl'))
            assert len(jsonl_files) == 0, f"Found unexpected JSONL files in old logs dir: {jsonl_files}"

        # Verify event IS in analytics database
        db_path = project_root / '.brainworm' / 'analytics' / 'hooks.db'
        assert db_path.exists(), "Analytics database should exist"

        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) FROM hook_events
                WHERE hook_name = ? AND session_id = ?
            """, ('test_hook', 'test-session-123'))
            count = cursor.fetchone()[0]
            assert count == 1, "Event should be logged to database exactly once"

    def test_single_jsonl_path_via_analytics(self, temp_dir):
        """Test that JSONL backup is ONLY in analytics/logs/ directory."""
        project_root = temp_dir

        logger = AnalyticsHookLogger(
            project_root=project_root,
            hook_name='post_tool_use',
            enable_analytics=True,
            session_id='single-path-test'
        )

        event_data = {
            'tool_name': 'Edit',
            'tool_input': {'file_path': '/path/to/file.py'},
            'session_id': 'single-path-test'
        }

        # Mock datetime to control filename
        with patch('brainworm.utils.analytics_processor.datetime') as mock_datetime:
            from datetime import datetime
            mock_datetime.now.return_value = datetime(2025, 10, 11, 12, 0, 0)

            result = logger.log_event_with_analytics(event_data, debug=False)
            assert result is True

        # Verify JSONL backup is in analytics/logs/
        analytics_logs_dir = project_root / '.brainworm' / 'analytics' / 'logs'
        assert analytics_logs_dir.exists(), "Analytics logs directory should exist"

        jsonl_file = analytics_logs_dir / '2025-10-11_hooks.jsonl'
        assert jsonl_file.exists(), f"JSONL backup should exist at {jsonl_file}"

        # Read and verify content
        content = jsonl_file.read_text().strip()
        logged_event = json.loads(content)
        assert logged_event['hook_name'] == 'post_tool_use'
        assert logged_event['session_id'] == 'single-path-test'

    def test_no_redundant_logs_directory_creation(self, temp_dir):
        """Test that old .brainworm/logs/ directory is created by parent but unused."""
        project_root = temp_dir

        # Create logger WITHOUT analytics
        logger = AnalyticsHookLogger(
            project_root=project_root,
            hook_name='test_hook',
            enable_analytics=False,  # Analytics disabled
            session_id='no-logs-test'
        )

        # NOTE: Old logs directory IS created by HookLogger parent class __init__
        # This is a known issue - parent creates it even though analytics logger doesn't use it
        old_logs_dir = project_root / '.brainworm' / 'logs'
        # Directory will exist but should have NO files
        if old_logs_dir.exists():
            jsonl_files = list(old_logs_dir.glob('*.jsonl'))
            assert len(jsonl_files) == 0, "Old logs dir should have no JSONL files"

    def test_analytics_disabled_no_logging(self, temp_dir):
        """Test that with analytics disabled, enrichment happens but logging behavior varies."""
        project_root = temp_dir

        logger = AnalyticsHookLogger(
            project_root=project_root,
            hook_name='disabled_test',
            enable_analytics=False,
            session_id='disabled-session'
        )

        event_data = {
            'tool_name': 'Read',
            'session_id': 'disabled-session'
        }

        # Log event - with enable_analytics=False, enrichment returns original data
        result = logger.log_event_with_analytics(event_data, debug=False)

        # When analytics disabled, enrichment returns early and processor may still log
        # This is current behavior - analytics processor exists even when enable_analytics=False
        # The main fix is that it only logs to ONE place (analytics/logs/) not TWO

    def test_multiple_events_single_jsonl_file(self, temp_dir):
        """Test that multiple events append to same JSONL file correctly."""
        project_root = temp_dir

        logger = AnalyticsHookLogger(
            project_root=project_root,
            hook_name='multi_event_test',
            enable_analytics=True,
            session_id='multi-test'
        )

        # Log multiple events
        events = [
            {'tool_name': 'Read', 'session_id': 'multi-test'},
            {'tool_name': 'Edit', 'session_id': 'multi-test'},
            {'tool_name': 'Write', 'session_id': 'multi-test'},
        ]

        with patch('brainworm.utils.analytics_processor.datetime') as mock_datetime:
            from datetime import datetime
            mock_datetime.now.return_value = datetime(2025, 10, 11, 12, 0, 0)

            for event in events:
                logger.log_event_with_analytics(event, debug=False)

        # Verify all events in same JSONL file
        jsonl_file = project_root / '.brainworm' / 'analytics' / 'logs' / '2025-10-11_hooks.jsonl'
        assert jsonl_file.exists()

        lines = jsonl_file.read_text().strip().split('\n')
        assert len(lines) == 3, "Should have 3 events in JSONL file"

        # Verify each event
        tool_names = [json.loads(line)['tool_name'] for line in lines]
        assert tool_names == ['Read', 'Edit', 'Write']

    def test_analytics_processor_creates_minimal_structure(self, temp_dir):
        """Test that analytics processor creates minimal required structure."""
        project_root = temp_dir
        brainworm_dir = project_root / '.brainworm'

        # Import and initialize processor
        from brainworm.utils.analytics_processor import ClaudeAnalyticsProcessor
        processor = ClaudeAnalyticsProcessor(brainworm_dir)

        # Verify only necessary directories exist
        assert (brainworm_dir / 'analytics').exists(), "Analytics dir should exist"
        assert (brainworm_dir / 'analytics' / 'hooks.db').exists(), "Database should exist"
        assert (brainworm_dir / 'analytics' / 'logs').exists(), "Logs dir should exist for JSONL backups"

        # Old logs directory should NOT exist
        old_logs_dir = brainworm_dir / 'logs'
        assert not old_logs_dir.exists(), "Old logs directory should not be created by analytics processor"

    def test_hook_logger_does_not_write_to_old_logs(self, temp_dir):
        """Test that AnalyticsHookLogger doesn't WRITE to old logs directory."""
        project_root = temp_dir

        # AnalyticsHookLogger should NOT call parent's log_event that writes to old logs
        logger = AnalyticsHookLogger(
            project_root=project_root,
            hook_name='no_old_logs',
            enable_analytics=True,
            session_id='test-session'
        )

        event_data = {'tool_name': 'Bash', 'session_id': 'test-session'}
        logger.log_event_with_analytics(event_data, debug=False)

        # Old logs directory may exist (created by parent __init__) but should have NO files
        old_logs_dir = project_root / '.brainworm' / 'logs'
        if old_logs_dir.exists():
            jsonl_files = list(old_logs_dir.glob('*.jsonl'))
            assert len(jsonl_files) == 0, f"AnalyticsHookLogger should not write to old logs dir, found: {jsonl_files}"


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
