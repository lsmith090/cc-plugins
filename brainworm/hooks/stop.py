#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
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

from utils.hook_framework import HookFramework

def stop_session_logic(framework, typed_input):
    """Custom logic for session stop with correlation cleanup."""
    # Handle both typed input and raw dict for graceful degradation
    if hasattr(typed_input, 'session_id'):
        session_id = typed_input.session_id
    elif isinstance(typed_input, dict):
        session_id = typed_input.get('session_id', 'unknown')
    else:
        session_id = 'unknown'

    # Debug logging - INFO level
    if framework.debug_logger:
        session_short = session_id[:8] if len(session_id) >= 8 else session_id
        framework.debug_logger.info(f"🧹 Clearing session correlation for {session_short}")

    try:
        from utils.correlation_manager import CorrelationManager

        correlation_manager = CorrelationManager(framework.project_root)
        correlation_manager.clear_session_correlation(session_id)

        # Debug logging - DEBUG level
        if framework.debug_logger:
            framework.debug_logger.debug("✓ Session correlation cleared")

    except Exception as e:
        if framework.debug_logger:
            framework.debug_logger.warning(f"⚠️ Session correlation cleanup failed: {type(e).__name__}")
        print(f"Warning: Session correlation cleanup failed", file=sys.stderr)

def stop_success_message(framework):
    """Custom success message for stop hook."""
    # Handle both typed input and raw dict for graceful degradation
    if hasattr(framework, 'typed_input') and framework.typed_input:
        typed_input = framework.typed_input
        if hasattr(typed_input, 'session_id'):
            session_id = typed_input.session_id
        elif isinstance(typed_input, dict):
            session_id = typed_input.get('session_id', 'unknown')
        else:
            session_id = 'unknown'
    else:
        session_id = framework.raw_input_data.get('session_id', 'unknown')
    session_short = session_id[:8] if len(session_id) >= 8 else session_id
    print(f"✅ Session stopped: {session_short}", file=sys.stderr)

if __name__ == "__main__":
    HookFramework("stop", enable_event_logging=True) \
        .with_custom_logic(stop_session_logic) \
        .with_success_handler(stop_success_message) \
        .execute()