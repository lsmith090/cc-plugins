#!/usr/bin/env python3
"""
Analytics Processor for Claude Code Hooks

Lightweight analytics processing for hook events with SQLite storage.
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

class ClaudeAnalyticsProcessor:
    """Lightweight analytics processor for Claude Code hooks"""

    def __init__(self, brainworm_dir: Path):
        """Initialize processor with .brainworm directory"""
        self.brainworm_dir = Path(brainworm_dir)
        self.analytics_dir = self.brainworm_dir / "analytics"
        self.analytics_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.analytics_dir / "hooks.db"
        self.logs_dir = self.analytics_dir / "logs"
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
    
    def _extract_typed_metadata(self, typed_event) -> Dict[str, Any]:
        """Extract rich metadata from typed events for enhanced analytics using type-safe processing"""
        metadata = {}
        
        # Type-safe processing instead of duck typing
        if PreToolUseLogEvent and isinstance(typed_event, PreToolUseLogEvent):
            # PreToolUseLogEvent specific data
            if typed_event.tool_name:
                metadata['tool_name'] = typed_event.tool_name
            if typed_event.blocked is not None:
                metadata['blocked'] = typed_event.blocked
            if typed_event.validation_issues:
                metadata['validation_issues_count'] = len(typed_event.validation_issues)
                metadata['has_validation_issues'] = True
                
        elif PostToolUseLogEvent and isinstance(typed_event, PostToolUseLogEvent):
            # PostToolUseLogEvent specific data
            if typed_event.tool_name:
                metadata['tool_name'] = typed_event.tool_name
            # Could extract tool_response metadata here in the future
                
        elif UserPromptSubmitLogEvent and isinstance(typed_event, UserPromptSubmitLogEvent):
            # UserPromptSubmitLogEvent specific data
            if typed_event.context_injected is not None:
                metadata['context_injected'] = typed_event.context_injected
            if typed_event.context_length is not None:
                metadata['context_length'] = typed_event.context_length
            if typed_event.intent_analysis:
                metadata['has_intent_analysis'] = True
                if 'primary_intent' in typed_event.intent_analysis:
                    metadata['primary_intent'] = typed_event.intent_analysis['primary_intent']
                if 'confidence' in typed_event.intent_analysis:
                    metadata['intent_confidence'] = typed_event.intent_analysis['confidence']
        
        # Common BaseLogEvent fields (all events have these) - check without isinstance for compatibility
        if hasattr(typed_event, 'workflow_phase') and typed_event.workflow_phase:
            metadata['workflow_phase'] = typed_event.workflow_phase
        if hasattr(typed_event, 'schema_version') and typed_event.schema_version:
            metadata['schema_version'] = typed_event.schema_version
                
        return metadata
    
    def _extract_tool_name(self, event_data: Dict[str, Any]) -> Optional[str]:
        """Extract tool name from event data"""
        # Check direct tool_name field first
        if 'tool_name' in event_data:
            return event_data['tool_name']
        
        # Check in tool_input structure
        if 'tool_input' in event_data:
            return event_data.get('tool_input', {}).get('tool_name')
        
        return None
    
    def _extract_file_path(self, event_data: Dict[str, Any]) -> Optional[str]:
        """Extract file path from tool operations with improved parsing"""
        tool_input = event_data.get('tool_input', {})
        
        # For Edit/MultiEdit/Write tools
        if 'file_path' in tool_input:
            return tool_input['file_path']
        
        # For Bash commands, try to extract file operations
        if event_data.get('tool_name') == 'Bash' and 'command' in tool_input:
            command = tool_input['command']
            import re
            
            # Improved patterns that handle flags and find file paths (including quoted)
            file_patterns = [
                # File operations - handle quoted strings and skip flags
                r'(?:edit|vim|nano|cat|head|tail|grep|less|more)\s+(?:-[^\s]*\s+)*(?!-|<<)([\'"][^\'"|<>]+[\'"]|[^\s|<>]+)(?:\s|$|\|)',
                r'(?:touch|rm|mv|cp|chmod|chown)\s+(?:-[^\s]*\s+)*(?!-)([\'"][^\'"|<>]+[\'"]|[^\s|<>]+)(?:\s|$|\|)',
                # Redirection - exclude /dev/null and heredocs, handle quoted paths
                r'>\s*(?!/dev/null|<<)([\'"][^\'"|<>]+[\'"]|[^\s|<>]+)(?:\s|$|\|)',
                r'<\s*(?!<<)([\'"][^\'"|<>]+[\'"]|[^\s|<>]+)(?:\s|$|\|)'
            ]
            
            for pattern in file_patterns:
                match = re.search(pattern, command)
                if match:
                    potential_path = match.group(1).strip('"\'')  # Remove quotes
                    if self._is_valid_file_path(potential_path):
                        return potential_path
        
        # For Read tool (duplicate check removed - already handled above)
        return None
    
    def _is_valid_file_path(self, path: str) -> bool:
        """Validate that a string looks like a real file path"""
        if not path or len(path) == 0:
            return False
        
        # Exclude obvious non-paths
        if path.startswith('-'):  # Command flags
            return False
        if path.startswith('<<'):  # Heredoc markers
            return False
        if path in ['EOF', 'EOL']:  # Common heredoc delimiters
            return False
        if path.isdigit():  # Pure numbers (from flags like -20)
            return False
        if path in ['/dev/null', '/dev/zero']:  # Special devices
            return False
        
        # Must look like a path - contain / or . or be a simple filename
        if '/' in path or '.' in path or path.isalnum():
            return True
            
        return False
    
    def _extract_change_summary(self, event_data: Dict[str, Any]) -> Optional[str]:
        """Generate change summary based on tool operation"""
        tool_name = event_data.get('tool_name')
        tool_input = event_data.get('tool_input', {})
        
        if tool_name == 'Edit':
            old_str = tool_input.get('old_string', '')[:50]  # First 50 chars
            new_str = tool_input.get('new_string', '')[:50]
            if old_str and new_str:
                return f"Edit: '{old_str}...' → '{new_str}...'"
        
        elif tool_name == 'Write':
            file_path = tool_input.get('file_path', '')
            content_size = len(tool_input.get('content', ''))
            if file_path:
                return f"Write: {content_size} chars to {Path(file_path).name}"
        
        elif tool_name == 'MultiEdit':
            edits_count = len(tool_input.get('edits', []))
            file_path = tool_input.get('file_path', '')
            if file_path:
                return f"MultiEdit: {edits_count} changes to {Path(file_path).name}"
        
        elif tool_name == 'Bash':
            command = tool_input.get('command', '')[:100]  # First 100 chars
            if command:
                return f"Bash: {command}"
        
        elif tool_name == 'Read':
            file_path = tool_input.get('file_path', '')
            if file_path:
                return f"Read: {Path(file_path).name}"
        
        elif tool_name == 'Task':
            subagent_type = tool_input.get('subagent_type', '')
            description = tool_input.get('description', '')
            if subagent_type:
                return f"Task: {subagent_type} - {description[:50]}..."
        
        return None
    
    def _calculate_original_data_size(self, event_data: Dict[str, Any]) -> Optional[int]:
        """Calculate original data size before any processing"""
        total_size = 0
        
        # Size of the entire event data structure
        event_json = json.dumps(event_data, default=str)
        total_size = len(event_json.encode('utf-8'))
        
        # Add sizes of specific large content fields
        tool_input = event_data.get('tool_input', {})
        if isinstance(tool_input, dict):
            # For Write operations, count content size
            if 'content' in tool_input:
                content_size = len(str(tool_input['content']).encode('utf-8'))
                total_size += content_size
            
            # For Edit operations, count old_string and new_string
            if 'old_string' in tool_input:
                old_size = len(str(tool_input['old_string']).encode('utf-8'))
                total_size += old_size
            if 'new_string' in tool_input:
                new_size = len(str(tool_input['new_string']).encode('utf-8'))
                total_size += new_size
        
        # Tool response data (for post_tool_use events)
        if 'tool_response' in event_data or 'tool_result' in event_data:
            tool_result = event_data.get('tool_response') or event_data.get('tool_result')
            if tool_result:
                result_json = json.dumps(tool_result, default=str)
                result_size = len(result_json.encode('utf-8'))
                total_size += result_size
        
        return total_size if total_size > 0 else None
    
    def _init_database(self):
        """Initialize SQLite database for analytics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS hook_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        hook_name TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        correlation_id TEXT,
                        session_id TEXT,
                        success BOOLEAN,
                        duration_ms REAL,
                        data TEXT,
                        developer_name TEXT,
                        developer_email TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Schema migration: Add columns if they don't exist
                migration_columns = [
                    ("developer_name", "TEXT"),
                    ("developer_email", "TEXT"),
                    ("timestamp", "DATETIME"),
                    ("tool_name", "TEXT"),
                    ("file_path", "TEXT"),
                    ("change_summary", "TEXT"),
                    ("original_data_size", "INTEGER"),
                ]

                for column_name, column_type in migration_columns:
                    try:
                        conn.execute(f"ALTER TABLE hook_events ADD COLUMN {column_name} {column_type}")
                    except sqlite3.OperationalError:
                        pass  # Column already exists

                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_hook_events_timestamp
                    ON hook_events(timestamp)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_hook_events_correlation 
                    ON hook_events(correlation_id)
                """)
        except Exception:
            # Analytics is optional - continue if database init fails
            pass
    
    def log_event(self, event_data: Dict[str, Any]) -> bool:
        """Log a hook event to the analytics system"""
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
                    
                    # Extract rich metadata from typed event
                    typed_metadata = self._extract_typed_metadata(typed_event)
                    
                    # Override with any direct fields from event_data
                    if 'event_type' in event_data:
                        event_type = event_data['event_type']
                    if 'success' in event_data:
                        success = event_data['success']
                    # Extract duration using helper function to handle nested timing structure
                    duration_ms = self._extract_duration_ms(event_data)
                    if 'timestamp' in event_data:
                        timestamp = format_for_database(str(event_data['timestamp']))
                    
                    # Merge typed metadata into event_data for enhanced database storage
                    event_data = {**event_data, **typed_metadata}
                        
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
            
            # Get developer information from DAIC state manager
            developer_info = DeveloperInfo() if DeveloperInfo else None
            try:
                from .daic_state_manager import DAICStateManager
                state_manager = DAICStateManager(self.brainworm_dir.parent)  # Pass project root
                developer_info = state_manager.get_developer_info()
            except (ImportError, FileNotFoundError, KeyError, AttributeError) as e:
                # Continue with fallback developer info if unavailable
                if DeveloperInfo:
                    developer_info = DeveloperInfo()
                else:
                    developer_info = None
            
            # Extract metadata for new schema columns
            tool_name = self._extract_tool_name(event_data)
            file_path = self._extract_file_path(event_data)
            change_summary = self._extract_change_summary(event_data)
            original_data_size = self._calculate_original_data_size(event_data)
            
            # Store in database with new schema columns
            with sqlite3.connect(self.db_path, timeout=1.0) as conn:
                conn.execute("""
                    INSERT INTO hook_events
                    (hook_name, event_type, correlation_id, session_id,
                     success, duration_ms, data, developer_name, developer_email,
                     timestamp, tool_name, file_path, change_summary, original_data_size)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    hook_name, event_type, correlation_id, session_id,
                    success, duration_ms, json.dumps(event_data),
                    developer_info.name if developer_info else None,
                    developer_info.email if developer_info else None,
                    timestamp,
                    tool_name, file_path, change_summary, original_data_size
                ))
            
            # Also write to JSONL log file for backup
            log_file = self.logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}_hooks.jsonl"
            with open(log_file, 'a', encoding='utf-8') as f:
                json.dump({
                    'created_at': timestamp,  # Already in ISO format
                    'hook_name': hook_name,
                    'event_type': event_type,
                    'correlation_id': correlation_id,
                    'session_id': session_id,
                    'success': success,
                    'duration_ms': duration_ms,
                    'developer_name': developer_info.name if developer_info else None,
                    'developer_email': developer_info.email if developer_info else None,
                    **event_data
                }, f, separators=(',', ':'))
                f.write('\n')
            
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
                        AVG(duration_ms) as avg_duration,
                        SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_events,
                        COUNT(DISTINCT session_id) as unique_sessions,
                        COUNT(DISTINCT correlation_id) as unique_correlations
                    FROM hook_events
                    WHERE datetime(timestamp) > datetime('now', '-1 day')
                """)  # Last 24 hours using SQLite datetime functions
                
                row = cursor.fetchone()
                if row:
                    total = row[0]
                    return {
                        'total_events': total,
                        'avg_duration_ms': round(row[1] or 0, 2),
                        'success_rate': round((row[2] / total * 100) if total > 0 else 0, 1),
                        'unique_sessions': row[3],
                        'unique_correlations': row[4],
                        'period': '24h'
                    }
        except Exception:
            pass
        
        return {
            'total_events': 0,
            'avg_duration_ms': 0,
            'success_rate': 0,
            'unique_sessions': 0,
            'unique_correlations': 0,
            'period': '24h'
        }

# Compatibility aliases for existing hook code
StreamProcessor = ClaudeAnalyticsProcessor

def create_analytics_processor(brainworm_dir: Path) -> ClaudeAnalyticsProcessor:
    """Create an analytics processor instance"""
    return ClaudeAnalyticsProcessor(brainworm_dir)