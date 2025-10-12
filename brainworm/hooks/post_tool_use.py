#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
# ]
# ///

"""
Post-Tool Use Hook - Framework Implementation

Captures tool execution results with event logging and subagent cleanup.
"""

# Add plugin root to sys.path before any utils imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Dict, Any

from utils.hook_framework import HookFramework
from utils.business_controllers import create_subagent_manager

def determine_tool_success(tool_response: Dict[str, Any]) -> bool:
    """Determine if tool execution was successful based on response indicators."""
    if not tool_response:
        return False

    # Check explicit success field
    if "success" in tool_response:
        return bool(tool_response["success"])

    # Check for error indicators
    if tool_response.get("is_error", False):
        return False

    if "error" in tool_response:
        return False

    # Check for common failure indicators in response text
    failure_indicators = ["failed", "error", "exception", "timeout"]
    response_text = str(tool_response).lower()
    if any(indicator in response_text for indicator in failure_indicators):
        return False

    return True

def post_tool_use_logic(framework, input_data: Dict[str, Any]):
    """Custom logic for post-tool use processing.

    Args:
        framework: HookFramework instance
        input_data: Raw input dict (always dict, typed input used for validation only)
    """
    # Extract data from dict - simple and direct
    tool_name = input_data.get('tool_name', 'unknown')
    tool_response = input_data.get('tool_response', {})

    # Clean up subagent flag if Task tool completed
    subagent_manager = create_subagent_manager(framework.project_root)
    cleanup_performed = subagent_manager.cleanup_on_task_completion(tool_name)

    if framework.debug_logger and cleanup_performed:
        framework.debug_logger.info(f"Subagent context cleanup performed for {tool_name}")

    # Analyze tool success - tool_response is already a dict
    success = determine_tool_success(tool_response)

    # Store success for the success message handler
    framework.tool_success = success

    # Debug logging - INFO level
    if framework.debug_logger:
        status_icon = "✅" if success else "❌"
        framework.debug_logger.info(f"{status_icon} Tool completed: {tool_name} (success={success})")

    # No decision output needed for post-tool-use hooks
    # (they observe what happened, don't control execution)

def post_tool_use_success_message(framework):
    """Custom success message for post-tool use hook."""
    # Direct dict access - simple and clear
    tool_name = framework.raw_input_data.get('tool_name', 'unknown')
    session_id = framework.raw_input_data.get('session_id', 'unknown')
    session_short = session_id[:8] if len(session_id) >= 8 else session_id

    # Get success status
    success = getattr(framework, 'tool_success', True)
    success_status = "✅" if success else "❌"

    print(f"{success_status} Tool completed: {tool_name} (Session: {session_short})", file=sys.stderr)

if __name__ == "__main__":
    HookFramework("post_tool_use", enable_event_logging=True).with_custom_logic(post_tool_use_logic).with_success_handler(post_tool_use_success_message).execute()