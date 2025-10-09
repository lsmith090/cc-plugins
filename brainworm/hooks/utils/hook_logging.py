#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""
Generic JSONL Logging Utilities
Centralized logging functionality for Claude Code hooks
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Union
from datetime import datetime, timezone


class HookLogger:
    """
    Centralized logging utility for Claude Code hooks.
    
    Provides JSONL logging with timestamp enrichment, error handling,
    and project-specific log organization.
    """
    
    def __init__(self, project_root: Path, hook_name: str):
        """
        Initialize the logger.
        
        Args:
            project_root: Project root directory
            hook_name: Name of the hook (e.g., 'post_tool_use', 'stop')
        """
        self.project_root = project_root
        self.hook_name = hook_name
        self.logs_dir = project_root / '.brainworm' / 'logs'
        self.log_file = self.logs_dir / f'{hook_name}.jsonl'
        
        # Ensure logs directory exists
        self._ensure_logs_dir()
    
    def _ensure_logs_dir(self) -> None:
        """Ensure the logs directory exists."""
        try:
            self.logs_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            print(f"[WARNING] Could not create logs directory: {e}", file=sys.stderr)
    
    def log_event(self, event_data: Dict[str, Any], 
                  additional_context: Optional[Dict[str, Any]] = None,
                  debug: bool = False) -> bool:
        """
        Log an event to the JSONL file.
        
        Args:
            event_data: The main event data to log
            additional_context: Additional context to include
            debug: Whether to print debug information
            
        Returns:
            bool: True if logging succeeded, False otherwise
        """
        try:
            if debug:
                print(f"[DEBUG] Creating logs directory: {self.logs_dir}", file=sys.stderr)
            
            # Ensure directory exists
            self._ensure_logs_dir()
            
            if debug:
                print("[DEBUG] Adding timestamp and context to data", file=sys.stderr)
            
            # Enrich the data with timestamp and context
            enriched_data = {
                **event_data,
                'logged_at': datetime.now(timezone.utc).isoformat(),  # Use UTC timezone
                'working_directory': str(Path.cwd()),
                'hook_name': self.hook_name,
                'project_root': str(self.project_root)
            }
            
            # Add additional context if provided
            if additional_context:
                enriched_data.update(additional_context)
            
            if debug:
                print(f"[DEBUG] Writing to log file: {self.log_file}", file=sys.stderr)
            
            # Append to JSONL file
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(enriched_data, ensure_ascii=False) + '\n')
            
            if debug:
                print(f"[DEBUG] {self.hook_name} event logged successfully", file=sys.stderr)
            
            return True
            
        except Exception as e:
            if debug:
                print(f"[DEBUG] Failed to log {self.hook_name} event: {e}", file=sys.stderr)
            print(f"[WARNING] Failed to log {self.hook_name} event: {e}", file=sys.stderr)
            return False
    
    def log_tool_use(self, input_data: Dict[str, Any], debug: bool = False) -> bool:
        """
        Log a tool use event with project-specific enrichment.
        
        Args:
            input_data: The hook input data
            debug: Whether to print debug information
            
        Returns:
            bool: True if logging succeeded
        """
        # Extract tool information
        tool_info = {
            'tool_name': input_data.get('tool_name', 'unknown'),
            'session_id': input_data.get('session_id', 'unknown'),
            'has_tool_input': 'tool_input' in input_data,
            'has_tool_response': 'tool_response' in input_data
        }
        
        # Add file path information for file-related tools
        if tool_input := input_data.get('tool_input', {}):
            if file_path := tool_input.get('file_path'):
                tool_info['file_path'] = file_path
                tool_info['is_documentation'] = self._is_documentation_file(file_path)
        
        return self.log_event(input_data, tool_info, debug)
    
    def log_stop_event(self, input_data: Dict[str, Any], 
                      agent_type: str = 'main', debug: bool = False) -> bool:
        """
        Log a stop event with project-specific enrichment.
        
        Args:
            input_data: The hook input data
            agent_type: Type of agent ('main' or 'subagent')
            debug: Whether to print debug information
            
        Returns:
            bool: True if logging succeeded
        """
        stop_info = {
            'agent_type': agent_type,
            'session_id': input_data.get('session_id', 'unknown'),
            'stop_hook_active': input_data.get('stop_hook_active', False)
        }
        
        return self.log_event(input_data, stop_info, debug)
    
    def _is_documentation_file(self, file_path: str) -> bool:
        """Check if the file is documentation-related."""
        if not file_path:
            return False
        
        doc_indicators = ['/docs/', '/documentation/', 'README.md', 'CLAUDE.md', '.md']
        return any(indicator in file_path for indicator in doc_indicators)
    
    def get_log_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the log file.
        
        Returns:
            Dict with log statistics
        """
        stats = {
            'log_file': str(self.log_file),
            'exists': self.log_file.exists(),
            'size_bytes': 0,
            'line_count': 0,
            'last_modified': None
        }
        
        if self.log_file.exists():
            try:
                stat = self.log_file.stat()
                stats['size_bytes'] = stat.st_size
                stats['last_modified'] = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
                
                # Count lines
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    stats['line_count'] = sum(1 for _ in f)
                    
            except (OSError, PermissionError) as e:
                stats['error'] = str(e)
        
        return stats


def create_logger(project_root: Path, hook_name: str) -> HookLogger:
    """
    Factory function to create a logger instance.
    
    Args:
        project_root: Project root directory
        hook_name: Name of the hook
        
    Returns:
        HookLogger instance
    """
    return HookLogger(project_root, hook_name)


def log_quick_event(project_root: Path, hook_name: str, 
                   event_data: Dict[str, Any], debug: bool = False) -> bool:
    """
    Quick logging function for simple events.
    
    Args:
        project_root: Project root directory
        hook_name: Name of the hook
        event_data: Event data to log
        debug: Whether to print debug information
        
    Returns:
        bool: True if logging succeeded
    """
    logger = create_logger(project_root, hook_name)
    return logger.log_event(event_data, debug=debug)


if __name__ == '__main__':
    # Test the logging utilities
    from pathlib import Path
    
    # Create test logger
    test_root = Path.cwd()
    logger = create_logger(test_root, 'test_hook')
    
    # Test logging
    test_data = {
        'test_event': True,
        'message': 'Testing generic hook logger'
    }
    
    success = logger.log_event(test_data, debug=True)
    print(f"Logging {'succeeded' if success else 'failed'}")
    
    # Show stats
    stats = logger.get_log_stats()
    print(f"Log stats: {stats}")