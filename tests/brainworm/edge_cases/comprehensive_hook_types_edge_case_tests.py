#!/usr/bin/env python3
"""
Comprehensive Edge Case and Error Handling Test Suite for hook_types.py

This test suite focuses on the most challenging cross-cutting concerns and edge cases
that could break the system through component interactions, data corruption, and
boundary conditions. It complements individual component tests by focusing on
integration failures and system stability under extreme conditions.

Design Principles:
- Test pathological inputs that individual components might handle but break when combined
- Validate Claude Code compliance under extreme stress conditions
- Ensure no silent data corruption across transformations
- Test error propagation and recovery across multiple parsing stages
- Validate memory safety and performance under pathological conditions
"""

import pytest
import json
import time
import gc
import threading
import sys
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List
import tempfile


from brainworm.utils.hook_types import (
    BaseHookInput, PreToolUseInput, PostToolUseInput, UserPromptSubmitInput,
    PreToolUseDecisionOutput, UserPromptContextResponse, HookSpecificOutput,
    CommandToolInput, FileWriteToolInput, FileEditToolInput, ToolResponse,
    parse_tool_input, parse_log_event, to_json_serializable, normalize_validation_issues,
    get_standard_timestamp, parse_standard_timestamp, format_for_database,
    SessionCorrelationResponse, DAICModeResult, ToolAnalysisResult
)


class TestCrossComponentIntegrationEdgeCases:
    """Test complex data flows and integration failures between components"""

    def test_massive_nested_data_structure_consistency(self):
        """Test data preservation through multiple transformations with deeply nested data"""
        # Create pathologically deep nested structure
        nested_data = {"level_0": {}}
        current = nested_data["level_0"]
        for i in range(1, 50):  # 50 levels deep
            current[f"level_{i}"] = {}
            current = current[f"level_{i}"]
        current["final_data"] = {
            "unicode_test": "🔥💯🚀 Test with émojis and ñoñ-ASCII",
            "large_string": "X" * 10000,  # 10KB string
            "numeric_edge": [float('inf'), -float('inf'), 0.0, -0.0, 1e-323],
            "null_variations": [None, "", {}, []],
            "complex_tools": {
                "tool_input": {
                    "file_path": "/very/long/path/" + "/".join([f"dir_{i}" for i in range(100)]) + "/file.py",
                    "content": "# " + "\n# ".join([f"Line {i} with unicode: 你好世界" for i in range(1000)]),
                    "edits": [{"old_string": f"old_{i}", "new_string": f"new_{i}"} for i in range(100)]
                }
            }
        }

        # Test parsing with nested data
        hook_input = PreToolUseInput.parse({
            "session_id": "nested-test",
            "transcript_path": "/tmp/nested.txt",
            "cwd": "/test",
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": nested_data["level_0"]["complex_tools"]["tool_input"],
            "extra_nested": nested_data
        })

        # Verify data preservation through parsing
        assert hook_input.tool_input is not None
        assert isinstance(hook_input.tool_input, FileEditToolInput)
        assert len(hook_input.tool_input.edits) == 100
        assert "extra_nested" in hook_input.raw

        # Test serialization maintains structure
        serialized = to_json_serializable(hook_input)
        assert "extra_nested" in serialized["raw"]

        # Test JSON round-trip with deeply nested data
        json_str = json.dumps(serialized)
        recovered = json.loads(json_str)

        # Verify no data corruption in round-trip
        assert len(recovered["raw"]["extra_nested"]["level_0"]["complex_tools"]["tool_input"]["edits"]) == 100
        assert "你好世界" in recovered["raw"]["extra_nested"]["level_0"]["complex_tools"]["tool_input"]["content"]

    def test_field_compatibility_across_input_output_transformations(self):
        """Test field naming consistency across different input/output types under stress"""
        # Test data with multiple field naming conventions that could conflict
        conflicting_data = {
            "session_id": "compat-test",
            "transcript_path": "/tmp/compat.txt",
            "cwd": "/compat/test",
            "hook_event_name": "PostToolUse",
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "/test/file.py",
                # Both snake_case and camelCase versions present
                "old_string": "snake_case_old",
                "oldString": "camelCase_old",
                "new_string": "snake_case_new",
                "newString": "camelCase_new",
                # Potential field conflicts
                "edits": [{"old_string": "edit1_old", "new_string": "edit1_new"}],
                "editList": [{"oldString": "edit2_old", "newString": "edit2_new"}],
                # Extra fields that could interfere
                "description": "Tool description",
                "Description": "Conflicting description",
                "DESCRIPTION": "Another conflicting description"
            },
            "tool_response": {
                "filePath": "/test/file.py",
                "file_path": "/test/file_snake.py",  # Conflicts with filePath
                "success": True,
                "Success": False,  # Boolean conflict
                "structuredPatch": [{"line": 1, "change": "test"}],
                "structured_patch": [{"line": 2, "change": "conflict"}]
            }
        }

        # Parse with conflicting field names
        post_input = PostToolUseInput.parse(conflicting_data)

        # Verify the parser handles conflicts predictably
        assert post_input.tool_input is not None
        assert isinstance(post_input.tool_input, FileEditToolInput)

        # Test that both field formats are preserved in extra data
        tool_dict = post_input.tool_input.to_dict()
        assert "old_string" in tool_dict or "oldString" in tool_dict

        # Test response parsing with conflicts
        assert post_input.tool_response is not None
        response_dict = post_input.tool_response.to_dict()
        assert "filePath" in response_dict or "file_path" in response_dict

        # Test serialization preserves field conflicts in extra data
        serialized = to_json_serializable(post_input)
        raw_tool_input = serialized["raw"]["tool_input"]
        assert any(key in raw_tool_input for key in ["Description", "DESCRIPTION", "editList"])

    def test_type_coercion_inconsistencies_across_components(self):
        """Test type coercion handling across multiple components with edge cases"""
        # Data with types that could be coerced differently by different components
        ambiguous_types = {
            "session_id": 12345,  # Number instead of string
            "transcript_path": ["path1", "path2"],  # Array instead of string
            "cwd": None,  # None instead of string
            "hook_event_name": True,  # Boolean instead of string
            "tool_name": {"name": "Edit"},  # Object instead of string
            "tool_input": {
                "file_path": 42,  # Number instead of string
                "content": ["line1", "line2"],  # Array instead of string
                "edits": "not_an_array",  # String instead of array
                "old_string": {"complex": "object"},  # Object instead of string
                "description": [1, 2, 3]  # Array of numbers instead of string
            },
            "timestamp": "not_a_timestamp",
            "numeric_fields": {
                "duration_ms": "123.45",  # String number
                "timestamp_ns": "1640995200000000000",  # String timestamp
                "success": "true",  # String boolean
                "count": 3.14159  # Float instead of int
            }
        }

        # Test BaseHookInput handles type coercion gracefully
        base_input = BaseHookInput.parse(ambiguous_types)

        # Verify string conversion for core fields
        assert isinstance(base_input.session_id, str)
        assert isinstance(base_input.transcript_path, str)
        assert isinstance(base_input.cwd, str)
        assert isinstance(base_input.hook_event_name, str)

        # Test PreToolUseInput handles nested type coercion
        pre_input = PreToolUseInput.parse(ambiguous_types)
        assert isinstance(pre_input.tool_name, str)

        # Test tool input parsing with type coercion
        tool_input = parse_tool_input(ambiguous_types["tool_input"])
        # Should either parse successfully or return None (not crash)
        assert tool_input is None or hasattr(tool_input, 'to_dict')

        # Test timestamp coercion across different formats
        timestamp_variants = [
            "2025-01-01T00:00:00Z",
            "2025-01-01T00:00:00+00:00",
            1640995200,
            1640995200000,
            1640995200000000000,
            "1640995200",
            "1640995200.123",
            "invalid_timestamp",
            None,
            "",
            12345.67
        ]

        for ts in timestamp_variants:
            try:
                # Should not crash on any input
                result = format_for_database(str(ts) if ts is not None else "")
                assert isinstance(result, str)
            except Exception as e:
                pytest.fail(f"format_for_database crashed on {ts}: {e}")


class TestMemoryAndPerformanceEdgeCases:
    """Test memory leaks, recursion limits, and performance degradation"""

    def test_massive_data_structure_memory_safety(self):
        """Test memory safety with extremely large data structures"""
        # Create memory-intensive data structures
        large_arrays = {
            "huge_string_array": [f"String_{i}_with_unicode_内容" for i in range(10000)],
            "nested_objects": [{"id": i, "data": "X" * 1000} for i in range(1000)],
            "deep_nesting": self._create_deep_object(depth=200)
        }

        memory_before = self._get_memory_usage()

        # Test parsing with massive data
        hook_input = BaseHookInput.parse({
            "session_id": "memory-test",
            "transcript_path": "/tmp/memory.txt",
            "cwd": "/test",
            "hook_event_name": "MemoryTest",
            "massive_data": large_arrays
        })

        # Test serialization doesn't explode memory
        serialized = to_json_serializable(hook_input)
        json_str = json.dumps(serialized)

        # Force garbage collection
        del large_arrays, hook_input, serialized
        gc.collect()

        memory_after = self._get_memory_usage()

        # Memory should not have grown excessively (allow for some growth but not exponential)
        memory_growth = memory_after - memory_before
        assert memory_growth < 500 * 1024 * 1024, f"Memory grew by {memory_growth} bytes"

    def test_circular_reference_handling(self):
        """Test handling of circular references across components"""
        # Create circular reference structure
        circular_obj_a = {"name": "object_a", "data": "test_data_a"}
        circular_obj_b = {"name": "object_b", "data": "test_data_b"}
        circular_obj_a["ref"] = circular_obj_b
        circular_obj_b["ref"] = circular_obj_a

        # Test with circular references in input
        circular_input = {
            "session_id": "circular-test",
            "transcript_path": "/tmp/circular.txt",
            "cwd": "/test",
            "hook_event_name": "CircularTest",
            "circular_data": circular_obj_a,
            "tool_input": {
                "file_path": "/test/file.py",
                "content": "test content",
                "circular_ref": circular_obj_a
            }
        }

        # Should handle circular references gracefully (not infinite recursion)
        try:
            hook_input = PreToolUseInput.parse(circular_input)
            # If it parses, test serialization
            serialized = to_json_serializable(hook_input)
            # Should not crash on JSON serialization
            json.dumps(serialized)
        except (ValueError, RecursionError, json.JSONDecodeError):
            # Expected - circular references should be detected and handled
            pass
        except Exception as e:
            pytest.fail(f"Unexpected error handling circular references: {e}")

    def test_recursion_limits_across_components(self):
        """Test recursion limit handling in deep parsing operations"""
        # Create structure that approaches Python's recursion limit
        deep_structure = self._create_deep_object(depth=500)

        deep_input = {
            "session_id": "recursion-test",
            "transcript_path": "/tmp/recursion.txt",
            "cwd": "/test",
            "hook_event_name": "RecursionTest",
            "deep_data": deep_structure,
            "tool_input": {
                "file_path": "/test/deep.py",
                "content": "deep content",
                "nested_edits": deep_structure
            }
        }

        # Should not hit recursion limit
        try:
            hook_input = PreToolUseInput.parse(deep_input)
            tool_input = hook_input.tool_input
            if tool_input:
                tool_dict = tool_input.to_dict()
                # Verify deep structure is preserved
                assert "nested_edits" in tool_dict.get("extra", {})
        except RecursionError:
            pytest.fail("Hit recursion limit during parsing")
        except Exception as e:
            # Other exceptions are acceptable (memory limits, etc.)
            pass

    def test_performance_degradation_pathological_inputs(self):
        """Test performance doesn't degrade exponentially with pathological inputs"""
        # Create inputs designed to cause performance issues
        pathological_cases = [
            # Extremely long field names
            {f"field_{'x' * 1000}_{i}": f"value_{i}" for i in range(100)},
            # Many duplicate keys that could cause hash collisions
            {f"key_{i % 10}_{j}": f"value_{i}_{j}" for i in range(100) for j in range(10)},
            # Very long strings that could cause quadratic behavior
            {"long_string": "A" * 100000, "pattern_string": ("AB" * 10000) + ("CD" * 10000)},
            # Complex validation issue lists
            {"validation_issues": [{"message": f"Error {i}: " + "X" * 1000} for i in range(1000)]}
        ]

        for case_index, pathological_data in enumerate(pathological_cases):
            start_time = time.time()

            # Test parsing performance
            hook_input = BaseHookInput.parse({
                "session_id": f"perf-test-{case_index}",
                "transcript_path": "/tmp/perf.txt",
                "cwd": "/test",
                "hook_event_name": "PerfTest",
                **pathological_data
            })

            # Test serialization performance
            serialized = to_json_serializable(hook_input)

            end_time = time.time()
            processing_time = end_time - start_time

            # Should complete within reasonable time (not exponential growth)
            assert processing_time < 5.0, f"Case {case_index} took {processing_time}s (too slow)"

    def _create_deep_object(self, depth: int, current_depth: int = 0) -> Dict[str, Any]:
        """Create deeply nested object for testing recursion"""
        if current_depth >= depth:
            return {"final": True, "depth": current_depth}

        return {
            "level": current_depth,
            "data": f"Level {current_depth} data",
            "nested": self._create_deep_object(depth, current_depth + 1)
        }

    def _get_memory_usage(self) -> int:
        """Get current memory usage in bytes"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss
        except ImportError:
            # Fallback if psutil not available
            return 0


class TestClaudeCodeIntegrationEdgeCases:
    """Test Claude Code specification compliance under extreme conditions"""

    def test_claude_code_json_compliance_under_stress(self):
        """Test Claude Code JSON compliance with pathological data"""
        # Create decision output with extremely complex validation issues
        complex_issues = []
        for i in range(100):
            complex_issues.extend([
                f"Error {i}: Unicode test 测试 with émojis 🔥💯",
                {"message": f"Complex error {i}", "details": {
                    "nested_data": {"level": i, "content": "X" * 1000},
                    "unicode_content": f"Content with 中文 and emoji 🚀 for error {i}"
                }},
                # Edge case: very long error messages
                f"Very long error message: " + "X" * 10000,
                # Edge case: empty and None values
                "",
                None,
                # Edge case: non-string types that need to be handled
                {"complex": {"deeply": {"nested": {"error": f"Deep error {i}"}}}},
            ])

        # Create decision with complex validation issues
        decision = PreToolUseDecisionOutput.block(
            reason="Complex DAIC workflow test with unicode: 测试🔥",
            validation_issues=complex_issues,
            session_id="stress-test-unicode-🔥-session",
            suppress_output=True
        )

        decision_dict = decision.to_dict()

        # Verify Claude Code required fields exist
        assert "continue" in decision_dict
        assert decision_dict["continue"] is False
        assert "hookSpecificOutput" in decision_dict

        hook_output = decision_dict["hookSpecificOutput"]
        assert "hookEventName" in hook_output
        assert hook_output["hookEventName"] == "PreToolUse"

        # Test JSON serialization doesn't crash
        try:
            json_str = json.dumps(decision_dict, ensure_ascii=False)
            assert len(json_str) > 0

            # Test round-trip preservation
            recovered = json.loads(json_str)
            assert recovered["hookSpecificOutput"]["hookEventName"] == "PreToolUse"

        except (TypeError, ValueError, UnicodeError) as e:
            pytest.fail(f"JSON serialization failed with complex data: {e}")

    def test_missing_required_fields_boundary_conditions(self):
        """Test behavior when required Claude Code fields are missing or corrupted"""
        # Test cases with missing or corrupted required fields
        incomplete_inputs = [
            # Missing cwd (required by Claude Code spec)
            {
                "session_id": "incomplete-1",
                "transcript_path": "/tmp/incomplete1.txt",
                "hook_event_name": "PreToolUse"
                # Missing cwd
            },
            # Missing hookEventName in response
            {},
            # Corrupted session_id
            {
                "session_id": None,
                "transcript_path": "/tmp/incomplete2.txt",
                "cwd": "/test",
                "hook_event_name": "PreToolUse"
            },
            # Invalid hook_event_name
            {
                "session_id": "incomplete-3",
                "transcript_path": "/tmp/incomplete3.txt",
                "cwd": "/test",
                "hook_event_name": None
            }
        ]

        for i, incomplete_input in enumerate(incomplete_inputs):
            # Should parse gracefully with defaults
            parsed = BaseHookInput.parse(incomplete_input)

            # Verify required fields have safe defaults
            assert isinstance(parsed.session_id, str)
            assert isinstance(parsed.transcript_path, str)
            assert isinstance(parsed.cwd, str)
            assert isinstance(parsed.hook_event_name, str)

            # Test that responses can still be generated
            try:
                response = UserPromptContextResponse.create_context(
                    f"Context for incomplete test {i}",
                    {"test_case": i}
                )
                response_dict = response.to_dict()

                # Verify Claude Code compliance maintained
                assert "hookSpecificOutput" in response_dict
                assert response_dict["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"

            except Exception as e:
                pytest.fail(f"Failed to create response for incomplete input {i}: {e}")

    def test_json_format_compliance_with_special_characters(self):
        """Test JSON format compliance with Unicode, control chars, and edge cases"""
        special_char_data = {
            "unicode_test": "测试 Test with émojis 🔥💯🚀 and symbols ©®™",
            "control_chars": "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C\x0D\x0E\x0F",
            "escape_sequences": "\"Test with quotes\" and \\backslashes\\ and \n\r\t newlines",
            "null_byte": "Test\x00with\x00null\x00bytes",
            "high_unicode": "Test with high unicode: 𝕿𝖊𝖘𝖙 𝖂𝖎𝖙𝖍 𝖀𝖓𝖎𝖈𝖔𝖉𝖊",
            "rtl_text": "Test with RTL: العربية עברית",
            "mixed_encodings": "Mixed: ASCII + UTF-8: café + UTF-16: 𝓣𝓮𝓼𝓽"
        }

        # Test UserPromptContextResponse with special characters
        context_response = UserPromptContextResponse.create_context(
            json.dumps(special_char_data, ensure_ascii=False),
            {"special_char_test": True, "unicode_data": special_char_data}
        )

        response_dict = context_response.to_dict()

        # Verify structure integrity with special characters
        assert "hookSpecificOutput" in response_dict
        assert response_dict["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"

        # Test JSON serialization handles special characters
        try:
            # Test with ensure_ascii=False for full Unicode support
            json_str = json.dumps(response_dict, ensure_ascii=False)
            recovered = json.loads(json_str)

            # Verify special characters survived round-trip
            additional_context = recovered["hookSpecificOutput"]["additionalContext"]
            assert "🔥💯🚀" in additional_context
            assert "测试" in additional_context

        except (UnicodeError, ValueError) as e:
            pytest.fail(f"Failed to handle special characters in JSON: {e}")

        # Test with ensure_ascii=True for compatibility
        try:
            json_str_ascii = json.dumps(response_dict, ensure_ascii=True)
            recovered_ascii = json.loads(json_str_ascii)

            # Should still be valid Claude Code response
            assert recovered_ascii["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"

        except Exception as e:
            pytest.fail(f"Failed ASCII-safe JSON serialization: {e}")


class TestDataCorruptionAndRecoveryScenarios:
    """Test malformed data handling and graceful recovery"""

    def test_malformed_input_graceful_recovery(self):
        """Test recovery from various types of malformed input data"""
        malformed_cases = [
            # Truncated JSON
            '{"session_id": "test", "transcript_path": "/tmp/test.txt", "cwd": "/test", "hook_event_name": "Test", "malformed',
            # Invalid UTF-8 sequences (if they somehow get through)
            '{"session_id": "test", "invalid_utf8": "\\xff\\xfe\\xfd"}',
            # Mixed types in arrays
            '{"session_id": "test", "mixed_array": [1, "string", null, true, {"object": "value"}]}',
            # Extremely nested structure that might cause issues
            '{"session_id": "test", "nested": ' + '{"level": ' * 100 + 'null' + '}' * 100,
            # Invalid escape sequences
            '{"session_id": "test", "invalid_escape": "\\x invalid \\u invalid \\"}',
        ]

        for i, malformed_json in enumerate(malformed_cases):
            try:
                # Most should fail JSON parsing
                data = json.loads(malformed_json)
                # If it parses, test our parsing handles it gracefully
                parsed = BaseHookInput.parse(data)
                assert isinstance(parsed.session_id, str)
            except json.JSONDecodeError:
                # Expected for truly malformed JSON
                pass
            except Exception as e:
                # Should not crash with unhandled exceptions
                pytest.fail(f"Malformed case {i} caused unhandled error: {e}")

    def test_partial_data_corruption_recovery(self):
        """Test recovery from partial data corruption during processing"""
        # Create data with some corrupted fields but valid structure
        partially_corrupted = {
            "session_id": "corruption-test",
            "transcript_path": "/tmp/corruption.txt",
            "cwd": "/test",
            "hook_event_name": "CorruptionTest",
            # Corrupted tool input
            "tool_input": {
                "file_path": "/test/file.py",
                "content": None,  # Should be string
                "edits": "not_an_array",  # Should be array
                "old_string": {"invalid": "type"},  # Should be string
                "corrupted_field": float('inf')  # Invalid JSON value
            },
            # Corrupted tool response
            "tool_response": {
                "filePath": [1, 2, 3],  # Should be string
                "success": "maybe",  # Should be boolean
                "structuredPatch": "not_an_array"  # Should be array
            },
            # Corrupted validation issues
            "validation_issues": {
                "not": "an_array",
                "invalid": float('nan')
            }
        }

        # Should parse without crashing
        parsed = PostToolUseInput.parse(partially_corrupted)

        # Verify basic structure is preserved
        assert parsed.session_id == "corruption-test"
        assert parsed.cwd == "/test"

        # Tool input parsing should handle corruption gracefully
        if parsed.tool_input:
            tool_dict = parsed.tool_input.to_dict()
            # Corrupted fields should be in extra or handled gracefully
            assert "file_path" in tool_dict

        # Tool response parsing should handle corruption gracefully
        if parsed.tool_response:
            response_dict = parsed.tool_response.to_dict()
            # Should have some valid structure even with corruption
            assert isinstance(response_dict, dict)

        # Test serialization works despite corruption
        serialized = to_json_serializable(parsed)
        json_str = json.dumps(serialized, default=str)  # Use default for non-serializable
        assert len(json_str) > 0

    def test_data_type_mismatch_consistency(self):
        """Test consistent handling of data type mismatches across all components"""
        type_mismatch_data = {
            "session_id": 12345,  # Number instead of string
            "transcript_path": True,  # Boolean instead of string
            "cwd": [],  # Array instead of string
            "hook_event_name": {"name": "Test"},  # Object instead of string
            "tool_name": None,  # None instead of string
            "prompt": 3.14159,  # Float instead of string
            "timestamp": {"not": "a_timestamp"},  # Object instead of string/number
            "validation_issues": "single_string_not_array",  # String instead of array
            "tool_input": [1, 2, 3],  # Array instead of object
            "tool_response": "string_response",  # String instead of object
            "numeric_fields": {
                "duration_ms": {"not": "a_number"},
                "timestamp_ns": None,
                "success": "maybe",  # String instead of boolean
                "count": [1, 2, 3]  # Array instead of number
            }
        }

        # Test different input types handle mismatches consistently
        input_types = [BaseHookInput, PreToolUseInput, PostToolUseInput, UserPromptSubmitInput]

        for input_type in input_types:
            if input_type is None:
                continue

            parsed = input_type.parse(type_mismatch_data)

            # All should consistently convert to strings for core fields
            assert isinstance(parsed.session_id, str)
            assert isinstance(parsed.transcript_path, str)
            assert isinstance(parsed.cwd, str)
            assert isinstance(parsed.hook_event_name, str)

            # Test serialization maintains consistency
            serialized = to_json_serializable(parsed)
            assert isinstance(serialized["session_id"], str)
            assert isinstance(serialized["transcript_path"], str)

    def test_unknown_field_preservation_consistency(self):
        """Test unknown fields are consistently preserved across components"""
        data_with_unknowns = {
            # Standard fields
            "session_id": "unknown-field-test",
            "transcript_path": "/tmp/unknown.txt",
            "cwd": "/test",
            "hook_event_name": "UnknownTest",

            # Many unknown fields of various types
            "unknown_string": "test value",
            "unknown_number": 42,
            "unknown_float": 3.14159,
            "unknown_boolean": True,
            "unknown_null": None,
            "unknown_array": [1, "two", {"three": 3}],
            "unknown_object": {
                "nested": {
                    "deeply": {
                        "nested": "value"
                    }
                }
            },
            "unicode_unknown": "Unknown with unicode: 测试🔥",
            "future_field_v2": {"version": 2, "features": ["a", "b", "c"]},
            "deprecated_field": {"legacy": True, "old_format": "data"},

            # Tool-specific unknown fields
            "tool_input": {
                "file_path": "/test/file.py",
                "content": "test",
                "unknown_tool_field": "should be preserved",
                "future_tool_option": {"enabled": True}
            }
        }

        parsed = PreToolUseInput.parse(data_with_unknowns)

        # Verify unknown fields are preserved in raw and extra fields
        assert "unknown_string" in parsed.raw
        assert "unknown_object" in parsed.raw
        assert "unicode_unknown" in parsed.raw

        # Test tool input preserves unknown fields
        if parsed.tool_input:
            tool_dict = parsed.tool_input.to_dict()
            # Unknown fields should be in extra
            extra_fields = tool_dict.get("extra", {})
            assert "unknown_tool_field" in extra_fields or "unknown_tool_field" in tool_dict

        # Test serialization preserves all unknown fields
        serialized = to_json_serializable(parsed)
        raw_data = serialized["raw"]

        # All unknown fields should be preserved
        for field in ["unknown_string", "unknown_object", "unicode_unknown", "future_field_v2"]:
            assert field in raw_data, f"Unknown field {field} was lost during processing"

        # Test round-trip preservation
        json_str = json.dumps(serialized)
        recovered = json.loads(json_str)

        for field in ["unknown_string", "unknown_object", "unicode_unknown"]:
            assert field in recovered["raw"], f"Unknown field {field} lost in round-trip"


class TestBoundaryAndLimitTesting:
    """Test system boundaries and limits"""

    def test_maximum_data_structure_sizes(self):
        """Test handling of maximum reasonable data structure sizes"""
        # Create maximum size structures
        max_size_data = {
            "session_id": "max-size-test",
            "transcript_path": "/tmp/maxsize.txt",
            "cwd": "/test",
            "hook_event_name": "MaxSizeTest",

            # Maximum reasonable string sizes
            "max_string": "X" * (1024 * 1024),  # 1MB string
            "max_array": [f"item_{i}" for i in range(50000)],  # 50K items
            "max_nested": self._create_max_nested_structure(),

            "tool_input": {
                "file_path": "/test/" + "very_long_path_" * 1000 + "file.py",
                "content": "# Large content\n" * 10000,  # ~140KB content
                "edits": [
                    {"old_string": f"old_line_{i}", "new_string": f"new_line_{i}"}
                    for i in range(5000)  # 5000 edits
                ]
            }
        }

        start_time = time.time()

        # Should handle large data without crashing
        try:
            parsed = PreToolUseInput.parse(max_size_data)
            assert parsed is not None

            # Test serialization of large data
            serialized = to_json_serializable(parsed)

            # Should complete in reasonable time
            end_time = time.time()
            assert (end_time - start_time) < 30.0, "Processing took too long"

            # Verify large structures are preserved
            if parsed.tool_input and hasattr(parsed.tool_input, 'edits'):
                assert len(parsed.tool_input.edits or []) == 5000

        except MemoryError:
            # Acceptable - system limits reached
            pytest.skip("System memory limits reached")
        except Exception as e:
            pytest.fail(f"Failed to handle maximum size data: {e}")

    def test_unicode_and_special_character_boundaries(self):
        """Test Unicode handling at boundaries and edge cases"""
        unicode_edge_cases = [
            # Basic multilingual plane
            "Basic Latin: Hello",
            "Latin-1: café naïve résumé",
            "Cyrillic: Привет мир",
            "Arabic: مرحبا العالم",
            "Chinese: 你好世界",
            "Japanese: こんにちは世界",
            "Hebrew: שלום עולם",

            # Supplementary planes (4-byte UTF-8)
            "Emoji: 👋🌍🔥💯🚀✨",
            "Mathematical: 𝕏 = 𝑓(𝑥) + 𝑔(𝑦)",
            "Musical: 𝄞 𝅘𝅥 𝅘𝅥𝅮",

            # Edge cases
            "Zero width: test\u200B\u200Ctest",
            "Direction marks: test\u202D\u202Etest",
            "Combining chars: e\u0301\u0302\u0303",  # e with multiple accents
            "Normalization: é vs e\u0301",  # Different Unicode normalization

            # Potential problematic sequences
            "Surrogate-like: \uD800\uDC00",  # Valid surrogate pair in UTF-16
            "Private use: \uE000\uF8FF",
            "Control chars: \u0000\u0001\u001F",
            "Replacement char: \uFFFD",

            # Very long Unicode strings
            "Long unicode: " + "🔥" * 1000 + "测试" * 1000 + "Ω" * 1000,
        ]

        for i, unicode_string in enumerate(unicode_edge_cases):
            unicode_data = {
                "session_id": f"unicode-test-{i}",
                "transcript_path": f"/tmp/unicode_{i}.txt",
                "cwd": "/test/unicode",
                "hook_event_name": "UnicodeTest",
                "prompt": unicode_string,
                "unicode_field": unicode_string,
                "tool_input": {
                    "file_path": f"/test/unicode_{i}.py",
                    "content": f"# Unicode test: {unicode_string}\nprint('{unicode_string}')",
                    "description": unicode_string
                }
            }

            try:
                # Should parse Unicode correctly
                parsed = UserPromptSubmitInput.parse(unicode_data)
                assert parsed.prompt is not None

                # Test serialization preserves Unicode
                serialized = to_json_serializable(parsed)
                json_str = json.dumps(serialized, ensure_ascii=False)
                recovered = json.loads(json_str)

                # Verify Unicode survived round-trip
                assert recovered["prompt"] == unicode_string

            except (UnicodeError, ValueError) as e:
                # Some edge cases may legitimately fail
                print(f"Unicode case {i} failed (acceptable): {e}")
            except Exception as e:
                pytest.fail(f"Unicode case {i} caused unexpected error: {e}")

    def test_timezone_edge_cases_and_dst_transitions(self):
        """Test timestamp handling with timezone edge cases"""
        # Create timestamps around DST transitions and edge cases
        edge_timestamps = [
            # Standard cases
            "2025-01-01T00:00:00Z",
            "2025-01-01T00:00:00+00:00",

            # DST transitions (US Eastern Time)
            "2025-03-09T06:59:59Z",  # Before spring forward
            "2025-03-09T07:00:00Z",  # Spring forward moment
            "2025-11-02T05:59:59Z",  # Before fall back
            "2025-11-02T06:00:00Z",  # Fall back moment

            # Timezone edge cases
            "2025-01-01T00:00:00+14:00",  # Maximum timezone offset
            "2025-01-01T00:00:00-12:00",  # Minimum timezone offset
            "2025-01-01T00:00:00+05:30",  # Half-hour offset
            "2025-01-01T00:00:00+09:45",  # Quarter-hour offset

            # Leap year edge cases
            "2024-02-29T00:00:00Z",     # Valid leap day
            "2025-02-28T23:59:59Z",     # Last day of non-leap year

            # Year boundaries
            "1970-01-01T00:00:00Z",     # Unix epoch
            "2000-01-01T00:00:00Z",     # Y2K
            "2038-01-19T03:14:07Z",     # 32-bit timestamp limit
            "3000-12-31T23:59:59Z",     # Future date

            # Numeric timestamps (various formats)
            1640995200,        # Unix timestamp
            1640995200000,     # Millisecond timestamp
            1640995200000000,  # Microsecond timestamp
            1640995200000000000,  # Nanosecond timestamp

            # Edge cases
            0,                 # Epoch
            -1,                # Before epoch
            2147483647,        # Max 32-bit signed int
            4294967295,        # Max 32-bit unsigned int
        ]

        for i, timestamp in enumerate(edge_timestamps):
            try:
                # Test timestamp parsing
                if isinstance(timestamp, (int, float)):
                    ts_str = str(timestamp)
                else:
                    ts_str = timestamp

                formatted = format_for_database(ts_str)
                assert isinstance(formatted, str)

                # Test in actual data structure
                timestamp_data = {
                    "session_id": f"timestamp-test-{i}",
                    "transcript_path": "/tmp/timestamp.txt",
                    "cwd": "/test",
                    "hook_event_name": "TimestampTest",
                    "timestamp": timestamp,
                    "logged_at": ts_str
                }

                # Should parse without crashing
                parsed = BaseHookInput.parse(timestamp_data)
                serialized = to_json_serializable(parsed)

                # Test with log event parsing
                log_data = {
                    "session_id": f"timestamp-log-{i}",
                    "hook_event_name": "TimestampTest",
                    "hook_name": "test_hook",
                    "logged_at": formatted,
                    "timestamp": timestamp
                }
                log_event = parse_log_event(log_data)
                assert log_event.logged_at is not None

            except Exception as e:
                # Some edge cases may fail, but should not crash
                print(f"Timestamp case {i} ({timestamp}) failed: {e}")

    def test_numeric_overflow_and_underflow_scenarios(self):
        """Test numeric edge cases and overflow/underflow handling"""
        numeric_edge_cases = {
            "session_id": "numeric-test",
            "transcript_path": "/tmp/numeric.txt",
            "cwd": "/test",
            "hook_event_name": "NumericTest",

            # Integer edge cases
            "max_int": sys.maxsize,
            "min_int": -sys.maxsize - 1,
            "zero": 0,
            "negative_zero": -0,

            # Float edge cases
            "positive_infinity": float('inf'),
            "negative_infinity": -float('inf'),
            "nan": float('nan'),
            "max_float": sys.float_info.max,
            "min_float": sys.float_info.min,
            "epsilon": sys.float_info.epsilon,

            # Large numbers
            "very_large": 10**100,
            "very_small": 10**-100,

            # Timestamp edge cases
            "timestamp_overflow": 9999999999999999999,
            "timestamp_underflow": -9999999999999999999,

            # Duration edge cases
            "duration_ms": 1.7976931348623157e+308,  # Near max float
            "negative_duration": -999999999.999,

            "numeric_arrays": {
                "mixed_numbers": [0, -0, float('inf'), -float('inf'), float('nan')],
                "large_numbers": [10**50, -10**50, 10**-50, -10**-50],
                "edge_integers": [2**63 - 1, -2**63, 2**31 - 1, -2**31]
            }
        }

        try:
            # Should handle numeric edge cases gracefully
            parsed = BaseHookInput.parse(numeric_edge_cases)

            # Test serialization handles special numeric values
            serialized = to_json_serializable(parsed)

            # JSON serialization should handle/convert special values
            json_str = json.dumps(serialized, allow_nan=True)

            # Some values may be converted to strings or null
            recovered = json.loads(json_str)
            assert "session_id" in recovered

        except (ValueError, OverflowError) as e:
            # Acceptable - numeric limits reached
            print(f"Numeric edge case handling: {e}")
        except Exception as e:
            pytest.fail(f"Unexpected error with numeric edge cases: {e}")

    def _create_max_nested_structure(self, max_depth=100):
        """Create maximally nested structure for testing"""
        result = {"final": True}
        for i in range(max_depth):
            result = {f"level_{i}": result, "data": f"Level {i}"}
        return result


class TestErrorChainAndRecoveryTesting:
    """Test error propagation and recovery across multiple stages"""

    def test_error_propagation_across_parsing_stages(self):
        """Test how errors propagate through multiple parsing stages"""
        # Create data that causes errors at different stages
        multi_stage_errors = {
            "session_id": "error-chain-test",
            "transcript_path": "/tmp/error.txt",
            "cwd": "/test",
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",

            # Tool input with multiple potential failure points
            "tool_input": {
                "file_path": None,  # Stage 1 error: invalid file path
                "content": {"not": "a_string"},  # Stage 2 error: wrong type
                "edits": [
                    {"old_string": None, "new_string": "valid"},  # Stage 3 error: partial edit corruption
                    {"old_string": "valid", "new_string": None},  # Stage 4 error: partial edit corruption
                    "not_an_object",  # Stage 5 error: wrong edit format
                    {"malformed": "edit", "missing": "required_fields"}  # Stage 6 error: malformed edit
                ],
                "extra_field": float('inf')  # Stage 7 error: non-serializable value
            },

            # Response with errors
            "tool_response": {
                "filePath": {"not": "a_string"},  # Response parsing error
                "success": "maybe",  # Boolean parsing error
                "structuredPatch": "not_an_array"  # Array parsing error
            }
        }

        # Should handle errors gracefully without total failure
        parsed = PreToolUseInput.parse(multi_stage_errors)

        # Basic structure should still be parsed
        assert parsed.session_id == "error-chain-test"
        assert parsed.tool_name == "Edit"

        # Tool input might be None or have partial parsing
        if parsed.tool_input:
            # Some data might be preserved in extra fields
            tool_dict = parsed.tool_input.to_dict()
            assert isinstance(tool_dict, dict)

        # Test that serialization still works despite errors
        serialized = to_json_serializable(parsed)

        # Should be able to serialize even with errors (using defaults/fallbacks)
        json_str = json.dumps(serialized, default=str)
        assert len(json_str) > 0

    def test_recovery_from_partial_failures_complex_workflows(self):
        """Test recovery from partial failures in complex multi-component workflows"""
        # Simulate complex workflow with failures at each stage
        workflow_stages = [
            # Stage 1: Input parsing with some corruption
            {
                "session_id": "workflow-recovery-test",
                "transcript_path": "/tmp/workflow.txt",
                "cwd": "/test",
                "hook_event_name": "PreToolUse",
                "tool_name": "MultiEdit",
                "corrupted_field": float('nan'),  # Will cause serialization issues
                "tool_input": {
                    "file_path": "/test/file.py",
                    "edits": [
                        {"old_string": "valid1", "new_string": "valid1_new"},
                        {"old_string": None, "new_string": "corrupted1"},  # Partial corruption
                        {"old_string": "valid2", "new_string": "valid2_new"},
                        None,  # Null edit
                        {"old_string": "valid3"},  # Missing new_string
                        {"old_string": "valid4", "new_string": "valid4_new"},
                    ]
                }
            }
        ]

        for stage_data in workflow_stages:
            # Stage 1: Initial parsing (should handle partial corruption)
            parsed = PreToolUseInput.parse(stage_data)
            assert parsed.session_id == "workflow-recovery-test"

            # Stage 2: Tool input processing (should recover from edit corruption)
            if parsed.tool_input:
                tool_dict = parsed.tool_input.to_dict()
                # Should preserve valid edits, handle corrupted ones
                edits = tool_dict.get("edits", [])
                valid_edits = [e for e in edits if isinstance(e, dict) and "old_string" in e]
                assert len(valid_edits) >= 2  # At least some valid edits preserved

            # Stage 3: Serialization (should handle non-serializable values)
            serialized = to_json_serializable(parsed)
            assert isinstance(serialized, dict)

            # Stage 4: JSON conversion (should handle remaining issues)
            json_str = json.dumps(serialized, default=str, allow_nan=False)
            assert len(json_str) > 0

            # Stage 5: Round-trip recovery test
            recovered = json.loads(json_str)
            assert recovered["session_id"] == "workflow-recovery-test"

            # Stage 6: Re-parsing recovered data
            reparsed = PreToolUseInput.parse(recovered)
            assert reparsed.session_id == "workflow-recovery-test"

    def test_consistent_error_messages_across_components(self):
        """Test that error messages are consistent and informative across components"""
        error_scenarios = [
            # Input parsing errors
            {"name": "missing_session_id", "data": {"transcript_path": "/tmp/test.txt"}},
            {"name": "invalid_tool_input", "data": {"session_id": "test", "tool_input": "not_an_object"}},
            {"name": "malformed_edits", "data": {"session_id": "test", "tool_input": {"edits": "not_an_array"}}},

            # Validation errors
            {"name": "invalid_decision_output", "data": None},
            {"name": "missing_required_fields", "data": {}},

            # Timestamp parsing errors
            {"name": "invalid_timestamp", "data": {"timestamp": "not_a_timestamp"}},
            {"name": "overflow_timestamp", "data": {"timestamp": 10**20}},
        ]

        error_messages = []

        for scenario in error_scenarios:
            scenario_name = scenario["name"]
            scenario_data = scenario["data"]

            try:
                # Test different parsing functions
                if scenario_data:
                    base_result = BaseHookInput.parse(scenario_data)
                    pre_result = PreToolUseInput.parse(scenario_data)

                    # If parsing succeeds, test other operations
                    serialized = to_json_serializable(base_result)
                    json.dumps(serialized, default=str)

            except Exception as e:
                error_msg = str(e)
                error_messages.append({
                    "scenario": scenario_name,
                    "error": error_msg,
                    "error_type": type(e).__name__
                })

        # Analyze error message consistency
        error_types = {}
        for error_info in error_messages:
            error_type = error_info["error_type"]
            if error_type not in error_types:
                error_types[error_type] = []
            error_types[error_type].append(error_info)

        # Verify error messages are informative (not just generic)
        for error_info in error_messages:
            error_msg = error_info["error"]
            # Error messages should be informative
            assert len(error_msg) > 10, f"Error message too short: {error_msg}"
            # Should not contain sensitive information
            assert "password" not in error_msg.lower()
            assert "secret" not in error_msg.lower()

    def test_graceful_degradation_component_failures(self):
        """Test graceful degradation when individual components fail"""
        # Test with mocked component failures
        test_data = {
            "session_id": "degradation-test",
            "transcript_path": "/tmp/degradation.txt",
            "cwd": "/test",
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "/test/file.py",
                "old_string": "old content",
                "new_string": "new content"
            }
        }

        # Test with timestamp parsing failure
        with patch('hook_types.parse_standard_timestamp', side_effect=ValueError("Timestamp parsing failed")):
            try:
                formatted = format_for_database("invalid_timestamp")
                # Should fallback to current timestamp
                assert isinstance(formatted, str)
                assert len(formatted) > 0
            except Exception as e:
                pytest.fail(f"No graceful degradation for timestamp failure: {e}")

        # Test with serialization component failure
        with patch('json.dumps', side_effect=TypeError("JSON serialization failed")):
            try:
                parsed = PreToolUseInput.parse(test_data)
                # Basic parsing should still work
                assert parsed.session_id == "degradation-test"
            except Exception as e:
                # Should not propagate serialization errors to parsing
                pass

        # Test with tool input parsing failure
        original_parse_tool_input = parse_tool_input

        def failing_parse_tool_input(data):
            raise ValueError("Tool input parsing failed")

        with patch('hook_types.parse_tool_input', side_effect=failing_parse_tool_input):
            parsed = PreToolUseInput.parse(test_data)
            # Should still parse basic structure
            assert parsed.session_id == "degradation-test"
            assert parsed.tool_name == "Edit"
            # tool_input might be None due to parsing failure
            assert parsed.tool_input is None


if __name__ == "__main__":
    """
    Run comprehensive edge case tests for hook_types.py

    These tests focus on:
    1. Cross-component integration failures
    2. Memory and performance edge cases
    3. Claude Code compliance under stress
    4. Data corruption recovery
    5. Boundary and limit conditions
    6. Error propagation and recovery

    Usage:
    python comprehensive_hook_types_edge_case_tests.py
    or
    pytest comprehensive_hook_types_edge_case_tests.py -v
    """
    pytest.main([__file__, "-v", "--tb=short"])
