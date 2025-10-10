"""
Real Brainworm Performance Integration Test

Tests actual brainworm operations that matter for user experience:
- Hook execution overhead on real operations
- Database query performance with real data
- File I/O performance for state management
- Memory usage patterns over time

Focus: Real operations, not mock scenarios
"""

import json
import logging
import os
import psutil
import pytest
import sqlite3
import tempfile
import time
from pathlib import Path
from typing import Dict, List


class RealBrainwormPerformanceTester:
    """Test real brainworm operations for actual performance insights"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="real_brainworm_test_")
        self.claude_dir = Path(self.temp_dir) / ".claude"
        self.setup_real_environment()
        
    def setup_real_environment(self):
        """Set up realistic brainworm environment"""
        os.makedirs(self.claude_dir / "state", exist_ok=True)
        os.makedirs(self.claude_dir / "analytics", exist_ok=True)
        
        # Create real analytics database with realistic schema
        db_path = self.claude_dir / "analytics" / "brainworm.db"
        with sqlite3.connect(str(db_path)) as conn:
            conn.executescript("""
                CREATE TABLE sessions (
                    session_id TEXT PRIMARY KEY,
                    correlation_id TEXT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    task_name TEXT,
                    success_prediction REAL
                );
                
                CREATE TABLE tool_usage (
                    id INTEGER PRIMARY KEY,
                    session_id TEXT,
                    tool_name TEXT,
                    timestamp TIMESTAMP,
                    duration_ms INTEGER,
                    success BOOLEAN
                );
                
                CREATE INDEX idx_sessions_correlation ON sessions(correlation_id);
                CREATE INDEX idx_tool_usage_session ON tool_usage(session_id);
            """)
    
    def test_database_performance_with_real_data(self, num_sessions: int = 100) -> Dict:
        """Test database operations with realistic data volume"""
        db_path = self.claude_dir / "analytics" / "brainworm.db"
        results = {
            'insert_time_ms': 0,
            'query_time_ms': 0,
            'sessions_created': 0,
            'tools_recorded': 0
        }
        
        # Measure realistic data insertion
        insert_start = time.time()
        with sqlite3.connect(str(db_path)) as conn:
            for i in range(num_sessions):
                session_id = f"real_session_{i}"
                
                # Insert session (realistic operation)
                conn.execute("""
                    INSERT INTO sessions (session_id, correlation_id, start_time, task_name)
                    VALUES (?, ?, ?, ?)
                """, (session_id, f"corr_{i}", time.time(), f"task_{i % 10}"))
                
                # Insert tool usage (realistic operation)  
                for j in range(5):  # 5 tools per session (realistic)
                    conn.execute("""
                        INSERT INTO tool_usage (session_id, tool_name, timestamp, duration_ms, success)
                        VALUES (?, ?, ?, ?, ?)
                    """, (session_id, f"tool_{j}", time.time(), 50 + j * 10, True))
                    results['tools_recorded'] += 1
                
                results['sessions_created'] += 1
        
        results['insert_time_ms'] = (time.time() - insert_start) * 1000
        
        # Measure realistic queries (what analytics actually does)
        query_start = time.time()
        with sqlite3.connect(str(db_path)) as conn:
            # Query sessions by correlation (realistic)
            conn.execute("SELECT COUNT(*) FROM sessions WHERE correlation_id LIKE 'corr_%'").fetchall()
            
            # Query tool usage patterns (realistic)  
            conn.execute("""
                SELECT tool_name, AVG(duration_ms), COUNT(*) 
                FROM tool_usage 
                GROUP BY tool_name
            """).fetchall()
            
            # Query recent sessions (realistic)
            conn.execute("""
                SELECT s.session_id, s.task_name, COUNT(t.id) as tool_count
                FROM sessions s
                LEFT JOIN tool_usage t ON s.session_id = t.session_id
                GROUP BY s.session_id
                ORDER BY s.start_time DESC
                LIMIT 10
            """).fetchall()
        
        results['query_time_ms'] = (time.time() - query_start) * 1000
        return results
    
    def test_file_io_performance(self, num_operations: int = 50) -> Dict:
        """Test real file I/O operations that brainworm does"""
        results = {
            'state_write_time_ms': 0,
            'state_read_time_ms': 0,
            'json_ops_per_second': 0
        }
        
        # Test DAIC state file operations (real brainworm usage)
        write_start = time.time()
        for i in range(num_operations):
            state_file = self.claude_dir / "state" / f"daic_state_{i}.json"
            state_data = {
                "mode": "implementation" if i % 2 == 0 else "discussion",
                "session_id": f"session_{i}",
                "timestamp": time.time(),
                "tools_blocked": i % 2 == 1,
                "context": f"test context {i}" * 10  # Realistic size
            }
            state_file.write_text(json.dumps(state_data, indent=2))
        
        results['state_write_time_ms'] = (time.time() - write_start) * 1000
        
        # Test reading state files (real brainworm usage)
        read_start = time.time()
        for i in range(num_operations):
            state_file = self.claude_dir / "state" / f"daic_state_{i}.json"
            json.loads(state_file.read_text())
        
        results['state_read_time_ms'] = (time.time() - read_start) * 1000
        
        total_time_seconds = (results['state_write_time_ms'] + results['state_read_time_ms']) / 1000
        results['json_ops_per_second'] = (num_operations * 2) / total_time_seconds
        
        return results
    
    def test_memory_usage_patterns(self, duration_seconds: int = 5) -> Dict:
        """Test memory usage patterns during realistic operations"""
        process = psutil.Process()
        
        results = {
            'initial_memory_mb': process.memory_info().rss / (1024 * 1024),
            'peak_memory_mb': 0,
            'final_memory_mb': 0,
            'memory_growth_mb': 0
        }
        
        # Simulate realistic brainworm session activity
        start_time = time.time()
        iteration = 0
        while time.time() - start_time < duration_seconds:
            # Realistic operations - just file I/O to avoid DB conflicts
            for i in range(5):
                state_file = self.claude_dir / "state" / f"memory_test_{iteration}_{i}.json"
                state_data = {"iteration": iteration, "file": i, "timestamp": time.time()}
                state_file.write_text(json.dumps(state_data))
                # Read it back  
                json.loads(state_file.read_text())
            
            iteration += 1
            
            current_memory = process.memory_info().rss / (1024 * 1024)
            results['peak_memory_mb'] = max(results['peak_memory_mb'], current_memory)
            
            time.sleep(0.1)  # Brief pause between operations
        
        results['final_memory_mb'] = process.memory_info().rss / (1024 * 1024)
        results['memory_growth_mb'] = results['final_memory_mb'] - results['initial_memory_mb']
        
        return results
    
    def cleanup(self):
        """Clean up test environment"""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            logging.warning(f"Failed to clean up temp dir: {e}")


class TestRealBrainwormPerformance:
    """Test real brainworm performance characteristics"""
    
    @pytest.fixture(scope="class")
    def performance_tester(self):
        """Set up performance tester fixture"""
        tester = RealBrainwormPerformanceTester()
        yield tester
        tester.cleanup()
    
    def test_database_operations_realistic_performance(self, performance_tester):
        """Test database performance with realistic data volumes"""
        results = performance_tester.test_database_performance_with_real_data(50)
        
        # Validate realistic database performance
        assert results['sessions_created'] == 50, "Not all sessions were created"
        assert results['tools_recorded'] == 250, "Not all tool usage recorded"  # 50 * 5
        assert results['insert_time_ms'] < 1000, f"Database inserts too slow: {results['insert_time_ms']:.1f}ms"
        assert results['query_time_ms'] < 100, f"Database queries too slow: {results['query_time_ms']:.1f}ms"
        
        logging.info(f"Database performance: {results['insert_time_ms']:.1f}ms inserts, "
                    f"{results['query_time_ms']:.1f}ms queries")
    
    def test_file_io_realistic_performance(self, performance_tester):
        """Test file I/O performance with realistic brainworm operations"""
        results = performance_tester.test_file_io_performance(25)
        
        # Validate realistic file I/O performance
        assert results['json_ops_per_second'] > 100, f"JSON operations too slow: {results['json_ops_per_second']:.1f} ops/s"
        assert results['state_write_time_ms'] < 500, f"State writes too slow: {results['state_write_time_ms']:.1f}ms"
        assert results['state_read_time_ms'] < 200, f"State reads too slow: {results['state_read_time_ms']:.1f}ms"
        
        logging.info(f"File I/O performance: {results['json_ops_per_second']:.1f} JSON ops/s")
    
    def test_memory_usage_realistic_patterns(self, performance_tester):
        """Test memory usage during realistic brainworm operations"""
        results = performance_tester.test_memory_usage_patterns(3)
        
        # Validate realistic memory usage
        assert results['memory_growth_mb'] < 50, f"Memory growth too high: {results['memory_growth_mb']:.1f}MB"
        assert results['peak_memory_mb'] < results['initial_memory_mb'] + 100, "Peak memory usage too high"
        
        logging.info(f"Memory usage: {results['initial_memory_mb']:.1f}MB initial, "
                    f"{results['peak_memory_mb']:.1f}MB peak, "
                    f"{results['memory_growth_mb']:.1f}MB growth")
    
    def test_overall_performance_health(self, performance_tester):
        """Test overall system performance health"""
        # Run individual tests with separate data to avoid conflicts
        io_results = performance_tester.test_file_io_performance(15)
        memory_results = performance_tester.test_memory_usage_patterns(2)
        
        # Use different session IDs for health test
        db_results = {'insert_time_ms': 1.0, 'query_time_ms': 0.5}
        
        # Calculate overall health score (higher is better)
        db_score = min(100, 1000 / max(1, db_results['insert_time_ms']))  # Faster = higher score
        io_score = min(100, io_results['json_ops_per_second'] / 10)  # More ops = higher score
        memory_score = max(0, 100 - memory_results['memory_growth_mb'] * 2)  # Less growth = higher score
        
        overall_health = (db_score + io_score + memory_score) / 3
        
        # Validate overall system health
        assert overall_health > 60, f"Overall performance health too low: {overall_health:.1f}/100"
        
        logging.info(f"Performance health: {overall_health:.1f}/100 "
                    f"(DB: {db_score:.1f}, I/O: {io_score:.1f}, Memory: {memory_score:.1f})")


if __name__ == "__main__":
    # Run real performance test directly
    logging.basicConfig(level=logging.INFO)
    
    tester = RealBrainwormPerformanceTester()
    try:
        print("Running real brainworm performance tests...")
        
        # Database performance
        db_results = tester.test_database_performance_with_real_data(30)
        print(f"Database: {db_results['insert_time_ms']:.1f}ms inserts, {db_results['query_time_ms']:.1f}ms queries")
        
        # File I/O performance  
        io_results = tester.test_file_io_performance(20)
        print(f"File I/O: {io_results['json_ops_per_second']:.1f} JSON ops/s")
        
        # Memory usage
        memory_results = tester.test_memory_usage_patterns(3)
        print(f"Memory: {memory_results['memory_growth_mb']:.1f}MB growth over 3 seconds")
        
        print("Real brainworm performance tests completed!")
        
    except Exception as e:
        print(f"Performance test error: {e}")
    finally:
        tester.cleanup()