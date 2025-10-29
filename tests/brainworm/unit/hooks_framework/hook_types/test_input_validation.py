#!/usr/bin/env python3
"""
Comprehensive Input Validation Tests for hook_types.py

Tests the most critical and complex input validation scenarios including:
- Tool input parsing with type detection logic
- Hook input types with required field handling
- Complex field mapping and edge cases
- Error handling and graceful degradation

Focus: Real bug detection over test theater, following brainworm testing principles.
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, Any

# Import from brainworm plugin package
from brainworm.utils.hook_types import (
    # Tool input types
    CommandToolInput, FileWriteToolInput, FileEditToolInput,
    parse_tool_input, ToolInputVariant,
    # Hook input types
    BaseHookInput, PreToolUseInput, PostToolUseInput, UserPromptSubmitInput,
    # Log event parsing
    parse_log_event, PreToolUseLogEvent, PostToolUseLogEvent, UserPromptSubmitLogEvent, BaseLogEvent,
    # Tool response
    ToolResponse
)


class TestToolInputParsing:
    """Test parse_tool_input() function - HIGH RISK component with complex type detection logic"""

    def test_command_tool_input_parsing_happy_path(self):
        """Test normal CommandToolInput parsing"""
        input_data = {"command": "git status", "description": "Check git status"}
        result = parse_tool_input(input_data)

        assert isinstance(result, CommandToolInput)
        assert result.command == "git status"
        assert result.description == "Check git status"
        assert result.extra == {}

    def test_file_write_tool_input_parsing_happy_path(self):
        """Test normal FileWriteToolInput parsing"""
        input_data = {"file_path": "/tmp/test.txt", "content": "hello world"}
        result = parse_tool_input(input_data)

        assert isinstance(result, FileWriteToolInput)
        assert result.file_path == "/tmp/test.txt"
        assert result.content == "hello world"
        assert result.description is None
        assert result.extra == {}

    def test_file_edit_tool_input_parsing_snake_case(self):
        """Test FileEditToolInput with snake_case fields"""
        input_data = {"file_path": "/tmp/test.txt", "old_string": "foo", "new_string": "bar"}
        result = parse_tool_input(input_data)

        assert isinstance(result, FileEditToolInput)
        assert result.file_path == "/tmp/test.txt"
        assert result.old_string == "foo"
        assert result.new_string == "bar"
        assert result.oldString is None
        assert result.newString is None
        assert result.extra == {}

    def test_file_edit_tool_input_parsing_camel_case(self):
        """Test FileEditToolInput with camelCase fields"""
        input_data = {"file_path": "/tmp/test.txt", "oldString": "foo", "newString": "bar"}
        result = parse_tool_input(input_data)

        assert isinstance(result, FileEditToolInput)
        assert result.file_path == "/tmp/test.txt"
        assert result.oldString == "foo"
        assert result.newString == "bar"
        assert result.old_string is None
        assert result.new_string is None
        assert result.extra == {}

    def test_tool_input_parsing_priority_order_command_wins(self):
        """
        HIGH RISK: Test type detection logic with ambiguous input
        CommandToolInput should win when input matches multiple types
        """
        input_data = {
            "command": "echo 'test' > /tmp/file.txt",
            "file_path": "/tmp/file.txt",  # Could suggest file operation
            "description": "Create test file"
        }

        result = parse_tool_input(input_data)

        # Should prioritize CommandToolInput (first match wins)
        assert isinstance(result, CommandToolInput), "Should return CommandToolInput for ambiguous input"
        assert result.command == "echo 'test' > /tmp/file.txt"
        assert result.description == "Create test file"

        # Extra fields should be preserved
        assert "file_path" in result.extra, "Non-matching fields should be preserved in extra"
        assert result.extra["file_path"] == "/tmp/file.txt"

    def test_file_edit_mixed_case_fields(self):
        """HIGH RISK: Test mixed case field handling"""
        input_data = {
            "file_path": "/tmp/test.txt",
            "old_string": "snake_case",
            "newString": "camelCase"
        }
        result = parse_tool_input(input_data)

        assert isinstance(result, FileEditToolInput)
        assert result.old_string == "snake_case"
        assert result.newString == "camelCase"
        # Both fields should be preserved separately
        assert result.new_string is None  # Only newString was provided

    def test_file_edit_edits_array_parsing(self):
        """HIGH RISK: Test edits array with complex nested operations"""
        input_data = {
            "file_path": "/tmp/test.txt",
            "edits": [
                {"old_string": "foo", "new_string": "bar"},
                {"oldString": "baz", "newString": "qux"}
            ]
        }
        result = parse_tool_input(input_data)

        assert isinstance(result, FileEditToolInput)
        assert result.file_path == "/tmp/test.txt"
        assert len(result.edits) == 2
        assert result.edits[0]["old_string"] == "foo"
        assert result.edits[0]["new_string"] == "bar"
        assert result.edits[1]["oldString"] == "baz"
        assert result.edits[1]["newString"] == "qux"

    def test_tool_input_parsing_null_input(self):
        """Test null input handling"""
        assert parse_tool_input(None) is None

    def test_tool_input_parsing_empty_dict(self):
        """Test empty dict handling"""
        assert parse_tool_input({}) is None

    def test_tool_input_parsing_invalid_type(self):
        """Test invalid input type handling"""
        assert parse_tool_input("not a dict") is None
        assert parse_tool_input(123) is None
        assert parse_tool_input([]) is None

    def test_tool_input_parsing_unknown_tool_structure(self):
        """HIGH RISK: Test unknown tool types fail gracefully"""
        input_data = {"unknown_field": "value", "other_field": "data"}
        result = parse_tool_input(input_data)

        assert result is None, "Unknown tool types should return None"

    def test_extra_fields_preservation_command_tool(self):
        """HIGH RISK: Test data preservation for extensibility"""
        input_data = {
            "command": "test",
            "custom_field": "value",
            "metadata": {"key": "val", "nested": {"data": True}}
        }
        result = parse_tool_input(input_data)

        assert isinstance(result, CommandToolInput)
        assert result.extra["custom_field"] == "value"
        assert result.extra["metadata"]["key"] == "val"
        assert result.extra["metadata"]["nested"]["data"] is True

    def test_file_edit_matches_edge_cases(self):
        """HIGH RISK: Test match detection logic edge cases"""
        # file_path only - should NOT match (needs edit fields)
        assert FileEditToolInput.matches({"file_path": "/tmp/test"}) is False

        # Has file_path and edit field - should match
        assert FileEditToolInput.matches({"file_path": "/tmp/test", "old_string": "x"}) is True
        assert FileEditToolInput.matches({"file_path": "/tmp/test", "oldString": "x"}) is True
        assert FileEditToolInput.matches({"file_path": "/tmp/test", "edits": []}) is True

    def test_file_edit_malformed_edits_array(self):
        """HIGH RISK: Test graceful handling of malformed edits"""
        input_data = {"file_path": "/tmp/test.txt", "edits": "not an array"}
        result = parse_tool_input(input_data)

        # Should still create FileEditToolInput but handle gracefully
        assert isinstance(result, FileEditToolInput)
        assert result.edits == "not an array"  # Preserved as-is

    def test_file_edit_to_dict_roundtrip(self):
        """HIGH RISK: Test serialization consistency"""
        original = FileEditToolInput(
            file_path="/tmp/test.txt",
            old_string="old",
            new_string="new",
            oldString="camelOld",
            newString="camelNew",
            edits=[{"test": "edit"}],
            extra={"custom": "data"}
        )

        serialized = original.to_dict()

        # Verify all fields are present
        assert serialized["file_path"] == "/tmp/test.txt"
        assert serialized["old_string"] == "old"
        assert serialized["new_string"] == "new"
        assert serialized["oldString"] == "camelOld"
        assert serialized["newString"] == "camelNew"
        assert serialized["edits"] == [{"test": "edit"}]
        assert serialized["custom"] == "data"


class TestHookInputTypes:
    """Test hook input parsing - HIGH RISK for required field validation"""

    def test_base_hook_input_complete(self):
        """Test BaseHookInput with all required fields"""
        input_data = {
            "session_id": "session-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/tmp/project",
            "hook_event_name": "pre_tool_use"
        }
        result = BaseHookInput.parse(input_data)

        assert result.session_id == "session-123"
        assert result.transcript_path == "/tmp/transcript.json"
        assert result.cwd == "/tmp/project"
        assert result.hook_event_name == "pre_tool_use"
        assert result.raw == input_data

    def test_pre_tool_use_input_complete(self):
        """Test PreToolUseInput with valid tool_input"""
        tool_input_data = {"command": "git status"}
        input_data = {
            "session_id": "session-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/tmp/project",
            "hook_event_name": "pre_tool_use",
            "tool_name": "Bash",
            "tool_input": tool_input_data
        }
        result = PreToolUseInput.parse(input_data)

        assert result.session_id == "session-123"
        assert result.tool_name == "Bash"
        assert isinstance(result.tool_input, CommandToolInput)
        assert result.tool_input.command == "git status"

    def test_hook_input_missing_optional_fields(self):
        """HIGH RISK: Test default value handling"""
        input_data = {}  # No fields provided
        result = BaseHookInput.parse(input_data)

        # Should get empty string defaults, not crash
        assert result.session_id == ""
        assert result.transcript_path == ""
        assert result.cwd == ""
        assert result.hook_event_name == ""

    def test_hook_input_extra_unknown_fields(self):
        """HIGH RISK: Test forward compatibility with unknown fields"""
        input_data = {
            "session_id": "session-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/tmp/project",
            "hook_event_name": "pre_tool_use",
            "future_field": "future_value",
            "nested_unknown": {"data": "preserved"}
        }
        result = BaseHookInput.parse(input_data)

        # Raw data should contain everything
        assert result.raw == input_data
        assert result.raw["future_field"] == "future_value"
        assert result.raw["nested_unknown"]["data"] == "preserved"

    def test_pre_tool_use_malformed_tool_input(self):
        """HIGH RISK: Test error handling in nested parsing"""
        input_data = {
            "session_id": "session-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/tmp/project",
            "hook_event_name": "pre_tool_use",
            "tool_name": "Bash",
            "tool_input": {"invalid": "structure"}  # Won't match any tool type
        }
        result = PreToolUseInput.parse(input_data)

        # Should not crash, tool_input should be None
        assert result.tool_input is None
        assert result.tool_name == "Bash"  # Other fields should be preserved


class TestLogEventParsing:
    """Test parse_log_event() routing logic - HIGH RISK for fallback behavior"""

    def test_log_event_pre_tool_use_routing(self):
        """Test routing to PreToolUseLogEvent"""
        input_data = {
            "hook_name": "pre_tool_use",
            "session_id": "session-123",
            "hook_event_name": "pre_tool_use",
            "logged_at": "2025-09-08T00:00:00+00:00",
            "tool_name": "Bash"
        }
        result = parse_log_event(input_data)

        assert isinstance(result, PreToolUseLogEvent)
        assert result.hook_name == "pre_tool_use"
        assert result.tool_name == "Bash"

    def test_log_event_post_tool_use_routing(self):
        """Test routing to PostToolUseLogEvent"""
        input_data = {
            "hook_name": "post_tool_use",
            "session_id": "session-123",
            "hook_event_name": "post_tool_use",
            "logged_at": "2025-09-08T00:00:00+00:00",
            "tool_name": "Edit"
        }
        result = parse_log_event(input_data)

        assert isinstance(result, PostToolUseLogEvent)
        assert result.tool_name == "Edit"

    def test_log_event_user_prompt_submit_routing(self):
        """Test routing to UserPromptSubmitLogEvent"""
        input_data = {
            "hook_name": "user_prompt_submit",
            "session_id": "session-123",
            "hook_event_name": "user_prompt_submit",
            "logged_at": "2025-09-08T00:00:00+00:00",
            "prompt": "Test prompt"
        }
        result = parse_log_event(input_data)

        assert isinstance(result, UserPromptSubmitLogEvent)
        assert result.prompt == "Test prompt"

    def test_log_event_unknown_hook_name_fallback(self):
        """HIGH RISK: Test fallback logic for unknown hooks"""
        input_data = {
            "hook_name": "unknown_hook",
            "session_id": "session-123",
            "logged_at": "2025-09-08T00:00:00+00:00"
        }
        result = parse_log_event(input_data)

        assert isinstance(result, BaseLogEvent)
        assert type(result) == BaseLogEvent  # Exact type, not subclass
        assert result.hook_name == "unknown_hook"

    def test_log_event_missing_hook_name_fallback(self):
        """HIGH RISK: Test missing hook name handling"""
        input_data = {
            "session_id": "session-123",
            "logged_at": "2025-09-08T00:00:00+00:00"
        }
        result = parse_log_event(input_data)

        assert isinstance(result, BaseLogEvent)
        assert result.hook_name == ""  # Empty string default

    def test_log_event_null_hook_name_fallback(self):
        """HIGH RISK: Test null hook name handling"""
        input_data = {
            "hook_name": None,
            "session_id": "session-123",
            "logged_at": "2025-09-08T00:00:00+00:00"
        }
        result = parse_log_event(input_data)

        assert isinstance(result, BaseLogEvent)
        assert result.hook_name is None  # Explicit None is preserved

    def test_log_event_completely_empty_input(self):
        """HIGH RISK: Test robustness with empty data"""
        result = parse_log_event({})

        assert isinstance(result, BaseLogEvent)
        # Should not crash, should have sensible defaults
        assert result.session_id == ""
        assert result.hook_name == ""
        assert result.hook_event_name == ""

    def test_log_event_validation_issues_normalization(self):
        """HIGH RISK: Test validation issue data normalization"""
        input_data = {
            "hook_name": "pre_tool_use",
            "session_id": "session-123",
            "validation_issues": [
                "String issue",
                {"message": "Dict issue"},
                {"detail": "Detail issue", "code": "E001"},
                {"custom": "field", "message": "Complex issue"}
            ]
        }
        result = parse_log_event(input_data)

        assert isinstance(result, PreToolUseLogEvent)
        assert len(result.validation_issues) == 4

        # All should be normalized to dict format with 'message' field
        for issue in result.validation_issues:
            assert isinstance(issue, dict)
            assert 'message' in issue or 'detail' in issue or 'custom' in issue


class TestToolResponse:
    """Test ToolResponse parsing and serialization"""

    def test_tool_response_parse_roundtrip(self):
        """HIGH RISK: Test parse and serialization consistency"""
        original_data = {
            'filePath': '/test/roundtrip.py',
            'oldString': 'before',
            'newString': 'after',
            'type': 'edit',
            'extra_field': 'preserved'
        }

        # Parse and re-serialize
        parsed = ToolResponse.parse(original_data)
        reserialized = parsed.to_dict()

        # Verify roundtrip consistency
        assert reserialized['filePath'] == original_data['filePath']
        assert reserialized['oldString'] == original_data['oldString']
        assert reserialized['newString'] == original_data['newString']
        assert reserialized['extra_field'] == original_data['extra_field']

    def test_tool_response_parse_invalid_data(self):
        """Test handling of invalid parsing input"""
        assert ToolResponse.parse("invalid") is None
        assert ToolResponse.parse(None) is None
        assert ToolResponse.parse([]) is None

    def test_tool_response_parse_empty_dict(self):
        """Test parsing empty dict creates valid object"""
        result = ToolResponse.parse({})
        assert result is not None
        assert result.to_dict() == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
