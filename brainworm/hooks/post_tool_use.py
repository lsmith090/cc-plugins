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

from utils.hook_framework import HookFramework
from utils.business_controllers import create_subagent_manager, create_tool_analyzer
from utils.analysis_utils import create_file_path_extractor, create_command_extractor
import sys

def post_tool_use_logic(framework, typed_input):
    """Custom logic for post-tool use processing."""
    # Extract basic info from typed input
    tool_name = typed_input.tool_name
    
    # Clean up subagent flag if Task tool completed
    subagent_manager = create_subagent_manager(framework.project_root)
    subagent_manager.cleanup_on_task_completion(tool_name)
    
    # Analyze tool success
    tool_analyzer = create_tool_analyzer()
    tool_response = typed_input.tool_response
    tool_response_dict = tool_response.to_dict() if tool_response and hasattr(tool_response, 'to_dict') else {}
    success = tool_analyzer.determine_success(tool_response_dict)
    
    # Extract file paths and commands for analytics
    file_extractor = create_file_path_extractor()
    command_extractor = create_command_extractor()
    
    tool_input_dict = typed_input.tool_input.to_dict() if typed_input.tool_input and hasattr(typed_input.tool_input, 'to_dict') else {}
    file_paths = file_extractor.extract_from_tool_input(tool_input_dict)
    command_info = command_extractor.extract_command_info(tool_input_dict)
    
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
    # Access typed input from framework if available, fallback to raw data
    if hasattr(framework, 'typed_input') and framework.typed_input:
        tool_name = framework.typed_input.tool_name
        session_id = framework.typed_input.session_id
    else:
        tool_name = framework.raw_input_data.get('tool_name', 'unknown')
        session_id = framework.raw_input_data.get('session_id', 'unknown')
    
    session_short = session_id[:8] if len(session_id) >= 8 else session_id
    
    # Get success status
    success = getattr(framework, 'extracted_data', {}).get('tool_success', True)
    success_status = "✅" if success else "❌"
    
    print(f"{success_status} Tool completed: {tool_name} (Session: {session_short})", file=sys.stderr)

if __name__ == "__main__":
    HookFramework("post_tool_use").with_custom_logic(post_tool_use_logic).with_extractor(post_tool_use_analytics_extractor).with_success_handler(post_tool_use_success_message).execute()