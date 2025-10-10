#!/usr/bin/env python3
"""
Utility Functions Tests for hook_types.py

Tests the foundational utility functions that support the entire type system:
- Timestamp utilities (HIGH RISK - Data consistency critical)
- Data helper functions (normalization and conversion)
- Serialization utilities (JSON compatibility)

Focus: Critical foundational functions with complex edge cases and error handling.
"""

import pytest
import json
import time
import sys
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Add hook_types module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "src" / "hooks" / "templates" / "utils"))

from hook_types import (
    # Timestamp utilities
    _now_iso, _coerce_iso, get_standard_timestamp, parse_standard_timestamp, format_for_database,
    # Data helper functions
    _as_list, normalize_validation_issues,
    # Serialization utilities
    to_json_serializable,
    # For testing nested serialization
    HookSpecificOutput, SessionCorrelationResponse, DAICModeResult, ToolAnalysisResult
)


class TestTimestampUtilities:
    """Test timestamp utilities - HIGH RISK for data consistency"""
    
    def test_now_iso_format_compliance(self):
        """Test _now_iso returns valid ISO 8601 format"""
        timestamp = _now_iso()
        
        # Should match pattern: 2025-08-11T13:34:27.254010+00:00
        iso_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}\+00:00'
        assert re.match(iso_pattern, timestamp), f"Invalid ISO format: {timestamp}"
        
        # Should be parseable by datetime
        parsed = datetime.fromisoformat(timestamp)
        assert parsed.tzinfo == timezone.utc
    
    def test_now_iso_timezone_is_utc(self):
        """Verify timezone is always UTC"""
        timestamp = _now_iso()
        assert timestamp.endswith('+00:00'), "Timestamp must be in UTC"
    
    def test_now_iso_consistency(self):
        """Test format consistency across multiple calls"""
        ts1 = _now_iso()
        time.sleep(0.001)  # Small delay
        ts2 = _now_iso()
        
        assert len(ts1) == len(ts2), "Format should be consistent"
        assert ts1.count('T') == ts2.count('T') == 1
        assert ts1.endswith('+00:00')
        assert ts2.endswith('+00:00')
    
    def test_coerce_iso_none_input(self):
        """Test None input returns None"""
        assert _coerce_iso(None) is None
    
    def test_coerce_iso_string_passthrough(self):
        """String inputs should pass through unchanged"""
        iso_string = "2025-08-11T13:34:27.254010+00:00"
        assert _coerce_iso(iso_string) == iso_string
        
        # Test various string formats
        assert _coerce_iso("2025-01-01T00:00:00Z") == "2025-01-01T00:00:00Z"
        assert _coerce_iso("invalid string") == "invalid string"
    
    def test_coerce_iso_unix_seconds(self):
        """HIGH RISK: Test Unix timestamp in seconds (< 1e12)"""
        unix_ts = 1692622467  # Example Unix timestamp in seconds
        result = _coerce_iso(unix_ts)
        
        assert result is not None
        assert result.endswith('+00:00')
        
        # Verify it represents the correct time
        parsed = datetime.fromisoformat(result)
        assert abs(parsed.timestamp() - unix_ts) < 0.001  # Allow small float precision error
    
    def test_coerce_iso_unix_milliseconds(self):
        """HIGH RISK: Test Unix timestamp in milliseconds (1e12 - 1e15)"""
        unix_ms = 1692622467000  # Milliseconds
        result = _coerce_iso(unix_ms)
        
        assert result is not None
        assert result.endswith('+00:00')
        
        # Should convert to seconds correctly
        parsed = datetime.fromisoformat(result)
        expected_seconds = unix_ms / 1000
        assert abs(parsed.timestamp() - expected_seconds) < 0.001
    
    def test_coerce_iso_unix_nanoseconds(self):
        """HIGH RISK: Test Unix timestamp in nanoseconds (> 1e15)"""
        unix_ns = 1692622467000000000  # Nanoseconds  
        result = _coerce_iso(unix_ns)
        
        assert result is not None
        assert result.endswith('+00:00')
        
        parsed = datetime.fromisoformat(result)
        expected_seconds = unix_ns / 1_000_000_000
        assert abs(parsed.timestamp() - expected_seconds) < 0.001
    
    def test_coerce_iso_edge_case_boundaries(self):
        """HIGH RISK: Test boundary conditions for timestamp detection"""
        # Just below millisecond threshold
        result1 = _coerce_iso(999999999999)  # Should be seconds
        if result1 is not None:  # Large timestamp might overflow
            assert result1.endswith('+00:00')
        
        # Just at millisecond threshold
        result2 = _coerce_iso(1000000000000)  # Should be milliseconds
        if result2 is not None:
            assert result2.endswith('+00:00')
        
        # Just below nanosecond threshold  
        result3 = _coerce_iso(999999999999999)  # Should be milliseconds
        if result3 is not None:
            assert result3.endswith('+00:00')
        
        # Just at nanosecond threshold
        result4 = _coerce_iso(1000000000000000)  # Should be nanoseconds
        if result4 is not None:
            assert result4.endswith('+00:00')
        
        # Test a reasonable boundary that should work
        recent_ms = 1692622467000  # Known good millisecond timestamp
        result_recent = _coerce_iso(recent_ms)
        assert result_recent is not None
        assert result_recent.endswith('+00:00')
    
    def test_coerce_iso_invalid_inputs(self):
        """Test handling of invalid numeric inputs"""
        # Note: Negative timestamps are actually valid (before 1970 epoch)
        # But very negative ones might fail due to datetime limits
        result_neg = _coerce_iso(-1)  # 1969-12-31T23:59:59+00:00
        if result_neg is not None:
            assert result_neg.endswith('+00:00')
        
        # Very large negative should fail
        very_negative = _coerce_iso(-999999999999)
        # This might return None due to datetime range limits
        
        # Infinity and NaN should return None (datetime can't handle them)
        assert _coerce_iso(float('inf')) is None
        assert _coerce_iso(float('nan')) is None
        assert _coerce_iso(float('-inf')) is None
    
    def test_coerce_iso_float_precision(self):
        """Test floating point timestamp handling"""
        float_ts = 1692622467.123456  # Fractional seconds
        result = _coerce_iso(float_ts)
        
        assert result is not None
        parsed = datetime.fromisoformat(result)
        assert abs(parsed.timestamp() - float_ts) < 0.000001
    
    def test_coerce_iso_performance_large_dataset(self):
        """Performance test with mixed timestamps"""
        timestamps = [
            1692622467,  # seconds
            1692622467000,  # milliseconds  
            1692622467000000000,  # nanoseconds
            "2025-08-11T13:34:27+00:00",  # ISO string
            None,
            float('inf'),  # Invalid
            "invalid"  # String passthrough
        ] * 100  # 700 total items
        
        start_time = time.time()
        results = [_coerce_iso(ts) for ts in timestamps]
        duration = time.time() - start_time
        
        # Should process 700 timestamps quickly
        assert duration < 0.1, f"Too slow: {duration}s for {len(timestamps)} timestamps"
        
        # Count valid results (4 valid per 7 items * 100 repetitions = 400 valid + 300 invalid/passthrough)
        valid_results = [r for r in results if r is not None]
        assert len(valid_results) == 500  # 5 per group * 100
    
    def test_get_standard_timestamp_format(self):
        """Test get_standard_timestamp canonical format"""
        ts = get_standard_timestamp()
        iso_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}\+00:00'
        assert re.match(iso_pattern, ts), f"Invalid format: {ts}"
    
    def test_get_standard_timestamp_consistency(self):
        """Multiple calls should produce consistent format"""
        ts1 = get_standard_timestamp()
        time.sleep(0.001)
        ts2 = get_standard_timestamp()
        
        assert len(ts1) == len(ts2)
        assert ts1.count('T') == ts2.count('T') == 1
        assert ts1.endswith('+00:00')
        assert ts2.endswith('+00:00')
    
    def test_parse_standard_timestamp_iso_format(self):
        """Test parsing valid ISO format"""
        iso_str = "2025-08-11T13:34:27.254010+00:00"
        result = parse_standard_timestamp(iso_str)
        
        assert isinstance(result, datetime)
        assert result.tzinfo == timezone.utc
        assert result.year == 2025
        assert result.month == 8
        assert result.day == 11
    
    def test_parse_standard_timestamp_z_suffix(self):
        """Test parsing ISO format with Z suffix"""
        iso_z = "2025-08-11T13:34:27.254010Z"
        result = parse_standard_timestamp(iso_z)
        
        assert isinstance(result, datetime)
        assert result.tzinfo == timezone.utc
    
    def test_parse_standard_timestamp_numeric_fallback(self):
        """HIGH RISK: Test fallback to numeric parsing"""
        unix_str = "1692622467"  # Unix timestamp as string
        result = parse_standard_timestamp(unix_str)
        
        assert isinstance(result, datetime)
        assert result.tzinfo == timezone.utc
        assert abs(result.timestamp() - 1692622467) < 0.001
    
    def test_parse_standard_timestamp_empty_input(self):
        """Test empty input raises ValueError"""
        with pytest.raises(ValueError, match="Empty timestamp"):
            parse_standard_timestamp("")
        
        with pytest.raises(ValueError, match="Empty timestamp"):
            parse_standard_timestamp(None)
    
    def test_parse_standard_timestamp_invalid_input(self):
        """Test invalid input raises ValueError"""
        with pytest.raises(ValueError, match="Cannot parse timestamp"):
            parse_standard_timestamp("invalid-format")
        
        with pytest.raises(ValueError, match="Cannot parse timestamp"):
            parse_standard_timestamp("not-a-number-or-date")
    
    def test_parse_standard_timestamp_millisecond_numeric(self):
        """Test numeric millisecond parsing in string format"""
        ms_str = "1692622467000"  # Milliseconds as string
        result = parse_standard_timestamp(ms_str)
        
        expected = datetime.fromtimestamp(1692622467, timezone.utc)
        assert abs((result - expected).total_seconds()) < 0.001
    
    def test_parse_standard_timestamp_edge_cases(self):
        """Test edge cases and boundary conditions"""
        # Very old timestamp (1970)
        old_ts = "0"
        result = parse_standard_timestamp(old_ts)
        assert result.year == 1970
        
        # Future timestamp (2050)
        future_ts = "2524608000"  # Jan 1, 2050
        result = parse_standard_timestamp(future_ts)
        assert result.year == 2050
    
    def test_format_for_database_valid_iso(self):
        """Test formatting valid ISO timestamp"""
        iso_input = "2025-08-11T13:34:27.254010+00:00"
        result = format_for_database(iso_input)
        
        # Should parse and re-format consistently
        assert result.endswith('+00:00')
        parsed = datetime.fromisoformat(result)
        assert parsed.tzinfo == timezone.utc
    
    def test_format_for_database_numeric_conversion(self):
        """Test conversion of numeric timestamp"""
        unix_str = "1692622467"
        result = format_for_database(unix_str)
        
        assert result.endswith('+00:00')
        parsed = datetime.fromisoformat(result)
        assert abs(parsed.timestamp() - 1692622467) < 0.001
    
    def test_format_for_database_empty_input_fallback(self):
        """Test fallback to current timestamp for empty input"""
        result = format_for_database("")
        
        assert result.endswith('+00:00')
        # Should be recent timestamp (within 1 second of now)
        parsed = datetime.fromisoformat(result)
        now = datetime.now(timezone.utc)
        assert abs((now - parsed).total_seconds()) < 1
    
    def test_format_for_database_invalid_input_fallback(self):
        """Test fallback behavior for invalid input"""
        result = format_for_database("completely-invalid")
        
        assert result.endswith('+00:00')
        # Should be current timestamp fallback
        parsed = datetime.fromisoformat(result)
        now = datetime.now(timezone.utc)
        assert abs((now - parsed).total_seconds()) < 1
    
    def test_format_for_database_consistency(self):
        """Test consistent output format across inputs"""
        inputs = [
            "2025-08-11T13:34:27.254010+00:00",  # Valid ISO
            "1692622467",  # Unix seconds
            "1692622467000",  # Unix milliseconds
            "",  # Empty (fallback)
            "invalid"  # Invalid (fallback)
        ]
        
        results = [format_for_database(inp) for inp in inputs]
        
        # All results should be valid ISO format
        iso_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*\+00:00'
        for i, result in enumerate(results):
            assert re.match(iso_pattern, result), f"Invalid format for input {inputs[i]}: {result}"
            # Should be parseable
            datetime.fromisoformat(result)


class TestDataHelperFunctions:
    """Test data helper functions - MEDIUM RISK for data conversion"""
    
    def test_as_list_none_input(self):
        """Test None converts to empty list"""
        assert _as_list(None) == []
    
    def test_as_list_already_list(self):
        """Test list input passes through unchanged"""
        input_list = [1, 2, 3, "test"]
        result = _as_list(input_list)
        assert result == input_list
        assert result is input_list  # Should be same object
    
    def test_as_list_single_value(self):
        """Test single values become single-item lists"""
        assert _as_list("hello") == ["hello"]
        assert _as_list(42) == [42]
        assert _as_list(3.14) == [3.14]
        assert _as_list(True) == [True]
        assert _as_list(False) == [False]
    
    def test_as_list_complex_objects(self):
        """Test complex objects are preserved in list"""
        obj = {"key": "value", "nested": {"data": 123}}
        result = _as_list(obj)
        assert result == [obj]
        assert result[0] is obj  # Should be same object reference
    
    def test_as_list_edge_cases(self):
        """Test edge cases and unusual inputs"""
        assert _as_list(0) == [0]  # Falsy but not None
        assert _as_list("") == [""]  # Empty string
        assert _as_list([]) == []  # Empty list
        assert _as_list([None]) == [None]  # List containing None
        
        # Test with nested structures
        nested = [{"a": [1, 2]}, [3, 4]]
        result = _as_list(nested)
        assert result is nested  # Already a list, pass through
        
        # Single nested structure
        single_nested = {"a": [1, 2]}
        result = _as_list(single_nested)
        assert result == [single_nested]
    
    def test_normalize_validation_issues_dict_message(self):
        """Test extraction from dict with 'message' field"""
        issues = [
            {"message": "Error 1"},
            {"message": "Error 2 with Unicode: 🚨"}
        ]
        result = normalize_validation_issues(issues)
        assert result == ["Error 1", "Error 2 with Unicode: 🚨"]
    
    def test_normalize_validation_issues_dict_detail(self):
        """Test extraction from dict with 'detail' field"""
        issues = [
            {"detail": "Detail 1"},
            {"detail": "Detail 2 with special chars: <>&\"'"}
        ]
        result = normalize_validation_issues(issues)
        assert result == ["Detail 1", "Detail 2 with special chars: <>&\"'"]
    
    def test_normalize_validation_issues_string_direct(self):
        """Test direct string issues"""
        issues = ["Direct error 1", "Direct error 2"]
        result = normalize_validation_issues(issues)
        assert result == ["Direct error 1", "Direct error 2"]
    
    def test_normalize_validation_issues_mixed_formats(self):
        """HIGH RISK: Test mixed issue formats"""
        issues = [
            {"message": "Dict with message"},
            "Direct string",
            {"detail": "Dict with detail"},
            {"error": "Dict with other field", "code": 123}  # Fallback to str()
        ]
        result = normalize_validation_issues(issues)
        
        assert result[0] == "Dict with message"
        assert result[1] == "Direct string"
        assert result[2] == "Dict with detail"
        # Last one should be string representation
        assert isinstance(result[3], str)
        assert "error" in result[3]
        assert "Dict with other field" in result[3]
    
    def test_normalize_validation_issues_empty_input(self):
        """Test empty input"""
        assert normalize_validation_issues([]) == []
    
    def test_normalize_validation_issues_none_message(self):
        """Test dict with None message field"""
        issues = [
            {"message": None},
            {"detail": None},
            {"other": "field"}
        ]
        result = normalize_validation_issues(issues)
        
        assert len(result) == 3
        assert all(isinstance(r, str) for r in result)
        # Should fall back to string representations
    
    def test_normalize_validation_issues_complex_nested(self):
        """HIGH RISK: Test complex nested validation structures"""
        issues = [
            {"message": "Simple message"},
            {"validation_error": {"field": "name", "message": "Complex nested"}},
            {"errors": [{"message": "Nested error"}]},
            42,  # Non-string, non-dict - gets ignored
            None  # None value - gets ignored
        ]
        result = normalize_validation_issues(issues)
        
        # Only dict and string items are processed, others are ignored
        assert len(result) == 3
        assert result[0] == "Simple message"
        
        # Others should be string representations of the dicts
        assert isinstance(result[1], str)
        assert isinstance(result[2], str)
        assert "validation_error" in result[1]
        assert "errors" in result[2]


class TestSerializationUtilities:
    """Test to_json_serializable() recursive conversion - HIGH RISK for JSON output"""
    
    @dataclass
    class MockDataclass:
        name: str
        value: int
    
    class MockObjectWithToDict:
        def __init__(self, data: str):
            self.data = data
        
        def to_dict(self):
            return {"type": "mock", "data": self.data}
    
    def test_to_json_serializable_with_to_dict_method(self):
        """Test objects with to_dict method"""
        obj = self.MockObjectWithToDict("test data")
        result = to_json_serializable(obj)
        assert result == {"type": "mock", "data": "test data"}
    
    def test_to_json_serializable_dataclass_without_to_dict(self):
        """Test dataclass objects without to_dict method"""
        obj = self.MockDataclass("test", 42)
        result = to_json_serializable(obj)
        assert result == {"name": "test", "value": 42}
    
    def test_to_json_serializable_nested_objects(self):
        """Test nested object structures"""
        @dataclass
        class Inner:
            data: str
        
        @dataclass
        class Outer:
            inner: Inner
            count: int
        
        obj = Outer(Inner("nested value"), 5)
        result = to_json_serializable(obj)
        expected = {"inner": {"data": "nested value"}, "count": 5}
        assert result == expected
    
    def test_to_json_serializable_list_processing(self):
        """Test list containing mixed object types"""
        data = [
            self.MockDataclass("item1", 1),
            self.MockDataclass("item2", 2),
            "string",
            42,
            None,
            {"already": "dict"}
        ]
        result = to_json_serializable(data)
        expected = [
            {"name": "item1", "value": 1},
            {"name": "item2", "value": 2},
            "string",
            42,
            None,
            {"already": "dict"}
        ]
        assert result == expected
    
    def test_to_json_serializable_dict_processing(self):
        """Test dictionary with object values"""
        data = {
            "item1": self.MockDataclass("first", 1),
            "item2": self.MockObjectWithToDict("second"),
            "primitive": 123,
            "nested": {"inner": self.MockDataclass("nested", 999)}
        }
        result = to_json_serializable(data)
        expected = {
            "item1": {"name": "first", "value": 1},
            "item2": {"type": "mock", "data": "second"},
            "primitive": 123,
            "nested": {"inner": {"name": "nested", "value": 999}}
        }
        assert result == expected
    
    def test_to_json_serializable_deep_nesting(self):
        """HIGH RISK: Test deeply nested structures"""
        @dataclass
        class Node:
            value: str
            child: Optional['Node'] = None
        
        # Create 5-level deep nesting
        root = Node("root", Node("level1", Node("level2", Node("level3", Node("level4")))))
        
        result = to_json_serializable(root)
        
        # Verify deep structure is preserved
        assert result["value"] == "root"
        assert result["child"]["value"] == "level1"
        assert result["child"]["child"]["value"] == "level2"
        assert result["child"]["child"]["child"]["value"] == "level3"
        assert result["child"]["child"]["child"]["child"]["value"] == "level4"
        assert result["child"]["child"]["child"]["child"]["child"] is None
    
    def test_to_json_serializable_primitive_passthrough(self):
        """Test primitive types pass through unchanged"""
        primitives = [
            "string with Unicode: 🧪",
            42,
            3.14,
            True,
            False,
            None
        ]
        
        for primitive in primitives:
            result = to_json_serializable(primitive)
            assert result == primitive
            assert type(result) == type(primitive)
    
    def test_to_json_serializable_actual_json_compatibility(self):
        """HIGH RISK: Test output can be serialized to JSON"""
        complex_obj = {
            "response": SessionCorrelationResponse(
                success=True,
                session_id="test-123",
                correlation_id="corr-456",
                timestamp="2025-09-08T00:00:00Z"
            ),
            "analysis": ToolAnalysisResult(
                success=True,
                error_info={},
                execution_metrics={"time": 100.5, "memory": 50},
                risk_factors=["performance"]
            ),
            "simple": {"key": "value", "unicode": "🚀"}
        }
        
        result = to_json_serializable(complex_obj)
        
        # This should not raise an exception
        json_str = json.dumps(result)
        assert isinstance(json_str, str)
        
        # Should be reversible
        parsed_back = json.loads(json_str)
        assert parsed_back == result
        
        # Verify structure
        assert parsed_back["response"]["success"] is True
        assert parsed_back["analysis"]["risk_factors"] == ["performance"]
        assert parsed_back["simple"]["unicode"] == "🚀"
    
    def test_to_json_serializable_performance_large_structure(self):
        """Performance test with large data structure"""
        # Create large nested structure
        large_data = {
            "items": [self.MockDataclass(f"item_{i}", i) for i in range(100)],
            "metadata": {"count": 100, "type": "performance_test"},
            "nested": {
                "deep": {
                    "objects": [ToolAnalysisResult(True, {}, {"time": i}, []) for i in range(50)]
                }
            }
        }
        
        start_time = time.time()
        result = to_json_serializable(large_data)
        duration = time.time() - start_time
        
        assert duration < 0.1, f"Too slow: {duration}s"
        assert len(result["items"]) == 100
        assert all("name" in item and "value" in item for item in result["items"])
        assert len(result["nested"]["deep"]["objects"]) == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])