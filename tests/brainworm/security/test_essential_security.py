"""
Essential Security Tests

Focused security testing for core protection measures in the brainworm event storage system.
Tests only the essential security concerns for a Claude Code hooks system.
"""

import os
import sys
import json
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from brainworm.utils.event_store import HookEventStore


class TestEssentialSecurity:
    """Essential security tests for the event storage system"""

    def test_event_storage_directory_permissions(self, temp_dir):
        """Test that event storage directory has appropriate permissions"""
        brainworm_dir = temp_dir / ".brainworm"
        brainworm_dir.mkdir(parents=True, exist_ok=True)

        event_store = HookEventStore(brainworm_dir)

        # Check that events directory exists and is writable
        events_dir = brainworm_dir / "events"
        assert events_dir.exists()
        assert os.access(events_dir, os.W_OK)

    def test_database_file_permissions(self, temp_dir):
        """Test that database file has appropriate permissions"""
        brainworm_dir = temp_dir / ".brainworm"
        brainworm_dir.mkdir(parents=True, exist_ok=True)

        event_store = HookEventStore(brainworm_dir)

        # Create a test event to ensure database is created
        event_store.log_event({
            "hook_name": "test_hook",
            "session_id": "test_session",
            "test": "data"
        })

        # Check database file permissions
        db_file = brainworm_dir / "events" / "hooks.db"
        assert db_file.exists()
        assert os.access(db_file, os.R_OK | os.W_OK)

    def test_event_data_storage(self, temp_dir):
        """Test that event data is properly stored in database"""
        brainworm_dir = temp_dir / ".brainworm"
        brainworm_dir.mkdir(parents=True, exist_ok=True)

        event_store = HookEventStore(brainworm_dir)

        # Store a test event
        event_data = {
            "hook_name": "pre_tool_use",
            "session_id": "test_session_123",
            "tool_name": "Read",
            "tool_input": {"file_path": "/test/file.py"}
        }

        success = event_store.log_event(event_data)
        assert success

        # Verify data was stored
        db_file = brainworm_dir / "events" / "hooks.db"
        conn = sqlite3.connect(db_file)
        cursor = conn.execute("SELECT COUNT(*) FROM hook_events WHERE session_id = ?", ("test_session_123",))
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 1

    def test_database_isolation(self, temp_dir):
        """Test that each brainworm instance has isolated database"""
        # Create two separate brainworm directories
        brainworm_dir_1 = temp_dir / "project1" / ".brainworm"
        brainworm_dir_2 = temp_dir / "project2" / ".brainworm"

        brainworm_dir_1.mkdir(parents=True, exist_ok=True)
        brainworm_dir_2.mkdir(parents=True, exist_ok=True)

        event_store_1 = HookEventStore(brainworm_dir_1)
        event_store_2 = HookEventStore(brainworm_dir_2)

        # Store events in each
        event_store_1.log_event({"hook_name": "test", "session_id": "project1_session"})
        event_store_2.log_event({"hook_name": "test", "session_id": "project2_session"})

        # Verify databases are separate
        db1 = brainworm_dir_1 / "events" / "hooks.db"
        db2 = brainworm_dir_2 / "events" / "hooks.db"

        assert db1.exists()
        assert db2.exists()
        assert db1 != db2


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)