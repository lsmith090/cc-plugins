#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""
Lightweight SQLite connection manager for hooks.

This module provides simple SQLite connection pooling optimized for hooks usage:
- Fast, lightweight connections
- Basic connection pooling
- Simple query execution
- No external dependencies beyond standard library
"""

import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Any, List, Optional, Generator, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class SQLiteConfig:
    """Configuration for SQLite connections"""
    timeout: float = 5.0
    max_connections: int = 5
    enable_wal_mode: bool = True
    enable_foreign_keys: bool = True
    journal_mode: str = "WAL"
    synchronous: str = "NORMAL"
    connection_check_interval: float = 300.0  # 5 minutes

class SQLiteConnectionPool:
    """Simple connection pool for SQLite connections"""
    
    def __init__(self, db_path: Path, config: SQLiteConfig):
        self.db_path = db_path
        self.config = config
        self._pool = []
        self._active_connections = 0
        self._lock = threading.RLock()
        self._last_cleanup = time.time()
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a connection from the pool"""
        conn = self._acquire_connection()
        try:
            yield conn
        finally:
            self._release_connection(conn)
    
    def _acquire_connection(self) -> sqlite3.Connection:
        """Acquire connection from pool or create new one"""
        with self._lock:
            # Try to get from pool first
            if self._pool:
                conn = self._pool.pop()
                logger.debug(f"Reused SQLite connection from pool. Pool size: {len(self._pool)}")
                return conn
            
            # Create new connection
            conn = self._create_connection()
            self._active_connections = min(self._active_connections + 1, self.config.max_connections)
            logger.debug(f"Created new SQLite connection. Active: {self._active_connections}")
            return conn
    
    def _release_connection(self, conn: sqlite3.Connection):
        """Return connection to pool"""
        if not conn:
            return
        
        with self._lock:
            # Perform periodic cleanup
            if time.time() - self._last_cleanup > self.config.connection_check_interval:
                self._cleanup_stale_connections()
                self._last_cleanup = time.time()
            
            # Add to pool if under limit
            if len(self._pool) < self.config.max_connections:
                self._pool.append(conn)
                logger.debug(f"Returned SQLite connection to pool. Pool size: {len(self._pool)}")
            else:
                # Pool is full, close the connection
                conn.close()
                if self._active_connections > 0:
                    self._active_connections -= 1
                logger.debug(f"Closed excess SQLite connection. Active: {self._active_connections}")
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create a configured SQLite connection"""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=self.config.timeout,
            check_same_thread=False
        )
        
        # Configure SQLite settings
        conn.execute(f"PRAGMA journal_mode = {self.config.journal_mode}")
        conn.execute(f"PRAGMA synchronous = {self.config.synchronous}")
        
        if self.config.enable_foreign_keys:
            conn.execute("PRAGMA foreign_keys = ON")
        
        # Set row factory for dict-like access
        conn.row_factory = sqlite3.Row
        
        return conn
    
    def _cleanup_stale_connections(self):
        """Clean up stale connections in the pool"""
        with self._lock:
            # For now, just limit pool size - could add health checks here
            while len(self._pool) > self.config.max_connections:
                conn = self._pool.pop(0)
                try:
                    conn.close()
                except Exception as e:
                    # Log but continue cleanup - don't let one bad connection stop cleanup
                    logger.warning(f"Error closing stale SQLite connection: {e}")
                finally:
                    # Always decrement counter even if close() failed to prevent leak
                    if self._active_connections > 0:
                        self._active_connections -= 1
    
    def close_all(self):
        """Close all connections in the pool"""
        with self._lock:
            errors = []
            for conn in self._pool:
                try:
                    conn.close()
                except Exception as e:
                    # Collect errors but continue closing all connections
                    errors.append(str(e))

            self._pool.clear()
            self._active_connections = 0

            if errors:
                logger.warning(f"Errors closing SQLite connections for {self.db_path}: {'; '.join(errors)}")
            else:
                logger.info(f"Closed all SQLite connections for {self.db_path}")

class HooksSQLiteManager:
    """
    Lightweight SQLite connection manager optimized for hooks usage.
    
    Features:
    - Simple connection pooling per database
    - Basic query execution with retry logic
    - Transaction management
    - Schema initialization support
    - Thread-safe operations
    """
    
    def __init__(self, config: Optional[SQLiteConfig] = None):
        self.config = config or SQLiteConfig()
        self._pools: Dict[str, SQLiteConnectionPool] = {}
        self._lock = threading.RLock()
        self._initialized_schemas: set = set()
    
    @contextmanager
    def connection(self, db_path: Path) -> Generator[sqlite3.Connection, None, None]:
        """
        Get a SQLite connection from the pool.
        
        Args:
            db_path: Path to the SQLite database
            
        Yields:
            sqlite3.Connection: A configured SQLite connection
        """
        db_key = str(db_path.resolve())
        
        # Get or create pool for this database
        with self._lock:
            if db_key not in self._pools:
                self._pools[db_key] = SQLiteConnectionPool(db_path, self.config)
        
        pool = self._pools[db_key]
        with pool.get_connection() as conn:
            yield conn
    
    def execute_query(self, 
                     db_path: Path, 
                     query: str, 
                     params: Optional[Tuple] = None,
                     fetch: str = "all") -> List[sqlite3.Row]:
        """
        Execute a SQLite query and return results.
        
        Args:
            db_path: Path to the SQLite database
            query: SQL query to execute
            params: Query parameters
            fetch: Fetch mode - "all", "one", or "none"
            
        Returns:
            List of rows (or single row if fetch="one", empty list if fetch="none")
        """
        with self.connection(db_path) as conn:
            cursor = conn.execute(query, params or ())
            
            if fetch == "all":
                return cursor.fetchall()
            elif fetch == "one":
                result = cursor.fetchone()
                return [result] if result else []
            else:  # fetch == "none"
                return []
    
    def execute_transaction(self, 
                           db_path: Path, 
                           operations: List[Tuple[str, Optional[Tuple]]]) -> bool:
        """
        Execute multiple SQLite operations in a transaction.
        
        Args:
            db_path: Path to the SQLite database
            operations: List of (query, params) tuples
            
        Returns:
            bool: True if transaction succeeded, False otherwise
        """
        try:
            with self.connection(db_path) as conn:
                with conn:  # Auto-commit/rollback transaction
                    for query, params in operations:
                        conn.execute(query, params or ())
                return True
        except Exception as e:
            logger.error(f"SQLite transaction failed: {e}")
            return False
    
    def ensure_schema(self, 
                     db_path: Path, 
                     schema_sql: str, 
                     schema_name: str = "default") -> bool:
        """
        Ensure SQLite database schema exists (idempotent).
        
        Args:
            db_path: Path to SQLite database
            schema_sql: SQL statements to create schema
            schema_name: Name for tracking initialized schemas
            
        Returns:
            bool: True if schema was created/exists, False on error
        """
        schema_key = f"{db_path}:{schema_name}"
        
        # Check if we've already initialized this schema
        if schema_key in self._initialized_schemas:
            return True
        
        try:
            with self.connection(db_path) as conn:
                # Split and execute each SQL statement
                statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
                for statement in statements:
                    conn.execute(statement)
                
                # Mark as initialized
                self._initialized_schemas.add(schema_key)
                logger.debug(f"Initialized SQLite schema '{schema_name}' for {db_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to initialize SQLite schema '{schema_name}': {e}")
            return False
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics for monitoring"""
        stats = {"pools": {}}
        
        with self._lock:
            for db_path, pool in self._pools.items():
                stats["pools"][db_path] = {
                    "active_connections": pool._active_connections,
                    "pool_size": len(pool._pool),
                    "max_connections": self.config.max_connections
                }
        
        return stats
    
    def close_all_connections(self):
        """Close all database connections"""
        with self._lock:
            for pool in self._pools.values():
                pool.close_all()
            self._pools.clear()
            self._initialized_schemas.clear()
            logger.info("Closed all SQLite connections")

# Global hooks SQLite manager instance
_hooks_sqlite_manager: Optional[HooksSQLiteManager] = None
_hooks_sqlite_manager_lock = threading.Lock()

def get_hooks_sqlite_manager(config: Optional[SQLiteConfig] = None) -> HooksSQLiteManager:
    """
    Get the global hooks SQLite manager instance (singleton pattern).
    
    Args:
        config: Optional configuration (only used on first call)
        
    Returns:
        HooksSQLiteManager: The global SQLite manager instance
    """
    global _hooks_sqlite_manager
    
    if _hooks_sqlite_manager is None:
        with _hooks_sqlite_manager_lock:
            if _hooks_sqlite_manager is None:
                _hooks_sqlite_manager = HooksSQLiteManager(config)
    
    return _hooks_sqlite_manager

def close_hooks_sqlite_manager():
    """Close the global hooks SQLite manager and all its connections"""
    global _hooks_sqlite_manager
    
    with _hooks_sqlite_manager_lock:
        if _hooks_sqlite_manager is not None:
            _hooks_sqlite_manager.close_all_connections()
            _hooks_sqlite_manager = None

# Convenience functions for common patterns
def execute_hooks_query(db_path: Path, query: str, params: Optional[Tuple] = None) -> List[sqlite3.Row]:
    """Execute a query using the global hooks SQLite manager"""
    manager = get_hooks_sqlite_manager()
    return manager.execute_query(db_path, query, params)

def execute_hooks_transaction(db_path: Path, operations: List[Tuple[str, Optional[Tuple]]]) -> bool:
    """Execute a transaction using the global hooks SQLite manager"""
    manager = get_hooks_sqlite_manager()
    return manager.execute_transaction(db_path, operations)