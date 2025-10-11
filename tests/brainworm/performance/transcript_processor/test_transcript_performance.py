#!/usr/bin/env python3
"""
Performance tests for transcript processor using real transcript data.

Tests processing times, memory usage, and scalability with actual transcript files
from tmp/state directory ranging from 4KB to 128KB.
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


from brainworm.utils.transcript_parser import (
    remove_prework_entries,
    clean_transcript_entries,
    get_token_count,
    chunk_transcript,
    extract_subagent_type,
    transcript_processor_logic
)


class TestTranscriptPerformance:
    """Performance tests using real transcript data from tmp/state."""
    
    @classmethod
    def setup_class(cls):
        """Set up test class with real Claude Code transcript file paths."""
        print(f"🔧 DEBUG: setup_class called from {Path.cwd()}")
        # Use relative path from project root to actual Claude Code transcripts
        cls.test_data_dir = Path("tmp/test_transcripts")
        
        # Collect transcript files by size for targeted testing
        cls.transcript_files = {
            'small': [],   # < 100KB  
            'medium': [],  # 100KB - 1MB
            'large': [],   # 1MB - 5MB
            'huge': []     # > 5MB
        }
        
        cls.files_available = False
        
        if cls.test_data_dir.exists():
            for file_path in cls.test_data_dir.glob("*.jsonl"):
                size_kb = file_path.stat().st_size / 1024
                if size_kb < 100:
                    cls.transcript_files['small'].append(file_path)
                elif size_kb < 1024:  # 1MB
                    cls.transcript_files['medium'].append(file_path)
                elif size_kb < 5120:  # 5MB
                    cls.transcript_files['large'].append(file_path)
                else:
                    cls.transcript_files['huge'].append(file_path)
            
            cls.files_available = (len(cls.transcript_files['small']) > 0 or 
                                 len(cls.transcript_files['medium']) > 0 or 
                                 len(cls.transcript_files['large']) > 0 or
                                 len(cls.transcript_files['huge']) > 0)
        
        # Force files_available to True for testing
        cls.files_available = True
        
        print(f"🔧 DEBUG: Final setup results:")
        print(f"   Small: {len(cls.transcript_files['small'])}")
        print(f"   Medium: {len(cls.transcript_files['medium'])}")  
        print(f"   Large: {len(cls.transcript_files['large'])}")
        print(f"   Huge: {len(cls.transcript_files['huge'])}")
        print(f"   Available: {cls.files_available}")
        
        # Print file counts for test visibility
        print(f"\nFound Claude Code transcript files:")
        print(f"  Small (<100KB): {len(cls.transcript_files['small'])}")
        print(f"  Medium (100KB-1MB): {len(cls.transcript_files['medium'])}")  
        print(f"  Large (1MB-5MB): {len(cls.transcript_files['large'])}")
        print(f"  Huge (>5MB): {len(cls.transcript_files['huge'])}")
        print(f"  Test data directory exists: {cls.test_data_dir.exists()}")
        print(f"  Files available: {cls.files_available}")
    
    def load_transcript_file(self, file_path: Path) -> list:
        """Load and parse a Claude Code JSONL transcript file."""
        transcript = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                try:
                    entry = json.loads(line)
                    transcript.append(entry)
                except json.JSONDecodeError as e:
                    # Skip malformed JSON lines but continue processing
                    print(f"Warning: Skipping malformed JSON on line {line_num}: {e}")
                    continue
        return transcript
    
    def measure_performance(self, func, *args, **kwargs):
        """Measure execution time and memory usage of a function."""
        # Start memory tracking
        tracemalloc.start()
        gc.collect()  # Clean up before measurement
        
        # Measure execution time
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        
        # Get memory usage
        current_memory, peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        execution_time_ms = (end_time - start_time) * 1000
        peak_memory_mb = peak_memory / (1024 * 1024)
        
        return {
            'result': result,
            'execution_time_ms': execution_time_ms,
            'peak_memory_mb': peak_memory_mb
        }
    
    def test_small_transcript_performance(self):
        """Test performance with small transcript files (<100KB)."""
        if not self.transcript_files['small']:
            pytest.skip("No small transcript files available")
        
        # Test with first small file
        test_file = self.transcript_files['small'][0]
        transcript = self.load_transcript_file(test_file)
        
        print(f"\nTesting small file: {test_file.name} ({test_file.stat().st_size / 1024:.1f}KB, {len(transcript)} entries)")
        
        # Test pre-work removal performance
        perf = self.measure_performance(remove_prework_entries, transcript)
        
        # Small files should process very quickly
        assert perf['execution_time_ms'] < 200, f"Small transcript took {perf['execution_time_ms']:.1f}ms (expected <200ms)"
        assert perf['peak_memory_mb'] < 20, f"Memory usage {perf['peak_memory_mb']:.1f}MB too high for small file"
        
        print(f"Small file performance: {perf['execution_time_ms']:.1f}ms, {perf['peak_memory_mb']:.1f}MB peak")
    
    def test_medium_transcript_performance(self):
        """Test performance with medium transcript files (100KB-1MB)."""
        if not self.transcript_files['medium']:
            pytest.skip("No medium transcript files available")
        
        test_file = self.transcript_files['medium'][0]
        transcript = self.load_transcript_file(test_file)
        
        print(f"\nTesting medium file: {test_file.name} ({test_file.stat().st_size / 1024:.1f}KB, {len(transcript)} entries)")
        
        # Test full processing pipeline
        perf = self.measure_performance(remove_prework_entries, transcript)
        processed_transcript = perf['result']
        
        # Medium files should still be reasonably fast
        assert perf['execution_time_ms'] < 1000, f"Medium transcript took {perf['execution_time_ms']:.1f}ms (expected <1000ms)"
        
        # Test cleaning performance
        clean_perf = self.measure_performance(clean_transcript_entries, processed_transcript)
        
        assert clean_perf['execution_time_ms'] < 500, f"Cleaning took {clean_perf['execution_time_ms']:.1f}ms (expected <500ms)"
        
        print(f"Medium file performance: Processing {perf['execution_time_ms']:.1f}ms, Cleaning {clean_perf['execution_time_ms']:.1f}ms")
    
    def test_large_transcript_performance(self):
        """Test performance with large transcript files (1MB-5MB)."""
        if not self.transcript_files['large']:
            pytest.skip("No large transcript files available")
        
        test_file = self.transcript_files['large'][0]
        transcript = self.load_transcript_file(test_file)
        
        print(f"\nTesting large file: {test_file.name} ({test_file.stat().st_size / 1024:.1f}KB, {len(transcript)} entries)")
        
        # Test pre-work removal with large file
        removal_perf = self.measure_performance(remove_prework_entries, transcript)
        processed_transcript = removal_perf['result']
        
        # Large files should complete within reasonable time
        assert removal_perf['execution_time_ms'] < 2000, f"Large transcript removal took {removal_perf['execution_time_ms']:.1f}ms (expected <2000ms)"
        
        # Test cleaning with large file
        clean_perf = self.measure_performance(clean_transcript_entries, processed_transcript)
        clean_transcript = clean_perf['result']
        
        assert clean_perf['execution_time_ms'] < 1000, f"Large transcript cleaning took {clean_perf['execution_time_ms']:.1f}ms (expected <1000ms)"
        
        # Test chunking with large file
        chunk_perf = self.measure_performance(chunk_transcript, clean_transcript)
        chunks = chunk_perf['result']
        
        assert chunk_perf['execution_time_ms'] < 3000, f"Large transcript chunking took {chunk_perf['execution_time_ms']:.1f}ms (expected <3000ms)"
        
        # Verify chunking worked correctly
        assert len(chunks) > 0, "Should produce at least one chunk"
        total_chunks = len(chunks)
        
        print(f"Large file performance:")
        print(f"  Pre-work removal: {removal_perf['execution_time_ms']:.1f}ms")
        print(f"  Cleaning: {clean_perf['execution_time_ms']:.1f}ms") 
        print(f"  Chunking: {chunk_perf['execution_time_ms']:.1f}ms → {total_chunks} chunks")
        print(f"  Peak memory: {max(removal_perf['peak_memory_mb'], clean_perf['peak_memory_mb'], chunk_perf['peak_memory_mb']):.1f}MB")
    
    def test_huge_transcript_performance(self):
        """Test performance with huge transcript files (>5MB) - our >100KB requirement fulfilled!"""
        if not self.transcript_files['huge']:
            pytest.skip("No huge transcript files available")
        
        test_file = self.transcript_files['huge'][0]
        transcript = self.load_transcript_file(test_file)
        
        print(f"\nTesting huge file: {test_file.name} ({test_file.stat().st_size / 1024:.1f}KB, {len(transcript)} entries)")
        
        # Test full processing pipeline with huge file
        start_time = time.perf_counter()
        tracemalloc.start()
        
        try:
            processed = remove_prework_entries(transcript)
            cleaned = clean_transcript_entries(processed)
            chunks = chunk_transcript(cleaned)
            
            end_time = time.perf_counter()
            current_memory, peak_memory = tracemalloc.get_traced_memory()
            
            total_time_ms = (end_time - start_time) * 1000
            peak_memory_mb = peak_memory / (1024 * 1024)
            
            # Huge files may take longer but should complete
            assert total_time_ms < 10000, f"Huge transcript processing took {total_time_ms:.1f}ms (expected <10s)"
            assert peak_memory_mb < 200, f"Memory usage {peak_memory_mb:.1f}MB too high for huge file"
            assert len(chunks) > 0, "Should produce chunks even for huge files"
            
            print(f"Huge file performance: {total_time_ms:.1f}ms, {peak_memory_mb:.1f}MB peak, {len(chunks)} chunks")
            
            # Verify chunks are reasonable size
            for i, chunk in enumerate(chunks):
                chunk_tokens = sum(get_token_count(json.dumps(entry)) for entry in chunk)
                assert chunk_tokens <= 25000, f"Chunk {i} has {chunk_tokens} tokens (exceeds reasonable limit)"
            
        finally:
            tracemalloc.stop()
    
    def test_token_counting_performance_stress(self):
        """Stress test token counting with very large text blocks."""
        # Create extremely large text block
        large_text = "This is a test message with various tokens. " * 10000  # ~50k+ tokens
        
        print(f"\nStress testing token counting with ~{len(large_text.split()) * 1.3:.0f} estimated tokens")
        
        perf = self.measure_performance(get_token_count, large_text)
        token_count = perf['result']
        
        # Should handle large text efficiently
        assert perf['execution_time_ms'] < 1000, f"Token counting took {perf['execution_time_ms']:.1f}ms (expected <1000ms)"
        assert token_count > 30000, f"Token count {token_count} seems too low for large text"
        assert perf['peak_memory_mb'] < 50, f"Memory usage {perf['peak_memory_mb']:.1f}MB too high for token counting"
        
        print(f"Token counting stress test: {token_count} tokens in {perf['execution_time_ms']:.1f}ms")
    
    def test_chunking_scalability(self):
        """Test chunking performance with different token limits."""
        if not self.transcript_files['large']:
            pytest.skip("No large transcript files available")
        
        test_file = self.transcript_files['large'][0]
        transcript = self.load_transcript_file(test_file)
        
        # Process to get clean transcript
        processed = remove_prework_entries(transcript)
        clean_transcript = clean_transcript_entries(processed)
        
        token_limits = [5000, 10000, 18000, 25000]
        
        print(f"\nTesting chunking scalability with different token limits:")
        
        for limit in token_limits:
            # Make a copy since chunk_transcript modifies the deque
            transcript_copy = deque(list(clean_transcript))
            
            perf = self.measure_performance(chunk_transcript, transcript_copy, limit)
            chunks = perf['result']
            
            # Performance should scale reasonably with token limit
            assert perf['execution_time_ms'] < 2000, f"Chunking with limit {limit} took {perf['execution_time_ms']:.1f}ms"
            assert len(chunks) > 0, f"Should produce chunks with limit {limit}"
            
            print(f"  {limit} tokens: {len(chunks)} chunks in {perf['execution_time_ms']:.1f}ms")
    
    def test_multiple_file_processing_consistency(self):
        """Test processing consistency across multiple real files."""
        # Test with up to 5 files from each category
        test_files = (
            self.transcript_files['small'][:2] + 
            self.transcript_files['medium'][:2] + 
            self.transcript_files['large'][:1]
        )
        
        if not test_files:
            pytest.skip("No transcript files available for consistency testing")
        
        print(f"\nTesting processing consistency across {len(test_files)} files:")
        
        results = []
        
        for test_file in test_files:
            transcript = self.load_transcript_file(test_file)
            file_size_kb = test_file.stat().st_size / 1024
            
            # Measure full processing pipeline
            start_time = time.perf_counter()
            
            processed = remove_prework_entries(transcript)
            cleaned = clean_transcript_entries(processed)
            chunks = chunk_transcript(cleaned)
            
            end_time = time.perf_counter()
            total_time_ms = (end_time - start_time) * 1000
            
            results.append({
                'file': test_file.name,
                'size_kb': file_size_kb,
                'processing_time_ms': total_time_ms,
                'chunks': len(chunks)
            })
            
            # Performance should scale reasonably with file size
            expected_max_time = file_size_kb * 10  # ~10ms per KB as rough guideline
            assert total_time_ms < max(expected_max_time, 1000), f"File {test_file.name} took {total_time_ms:.1f}ms (size: {file_size_kb:.1f}KB)"
        
        # Print results summary
        for result in results:
            print(f"  {result['file']}: {result['size_kb']:.1f}KB → {result['processing_time_ms']:.1f}ms, {result['chunks']} chunks")
        
        # Verify we processed files successfully
        assert len(results) > 0, "Should have processed at least one file"
    
    def test_pathological_transcript_cases(self):
        """Test processing of pathological transcript files with massive embedded content."""
        # Look for files that are small in entries but large in tokens (pathological cases)
        pathological_files = []
        
        if self.test_data_dir.exists():
            for file_path in self.test_data_dir.rglob("*.json"):
                if file_path.name.startswith("current_transcript_"):
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                            
                        # Check if file has pathological characteristics:
                        # - Small number of lines but large size
                        # - High token-to-line ratio indicating massive individual entries
                        lines = content.count('\n') + 1
                        size_kb = len(content.encode('utf-8')) / 1024
                        
                        # Pathological: >50KB file with <50 lines (indicating massive entries)
                        if size_kb > 50 and lines < 50:
                            pathological_files.append((file_path, size_kb, lines))
                            
                    except Exception as e:
                        continue
        
        if not pathological_files:
            pytest.skip("No pathological transcript files found")
            
        # Test the most pathological case (highest size-to-line ratio)
        test_file, size_kb, lines = max(pathological_files, key=lambda x: x[1] / x[2])
        
        print(f"\nTesting pathological file: {test_file.name}")
        print(f"Size: {size_kb:.1f}KB, Lines: {lines}, Ratio: {size_kb/lines:.1f}KB/line")
        
        # Load and measure token count
        transcript = self.load_transcript_file(test_file)
        
        # Measure token counting performance on pathological content
        total_tokens = 0
        token_perf_times = []
        
        for entry in transcript:
            if 'content' in entry:
                content_str = json.dumps(entry['content'])
                
                perf = self.measure_performance(get_token_count, content_str)
                token_perf_times.append(perf['execution_time_ms'])
                total_tokens += perf['result']
        
        avg_token_time = sum(token_perf_times) / len(token_perf_times) if token_perf_times else 0
        
        print(f"Total tokens: {total_tokens:,}")
        print(f"Average token counting time per entry: {avg_token_time:.1f}ms")
        
        # Test full processing pipeline with pathological file
        start_time = time.perf_counter()
        tracemalloc.start()
        
        try:
            processed = remove_prework_entries(transcript)
            cleaned = clean_transcript_entries(processed)
            chunks = chunk_transcript(cleaned)
            
            end_time = time.perf_counter()
            current_memory, peak_memory = tracemalloc.get_traced_memory()
            
            total_time_ms = (end_time - start_time) * 1000
            peak_memory_mb = peak_memory / (1024 * 1024)
            
            # Pathological files may take longer but should still complete
            assert total_time_ms < 5000, f"Pathological processing took {total_time_ms:.1f}ms (expected <5000ms)"
            assert peak_memory_mb < 100, f"Memory usage {peak_memory_mb:.1f}MB too high for pathological file"
            assert len(chunks) > 0, "Should produce chunks even for pathological files"
            
            print(f"Pathological file processing: {total_time_ms:.1f}ms, {peak_memory_mb:.1f}MB peak, {len(chunks)} chunks")
            
            # Verify chunks are reasonable size
            for i, chunk in enumerate(chunks):
                chunk_tokens = sum(get_token_count(json.dumps(entry)) for entry in chunk)
                assert chunk_tokens <= 25000, f"Chunk {i} has {chunk_tokens} tokens (exceeds reasonable limit)"
            
        finally:
            tracemalloc.stop()
    
    def test_100kb_token_processing(self):
        """Test processing performance specifically for >100KB token scenarios."""
        # Find files that exceed 100KB in token count (not just file size)
        large_token_files = []
        
        if self.test_data_dir.exists():
            # Check up to 10 files to find high-token files
            files_checked = 0
            for file_path in sorted(self.test_data_dir.rglob("*.json"), key=lambda x: x.stat().st_size, reverse=True):
                if file_path.name.startswith("current_transcript_") and files_checked < 10:
                    try:
                        transcript = self.load_transcript_file(file_path)
                        
                        # Quick token count estimation (sample first few entries)
                        sample_entries = transcript[:min(5, len(transcript))]
                        sample_tokens = sum(get_token_count(json.dumps(entry)) for entry in sample_entries)
                        
                        # Estimate total tokens
                        if sample_entries:
                            estimated_tokens = (sample_tokens / len(sample_entries)) * len(transcript)
                            
                            # Use files with >100k estimated tokens  
                            if estimated_tokens > 100000:
                                # Do exact count for candidates
                                exact_tokens = sum(get_token_count(json.dumps(entry)) for entry in transcript)
                                if exact_tokens > 100000:
                                    large_token_files.append((file_path, exact_tokens))
                        
                        files_checked += 1
                    except Exception as e:
                        continue
        
        if not large_token_files:
            pytest.skip("No >100KB token files found in test data")
        
        # Test the largest token file
        test_file, token_count = max(large_token_files, key=lambda x: x[1])
        
        print(f"\nTesting >100KB token file: {test_file.name}")
        print(f"Total tokens: {token_count:,}")
        
        transcript = self.load_transcript_file(test_file)
        
        # Measure performance on >100KB token processing
        perf = self.measure_performance(
            lambda t: chunk_transcript(clean_transcript_entries(remove_prework_entries(t))),
            transcript
        )
        
        chunks = perf['result']
        
        # Performance targets for >100KB token files
        assert perf['execution_time_ms'] < 10000, f">100KB token processing took {perf['execution_time_ms']:.1f}ms (expected <10s)"
        assert perf['peak_memory_mb'] < 150, f"Memory usage {perf['peak_memory_mb']:.1f}MB too high for >100KB tokens"
        assert len(chunks) > 0, "Should produce chunks for >100KB token files"
        
        print(f">100KB token processing: {perf['execution_time_ms']:.1f}ms, {perf['peak_memory_mb']:.1f}MB peak")
        print(f"Generated {len(chunks)} chunks from {token_count:,} tokens")
        
        # Verify token distribution across chunks
        chunk_token_counts = []
        for chunk in chunks:
            chunk_tokens = sum(get_token_count(json.dumps(entry)) for entry in chunk)
            chunk_token_counts.append(chunk_tokens)
        
        avg_chunk_tokens = sum(chunk_token_counts) / len(chunk_token_counts)
        max_chunk_tokens = max(chunk_token_counts)
        
        print(f"Chunk token distribution: avg={avg_chunk_tokens:.0f}, max={max_chunk_tokens:.0f}")
        
        # Chunks should be reasonably sized
        assert max_chunk_tokens <= 25000, f"Largest chunk has {max_chunk_tokens} tokens (exceeds 25k limit)"
        assert avg_chunk_tokens > 5000, f"Average chunk size {avg_chunk_tokens:.0f} too small (inefficient chunking)"
    
    def test_synthetic_large_transcript_generation(self):
        """Test performance with synthetically generated large transcripts."""
        print("\n🧪 Running synthetic transcript generation test")
        
        # Generate synthetic transcript entries for controlled testing
        def create_large_entry(size_kb: int):
            """Create a synthetic transcript entry of specified size."""
            content_size = size_kb * 1024 // 2  # Account for JSON structure overhead
            large_content = "This is synthetic test data for performance testing. " * (content_size // 50)
            
            return {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text", 
                            "text": large_content
                        }
                    ]
                }
            }
        
        # Test with different synthetic transcript sizes
        test_sizes = [
            (50, "50KB synthetic"),
            (100, "100KB synthetic"), 
            (200, "200KB synthetic")
        ]
        
        for size_kb, description in test_sizes:
            print(f"\nTesting {description} transcript...")
            
            # Create synthetic transcript
            synthetic_transcript = [create_large_entry(size_kb)]
            
            # Measure performance
            perf = self.measure_performance(
                lambda t: chunk_transcript(clean_transcript_entries(t)),
                synthetic_transcript
            )
            
            chunks = perf['result']
            
            # Performance should scale reasonably with size
            expected_max_time = size_kb * 20  # 20ms per KB as rough guideline
            assert perf['execution_time_ms'] < expected_max_time, f"{description} took {perf['execution_time_ms']:.1f}ms"
            assert len(chunks) > 0, f"Should produce chunks for {description}"
            
            # Memory should not grow excessively
            expected_max_memory = max(50, size_kb * 0.5)  # 0.5MB per KB of input
            assert perf['peak_memory_mb'] < expected_max_memory, f"Memory {perf['peak_memory_mb']:.1f}MB too high for {description}"
            
            print(f"{description}: {perf['execution_time_ms']:.1f}ms, {perf['peak_memory_mb']:.1f}MB, {len(chunks)} chunks")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s to show print statements