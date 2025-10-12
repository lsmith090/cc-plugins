#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
# ]
# ///

"""
Post-Tool Use Hook - Framework Implementation

Captures tool execution results with analytics and subagent cleanup.
"""

# Add plugin root to sys.path before any utils imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.hook_framework import HookFramework
from utils.business_controllers import create_subagent_manager, create_tool_analyzer
from utils.analysis_utils import create_file_path_extractor, create_command_extractor

def post_tool_use_logic(framework, typed_input):
    """Custom logic for post-tool use processing."""
    # Handle both typed input and raw dict for graceful degradation
    if hasattr(typed_input, 'tool_name'):
        tool_name = typed_input.tool_name
        tool_response = typed_input.tool_response
        tool_input = typed_input.tool_input
    elif isinstance(typed_input, dict):
        tool_name = typed_input.get('tool_name', 'unknown')
        tool_response = typed_input.get('tool_response')
        tool_input = typed_input.get('tool_input')
    else:
        tool_name = 'unknown'
        tool_response = None
        tool_input = None

    # Clean up subagent flag if Task tool completed
    subagent_manager = create_subagent_manager(framework.project_root)
    cleanup_performed = subagent_manager.cleanup_on_task_completion(tool_name)

    if framework.debug_logger and cleanup_performed:
        framework.debug_logger.info(f"Subagent context cleanup performed for {tool_name}")

    # Analyze tool success
    tool_analyzer = create_tool_analyzer()
    tool_response_dict = tool_response.to_dict() if tool_response and hasattr(tool_response, 'to_dict') else (tool_response if isinstance(tool_response, dict) else {})
    success = tool_analyzer.determine_success(tool_response_dict)

    # Debug logging - INFO level
    if framework.debug_logger:
        status_icon = "✅" if success else "❌"
        framework.debug_logger.info(f"{status_icon} Tool completed: {tool_name} (success={success})")

    # Extract file paths and commands for analytics
    file_extractor = create_file_path_extractor()
    command_extractor = create_command_extractor()

    tool_input_dict = tool_input.to_dict() if tool_input and hasattr(tool_input, 'to_dict') else (tool_input if isinstance(tool_input, dict) else {})
    file_paths = file_extractor.extract_from_tool_input(tool_input_dict)
    command_info = command_extractor.extract_command_info(tool_input_dict)

    # Debug logging - DEBUG level with details
    if framework.debug_logger:
        if file_paths:
            framework.debug_logger.debug(f"File paths: {', '.join(file_paths[:3])}" + (" ..." if len(file_paths) > 3 else ""))
        if command_info:
            cmd = command_info.get('command', '')
            if cmd:
                framework.debug_logger.debug(f"Command: {cmd[:80]}" + ("..." if len(cmd) > 80 else ""))

    # Store extracted data for analytics
    framework.extracted_data = {
        'tool_success': success,
        'file_paths': file_paths,
        'command_info': command_info
    }

    # No decision output needed for post-tool-use hooks
    # (they observe what happened, don't control execution)

def post_tool_use_analytics_extractor(raw_input_data):
    """Custom analytics extractor for post-tool use events."""
    extra_data = {}
    
    # Extract tool information
    tool_name = raw_input_data.get('tool_name', 'unknown')
    extra_data['tool_name'] = tool_name
    
    # Extract file path if it's a file operation
    tool_input = raw_input_data.get('tool_input', {})
    if 'file_path' in tool_input:
        extra_data['file_path'] = tool_input['file_path']
    
    # Extract command if it's a Bash operation
    if 'command' in tool_input:
        extra_data['command'] = tool_input['command']
    
    # Determine success
    tool_response = raw_input_data.get('tool_response', {})
    if isinstance(tool_response, dict):
        if tool_response.get('is_error', False):
            extra_data['success'] = False
        elif 'success' in tool_response:
            extra_data['success'] = tool_response['success']
        else:
            extra_data['success'] = True
    else:
        extra_data['success'] = True
    
    return extra_data

def post_tool_use_success_message(framework):
    """Custom success message for post-tool use hook."""
    # Handle both typed input and raw dict for graceful degradation
    if hasattr(framework, 'typed_input') and framework.typed_input:
        typed_input = framework.typed_input
        if hasattr(typed_input, 'tool_name'):
            tool_name = typed_input.tool_name
            session_id = typed_input.session_id
        elif isinstance(typed_input, dict):
            tool_name = typed_input.get('tool_name', 'unknown')
            session_id = typed_input.get('session_id', 'unknown')
        else:
            tool_name = 'unknown'
            session_id = 'unknown'
    else:
        tool_name = framework.raw_input_data.get('tool_name', 'unknown')
        session_id = framework.raw_input_data.get('session_id', 'unknown')

    session_short = session_id[:8] if len(session_id) >= 8 else session_id

    # Get success status
    success = getattr(framework, 'extracted_data', {}).get('tool_success', True)
    success_status = "✅" if success else "❌"

    print(f"{success_status} Tool completed: {tool_name} (Session: {session_short})", file=sys.stderr)

if __name__ == "__main__":
    HookFramework("post_tool_use", enable_event_logging=True).with_custom_logic(post_tool_use_logic).with_extractor(post_tool_use_analytics_extractor).with_success_handler(post_tool_use_success_message).execute()