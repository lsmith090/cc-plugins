"""
Essential Security Tests

Focused security testing for core protection measures in the brainworm analytics system.
Tests only the essential security concerns for a Claude Code hooks system.
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


from brainworm.utils.analytics_processor import ClaudeAnalyticsProcessor


class TestEssentialSecurity:
    """Essential security tests for the analytics system"""
    
    def test_sensitive_data_filtering(self, temp_dir):
        """Test that sensitive data like API keys are filtered from logs"""
        claude_dir = temp_dir / ".claude"
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        # Test API key filtering
        event_data = {
            "tool_input": {
                "api_key": "sk-1234567890abcdef",
                "content": "Regular content"
            }
        }
        
        # Process the event
        processor.log_event("test_session", "test_hook", event_data)
        
        # Read the JSONL log file
        log_files = list((claude_dir / "analytics" / "logs").glob("*.jsonl"))
        assert len(log_files) > 0
        
        with open(log_files[0], 'r') as f:
            log_content = f.read()
        
        # Verify sensitive data is not in logs
        assert "sk-1234567890abcdef" not in log_content
        assert "Regular content" in log_content

    def test_password_filtering(self, temp_dir):
        """Test that passwords are filtered from logs"""
        claude_dir = temp_dir / ".claude"
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        # Test password filtering
        event_data = {
            "tool_input": {
                "password": "secret123",
                "user": "testuser"
            }
        }
        
        processor.log_event("test_session", "test_hook", event_data)
        
        # Read the JSONL log file
        log_files = list((claude_dir / "analytics" / "logs").glob("*.jsonl"))
        with open(log_files[0], 'r') as f:
            log_content = f.read()
        
        # Verify password is filtered but user is kept
        assert "secret123" not in log_content
        assert "testuser" in log_content

    def test_analytics_directory_permissions(self, temp_dir):
        """Test that analytics directory has appropriate permissions"""
        claude_dir = temp_dir / ".claude"
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        # Check that analytics directory exists and is writable
        analytics_dir = claude_dir / "analytics"
        assert analytics_dir.exists()
        assert os.access(analytics_dir, os.W_OK)
        
        # Check that log directory exists and is writable
        logs_dir = analytics_dir / "logs"
        assert logs_dir.exists()
        assert os.access(logs_dir, os.W_OK)

    def test_database_file_permissions(self, temp_dir):
        """Test that database file has appropriate permissions"""
        claude_dir = temp_dir / ".claude"
        processor = ClaudeAnalyticsProcessor(claude_dir)
        
        # Create a test event to ensure database is created
        processor.log_event("test_session", "test_hook", {"test": "data"})
        
        # Check database file permissions
        db_file = claude_dir / "analytics" / "hooks.db"
        assert db_file.exists()
        assert os.access(db_file, os.R_OK | os.W_OK)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)