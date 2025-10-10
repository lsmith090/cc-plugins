#!/usr/bin/env python3
"""
Hooks Framework Type System Compliance Tests

Tests Claude Code specification compliance for input/output types,
JSON response formats, schema validation, and backward compatibility.

This module validates:
- JSON response format compliance with Claude Code specs
- Schema validation for all input/output types  
- Type system evolution and backward compatibility
- Error message formatting compliance
"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "hooks" / "templates"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "hooks" / "templates" / "utils"))

# Import type system components
from utils.hook_types import (
    BaseHookInput, PreToolUseInput, PostToolUseInput, UserPromptSubmitInput,
    PreToolUseDecisionOutput, UserPromptContextResponse, HookSpecificOutput,
    SessionCorrelationResponse, DAICModeResult, ToolAnalysisResult,
    CommandToolInput, FileWriteToolInput, FileEditToolInput, ToolResponse,
    parse_tool_input, parse_log_event, get_standard_timestamp,
    to_json_serializable, normalize_validation_issues
)
from utils.hook_framework import HookFramework

class TestTypeSystemCompliance:
    """Test Claude Code specification compliance for Hooks Framework"""

    def test_claude_code_json_response_format_compliance(self):
        """Test JSON response formats comply with Claude Code specifications"""
        # Test PreToolUse decision output compliance
        decision = PreToolUseDecisionOutput.approve("Test approval", "session-123")
        decision_dict = decision.to_dict()
        
        # Verify required Claude Code fields
        assert "continue" in decision_dict
        assert isinstance(decision_dict["continue"], bool)
        assert decision_dict["continue"] is True
        
        # Test blocking decision compliance
        block_decision = PreToolUseDecisionOutput.block(
            "Test block reason", 
            ["Issue 1", "Issue 2"],
            "session-123",
            suppress_output=True
        )
        block_dict = block_decision.to_dict()
        
        # Verify Claude Code compliance for blocking
        assert block_dict["continue"] is False
        assert "stopReason" in block_dict
        assert "suppressOutput" in block_dict
        assert block_dict["suppressOutput"] is True
        assert "hookSpecificOutput" in block_dict
        
        # Verify validation issues format
        hook_output = block_dict["hookSpecificOutput"]
        assert "validation_issues" in hook_output
        assert len(hook_output["validation_issues"]) == 2
        for issue in hook_output["validation_issues"]:
            assert isinstance(issue, dict)
            assert "message" in issue

    def test_user_prompt_context_response_compliance(self):
        """Test UserPromptSubmit context response compliance"""
        # Test context response creation
        context_response = UserPromptContextResponse.create_context(
            "Additional context for user prompt",
            debug_info={"processed_at": "2025-01-01T10:00:00Z"}
        )
        response_dict = context_response.to_dict()
        
        # Verify Claude Code required structure
        assert "hookSpecificOutput" in response_dict
        hook_output = response_dict["hookSpecificOutput"]
        assert hook_output["hookEventName"] == "UserPromptSubmit"
        assert "additionalContext" in hook_output
        assert hook_output["additionalContext"] == "Additional context for user prompt"
        
        # Verify debug information is preserved
        assert "debug" in response_dict
        assert response_dict["debug"]["processed_at"] == "2025-01-01T10:00:00Z"

    def test_input_schema_validation_all_types(self):
        """Test schema validation for all input types"""
        # Test BaseHookInput parsing
        base_input_data = {
            "session_id": "base-session-123",
            "transcript_path": "/tmp/base_transcript.txt",
            "cwd": "/base/working/dir",
            "hook_event_name": "BaseEvent"
        }
        base_input = BaseHookInput.parse(base_input_data)
        
        assert base_input.session_id == "base-session-123"
        assert base_input.transcript_path == "/tmp/base_transcript.txt" 
        assert base_input.cwd == "/base/working/dir"
        assert base_input.hook_event_name == "BaseEvent"
        assert base_input.raw == base_input_data
        
        # Test PreToolUseInput parsing with tool input
        pre_tool_data = {
            "session_id": "pre-tool-session",
            "transcript_path": "/tmp/pre_transcript.txt",
            "cwd": "/pre/working/dir",
            "hook_event_name": "PreToolUse", 
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "/test/file.py",
                "old_string": "old code",
                "new_string": "new code"
            }
        }
        pre_tool_input = PreToolUseInput.parse(pre_tool_data)
        
        assert pre_tool_input.tool_name == "Edit"
        assert pre_tool_input.tool_input is not None
        assert isinstance(pre_tool_input.tool_input, FileEditToolInput)
        assert pre_tool_input.tool_input.file_path == "/test/file.py"
        
        # Test PostToolUseInput parsing with response
        post_tool_data = {
            "session_id": "post-tool-session",
            "transcript_path": "/tmp/post_transcript.txt",
            "cwd": "/post/working/dir", 
            "hook_event_name": "PostToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "/test/newfile.py",
                "content": "print('hello world')"
            },
            "tool_response": {
                "filePath": "/test/newfile.py",
                "type": "file_creation",
                "success": True
            }
        }
        post_tool_input = PostToolUseInput.parse(post_tool_data)
        
        assert post_tool_input.tool_name == "Write"
        assert post_tool_input.tool_input is not None
        assert isinstance(post_tool_input.tool_input, FileWriteToolInput)
        assert post_tool_input.tool_response is not None
        assert post_tool_input.tool_response.filePath == "/test/newfile.py"
        
        # Test UserPromptSubmitInput parsing
        prompt_data = {
            "session_id": "prompt-session",
            "transcript_path": "/tmp/prompt_transcript.txt",
            "cwd": "/prompt/working/dir",
            "hook_event_name": "UserPromptSubmit",
            "prompt": "Please help me debug this code"
        }
        prompt_input = UserPromptSubmitInput.parse(prompt_data)
        
        assert prompt_input.prompt == "Please help me debug this code"
        assert prompt_input.session_id == "prompt-session"

    def test_tool_input_variant_parsing(self):
        """Test tool input variant parsing for different tool types"""
        # Test CommandToolInput (Bash tool)
        command_data = {
            "command": "ls -la /test",
            "description": "List test directory contents"
        }
        command_input = parse_tool_input(command_data)
        
        assert isinstance(command_input, CommandToolInput)
        assert command_input.command == "ls -la /test"
        assert command_input.description == "List test directory contents"
        
        # Test FileWriteToolInput (Write tool)
        write_data = {
            "file_path": "/test/new_file.py",
            "content": "def hello():\n    print('Hello, World!')",
            "description": "Create greeting function"
        }
        write_input = parse_tool_input(write_data)
        
        assert isinstance(write_input, FileWriteToolInput)
        assert write_input.file_path == "/test/new_file.py"
        assert "Hello, World!" in write_input.content
        
        # Test FileEditToolInput (Edit tool) - snake_case
        edit_data_snake = {
            "file_path": "/test/existing.py",
            "old_string": "def old_function():",
            "new_string": "def new_function():"
        }
        edit_input_snake = parse_tool_input(edit_data_snake)
        
        assert isinstance(edit_input_snake, FileEditToolInput)
        assert edit_input_snake.old_string == "def old_function():"
        assert edit_input_snake.new_string == "def new_function():"
        
        # Test FileEditToolInput (Edit tool) - camelCase  
        edit_data_camel = {
            "file_path": "/test/existing.py",
            "oldString": "def old_function():",
            "newString": "def new_function():"
        }
        edit_input_camel = parse_tool_input(edit_data_camel)
        
        assert isinstance(edit_input_camel, FileEditToolInput)
        assert edit_input_camel.oldString == "def old_function():"
        assert edit_input_camel.newString == "def new_function():"
        
        # Test MultiEdit input
        multi_edit_data = {
            "file_path": "/test/multi.py",
            "edits": [
                {"old_string": "import os", "new_string": "import sys"},
                {"old_string": "print('old')", "new_string": "print('new')"}
            ]
        }
        multi_edit_input = parse_tool_input(multi_edit_data)
        
        assert isinstance(multi_edit_input, FileEditToolInput)
        assert multi_edit_input.edits is not None
        assert len(multi_edit_input.edits) == 2

    def test_type_system_backward_compatibility(self):
        """Test type system handles legacy data formats"""
        # Test legacy input format without cwd field
        legacy_input = {
            "session_id": "legacy-session",
            "transcript_path": "/tmp/legacy.txt",
            "hook_event_name": "LegacyEvent"
            # Missing cwd field
        }
        base_input = BaseHookInput.parse(legacy_input)
        
        # Should handle missing cwd gracefully
        assert base_input.cwd == ""  # Default empty string
        assert base_input.session_id == "legacy-session"
        
        # Test legacy validation issues format (string instead of dict)
        legacy_validation = ["Error 1", "Error 2", "Error 3"]
        normalized = normalize_validation_issues([
            {"message": "Dict error"},
            "String error", 
            {"detail": "Detail error"}
        ])
        
        assert "Dict error" in normalized
        assert "String error" in normalized  
        assert "Detail error" in normalized
        
        # Test legacy timestamp formats
        legacy_timestamps = [
            "1640995200",      # Unix timestamp
            "1640995200000",   # Millisecond timestamp
            "2022-01-01T00:00:00Z",  # ISO with Z
            "2022-01-01T00:00:00+00:00"  # ISO with timezone
        ]
        
        for ts in legacy_timestamps:
            try:
                from utils.hook_types import parse_standard_timestamp
                parsed = parse_standard_timestamp(ts)
                assert parsed is not None
                assert parsed.year == 2022
            except Exception as e:
                pytest.fail(f"Failed to parse legacy timestamp {ts}: {e}")

    def test_output_schema_serialization(self):
        """Test output schemas serialize correctly for Claude Code"""
        # Test SessionCorrelationResponse
        correlation_response = SessionCorrelationResponse(
            success=True,
            session_id="correlation-session-123",
            correlation_id="correlation-456",
            timestamp=get_standard_timestamp()
        )
        correlation_dict = correlation_response.to_dict()
        
        assert correlation_dict["success"] is True
        assert correlation_dict["session_id"] == "correlation-session-123"
        assert "timestamp" in correlation_dict
        
        # Test DAICModeResult
        daic_result = DAICModeResult(
            success=True,
            old_mode="discussion",
            new_mode="implementation", 
            timestamp=get_standard_timestamp(),
            trigger="make it so"
        )
        daic_dict = daic_result.to_dict()
        
        assert daic_dict["old_mode"] == "discussion"
        assert daic_dict["new_mode"] == "implementation"
        assert daic_dict["trigger"] == "make it so"
        
        # Test ToolAnalysisResult
        tool_analysis = ToolAnalysisResult(
            success=True,
            error_info={"error_count": 0},
            execution_metrics={"duration_ms": 150.5},
            risk_factors=["file_modification", "network_access"]
        )
        analysis_dict = tool_analysis.to_dict()
        
        assert analysis_dict["success"] is True
        assert analysis_dict["execution_metrics"]["duration_ms"] == 150.5
        assert "file_modification" in analysis_dict["risk_factors"]

    def test_framework_json_response_compliance(self):
        """Test framework JSON responses comply with Claude Code specs"""
        framework = HookFramework("test_compliance")
        
        # Test typed response setting
        context_response = UserPromptContextResponse.create_context(
            "Test context",
            {"framework": "v2.0"}
        )
        framework.set_typed_response(context_response)
        
        # Verify JSON response is properly formatted
        assert framework.json_response is not None
        assert "hookSpecificOutput" in framework.json_response
        
        # Test JSON serialization
        serialized = to_json_serializable(context_response)
        assert isinstance(serialized, dict)
        assert "hookSpecificOutput" in serialized
        
        # Test framework output with mock stdout
        with patch("sys.stdout") as mock_stdout:
            with patch("sys.stdout.flush") as mock_flush:
                framework._output_json_response()
                
                # Should call print with JSON string
                mock_stdout.write.assert_called()
                mock_flush.assert_called()

    def test_error_message_format_compliance(self):
        """Test error messages follow Claude Code format requirements"""
        # Test PreToolUse blocking messages
        block_decision = PreToolUseDecisionOutput.block(
            "DAIC workflow prevents tool usage in discussion mode",
            [
                "Tool Write blocked in discussion mode",
                "Use trigger phrase to switch to implementation mode"
            ],
            "session-compliance-test",
            suppress_output=False
        )
        
        block_dict = block_decision.to_dict()
        
        # Verify error message format compliance
        assert "stopReason" in block_dict
        assert "DAIC workflow" in block_dict["stopReason"]
        assert "hookSpecificOutput" in block_dict
        
        validation_issues = block_dict["hookSpecificOutput"]["validation_issues"]
        assert len(validation_issues) == 2
        
        # Each validation issue should be properly formatted
        for issue in validation_issues:
            assert isinstance(issue, dict)
            assert "message" in issue
            assert len(issue["message"]) > 0
        
        # Test framework error handling preserves format
        framework = HookFramework("error_format_test")
        
        # Test invalid response schema handling
        invalid_schema = "not a schema object"
        try:
            framework.set_typed_response(invalid_schema)
            pytest.fail("Should have raised ValueError for invalid schema")
        except ValueError as e:
            assert "Response schema must have .to_dict() method" in str(e)

    def test_claude_code_specification_edge_cases(self):
        """Test edge cases in Claude Code specification compliance"""
        # Test empty input handling
        empty_input = {}
        base_empty = BaseHookInput.parse(empty_input)
        
        assert base_empty.session_id == ""
        assert base_empty.transcript_path == ""
        assert base_empty.cwd == ""
        assert base_empty.hook_event_name == ""
        
        # Test None input handling
        none_tool_input = parse_tool_input(None)
        assert none_tool_input is None
        
        # Test malformed tool input
        malformed_input = {"invalid": "structure"}
        malformed_tool = parse_tool_input(malformed_input)
        assert malformed_tool is None
        
        # Test decision output with minimal data
        minimal_decision = PreToolUseDecisionOutput(continue_=True)
        minimal_dict = minimal_decision.to_dict()
        
        assert "continue" in minimal_dict
        assert minimal_dict["continue"] is True
        assert len(minimal_dict) >= 1  # Only required field
        
        # Test response with empty context
        empty_context = UserPromptContextResponse.create_context("")
        empty_dict = empty_context.to_dict()
        
        assert empty_dict["hookSpecificOutput"]["additionalContext"] == ""
        assert empty_dict["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
        
        # Test timestamp edge cases
        current_timestamp = get_standard_timestamp()
        assert "T" in current_timestamp  # ISO format
        assert current_timestamp.endswith("+00:00") or current_timestamp.endswith("Z")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])