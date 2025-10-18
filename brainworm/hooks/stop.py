# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
#     "filelock>=3.13.0",
# ]
# ///

"""
Stop Hook - Framework Implementation

Handles session stop with correlation cleanup.
"""

# Add plugin root to sys.path before any utils imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Dict, Any
from utils.hook_framework import HookFramework
from utils.correlation_manager import CorrelationManager

def stop_session_logic(framework, input_data: Dict[str, Any]):
    """Custom logic for session stop with correlation cleanup.

    Args:
        framework: HookFramework instance
        input_data: Raw input dict (always dict, typed input used for validation only)
    """
    # Extract data from dict - simple and direct
    session_id = input_data.get('session_id', 'unknown')

    # Debug logging - INFO level
    if framework.debug_logger:
        session_short = session_id[:8] if len(session_id) >= 8 else session_id
        framework.debug_logger.info(f"🧹 Clearing session correlation for {session_short}")

    try:
        correlation_manager = CorrelationManager(framework.project_root)
        correlation_manager.clear_session_correlation(session_id)

        # Debug logging - DEBUG level
        if framework.debug_logger:
            framework.debug_logger.debug("✓ Session correlation cleared")

    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)

        # Provide actionable error messages based on error type
        if "Permission" in error_type or "PermissionError" in error_type:
            action = "Check file permissions on .brainworm/state directory"
        elif "FileNotFound" in error_type or "NotFound" in error_type:
            action = "Correlation state may already be cleared"
        elif "JSONDecodeError" in error_type:
            action = "Correlation state file may be corrupted, consider removing .brainworm/state/.correlation_state"
        else:
            action = "Check .brainworm/debug_*.log for details"

        if framework.debug_logger:
            framework.debug_logger.warning(
                f"⚠️ Session correlation cleanup failed: {error_type}: {error_msg}"
            )
        print(f"Warning: Session correlation cleanup failed ({error_type}). {action}", file=sys.stderr)

def stop_success_message(framework):
    """Custom success message for stop hook."""
    # Direct dict access - simple and clear
    session_id = framework.raw_input_data.get('session_id', 'unknown')
    session_short = session_id[:8] if len(session_id) >= 8 else session_id
    print(f"✅ Session stopped: {session_short}", file=sys.stderr)

if __name__ == "__main__":
    HookFramework("stop", enable_event_logging=True) \
        .with_custom_logic(stop_session_logic) \
        .with_success_handler(stop_success_message) \
        .execute()