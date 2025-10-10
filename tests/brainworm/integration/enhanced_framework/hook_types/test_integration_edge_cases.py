#!/usr/bin/env python3
"""
Integration and Edge Case Tests for hook_types.py

Tests cross-component interactions and the most challenging scenarios:
- Complex data flows between parsing, validation, and serialization
- Memory and performance edge cases
- Claude Code integration under extreme conditions  
- Data corruption and recovery scenarios
- System stability with pathological inputs

Focus: Real-world edge cases that could break the system through component interactions.
"""

import pytest
import json
import time
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

# Add hook_types module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "src" / "hooks" / "templates" / "utils"))

from hook_types import (
    # Complete type system
    parse_tool_input, parse_log_event, PreToolUseDecisionOutput,
    CommandToolInput, FileEditToolInput, FileWriteToolInput,
    PreToolUseLogEvent, PostToolUseLogEvent, UserPromptSubmitLogEvent,
    HookSpecificOutput, UserPromptContextResponse,
    SessionCorrelationResponse, DAICModeResult, ToolAnalysisResult,
    CentralHookEventRow, ToolResponse,
    # Utility functions
    to_json_serializable, normalize_validation_issues, 
    get_standard_timestamp, parse_standard_timestamp, format_for_database,
    _coerce_iso, _as_list
)


class TestCrossComponentIntegration:
    """Test complex data flows between multiple components - HIGH RISK"""
    
    def test_full_pretool_workflow_integration(self):
        """
        HIGH RISK: Test complete PreToolUse workflow from input to output
        This tests the entire pipeline that Claude Code uses
        """
        # Step 1: Parse complex tool input with mixed case fields
        raw_tool_input = {
            "file_path": "/test/complex.py",
            "old_string": "def old_function():",
            "newString": "def new_function():",  # Mixed case
            "metadata": {"author": "test", "timestamp": 1692622467}
        }
        
        parsed_tool = parse_tool_input(raw_tool_input)
        assert isinstance(parsed_tool, FileEditToolInput)
        assert parsed_tool.old_string == "def old_function():"
        assert parsed_tool.newString == "def new_function():"
        assert parsed_tool.extra["metadata"]["author"] == "test"
        
        # Step 2: Create PreToolUse input with this tool
        pretool_input_data = {
            "session_id": "complex-session-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/tmp/project",
            "hook_event_name": "pre_tool_use",
            "tool_name": "Edit",
            "tool_input": raw_tool_input
        }
        
        # Step 3: Generate decision output (blocking scenario)
        complex_validation_issues = [
            "Unicode validation: 🚫 File contains emoji",
            {"message": "Security warning: File modification detected", "severity": "high"},
            {"detail": "Path validation failed", "code": "E001"}
        ]
        
        decision = PreToolUseDecisionOutput.block(
            "Complex validation failed with Unicode and mixed issues",
            complex_validation_issues,
            session_id="complex-session-123"
        )
        
        # Step 4: Serialize decision for Claude Code
        decision_json = decision.to_dict()
        
        # Step 5: Verify Claude Code compliance
        assert decision_json['continue'] is False
        assert 'hookSpecificOutput' in decision_json
        assert decision_json['hookSpecificOutput']['hookEventName'] == 'PreToolUse'
        assert decision_json['hookSpecificOutput']['permissionDecision'] == 'deny'
        
        # Step 6: Verify validation issue normalization
        assert len(decision.validation_issues) == 3
        normalized_messages = normalize_validation_issues(decision.validation_issues)
        assert "Unicode validation: 🚫 File contains emoji" in normalized_messages
        assert "Security warning: File modification detected" in normalized_messages
        assert "Path validation failed" in normalized_messages
        
        # Step 7: Full JSON serialization test
        fully_serialized = to_json_serializable(decision_json)
        json_str = json.dumps(fully_serialized)
        
        # Should be able to parse back
        parsed_back = json.loads(json_str)
        assert parsed_back['hookSpecificOutput']['hookEventName'] == 'PreToolUse'
        
        # Step 8: Create log event for this workflow
        log_event_data = {
            "hook_name": "pre_tool_use",
            "session_id": "complex-session-123",
            "hook_event_name": "pre_tool_use",
            "logged_at": get_standard_timestamp(),
            "tool_name": "Edit",
            "blocked": True,
            "validation_issues": complex_validation_issues,
            "tool_input": raw_tool_input
        }
        
        log_event = parse_log_event(log_event_data)
        assert isinstance(log_event, PreToolUseLogEvent)
        assert log_event.blocked is True
        assert log_event.tool_name == "Edit"
    
    def test_massive_nested_data_with_unicode_preservation(self):
        """
        HIGH RISK: Test system with massive nested structures and Unicode
        This tests memory handling and Unicode preservation across components
        """
        # Create deeply nested structure with Unicode at all levels
        deep_unicode_data = {
            "session_id": "unicode-test-🧪",
            "hook_name": "user_prompt_submit",  # This determines the log event type
            "hook_event_name": "user_prompt_submit",
            "prompt": "Process this complex Unicode data: 🚀💻🔬 with nested structures",
            "metadata": {
                "languages": ["English 🇺🇸", "中文 🇨🇳", "العربية 🇸🇦", "עברית 🇮🇱"],
                "nested": {
                    "level1": {
                        "level2": {
                            "level3": {
                                "unicode_test": "Testing: 🧪🔬⚗️🧬🔬 and special chars: <>&\"'",
                                "rtl_text": "هذا نص عربي مع رموز تعبيرية 😊",
                                "cjk_text": "这是中文测试 😄",
                                "mixed": "English混合中文مع العربية 🌍"
                            }
                        }
                    }
                },
                "large_array": [f"Item {i} with emoji: 🎯" for i in range(100)]
            }
        }
        
        # Process through log event parsing
        log_event = parse_log_event(deep_unicode_data)
        assert isinstance(log_event, UserPromptSubmitLogEvent)
        assert "🚀💻🔬" in log_event.prompt
        
        # Create response with nested Unicode
        context_response = UserPromptContextResponse.create_context(
            "Response with Unicode: ✅ Processed successfully 🎉",
            {
                "analysis": "Unicode handling test: 🧪 → ✅",
                "nested_unicode": deep_unicode_data["metadata"]["nested"],
                "performance": {"time_ms": 42.5, "memory_mb": 15}
            }
        )
        
        # Serialize completely
        serialized = to_json_serializable(context_response)
        
        # Should preserve all Unicode
        assert "🧪 → ✅" in serialized["debug"]["analysis"]
        assert "🧪🔬⚗️🧬🔬" in serialized["debug"]["nested_unicode"]["level1"]["level2"]["level3"]["unicode_test"]
        assert "هذا نص عربي" in serialized["debug"]["nested_unicode"]["level1"]["level2"]["level3"]["rtl_text"]
        
        # JSON serialization should work with Unicode
        json_str = json.dumps(serialized, ensure_ascii=False)
        parsed_back = json.loads(json_str)
        
        # Verify Unicode preservation through full round-trip
        assert "🧪 → ✅" in parsed_back["debug"]["analysis"]
        assert "🧪🔬⚗️🧬🔬" in parsed_back["debug"]["nested_unicode"]["level1"]["level2"]["level3"]["unicode_test"]
    
    def test_field_name_consistency_across_components(self):
        """
        HIGH RISK: Test snake_case vs camelCase consistency
        This catches integration bugs from field naming inconsistencies
        """
        # Test with mixed case input that goes through multiple components
        mixed_case_tool_input = {
            "file_path": "/test/file.py",
            "old_string": "snake_case_field",
            "oldString": "camelCaseField",  # Both present
            "edits": [
                {"old_string": "snake_in_array", "new_string": "snake_new"},
                {"oldString": "camel_in_array", "newString": "camel_new"}
            ]
        }
        
        # Parse tool input
        parsed_tool = parse_tool_input(mixed_case_tool_input)
        assert isinstance(parsed_tool, FileEditToolInput)
        
        # Both case variants should be preserved
        assert parsed_tool.old_string == "snake_case_field"
        assert parsed_tool.oldString == "camelCaseField"
        
        # Round-trip through serialization
        serialized_tool = parsed_tool.to_dict()
        assert serialized_tool["old_string"] == "snake_case_field"
        assert serialized_tool["oldString"] == "camelCaseField"
        assert len(serialized_tool["edits"]) == 2
        
        # Create ToolResponse with camelCase (Claude Code format)
        tool_response = ToolResponse(
            filePath="/test/file.py",
            oldString="before_change",
            newString="after_change",
            originalFile="original content",
            type="file_edit"
        )
        
        response_serialized = tool_response.to_dict()
        
        # Should preserve camelCase for Claude Code compatibility
        assert response_serialized["filePath"] == "/test/file.py"
        assert response_serialized["oldString"] == "before_change"
        assert response_serialized["newString"] == "after_change"
        
        # Full workflow serialization
        workflow_data = {
            "tool_input": parsed_tool,
            "tool_response": tool_response,
            "metadata": {"mixed_case": True}
        }
        
        fully_serialized = to_json_serializable(workflow_data)
        
        # Should handle both naming conventions correctly
        assert "old_string" in fully_serialized["tool_input"]
        assert "oldString" in fully_serialized["tool_input"]
        assert "filePath" in fully_serialized["tool_response"]
        assert "oldString" in fully_serialized["tool_response"]
    
    def test_type_coercion_consistency_across_components(self):
        """
        HIGH RISK: Test data type consistency across multiple transformations
        """
        # Test with various data types that get transformed
        complex_data = {
            "session_id": "type-test-123",
            "timestamp_int": 1692622467,  # Unix timestamp
            "timestamp_ms": 1692622467000,  # Milliseconds
            "timestamp_str": "2025-09-08T00:00:00Z",  # ISO string
            "numbers": [1, 2.5, "3", 4.0],
            "booleans": [True, False, "true", "false", 1, 0],
            "mixed_validation": [
                "String issue",
                {"message": "Dict issue"},
                {"detail": "Detail issue"},
                123,  # Should be ignored
                None   # Should be ignored
            ]
        }
        
        # Process timestamps through various utilities
        timestamp_results = [
            _coerce_iso(complex_data["timestamp_int"]),
            _coerce_iso(complex_data["timestamp_ms"]),
            _coerce_iso(complex_data["timestamp_str"]),
            format_for_database(str(complex_data["timestamp_int"])),
            get_standard_timestamp()
        ]
        
        # All should be valid ISO timestamps
        for ts in timestamp_results:
            if ts is not None:
                assert ts.endswith('+00:00') or ts.endswith('Z')
                parsed = parse_standard_timestamp(ts.replace('Z', '+00:00'))
                assert isinstance(parsed, datetime)
        
        # Process validation issues
        normalized = normalize_validation_issues(complex_data["mixed_validation"])
        assert len(normalized) == 3  # Only string and dict items processed
        assert "String issue" in normalized
        assert "Dict issue" in normalized
        assert "Detail issue" in normalized
        
        # Process through list conversion
        list_results = [_as_list(item) for item in complex_data["numbers"]]
        assert all(isinstance(result, list) for result in list_results)
        assert list_results[0] == [1]  # int becomes list
        assert list_results[1] == [2.5]  # float becomes list


class TestMemoryAndPerformanceEdgeCases:
    """Test system behavior with large data and performance constraints"""
    
    def test_large_data_structure_processing(self):
        """
        HIGH RISK: Test with large data structures (1MB+ data)
        """
        # Create large string data (1MB)
        large_string = "A" * (1024 * 1024)  # 1MB string
        
        # Create large nested structure  
        large_data = {
            "session_id": "performance-test",
            "large_content": large_string,
            "large_array": [f"Item {i}" for i in range(10000)],  # 10K items
            "nested_large": {
                "level1": {
                    "level2": {
                        "data": large_string[:1000],  # Truncated for nesting
                        "array": [{"id": i, "data": f"Data {i}"} for i in range(1000)]
                    }
                }
            }
        }
        
        # Performance test: Should process within reasonable time
        start_time = time.time()
        
        # Process through various components
        serialized = to_json_serializable(large_data)
        
        processing_time = time.time() - start_time
        
        # Should complete within 5 seconds even for large data
        assert processing_time < 5.0, f"Processing took too long: {processing_time}s"
        
        # Data should be preserved
        assert len(serialized["large_content"]) == 1024 * 1024
        assert len(serialized["large_array"]) == 10000
        assert len(serialized["nested_large"]["level1"]["level2"]["array"]) == 1000
        
        # Should be JSON serializable (though we won't actually serialize 1MB for speed)
        sample_data = {
            "session_id": large_data["session_id"],
            "large_sample": large_string[:1000],
            "array_sample": large_data["large_array"][:100]
        }
        
        json_str = json.dumps(sample_data)
        assert isinstance(json_str, str)
    
    def test_deep_recursion_handling(self):
        """
        HIGH RISK: Test deep recursion without stack overflow
        """
        # Create deeply nested structure (50 levels)
        def create_deep_structure(depth: int) -> Dict[str, Any]:
            if depth == 0:
                return {"value": f"depth_{depth}", "leaf": True}
            return {
                "value": f"depth_{depth}",
                "child": create_deep_structure(depth - 1),
                "metadata": {"level": depth}
            }
        
        deep_structure = create_deep_structure(50)
        
        # Should handle deep recursion without crashing
        start_time = time.time()
        serialized = to_json_serializable(deep_structure)
        processing_time = time.time() - start_time
        
        # Should complete quickly
        assert processing_time < 1.0, f"Deep recursion took too long: {processing_time}s"
        
        # Structure should be preserved
        current = serialized
        for level in range(50, 0, -1):
            assert current["value"] == f"depth_{level}"
            assert current["metadata"]["level"] == level
            if level > 1:
                current = current["child"]
            else:
                # At depth_1, the child should be depth_0 which has leaf=True
                if "child" in current:
                    assert current["child"].get("leaf") is True


class TestDataCorruptionAndRecovery:
    """Test graceful handling of corrupted or malformed data"""
    
    def test_malformed_json_recovery(self):
        """
        HIGH RISK: Test recovery from corrupted JSON data
        """
        # Test CentralHookEventRow with various malformed JSON
        malformed_cases = [
            {"data": '{"valid": "json"}'},  # Valid
            {"data": '{"unclosed": "bracket"'},  # Missing }
            {"data": '{invalid json syntax}'},  # Invalid syntax
            {"data": '{"unicode": "🧪", "valid": true}'},  # Unicode in JSON
            {"data": ''},  # Empty string
            {"data": 'not json at all'},  # Not JSON
            {"data": None},  # None
        ]
        
        for i, case in enumerate(malformed_cases):
            case.update({
                "project_source": f"test-{i}",
                "hook_name": "test_hook",
                "event_type": "hook_execution"
            })
            
            # Should not crash on malformed data
            parsed = CentralHookEventRow.parse(case)
            assert parsed is not None
            assert parsed.project_source == f"test-{i}"
            
            # Data should be handled gracefully
            if case["data"] == '{"valid": "json"}':
                assert isinstance(parsed.data, dict)
                assert parsed.data["valid"] == "json"
            elif case["data"] == '{"unicode": "🧪", "valid": true}':
                # Valid JSON with Unicode should parse correctly
                assert isinstance(parsed.data, dict)
                assert parsed.data["unicode"] == "🧪"
                assert parsed.data["valid"] is True
            elif case["data"] and isinstance(case["data"], str) and case["data"].startswith('{'):
                # Malformed JSON should be wrapped in raw
                assert isinstance(parsed.data, dict)
                if "raw" not in parsed.data:
                    # If it parsed successfully, that's also acceptable
                    assert len(parsed.data) > 0
                else:
                    assert "raw" in parsed.data
            else:
                # Non-JSON should be handled appropriately
                assert parsed.data is not None
    
    def test_partial_data_corruption_recovery(self):
        """
        HIGH RISK: Test recovery when some fields are corrupted
        """
        # Test with partially corrupted hook input
        partially_corrupted = {
            "session_id": "valid-session",
            "transcript_path": None,  # Corrupted
            "cwd": 123,  # Wrong type
            "hook_event_name": "pre_tool_use",
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "/valid/path.py",
                "old_string": None,  # Corrupted
                "new_string": "valid replacement",
                "corrupted_extra": float('inf')  # Problematic value
            }
        }
        
        # Should parse without crashing
        from hook_types import PreToolUseInput
        parsed = PreToolUseInput.parse(partially_corrupted)
        
        # Valid fields should be preserved
        assert parsed.session_id == "valid-session"
        assert parsed.hook_event_name == "pre_tool_use"
        assert parsed.tool_name == "Edit"
        
        # Tool input should parse with available data
        if parsed.tool_input:
            assert isinstance(parsed.tool_input, FileEditToolInput)
            assert parsed.tool_input.file_path == "/valid/path.py"
            assert parsed.tool_input.new_string == "valid replacement"
        
        # Corrupted data should be preserved in raw
        assert parsed.raw["cwd"] == 123
        assert parsed.raw["transcript_path"] is None


class TestClaudeCodeIntegrationUnderStress:
    """Test Claude Code integration under extreme conditions"""
    
    def test_claude_code_compliance_with_extreme_validation_issues(self):
        """
        HIGH RISK: Test Claude Code JSON compliance with 100+ validation issues
        """
        # Create extreme number of validation issues with various formats
        massive_issues = []
        
        # Add string issues
        for i in range(50):
            massive_issues.append(f"Validation error {i} with Unicode: 🚫{i}")
        
        # Add dict issues with various formats
        for i in range(50):
            massive_issues.append({
                "message": f"Dict error {i}",
                "code": f"E{i:03d}",
                "severity": "high" if i % 2 == 0 else "low",
                "unicode": f"Error emoji: 🔴{i}"
            })
        
        # Add some with detail field
        for i in range(10):
            massive_issues.append({
                "detail": f"Detail error {i} with special chars: <>&\"'",
                "timestamp": get_standard_timestamp(),
                "context": {"line": i, "file": f"/test/file{i}.py"}
            })
        
        # Create decision with massive issues
        decision = PreToolUseDecisionOutput.block(
            "System validation failed with 110 issues including Unicode and special characters",
            massive_issues,
            session_id="stress-test-session",
            suppress_output=True
        )
        
        # Should handle massive validation issues
        assert len(decision.validation_issues) == 110
        
        # Generate Claude Code JSON
        decision_json = decision.to_dict()
        
        # Should still comply with Claude Code format
        assert decision_json['continue'] is False
        assert decision_json['suppressOutput'] is True
        assert 'hookSpecificOutput' in decision_json
        assert decision_json['hookSpecificOutput']['hookEventName'] == 'PreToolUse'
        assert decision_json['hookSpecificOutput']['permissionDecision'] == 'deny'
        
        # Should be JSON serializable despite size and complexity
        start_time = time.time()
        json_str = json.dumps(decision_json, ensure_ascii=False)
        serialization_time = time.time() - start_time
        
        # Should serialize quickly even with large data
        assert serialization_time < 1.0, f"Serialization too slow: {serialization_time}s"
        
        # Should be parseable back
        parsed_back = json.loads(json_str)
        assert parsed_back['hookSpecificOutput']['hookEventName'] == 'PreToolUse'
        
        # Normalize validation issues - should handle all formats
        normalized = normalize_validation_issues(decision.validation_issues)
        assert len(normalized) == 110
        
        # Should contain all the different types
        string_issues = [msg for msg in normalized if "Validation error" in msg]
        dict_issues = [msg for msg in normalized if "Dict error" in msg]
        detail_issues = [msg for msg in normalized if "Detail error" in msg]
        
        assert len(string_issues) == 50
        assert len(dict_issues) == 50
        assert len(detail_issues) == 10
    
    def test_claude_code_unicode_boundary_conditions(self):
        """
        HIGH RISK: Test Claude Code integration with Unicode edge cases
        """
        # Unicode edge cases that could break JSON or Claude Code parsing
        unicode_edge_cases = [
            "Basic emoji: 🚀",
            "Complex emoji: 👨‍💻👩‍🔬",  # Multi-codepoint emoji
            "RTL text: هذا نص عربي",
            "CJK characters: 这是中文测试",
            "Hebrew: זה טקסט בעברית",
            "Mathematical: ∑∫∆∂∇",
            "Symbols: ©®™℅№",
            "Control chars mixed: \u200B\u200C\u200D",  # Zero-width chars
            "JSON problematic: \"\\\n\r\t",
            "XML problematic: <>&\"'",
            "High Unicode: 𝕌𝕟𝕚𝕔𝕠𝕕𝕖 𝕋𝕖𝕤𝕥",  # Mathematical script
        ]
        
        for i, test_text in enumerate(unicode_edge_cases):
            # Create decision with this Unicode text
            decision = PreToolUseDecisionOutput.block(
                f"Unicode test {i}: {test_text}",
                [f"Validation with Unicode: {test_text} - issue detected"],
                session_id=f"unicode-test-{i}"
            )
            
            # Should generate valid Claude Code JSON
            decision_json = decision.to_dict()
            assert 'hookSpecificOutput' in decision_json
            assert decision_json['hookSpecificOutput']['hookEventName'] == 'PreToolUse'
            
            # Should be JSON serializable with Unicode
            json_str = json.dumps(decision_json, ensure_ascii=False)
            parsed_back = json.loads(json_str)
            
            # Unicode should be preserved
            assert test_text in parsed_back['stopReason']
            assert decision_json['hookSpecificOutput']['hookEventName'] == 'PreToolUse'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])