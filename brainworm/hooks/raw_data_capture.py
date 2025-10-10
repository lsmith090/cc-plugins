#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""
Raw Data Capture Utilities for Simplified Claude Code Hooks

Shared utilities for all simplified hooks to capture raw data.
All hooks should use the same basic pattern for consistency.
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any
from utils.project import find_project_root
from utils.git import get_basic_git_context


def read_raw_input() -> Dict[str, Any]:
    """Read raw JSON input from Claude Code stdin"""
    input_text = sys.stdin.read()
    return json.loads(input_text) if input_text.strip() else {}


# Removed - now using shared function from utils.project


# Removed - now using shared function from utils.git


def log_raw_event(hook_name: str, raw_input_data: Dict[str, Any], extra_data: Dict[str, Any] = None) -> bool:
    """Log raw event data using analytics processor"""
    try:
        # Import analytics processor
        sys.path.insert(0, str(Path(__file__).parent.parent))  # Add plugin root for utils access
        from utils.analytics_processor import ClaudeAnalyticsProcessor
        
        # Initialize processor
        processor = ClaudeAnalyticsProcessor(Path(__file__).parent.parent)
        
        # Find project root
        project_root = find_project_root()
        
        # Create standard raw event structure
        raw_event = {
            'hook_name': hook_name,
            'event_type': 'raw_execution',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'session_id': raw_input_data.get('session_id', 'unknown'),
            'raw_input': raw_input_data,
            'git_context': get_basic_git_context(project_root),
            'project_root': str(project_root),
            'success': True
        }
        
        # Add any extra data
        if extra_data:
            raw_event.update(extra_data)
        
        # Log the event
        return processor.log_event(raw_event)
        
    except Exception as e:
        print(f"Warning: Analytics processing failed: {e}", file=sys.stderr)
        return False


def create_standard_raw_hook(hook_name: str, extract_extra_data_fn=None):
    """Create a standardized raw data capture hook function"""
    
    def hook_main():
        """Standardized hook main function"""
        try:
            # Read raw input from Claude Code
            raw_input_data = read_raw_input()
            
            # Process analytics if requested
            if '--analytics' in sys.argv:
                # Get extra data if function provided
                extra_data = {}
                if extract_extra_data_fn:
                    try:
                        extra_data = extract_extra_data_fn(raw_input_data)
                    except Exception as e:
                        print(f"Warning: Extra data extraction failed: {e}", file=sys.stderr)
                
                # Log raw event
                success = log_raw_event(hook_name, raw_input_data, extra_data)
                
                if '--verbose' in sys.argv:
                    from rich.console import Console
                    console = Console()
                    if success:
                        console.print("[green]✅ Raw data logged to analytics[/green]")
                    else:
                        console.print("[yellow]⚠️ Analytics logging failed[/yellow]")
            
            # Display basic feedback
            if '--verbose' in sys.argv:
                from rich.console import Console
                console = Console()
                session_id = raw_input_data.get('session_id', 'unknown')
                console.print(f"[green]✅ {hook_name} completed:[/green] {session_id[:8]}")
            
            # Exit successfully
            sys.exit(0)
            
        except json.JSONDecodeError:
            print("Warning: Invalid JSON input", file=sys.stderr)
            sys.exit(0)
        except Exception as e:
            print(f"Warning: {hook_name} error: {e}", file=sys.stderr)
            sys.exit(0)
    
    return hook_main


# Specific data extractors for different hooks
def extract_file_data(raw_input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract file-related data for file operation hooks"""
    tool_input = raw_input_data.get('tool_input', {})
    extra_data = {}
    
    if file_path := tool_input.get('file_path'):
        extra_data['file_path'] = file_path
    
    return extra_data


def extract_command_data(raw_input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract command data for bash operation hooks"""
    tool_input = raw_input_data.get('tool_input', {})
    extra_data = {}
    
    if command := tool_input.get('command'):
        extra_data['command'] = command
    
    return extra_data


def extract_tool_data(raw_input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract tool execution data for tool operation hooks"""
    extra_data = {}
    
    if tool_name := raw_input_data.get('tool_name'):
        extra_data['tool_name'] = tool_name
    
    if tool_response := raw_input_data.get('tool_response'):
        # Determine success from tool response
        if isinstance(tool_response, dict):
            if tool_response.get('is_error', False):
                extra_data['tool_success'] = False
            elif 'success' in tool_response:
                extra_data['tool_success'] = tool_response['success']
            else:
                extra_data['tool_success'] = True
    
    return extra_data


def extract_prompt_data(raw_input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract basic prompt data for prompt submission hooks"""
    prompt = raw_input_data.get('prompt', '')
    
    return {
        'prompt_info': {
            'length_chars': len(prompt),
            'word_count': len(prompt.split()),
            'has_question': '?' in prompt,
            'has_code_references': bool('`' in prompt or '.py' in prompt or '.js' in prompt),
            'is_empty': len(prompt.strip()) == 0
        }
    }


if __name__ == '__main__':
    # This module provides utilities, not a standalone hook
    print("Raw Data Capture Utilities - not a standalone hook", file=sys.stderr)
    sys.exit(1)