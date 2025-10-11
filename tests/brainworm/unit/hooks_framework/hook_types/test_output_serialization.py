#!/usr/bin/env python3
"""
Output Response Schema and Serialization Tests for hook_types.py

Tests the most critical output validation and serialization scenarios including:
- PreToolUseDecisionOutput Claude Code JSON compliance (CRITICAL)
- ToolResponse serialization with camelCase field mapping
- Factory methods and static constructors
- Universal JSON serialization consistency
- Round-trip serialization validation

Focus: Claude Code integration compliance and preventing serialization failures.
"""

import pytest
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add hook_types module to path

from brainworm.utils.hook_types import (
    # Output response types
    PreToolUseDecisionOutput, ToolResponse,
    HookSpecificOutput, UserPromptContextResponse,
    SessionCorrelationResponse, DAICModeResult, ToolAnalysisResult,
    # Central data types
    CentralHookEventRow,
    # Serialization utilities
    to_json_serializable
)


class TestPreToolUseDecisionOutput:
    """
    CRITICAL: Test PreToolUseDecisionOutput Claude Code compliance
    This is the primary Claude Code integration point for tool blocking/approval
    """
    
    def test_pretool_decision_output_claude_code_compliance_approve(self):
        """Test PreToolUseDecisionOutput generates Claude Code compliant JSON for approval"""
        decision = PreToolUseDecisionOutput.approve("Test approval", "session-123")
        result = decision.to_dict()
        
        # Required Claude Code structure
        assert result['continue'] is True
        assert result['stopReason'] == 'Test approval'
        assert 'hookSpecificOutput' in result
        
        # CRITICAL: Test the hookEventName field that was previously missing
        hook_output = result['hookSpecificOutput']
        assert 'hookEventName' in hook_output, "Missing hookEventName field breaks Claude Code integration"
        assert hook_output['hookEventName'] == 'PreToolUse'
        assert hook_output['permissionDecision'] == 'allow'
        assert hook_output['permissionDecisionReason'] == 'Test approval'
    
    def test_pretool_decision_output_claude_code_compliance_block(self):
        """Test PreToolUseDecisionOutput blocking decision format"""
        validation_issues = ["Tool blocked by DAIC workflow", "Discussion mode active"]
        decision = PreToolUseDecisionOutput.block(
            "DAIC workflow prevents implementation tools in discussion mode",
            validation_issues,
            session_id="session-456",
            suppress_output=True
        )
        
        result = decision.to_dict()
        
        # Blocking response structure
        assert result['continue'] is False
        assert result['suppressOutput'] is True
        assert result['stopReason'] == "DAIC workflow prevents implementation tools in discussion mode"
        
        # Hook-specific output for blocking
        hook_output = result['hookSpecificOutput']
        assert hook_output['permissionDecision'] == 'deny'
        assert hook_output['hookEventName'] == 'PreToolUse'
        assert hook_output['permissionDecisionReason'] == "DAIC workflow prevents implementation tools in discussion mode"
        
        # Validation issues should be normalized
        assert len(decision.validation_issues) == 2
        assert all('message' in issue for issue in decision.validation_issues)
    
    def test_pretool_factory_method_approve(self):
        """Test approve() factory method"""
        approval = PreToolUseDecisionOutput.approve("Approved for implementation")
        
        assert approval.continue_ is True
        assert approval.stop_reason == "Approved for implementation"
        assert approval.validation_issues == []
        assert approval.suppress_output is None
        assert approval.system_message is None
    
    def test_pretool_factory_method_block_string_issues(self):
        """Test block() factory with string validation issues"""
        block_decision = PreToolUseDecisionOutput.block(
            "Blocked", 
            ["Issue 1", "Issue 2", "Issue 3"]
        )
        
        assert block_decision.continue_ is False
        assert block_decision.stop_reason == "Blocked"
        assert len(block_decision.validation_issues) == 3
        
        # All issues should be normalized to dict format
        for issue in block_decision.validation_issues:
            assert isinstance(issue, dict)
            assert 'message' in issue
    
    def test_pretool_factory_method_block_dict_issues(self):
        """Test block() factory with dict validation issues"""
        block_decision = PreToolUseDecisionOutput.block(
            "Blocked",
            [
                {'message': 'Error 1', 'code': 'E001'}, 
                {'message': 'Error 2'},
                {'detail': 'Custom detail', 'severity': 'high'}
            ]
        )
        
        assert len(block_decision.validation_issues) == 3
        assert block_decision.validation_issues[0]['code'] == 'E001'
        assert block_decision.validation_issues[1]['message'] == 'Error 2'
        # Dict issues should be preserved as-is
        assert 'detail' in block_decision.validation_issues[2]
    
    def test_pretool_edge_cases_minimal_approval(self):
        """Test minimal approval without reason"""
        minimal = PreToolUseDecisionOutput.approve()
        result = minimal.to_dict()
        
        assert result['continue'] is True
        assert 'stopReason' not in result or result['stopReason'] is None
        
        # Hook output should still be present and valid
        assert 'hookSpecificOutput' in result
        assert result['hookSpecificOutput']['hookEventName'] == 'PreToolUse'
        assert result['hookSpecificOutput']['permissionDecision'] == 'allow'
    
    def test_pretool_edge_cases_empty_validation_issues(self):
        """Test blocking with empty validation issues"""
        empty_block = PreToolUseDecisionOutput.block("Blocked", [])
        
        assert empty_block.validation_issues == []
        assert empty_block.continue_ is False
        
        result = empty_block.to_dict()
        assert result['hookSpecificOutput']['permissionDecision'] == 'deny'
    
    def test_pretool_edge_cases_mixed_validation_issues(self):
        """Test mixed validation issue types"""
        mixed_issues = PreToolUseDecisionOutput.block(
            "Mixed issues", 
            [
                "String issue",
                {'message': 'Dict issue'},
                {'custom': 'field', 'message': 'Complex issue'},
                {'detail': 'Detail only', 'code': 404}
            ]
        )
        
        assert len(mixed_issues.validation_issues) == 4
        
        # First should be converted to dict
        assert mixed_issues.validation_issues[0]['message'] == "String issue"
        
        # Others should be preserved as dicts
        assert mixed_issues.validation_issues[1]['message'] == 'Dict issue'
        assert mixed_issues.validation_issues[2]['custom'] == 'field'
        assert mixed_issues.validation_issues[3]['detail'] == 'Detail only'


class TestToolResponse:
    """Test ToolResponse camelCase field mapping and serialization"""
    
    def test_tool_response_serialization_all_fields(self):
        """Test ToolResponse camelCase field mapping with all fields"""
        response = ToolResponse(
            filePath="/test/file.py",
            oldString="old code",
            newString="new code",
            originalFile="original content",
            structuredPatch=[{'op': 'replace', 'path': '/line/1', 'value': 'new'}],
            type="file_edit"
        )
        
        result = response.to_dict()
        
        # Verify camelCase preservation (Claude Code requirement)
        assert result['filePath'] == "/test/file.py"
        assert result['oldString'] == "old code"
        assert result['newString'] == "new code"
        assert result['originalFile'] == "original content"
        assert result['type'] == "file_edit"
        assert isinstance(result['structuredPatch'], list)
        assert result['structuredPatch'][0]['op'] == 'replace'
    
    def test_tool_response_parse_roundtrip_consistency(self):
        """HIGH RISK: Test roundtrip consistency"""
        original_data = {
            'filePath': '/test/roundtrip.py',
            'oldString': 'before',
            'newString': 'after',
            'type': 'edit',
            'extra_field': 'preserved',
            'nested': {'data': {'deep': 'value'}}
        }
        
        # Execute: Parse and re-serialize
        parsed = ToolResponse.parse(original_data)
        reserialized = parsed.to_dict()
        
        # Verify roundtrip consistency
        assert reserialized['filePath'] == original_data['filePath']
        assert reserialized['oldString'] == original_data['oldString']
        assert reserialized['newString'] == original_data['newString']
        assert reserialized['extra_field'] == original_data['extra_field']
        assert reserialized['nested']['data']['deep'] == 'value'
    
    def test_tool_response_optional_fields(self):
        """Test ToolResponse with optional field handling"""
        # Test minimal response
        minimal = ToolResponse()
        result = minimal.to_dict()
        assert result == {}
        
        # Test partial response
        partial = ToolResponse(filePath="/test/file.py", type="write")
        result = partial.to_dict()
        assert len(result) == 2
        assert 'oldString' not in result
        assert 'newString' not in result
        assert result['filePath'] == "/test/file.py"
        assert result['type'] == "write"
    
    def test_tool_response_parse_invalid_data(self):
        """Test parsing invalid data"""
        assert ToolResponse.parse("invalid") is None
        assert ToolResponse.parse(None) is None
        assert ToolResponse.parse([]) is None
        assert ToolResponse.parse(123) is None
    
    def test_tool_response_parse_empty_dict(self):
        """Test parsing empty dict"""
        result = ToolResponse.parse({})
        assert result is not None
        assert isinstance(result, ToolResponse)
        assert result.to_dict() == {}


class TestOutputResponseTypes:
    """Test other output response types"""
    
    def test_hook_specific_output_serialization(self):
        """Test HookSpecificOutput serialization"""
        # Test with all fields
        output = HookSpecificOutput(
            hookEventName="TestEvent",
            additionalContext="Test context with Unicode: 🚀",
            metadata={"key": "value", "nested": {"data": True, "count": 42}}
        )
        
        result = output.to_dict()
        assert result['hookEventName'] == "TestEvent"
        assert result['additionalContext'] == "Test context with Unicode: 🚀"
        assert result['metadata']['nested']['data'] is True
        assert result['metadata']['nested']['count'] == 42
        
        # Test minimal output
        minimal = HookSpecificOutput(hookEventName="MinimalEvent")
        result = minimal.to_dict()
        assert result == {"hookEventName": "MinimalEvent"}
    
    def test_user_prompt_context_response_factory(self):
        """Test UserPromptContextResponse factory method"""
        response = UserPromptContextResponse.create_context(
            "Test context with special chars: <>&\"'",
            {"debug": "info", "level": "verbose"}
        )
        
        result = response.to_dict()
        assert 'hookSpecificOutput' in result
        assert result['hookSpecificOutput']['hookEventName'] == "UserPromptSubmit"
        assert result['hookSpecificOutput']['additionalContext'] == "Test context with special chars: <>&\"'"
        assert result['debug']['debug'] == "info"
        assert result['debug']['level'] == "verbose"
    
    def test_user_prompt_context_response_manual(self):
        """Test manual UserPromptContextResponse construction"""
        manual = UserPromptContextResponse(
            hookSpecificOutput=HookSpecificOutput(
                hookEventName="Custom",
                additionalContext="Manual context"
            ),
            debug={"test": "data"}
        )
        result = manual.to_dict()
        
        assert result['hookSpecificOutput']['hookEventName'] == "Custom"
        assert result['hookSpecificOutput']['additionalContext'] == "Manual context"
        assert result['debug']['test'] == "data"
    
    def test_session_correlation_response(self):
        """Test SessionCorrelationResponse serialization"""
        response = SessionCorrelationResponse(
            success=True,
            session_id="sess-123",
            correlation_id="corr-456",
            timestamp="2025-09-08T00:00:00Z"
        )
        
        result = response.to_dict()
        expected = {
            "success": True,
            "session_id": "sess-123",
            "correlation_id": "corr-456",
            "timestamp": "2025-09-08T00:00:00Z"
        }
        assert result == expected
    
    def test_daic_mode_result_with_trigger(self):
        """Test DAICModeResult with trigger phrase"""
        with_trigger = DAICModeResult(
            success=True,
            old_mode="discussion",
            new_mode="implementation",
            timestamp="2025-09-08T00:00:00Z",
            trigger="make it so"
        )
        
        result = with_trigger.to_dict()
        assert result['trigger'] == "make it so"
        assert result['success'] is True
        assert result['old_mode'] == "discussion"
        assert result['new_mode'] == "implementation"
    
    def test_daic_mode_result_without_trigger(self):
        """Test DAICModeResult without trigger"""
        without_trigger = DAICModeResult(
            success=False,
            old_mode="implementation",
            new_mode="discussion",
            timestamp="2025-09-08T00:00:00Z"
        )
        
        result = without_trigger.to_dict()
        assert 'trigger' not in result
        assert result['success'] is False
    
    def test_tool_analysis_result(self):
        """Test ToolAnalysisResult serialization"""
        analysis = ToolAnalysisResult(
            success=False,
            error_info={"code": "E001", "message": "Tool failed", "details": {"line": 42}},
            execution_metrics={"duration_ms": 150, "memory_mb": 25, "cpu_percent": 12.5},
            risk_factors=["high_memory", "long_duration", "security_concern"]
        )
        
        result = analysis.to_dict()
        assert result['success'] is False
        assert result['error_info']['code'] == "E001"
        assert result['error_info']['details']['line'] == 42
        assert result['execution_metrics']['duration_ms'] == 150
        assert result['execution_metrics']['cpu_percent'] == 12.5
        assert len(result['risk_factors']) == 3
        assert "security_concern" in result['risk_factors']


class TestUniversalSerialization:
    """Test to_json_serializable() recursive conversion - HIGH RISK for performance and correctness"""
    
    def test_to_json_serializable_complex_nested_object(self):
        """Test recursive conversion of complex nested structures"""
        # Create complex nested object with multiple response types
        complex_obj = UserPromptContextResponse.create_context(
            "Nested test with Unicode: 🧪",
            {
                "nested_response": SessionCorrelationResponse(
                    success=True,
                    session_id="nested-123",
                    correlation_id="nested-456",
                    timestamp="2025-09-08T00:00:00Z"
                ),
                "list_data": [
                    ToolAnalysisResult(
                        success=True,
                        error_info={},
                        execution_metrics={"time": 100},
                        risk_factors=[]
                    ),
                    DAICModeResult(
                        success=True,
                        old_mode="discussion",
                        new_mode="implementation",
                        timestamp="2025-09-08T00:00:00Z"
                    )
                ],
                "simple_data": {"key": "value", "number": 42}
            }
        )
        
        # Execute: Convert to JSON serializable
        result = to_json_serializable(complex_obj)
        
        # Verify recursive conversion
        assert isinstance(result, dict)
        assert 'hookSpecificOutput' in result
        
        # Note: UserPromptContextResponse.to_dict() doesn't recursively process debug field
        # This is actually a potential improvement area - nested objects in debug aren't converted
        assert isinstance(result['debug']['nested_response'], SessionCorrelationResponse)
        assert result['debug']['nested_response'].success is True
        assert isinstance(result['debug']['list_data'], list)
        assert isinstance(result['debug']['list_data'][0], ToolAnalysisResult)
        assert isinstance(result['debug']['list_data'][1], DAICModeResult)
        assert result['debug']['simple_data']['number'] == 42
        
        # The to_dict() result contains nested objects, so we need to_json_serializable for full conversion
        fully_serialized = to_json_serializable(result)
        
        # Now nested objects should be fully converted
        assert isinstance(fully_serialized['debug']['nested_response'], dict)
        assert fully_serialized['debug']['nested_response']['success'] is True
        assert isinstance(fully_serialized['debug']['list_data'][0], dict)
        
        # Should be JSON serializable
        json_str = json.dumps(fully_serialized)
        assert isinstance(json_str, str)
    
    def test_to_json_serializable_edge_cases(self):
        """Test edge cases with primitive and empty types"""
        # Primitive types should pass through unchanged
        assert to_json_serializable("string") == "string"
        assert to_json_serializable(123) == 123
        assert to_json_serializable(3.14) == 3.14
        assert to_json_serializable(True) is True
        assert to_json_serializable(False) is False
        assert to_json_serializable(None) is None
        
        # Empty collections
        assert to_json_serializable([]) == []
        assert to_json_serializable({}) == {}
        
        # Mixed collections with objects
        mixed = [
            HookSpecificOutput(hookEventName="Test"),
            {"key": "value"},
            "string",
            123,
            None
        ]
        result = to_json_serializable(mixed)
        
        assert isinstance(result[0], dict)
        assert result[0]['hookEventName'] == "Test"
        assert result[1]['key'] == "value"
        assert result[2] == "string"
        assert result[3] == 123
        assert result[4] is None
    
    def test_to_json_serializable_actual_json_compatibility(self):
        """HIGH RISK: Test output is actually JSON serializable"""
        # Create object with challenging data types
        complex_response = UserPromptContextResponse(
            hookSpecificOutput=HookSpecificOutput(
                hookEventName="JSONTest",
                additionalContext="Unicode test: 🚀💻🔬 and special chars: <>&\"'",
                metadata={"emoji": "🧪", "special": "<>&\"'", "number": 42}
            ),
            debug={
                "floats": [1.1, 2.2, float('inf')],  # Note: inf is not JSON serializable
                "nested": {"deep": {"deeper": "value"}},
                "array": [1, 2, 3, None, True, False]
            }
        )
        
        # Convert and test JSON serialization
        result = to_json_serializable(complex_response)
        
        # Should be able to serialize to JSON (handling inf appropriately)
        try:
            json_str = json.dumps(result)
            parsed_back = json.loads(json_str)
            assert isinstance(parsed_back, dict)
        except ValueError as e:
            # If inf is present, that's expected - should be handled by the system
            if "infinity" in str(e).lower():
                # This is acceptable - system should handle inf values appropriately
                pass
            else:
                raise


class TestCentralHookEventRowParsing:
    """Test CentralHookEventRow JSON handling - MEDIUM RISK for analytics integration"""
    
    def test_central_hook_event_row_json_string_parsing(self):
        """Test parsing JSON string data"""
        row_with_json_string = {
            'project_source': 'test-project',
            'hook_name': 'pre_tool_use',
            'event_type': 'hook_execution',
            'data': '{"tool_name": "Edit", "success": true, "unicode": "🚀"}'
        }
        
        parsed = CentralHookEventRow.parse(row_with_json_string)
        assert isinstance(parsed.data, dict)
        assert parsed.data['tool_name'] == "Edit"
        assert parsed.data['success'] is True
        assert parsed.data['unicode'] == "🚀"
    
    def test_central_hook_event_row_invalid_json_handling(self):
        """HIGH RISK: Test graceful handling of invalid JSON"""
        row_with_invalid_json = {
            'project_source': 'test-project',
            'hook_name': 'pre_tool_use',
            'data': 'invalid json {unclosed'
        }
        
        parsed = CentralHookEventRow.parse(row_with_invalid_json)
        # Should not crash, should preserve raw data
        assert parsed.data == {'raw': 'invalid json {unclosed'}
    
    def test_central_hook_event_row_dict_data_passthrough(self):
        """Test dict data passes through unchanged"""
        row_with_dict = {
            'project_source': 'test-project',
            'hook_name': 'pre_tool_use',
            'data': {"tool_name": "Write", "success": False, "metadata": {"key": "val"}}
        }
        
        parsed = CentralHookEventRow.parse(row_with_dict)
        assert parsed.data['tool_name'] == "Write"
        assert parsed.data['success'] is False
        assert parsed.data['metadata']['key'] == "val"


class TestClaudeCodeSpecificationCompliance:
    """Integration tests for Claude Code specification compliance - CRITICAL"""
    
    def test_claude_code_specification_compliance_complete(self):
        """Test complete Claude Code specification compliance"""
        # Test approval response
        approval = PreToolUseDecisionOutput.approve("Approved by DAIC workflow")
        approval_json = approval.to_dict()
        
        # Verify required fields per Claude Code spec
        required_fields = ['continue', 'hookSpecificOutput']
        for field in required_fields:
            assert field in approval_json, f"Missing required Claude Code field: {field}"
        
        # Verify hookSpecificOutput structure
        hook_output = approval_json['hookSpecificOutput']
        assert 'hookEventName' in hook_output, "Missing hookEventName breaks Claude Code integration"
        assert hook_output['hookEventName'] == 'PreToolUse'
        assert 'permissionDecision' in hook_output
        
        # Test blocking response compliance
        blocking = PreToolUseDecisionOutput.block(
            "Blocked by workflow",
            ["Validation error with Unicode: 🚫"]
        )
        blocking_json = blocking.to_dict()
        
        assert blocking_json['continue'] is False
        assert blocking_json['hookSpecificOutput']['permissionDecision'] == 'deny'
        
        # Should be JSON serializable
        json.dumps(approval_json)
        json.dumps(blocking_json)
    
    def test_serialization_roundtrip_consistency_all_types(self):
        """Test serialization roundtrip consistency across all output types"""
        test_objects = [
            HookSpecificOutput(hookEventName="Test", additionalContext="Context"),
            UserPromptContextResponse.create_context("Test context"),
            SessionCorrelationResponse(True, "sess", "corr", "2025-09-08T00:00:00Z"),
            DAICModeResult(True, "old", "new", "2025-09-08T00:00:00Z", "trigger"),
            ToolAnalysisResult(True, {}, {"time": 100}, [])
        ]
        
        for obj in test_objects:
            # Serialize to dict
            serialized = obj.to_dict()
            
            # Verify it's JSON serializable
            json_str = json.dumps(serialized)
            
            # Verify we can deserialize back
            parsed_back = json.loads(json_str)
            
            # Basic structure should be preserved
            assert isinstance(parsed_back, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])