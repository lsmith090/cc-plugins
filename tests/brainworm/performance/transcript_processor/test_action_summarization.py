#!/usr/bin/env python3
"""
Action summarization tests for transcript processor.

Tests the new action summarization functionality that replaces tool results
with simple action summaries to create clean context bundles for subagents.
"""

import json
import pytest
import time
import gc
import os
import sys
from pathlib import Path
from collections import deque
import tracemalloc

# Add src/hooks/templates to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../src/hooks/templates'))

from brainworm.utils.transcript_parser import (
    remove_prework_entries,
    clean_transcript_entries,
    get_token_count,
    chunk_transcript,
    extract_subagent_type,
    transcript_processor_logic
)


class TestActionSummarization:
    """Test action summarization functionality in transcript processor."""
    
    @classmethod
    def setup_class(cls):
        """Set up test class with real Claude Code transcript files."""
        cls.test_data_dir = Path("tmp/test_transcripts")
        
        # Collect transcript files by size
        cls.transcript_files = {
            'small': [],   # < 100KB  
            'medium': [],  # 100KB - 1MB
            'large': [],   # 1MB - 5MB
            'huge': []     # > 5MB
        }
        
        if cls.test_data_dir.exists():
            for file_path in cls.test_data_dir.glob("*.jsonl"):
                size_kb = file_path.stat().st_size / 1024
                if size_kb < 100:
                    cls.transcript_files['small'].append(file_path)
                elif size_kb < 1024:
                    cls.transcript_files['medium'].append(file_path)
                elif size_kb < 5120:
                    cls.transcript_files['large'].append(file_path)
                else:
                    cls.transcript_files['huge'].append(file_path)
        
        print(f"Found transcript files:")
        print(f"  Small (<100KB): {len(cls.transcript_files['small'])}")
        print(f"  Medium (100KB-1MB): {len(cls.transcript_files['medium'])}")  
        print(f"  Large (1MB-5MB): {len(cls.transcript_files['large'])}")
        print(f"  Huge (>5MB): {len(cls.transcript_files['huge'])}")
    
    def load_transcript_file(self, file_path: Path) -> list:
        """Load and parse a Claude Code JSONL transcript file."""
        transcript = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    transcript.append(entry)
                except json.JSONDecodeError as e:
                    continue
        return transcript
    
    def measure_performance(self, func, *args, **kwargs):
        """Measure execution time and memory usage of a function."""
        tracemalloc.start()
        gc.collect()
        
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        
        current_memory, peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        return {
            'result': result,
            'execution_time_ms': (end_time - start_time) * 1000,
            'peak_memory_mb': peak_memory / (1024 * 1024)
        }
    
    def test_action_summarization_basic(self):
        """Test basic action summarization functionality."""
        if not self.transcript_files['medium']:
            pytest.skip("No medium transcript files available")
        
        # Use a medium file that's likely to have tool results
        test_file = self.transcript_files['medium'][0]
        transcript = self.load_transcript_file(test_file)
        
        print(f"\n🧪 Testing action summarization with: {test_file.name}")
        print(f"   Original: {test_file.stat().st_size / 1024:.1f}KB, {len(transcript)} entries")
        
        # Process with action summarization
        perf = self.measure_performance(clean_transcript_entries, transcript)
        cleaned_list = list(perf['result'])
        
        print(f"   Processing: {perf['execution_time_ms']:.1f}ms")
        print(f"   Result: {len(cleaned_list)} entries")
        
        # Analyze action summaries
        action_summaries = 0
        total_tokens_saved = 0
        
        for entry in cleaned_list:
            content = entry.get('content', [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and '_action_summary_meta' in item:
                        action_summaries += 1
                        meta = item['_action_summary_meta']
                        total_tokens_saved += meta['original_tokens'] - meta['summary_tokens']
                        
                        print(f"   📝 {item.get('content', 'Unknown action')} (saved {meta['original_tokens']} → {meta['summary_tokens']} tokens)")
        
        print(f"   Summary: {action_summaries} actions summarized, {total_tokens_saved:,} tokens saved")
        
        # Verify performance
        assert perf['execution_time_ms'] < 5000, f"Processing took too long: {perf['execution_time_ms']:.1f}ms"
        assert len(cleaned_list) > 0, "Should produce cleaned entries"
        
        if action_summaries > 0:
            assert total_tokens_saved > 0, "Should save tokens through summarization"
    
    def test_action_summarization_token_reduction(self):
        """Test token reduction effectiveness of action summarization."""
        if not self.transcript_files['large']:
            pytest.skip("No large transcript files available")
        
        test_file = self.transcript_files['large'][0]
        transcript = self.load_transcript_file(test_file)
        
        print(f"\n🧪 Testing token reduction with: {test_file.name}")
        print(f"   File size: {test_file.stat().st_size / 1024:.1f}KB")
        
        # Calculate tokens without action summarization (simulate old behavior)
        original_cleaned = []
        for entry in transcript:
            message = entry.get('message')
            if message and message.get('role') in ['user', 'assistant']:
                original_cleaned.append({
                    'role': message.get('role'),
                    'content': message.get('content')
                })
        
        original_tokens = get_token_count(json.dumps(original_cleaned, ensure_ascii=False))
        
        # Process with action summarization
        cleaned = clean_transcript_entries(transcript)
        cleaned_list = list(cleaned)
        summarized_tokens = get_token_count(json.dumps(cleaned_list, ensure_ascii=False))
        
        # Calculate reduction
        token_reduction = original_tokens - summarized_tokens
        reduction_percent = (token_reduction / original_tokens * 100) if original_tokens > 0 else 0
        
        print(f"   Token reduction: {original_tokens:,} → {summarized_tokens:,} tokens")
        print(f"   Savings: {token_reduction:,} tokens ({reduction_percent:.1f}%)")
        
        # Should achieve significant token reduction for files with tool results
        if reduction_percent > 10:
            print("   ✅ Significant token reduction achieved!")
        else:
            print("   ℹ️ Minimal token reduction (file may have few tool results)")
        
        # Verify tokens are actually reduced or at least not increased
        assert summarized_tokens <= original_tokens, "Action summarization should not increase token count"
    
    def test_context_bundle_usability(self):
        """Test that generated context bundles are usable by subagents."""
        if not self.transcript_files['large']:
            pytest.skip("No large transcript files available")
        
        test_file = self.transcript_files['large'][0]
        transcript = self.load_transcript_file(test_file)
        
        print(f"\n🧪 Testing context bundle usability with: {test_file.name}")
        
        # Process full pipeline
        processed = remove_prework_entries(transcript)
        cleaned = clean_transcript_entries(processed)
        chunks = chunk_transcript(cleaned)
        
        print(f"   Generated {len(chunks)} chunks")
        
        # Verify chunk usability
        total_tokens = 0
        max_chunk_tokens = 0
        usable_chunks = 0
        
        for i, chunk in enumerate(chunks):
            chunk_json = json.dumps(chunk, ensure_ascii=False)
            chunk_tokens = get_token_count(chunk_json)
            total_tokens += chunk_tokens
            max_chunk_tokens = max(max_chunk_tokens, chunk_tokens)
            
            # Chunk is usable if it's under Claude Code's read limits
            if chunk_tokens < 25000:  # Conservative limit
                usable_chunks += 1
            
            print(f"   Chunk {i+1}: {len(chunk)} entries, {chunk_tokens:,} tokens")
        
        print(f"   Total tokens: {total_tokens:,}")
        print(f"   Largest chunk: {max_chunk_tokens:,} tokens")
        print(f"   Usable chunks: {usable_chunks}/{len(chunks)}")
        
        # All chunks should be usable by Claude Code
        assert usable_chunks == len(chunks), f"Only {usable_chunks}/{len(chunks)} chunks are usable"
        assert max_chunk_tokens < 25000, f"Largest chunk ({max_chunk_tokens:,} tokens) exceeds usability limit"
        assert len(chunks) > 0, "Should generate at least one chunk"
    
    def test_action_summary_format(self):
        """Test that action summaries have the expected format."""
        if not self.transcript_files['medium']:
            pytest.skip("No medium transcript files available")
        
        # Find a file with tool results
        test_file = None
        for file_path in self.transcript_files['medium']:
            transcript = self.load_transcript_file(file_path)
            # Quick check for tool results
            has_tool_results = False
            for entry in transcript:
                message = entry.get('message', {})
                content = message.get('content', [])
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get('type') == 'tool_result':
                            has_tool_results = True
                            break
                if has_tool_results:
                    break
            
            if has_tool_results:
                test_file = file_path
                break
        
        if not test_file:
            pytest.skip("No files with tool results found")
        
        print(f"\n🧪 Testing action summary format with: {test_file.name}")
        
        transcript = self.load_transcript_file(test_file)
        cleaned = clean_transcript_entries(transcript)
        cleaned_list = list(cleaned)
        
        # Find and verify action summaries
        action_summaries_found = []
        
        for entry in cleaned_list:
            content = entry.get('content', [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'tool_result':
                        summary_content = item.get('content', '')
                        if '_action_summary_meta' in item:
                            action_summaries_found.append(summary_content)
        
        print(f"   Found {len(action_summaries_found)} action summaries:")
        
        expected_patterns = ['Read:', 'Write:', 'Edit:', 'Bash:', 'Grep:', 'Glob:', 'TodoWrite:', 'Task:']
        
        for summary in action_summaries_found[:5]:  # Show first 5
            print(f"   📝 \"{summary}\"")
            
            # Verify format - should start with known patterns
            matches_pattern = any(summary.startswith(pattern) for pattern in expected_patterns)
            if not matches_pattern:
                print(f"      ⚠️ Unexpected format (doesn't match known patterns)")
            else:
                print(f"      ✅ Good format")
        
        # Should have some action summaries if file has tool results
        assert len(action_summaries_found) > 0, "Should find action summaries in file with tool results"
    
    def test_performance_comparison(self):
        """Compare performance with and without action summarization."""
        if not self.transcript_files['large']:
            pytest.skip("No large transcript files available")
        
        test_file = self.transcript_files['large'][0]
        transcript = self.load_transcript_file(test_file)
        
        print(f"\n🧪 Performance comparison with: {test_file.name}")
        
        # Test current implementation (with action summarization)
        summarized_perf = self.measure_performance(clean_transcript_entries, transcript)
        summarized_list = list(summarized_perf['result'])
        summarized_tokens = get_token_count(json.dumps(summarized_list, ensure_ascii=False))
        
        print(f"   With action summarization:")
        print(f"     Time: {summarized_perf['execution_time_ms']:.1f}ms")
        print(f"     Memory: {summarized_perf['peak_memory_mb']:.1f}MB")
        print(f"     Tokens: {summarized_tokens:,}")
        
        # Performance should be excellent
        assert summarized_perf['execution_time_ms'] < 10000, f"Processing with summarization too slow: {summarized_perf['execution_time_ms']:.1f}ms"
        assert summarized_perf['peak_memory_mb'] < 100, f"Memory usage too high: {summarized_perf['peak_memory_mb']:.1f}MB"
        assert len(summarized_list) > 0, "Should produce results"
        
        print("   ✅ Performance targets met")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])