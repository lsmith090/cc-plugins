#!/usr/bin/env python3
"""
Unit tests for core transcript processing functions.

Tests individual functions in transcript_processor.py for correctness,
edge cases, and performance characteristics.
"""

import json
import pytest
import tempfile
from pathlib import Path
from collections import deque
import sys
import os

# Add src/hooks/templates to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../src/hooks/templates'))

from transcript_processor import (
    remove_prework_entries,
    clean_transcript_entries,
    get_token_count,
    chunk_transcript,
    extract_subagent_type,
    detect_project_structure
)


class TestTokenCounting:
    """Test token counting functionality."""
    
    def test_counts_simple_text(self):
        """Test token counting for simple text."""
        text = "Hello world, this is a test."
        count = get_token_count(text)
        
        # Should return reasonable token count (typically 8-10 tokens)
        assert isinstance(count, int)
        assert 5 <= count <= 15
    
    def test_counts_empty_text(self):
        """Test token counting for empty text."""
        assert get_token_count("") == 0
    
    def test_counts_code_content(self):
        """Test token counting for code content."""
        code = """
        def test_function():
            return "Hello world"
        """
        count = get_token_count(code)
        
        # Code should have reasonable token count
        assert isinstance(count, int)
        assert count > 10


class TestRemovePrework:
    """Test pre-work removal logic."""
    
    def test_removes_content_before_first_edit_tool(self):
        """Test that content before first Edit tool is removed."""
        # Format must match actual transcript structure with message wrapper
        transcript = [
            {"message": {"role": "user", "content": "Hello"}},
            {"message": {"role": "assistant", "content": "Hi there"}},
            {"message": {"role": "assistant", "content": [{"type": "tool_use", "name": "Edit"}]}},
            {"message": {"role": "tool", "content": "File edited"}},
            {"message": {"role": "assistant", "content": "Done"}}
        ]
        
        result = remove_prework_entries(transcript)
        
        # Should start from the Edit tool call
        assert len(result) == 3
        assert result[0]["message"]["content"][0]["name"] == "Edit"
    
    def test_handles_empty_transcript(self):
        """Test handling of empty transcript."""
        result = remove_prework_entries([])
        assert result == []
    
    def test_returns_empty_if_no_target_tools(self):
        """Test that empty list is returned if no target tools found."""
        transcript = [
            {"message": {"role": "user", "content": "Hello"}},
            {"message": {"role": "assistant", "content": [{"type": "tool_use", "name": "Read"}]}}
        ]
        
        result = remove_prework_entries(transcript)
        assert result == []  # Function returns empty if no Edit/MultiEdit/Write tools found


class TestCleanTranscriptEntries:
    """Test transcript cleaning functionality."""
    
    def test_converts_to_simple_format(self):
        """Test conversion to simple {role, content} format."""
        transcript = [
            {"message": {"role": "user", "content": "Hello"}},
            {"message": {"role": "assistant", "content": "Hi there"}}
        ]
        
        result = clean_transcript_entries(transcript)
        
        # Should return a deque with simple format
        assert isinstance(result, deque)
        result_list = list(result)
        assert len(result_list) == 2
        assert result_list[0]["role"] == "user"
        assert result_list[0]["content"] == "Hello"
    
    def test_filters_only_user_and_assistant(self):
        """Test that only user and assistant messages are included."""
        transcript = [
            {"message": {"role": "user", "content": "Hello"}},
            {"message": {"role": "tool", "content": "Tool result"}},
            {"message": {"role": "assistant", "content": "Hi there"}}
        ]
        
        result = clean_transcript_entries(transcript)
        result_list = list(result)
        
        # Should only have user and assistant messages
        assert len(result_list) == 2
        assert result_list[0]["role"] == "user"
        assert result_list[1]["role"] == "assistant"


class TestExtractSubagentType:
    """Test subagent type extraction."""
    
    def test_extracts_from_tool_input(self):
        """Test extraction from tool input data."""
        input_data = {
            "tool_input": {
                "subagent_type": "test-agent"
            }
        }
        
        result = extract_subagent_type([], input_data)
        assert result == "test-agent"
    
    def test_defaults_to_shared_for_empty_data(self):
        """Test default fallback to 'shared'."""
        result = extract_subagent_type([], None)
        assert result == "shared"
    
    def test_extracts_from_transcript_task_call(self):
        """Test extraction from Task tool call in transcript."""
        transcript = [
            {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "tool_use",
                            "name": "Task",
                            "input": {
                                "subagent_type": "context-gathering"
                            }
                        }
                    ]
                }
            }
        ]
        
        result = extract_subagent_type(transcript)
        assert result == "context-gathering"


class TestChunkTranscript:
    """Test transcript chunking functionality."""
    
    def test_creates_single_chunk_for_small_transcript(self):
        """Test that small transcripts create a single chunk."""
        clean_transcript = deque([
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ])
        
        chunks = chunk_transcript(clean_transcript, max_tokens=18000)
        
        assert len(chunks) == 1
        assert len(chunks[0]) == 2
    
    def test_splits_large_transcript_into_chunks(self):
        """Test that large transcripts are split appropriately."""
        # Create a large transcript
        large_content = "This is a very long message. " * 1000  # ~6000+ tokens
        clean_transcript = deque([
            {"role": "user", "content": large_content},
            {"role": "assistant", "content": large_content},
            {"role": "user", "content": large_content}
        ])
        
        chunks = chunk_transcript(clean_transcript, max_tokens=5000)
        
        # Should create multiple chunks
        assert len(chunks) > 1
        
        # Each chunk should contain complete messages
        for chunk in chunks:
            for message in chunk:
                assert "role" in message
                assert "content" in message
    
    def test_handles_empty_transcript(self):
        """Test handling of empty transcript for chunking."""
        chunks = chunk_transcript(deque([]), max_tokens=18000)
        assert len(chunks) == 0  # Empty transcript should result in no chunks


class TestDetectProjectStructure:
    """Test project structure detection."""
    
    def test_detects_single_service_project(self):
        """Test detection of single service project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create a simple Python project
            (project_root / "pyproject.toml").touch()
            (project_root / "CLAUDE.md").touch()
            
            result = detect_project_structure(project_root)
            
            assert result["project_type"] == "single_service"
            assert len(result["services"]) == 1
            assert result["services"][0]["type"] == "python"


class TestPerformanceCharacteristics:
    """Test performance characteristics of core functions."""
    
    def test_token_counting_performance(self):
        """Test token counting performance with large text."""
        import time
        
        large_text = "This is a test message. " * 5000  # ~20k+ tokens
        
        start_time = time.time()
        count = get_token_count(large_text)
        end_time = time.time()
        
        # Should complete quickly
        assert (end_time - start_time) < 0.5  # Less than 500ms
        assert count > 10000  # Should count reasonable number of tokens


if __name__ == "__main__":
    pytest.main([__file__, "-v"])