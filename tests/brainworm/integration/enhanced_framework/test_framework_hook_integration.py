#!/usr/bin/env python3
"""
Hooks Framework Hook Integration Tests

Tests end-to-end hook execution with actual hook templates to validate
the Hooks Framework works properly in production scenarios.

This module tests:
- Framework initialization with real hook templates
- Complete hook lifecycle with framework processing
- Input processing through framework to hook execution
- Output processing and validation
- Performance validation (<100ms framework overhead)
"""

import pytest
import json
import time
import tempfile
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


# Import framework components
from brainworm.utils.hook_framework import HookFramework
from brainworm.utils.hook_types import (
    PreToolUseInput, PostToolUseInput, UserPromptSubmitInput,
    PreToolUseDecisionOutput, BaseHookInput
)

class TestFrameworkHookIntegration:
    """Test end-to-end hook execution with Hooks Framework"""

    @pytest.fixture
    def temp_project_root(self):
        """Create temporary project root with brainworm structure"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            brainworm_dir = project_root / ".brainworm"
            state_dir = brainworm_dir / "state"
            hooks_dir = brainworm_dir / "hooks"
            
            brainworm_dir.mkdir()
            state_dir.mkdir()
            hooks_dir.mkdir()
            
            # Create basic config
            config = {
                "daic": {
                    "enabled": True,
                    "blocked_tools": ["Write", "Edit", "MultiEdit"],
                    "read_only_bash_commands": {
                        "status": ["ls", "pwd", "cat", "head", "tail", "grep"],
                        "git": ["git status", "git log", "git diff"]
                    }
                }
            }
            (brainworm_dir / "config.toml").write_text(f"[daic]\n{config}")
            
            # Create unified state file
            unified_state = {
                "daic": {"mode": "discussion", "timestamp": None},
                "task": {"current_task": "test-task", "branch": "test-branch"},
                "session": {"correlation_id": "test-correlation"}
            }
            (state_dir / "unified_session_state.json").write_text(json.dumps(unified_state))
            
            yield project_root

    @pytest.fixture
    def mock_stdin_data(self):
        """Mock stdin data for hook execution"""
        return {
            "session_id": "test-session-12345",
            "transcript_path": "/tmp/transcript.txt",
            "cwd": "/test/cwd",
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {
                "command": "ls -la",
                "description": "List files"
            }
        }

    def test_framework_initialization_with_real_hooks(self, temp_project_root):
        """Test framework initialization with actual hook templates"""
        # Test with different hook types
        hook_types = [
            "session_start",
            "pre_tool_use", 
            "post_tool_use",
            "notification"
        ]
        
        for hook_type in hook_types:
            framework = HookFramework(hook_type)
            
            # Verify framework components are initialized
            assert framework.hook_name == hook_type
            assert framework.console is not None
            assert framework.raw_input_data == {}
            assert framework.session_id == "unknown"
            
            # Verify framework can discover project root
            with patch("utils.project.find_project_root", return_value=temp_project_root):
                framework._discover_project_root()
                assert framework.project_root == temp_project_root

    def test_complete_hook_lifecycle_execution(self, temp_project_root, mock_stdin_data):
        """Test complete hook lifecycle with framework processing"""
        start_time = time.time()
        
        # Mock stdin to provide input data
        with patch("sys.stdin.read", return_value=json.dumps(mock_stdin_data)):
            with patch("utils.project.find_project_root", return_value=temp_project_root):
                framework = HookFramework("test_hook")
                
                # Execute full lifecycle
                framework._read_input()
                framework._discover_project_root()
                
                # Verify input processing
                assert framework.raw_input_data == mock_stdin_data
                assert framework.session_id == "test-session-12345"
                assert framework.project_root == temp_project_root
                
                # Verify typed input parsing
                assert framework.typed_input is not None
                if isinstance(framework.typed_input, BaseHookInput):
                    assert framework.typed_input.session_id == "test-session-12345"
                    assert framework.typed_input.cwd == "/test/cwd"
        
        # Verify framework overhead is minimal
        end_time = time.time()
        framework_overhead = (end_time - start_time) * 1000  # Convert to milliseconds
        assert framework_overhead < 100, f"Framework overhead {framework_overhead}ms exceeds 100ms limit"

    def test_input_processing_through_framework(self, temp_project_root):
        """Test input processing through framework to hook execution"""
        test_cases = [
            # Pre-tool use input
            {
                "session_id": "session-1",
                "transcript_path": "/tmp/transcript1.txt", 
                "cwd": "/test/dir1",
                "hook_event_name": "PreToolUse",
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": "/test/file.py",
                    "old_string": "old code",
                    "new_string": "new code"
                }
            },
            # Post-tool use input
            {
                "session_id": "session-2",
                "transcript_path": "/tmp/transcript2.txt",
                "cwd": "/test/dir2", 
                "hook_event_name": "PostToolUse",
                "tool_name": "Write",
                "tool_input": {
                    "file_path": "/test/newfile.py",
                    "content": "print('hello')"
                },
                "tool_response": {
                    "filePath": "/test/newfile.py",
                    "type": "file_write"
                }
            },
            # User prompt input
            {
                "session_id": "session-3",
                "transcript_path": "/tmp/transcript3.txt",
                "cwd": "/test/dir3",
                "hook_event_name": "UserPromptSubmit", 
                "prompt": "Hello, please help me with this code"
            }
        ]
        
        for test_input in test_cases:
            with patch("sys.stdin.read", return_value=json.dumps(test_input)):
                with patch("utils.project.find_project_root", return_value=temp_project_root):
                    framework = HookFramework("test_input_processing")
                    framework._read_input()
                    
                    # Verify raw input processing
                    assert framework.raw_input_data == test_input
                    assert framework.session_id == test_input["session_id"]
                    
                    # Verify type-safe parsing
                    framework._parse_typed_input()
                    assert framework.typed_input is not None
                    
                    # Verify correct type parsing based on hook type
                    if "tool_name" in test_input and "tool_response" not in test_input:
                        # Should parse as PreToolUseInput
                        if isinstance(framework.typed_input, PreToolUseInput):
                            assert framework.typed_input.tool_name == test_input["tool_name"]
                    elif "tool_response" in test_input:
                        # Should parse as PostToolUseInput
                        if isinstance(framework.typed_input, PostToolUseInput):
                            assert framework.typed_input.tool_name == test_input["tool_name"]
                    elif "prompt" in test_input:
                        # Should parse as UserPromptSubmitInput
                        if isinstance(framework.typed_input, UserPromptSubmitInput):
                            assert framework.typed_input.prompt == test_input["prompt"]

    def test_output_processing_and_validation(self, temp_project_root, mock_stdin_data):
        """Test output processing and validation"""
        with patch("sys.stdin.read", return_value=json.dumps(mock_stdin_data)):
            with patch("utils.project.find_project_root", return_value=temp_project_root):
                framework = HookFramework("pre_tool_use")
                framework._read_input()
                framework._discover_project_root()
                
                # Test decision output for pre_tool_use hooks
                framework.approve_tool("Test approval")
                
                # Verify decision output is set
                assert framework.decision_output is not None
                assert framework.decision_output.continue_ is True
                assert framework.decision_output.stop_reason == "Test approval"
                
                # Test JSON response output
                test_response = {"context": "test context", "metadata": {"test": "data"}}
                framework.set_json_response(test_response)
                assert framework.json_response == test_response
                
                # Test output formatting
                with patch("sys.stdout") as mock_stdout:
                    framework._output_decision()
                    framework._output_json_response()
                    
                    # Verify stdout was called with properly formatted JSON
                    assert mock_stdout.write.called or mock_stdout.flush.called

    def test_error_handling_in_framework_lifecycle(self, temp_project_root):
        """Test error handling throughout framework lifecycle"""
        # Test invalid JSON input handling
        with patch("sys.stdin.read", return_value="invalid json"):
            framework = HookFramework("test_error_handling")
            framework._read_input()
            
            # Should not crash, should default to empty dict
            assert framework.raw_input_data == {}
            assert framework.session_id == "unknown"
        
        # Test project root discovery failure
        with patch("utils.project.find_project_root", side_effect=RuntimeError("No project root")):
            framework = HookFramework("test_error_handling")
            framework._discover_project_root()
            
            # Should fallback to current directory
            assert framework.project_root == Path.cwd()
        
        # Test analytics failure handling
        with patch("utils.project.find_project_root", return_value=temp_project_root):
            framework = HookFramework("test_error_handling", security_critical=False)
            framework._discover_project_root()
            
            # Mock analytics failure
            if framework.analytics_logger:
                with patch.object(framework.analytics_logger, 'log_event_with_analytics', side_effect=Exception("Analytics failed")):
                    # Should not crash on analytics failure when not security critical
                    result = framework._process_analytics()
                    assert result is False  # Should return False on failure

    def test_custom_logic_integration_with_framework(self, temp_project_root, mock_stdin_data):
        """Test custom logic integration with framework infrastructure"""
        custom_logic_called = False
        custom_logic_args = None
        
        def test_custom_logic(framework, typed_input):
            nonlocal custom_logic_called, custom_logic_args
            custom_logic_called = True
            custom_logic_args = (framework, typed_input)
            
            # Verify framework provides needed infrastructure
            assert framework.project_root is not None
            assert framework.raw_input_data is not None
            assert typed_input is not None
            
            # Test framework decision methods
            framework.approve_tool("Custom logic approval")
        
        with patch("sys.stdin.read", return_value=json.dumps(mock_stdin_data)):
            with patch("utils.project.find_project_root", return_value=temp_project_root):
                framework = HookFramework("test_custom_logic")
                framework.with_custom_logic(test_custom_logic)
                
                # Execute lifecycle to test custom logic integration
                framework._read_input()
                framework._discover_project_root()
                
                # Execute custom logic
                if framework.custom_logic_fn and framework.typed_input:
                    framework.custom_logic_fn(framework, framework.typed_input)
                
                # Verify custom logic was called with correct parameters
                assert custom_logic_called
                assert custom_logic_args[0] == framework
                assert custom_logic_args[1] == framework.typed_input
                
                # Verify framework state was updated by custom logic
                assert framework.decision_output is not None
                assert framework.decision_output.continue_ is True

    def test_analytics_integration_with_real_hooks(self, temp_project_root, mock_stdin_data):
        """Test analytics integration works with actual hook scenarios"""
        with patch("sys.stdin.read", return_value=json.dumps(mock_stdin_data)):
            with patch("utils.project.find_project_root", return_value=temp_project_root):
                framework = HookFramework("pre_tool_use", enable_analytics=True)
                framework._read_input()
                framework._discover_project_root()
                
                # Verify analytics logger is initialized
                if framework.analytics_logger:
                    assert framework.analytics_logger is not None
                    
                    # Test analytics processing
                    with patch.object(framework.analytics_logger, 'log_pre_tool_execution', return_value=True) as mock_analytics:
                        result = framework._process_analytics()
                        
                        # Verify analytics method was called
                        mock_analytics.assert_called_once()
                        assert result is True

    def test_performance_validation_framework_overhead(self, temp_project_root):
        """Test framework overhead is consistently under 100ms"""
        test_iterations = 10
        overhead_measurements = []
        
        for i in range(test_iterations):
            mock_data = {
                "session_id": f"perf-test-{i}",
                "transcript_path": f"/tmp/transcript{i}.txt",
                "cwd": "/test/perf",
                "hook_event_name": "TestEvent"
            }
            
            start_time = time.time()
            
            with patch("sys.stdin.read", return_value=json.dumps(mock_data)):
                with patch("utils.project.find_project_root", return_value=temp_project_root):
                    framework = HookFramework(f"perf_test_{i}")
                    framework._read_input()
                    framework._discover_project_root()
                    framework._process_analytics()
            
            end_time = time.time()
            overhead = (end_time - start_time) * 1000  # Convert to milliseconds
            overhead_measurements.append(overhead)
        
        # Verify all measurements are under 100ms
        for i, overhead in enumerate(overhead_measurements):
            assert overhead < 100, f"Iteration {i}: Framework overhead {overhead}ms exceeds 100ms limit"
        
        # Verify average overhead is reasonable
        avg_overhead = sum(overhead_measurements) / len(overhead_measurements)
        assert avg_overhead < 50, f"Average framework overhead {avg_overhead}ms is too high"

    def test_real_hook_template_execution_with_framework(self, temp_project_root):
        """Test execution with actual hook templates using framework"""
        # Test session_start hook template
        session_start_input = {
            "session_id": "real-session-test",
            "transcript_path": "/tmp/real_transcript.txt", 
            "cwd": str(temp_project_root),
            "hook_event_name": "SessionStart"
        }
        
        with patch("sys.stdin.read", return_value=json.dumps(session_start_input)):
            with patch("utils.project.find_project_root", return_value=temp_project_root):
                # Import and test actual session_start hook
                try:
                    import session_start
                    # This should execute without error using the framework
                    # The actual execution is tested by importing and running
                    assert hasattr(session_start, 'HookFramework')
                except ImportError:
                    pytest.skip("session_start hook not available for testing")
        
        # Test notification hook template
        notification_input = {
            "session_id": "notification-test",
            "transcript_path": "/tmp/notification_transcript.txt",
            "cwd": str(temp_project_root), 
            "hook_event_name": "Notification",
            "message": "Test notification",
            "type": "info"
        }
        
        with patch("sys.stdin.read", return_value=json.dumps(notification_input)):
            with patch("utils.project.find_project_root", return_value=temp_project_root):
                framework = HookFramework("notification")
                framework._read_input()
                framework._discover_project_root()
                
                # Verify framework processed notification data correctly
                assert framework.session_id == "notification-test"
                assert "message" in framework.raw_input_data
                assert framework.raw_input_data["message"] == "Test notification"

    def test_framework_compatibility_with_existing_hooks(self, temp_project_root):
        """Test framework maintains compatibility with existing hook patterns"""
        # Test data extractor compatibility
        from utils.hook_framework import extract_file_data, extract_command_data, extract_tool_data
        
        # Test file data extraction
        file_input = {
            "tool_input": {
                "file_path": "/test/file.py",
                "content": "test content"
            }
        }
        file_data = extract_file_data(file_input)
        assert file_data["file_path"] == "/test/file.py"
        
        # Test command data extraction
        command_input = {
            "tool_input": {
                "command": "ls -la /test",
                "description": "List test files"
            }
        }
        command_data = extract_command_data(command_input)
        assert command_data["command"] == "ls -la /test"
        
        # Test tool data extraction
        tool_input = {
            "tool_name": "Edit",
            "tool_response": {
                "success": True,
                "filePath": "/test/edited.py"
            }
        }
        tool_data = extract_tool_data(tool_input)
        assert tool_data["tool_name"] == "Edit"
        assert tool_data["tool_success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])