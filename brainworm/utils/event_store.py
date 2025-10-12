#!/usr/bin/env python3
"""
Event Store for Claude Code Hooks

Event storage system with session correlation and SQLite persistence.
"""

import json
import sqlite3
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import sys

# Add parent to path for hook_types
sys.path.insert(0, str(Path(__file__).parent))

# Import lightweight SQLite manager for hooks
try:
    from .sqlite_manager import HooksSQLiteManager
except ImportError:
    HooksSQLiteManager = None

# Import type definitions with fallback
try:
    from .hook_types import parse_log_event, BaseLogEvent, get_standard_timestamp, format_for_database, DeveloperInfo, PreToolUseLogEvent, PostToolUseLogEvent, UserPromptSubmitLogEvent
except ImportError:
    parse_log_event = None
    BaseLogEvent = None
    DeveloperInfo = None
    PreToolUseLogEvent = None
    PostToolUseLogEvent = None
    UserPromptSubmitLogEvent = None
    # Fallback timestamp functions
    def get_standard_timestamp():
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
    
    def format_for_database(ts):
        return ts if ts else get_standard_timestamp()

# Optional TOML support for configuration
try:
    import toml
    TOML_AVAILABLE = True
except ImportError:
    TOML_AVAILABLE = False

class HookEventStore:
    """Event storage system for Claude Code hooks with session correlation"""

    def __init__(self, brainworm_dir: Path):
        """Initialize event store with .brainworm directory"""
        self.brainworm_dir = Path(brainworm_dir)
        self.events_dir = self.brainworm_dir / "events"
        self.events_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.events_dir / "hooks.db"
        self.logs_dir = self.events_dir / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize database manager if available
        if HooksSQLiteManager:
            self.db_manager = HooksSQLiteManager()
        else:
            self.db_manager = None
            
        self._init_database()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from .brainworm/config.toml if available"""
        if not TOML_AVAILABLE:
            return self._default_config()
        
        # Look for .brainworm/config.toml in project root
        search_paths = [
            self.brainworm_dir / "config.toml",                 # .brainworm directory
            self.brainworm_dir.parent / ".brainworm" / "config.toml",  # Project root
        ]
        
        # Walk up directories to find config
        current = self.brainworm_dir.parent
        while current != current.parent:
            config_path = current / ".brainworm" / "config.toml"
            if config_path.exists():
                search_paths.insert(0, config_path)
                break
            current = current.parent
        
        for config_path in search_paths:
            try:
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        config = toml.load(f)
                    # Merge config with defaults
                    default_config = self._default_config()
                    analytics_config = config.get('analytics', {})
                    default_config.update(analytics_config)
                    return default_config
            except Exception:
                continue
        
        return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Default analytics configuration"""
        return {
            'real_time_processing': True,
            'correlation_timeout_minutes': 60,
            'success_rate_window_hours': 24,
            'max_processing_time_ms': 50,
            'retention_days': 30,
            'max_db_size_mb': 100
        }
    
    def _extract_duration_ms(self, event_data: Dict[str, Any]) -> float:
        """Extract duration from various possible structures in event data"""
        # Check for direct duration_ms field first
        if 'duration_ms' in event_data:
            return float(event_data['duration_ms'])
        
        # Check for nested timing structure from hook_analytics.py
        if 'timing' in event_data and isinstance(event_data['timing'], dict):
            timing_data = event_data['timing']
            if 'execution_duration_ms' in timing_data:
                return float(timing_data['execution_duration_ms'])
        
        # Default to 0 if no duration data found
        return 0.0
    
    def _init_database(self):
        """Initialize SQLite database for event storage with minimal schema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Simplified schema: minimal indexed columns + rich JSON
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS hook_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        hook_name TEXT NOT NULL,
                        correlation_id TEXT,
                        session_id TEXT,
                        execution_id TEXT,
                        timestamp DATETIME NOT NULL,
                        event_data TEXT NOT NULL
                    )
                """)

                # Indexes for efficient querying
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_hook_events_timestamp
                    ON hook_events(timestamp)
                """)

                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_hook_events_correlation
                    ON hook_events(correlation_id)
                """)

                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_hook_events_session
                    ON hook_events(session_id)
                """)

                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_hook_events_execution_id
                    ON hook_events(execution_id)
                """)
        except Exception:
            # Event storage is optional - continue if database init fails
            pass
    
    def log_event(self, event_data: Dict[str, Any]) -> bool:
        """Store a hook event to the database"""
        try:
            # Use typed event parsing if available
            if parse_log_event:
                try:
                    typed_event = parse_log_event(event_data)
                    hook_name = typed_event.hook_name or 'unknown'
                    event_type = 'hook_execution'  # Default for typed events
                    correlation_id = typed_event.correlation_id
                    session_id = typed_event.session_id
                    success = True  # Default for typed events
                    duration_ms = self._extract_duration_ms(event_data)  # Extract from timing data
                    timestamp = get_standard_timestamp()  # Use standard ISO format

                    # Override with any direct fields from event_data
                    if 'event_type' in event_data:
                        event_type = event_data['event_type']
                    if 'success' in event_data:
                        success = event_data['success']
                    # Extract duration using helper function to handle nested timing structure
                    duration_ms = self._extract_duration_ms(event_data)
                    if 'timestamp' in event_data:
                        timestamp = format_for_database(str(event_data['timestamp']))
                        
                except Exception:
                    # Fallback to untyped parsing
                    hook_name = event_data.get('hook_name', 'unknown')
                    event_type = event_data.get('event_type', 'hook_execution')
                    correlation_id = event_data.get('correlation_id')
                    session_id = event_data.get('session_id')
                    success = event_data.get('success', True)
                    duration_ms = self._extract_duration_ms(event_data)
                    raw_timestamp = event_data.get('timestamp')
                    timestamp = format_for_database(str(raw_timestamp)) if raw_timestamp else get_standard_timestamp()
            else:
                # Fallback to untyped parsing
                hook_name = event_data.get('hook_name', 'unknown')
                event_type = event_data.get('event_type', 'hook_execution')
                correlation_id = event_data.get('correlation_id')
                session_id = event_data.get('session_id')
                success = event_data.get('success', True)
                duration_ms = self._extract_duration_ms(event_data)
                raw_timestamp = event_data.get('timestamp')
                timestamp = format_for_database(str(raw_timestamp)) if raw_timestamp else get_standard_timestamp()
            
            # Extract minimal indexed fields
            execution_id = event_data.get('execution_id', None)

            # Store in database with simplified schema: minimal columns + rich JSON
            with sqlite3.connect(self.db_path, timeout=1.0) as conn:
                conn.execute("""
                    INSERT INTO hook_events
                    (hook_name, correlation_id, session_id, execution_id,
                     timestamp, event_data)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    hook_name, correlation_id, session_id, execution_id,
                    timestamp, json.dumps(event_data)
                ))

            return True
            
        except Exception as e:
            # Analytics failure should not break hooks
            return False
    
    def process_hook_event(self, event_data: Dict[str, Any]) -> bool:
        """Process a hook event with type-aware processing"""
        # Add timestamp normalization for typed events
        if parse_log_event and not event_data.get('logged_at'):
            event_data['logged_at'] = get_standard_timestamp()
            
        return self.log_event(event_data)
    
    def get_recent_events(self, limit: int = 100) -> list:
        """Get recent hook events for monitoring"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM hook_events 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get basic statistics about hook performance"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT
                        COUNT(*) as total_events,
                        COUNT(DISTINCT session_id) as unique_sessions,
                        COUNT(DISTINCT correlation_id) as unique_correlations
                    FROM hook_events
                    WHERE datetime(timestamp) > datetime('now', '-1 day')
                """)  # Last 24 hours using SQLite datetime functions

                row = cursor.fetchone()
                if row:
                    return {
                        'total_events': row[0],
                        'unique_sessions': row[1],
                        'unique_correlations': row[2],
                        'period': '24h'
                    }
        except Exception:
            pass

        return {
            'total_events': 0,
            'unique_sessions': 0,
            'unique_correlations': 0,
            'period': '24h'
        }

def create_event_store(brainworm_dir: Path) -> HookEventStore:
    """Create an event store instance"""
    return HookEventStore(brainworm_dir)