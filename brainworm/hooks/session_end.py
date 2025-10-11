#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["rich>=13.0.0"]
# ///

"""
Session End Hook - Framework Implementation

Creates session snapshot on actual session termination.
Handles session end with correlation cleanup.
"""

# Add plugin root to sys.path before any utils imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import subprocess
from utils.hook_framework import HookFramework

def session_end_logic(framework, typed_input):
    """Custom logic for session end with snapshot creation."""
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
        framework.debug_logger.info(f"🔚 Session ending: {session_short}")

    # Create session snapshot (moved from stop.py)
    try:
        snapshot_script = framework.project_root / ".brainworm" / "scripts" / "snapshot_session.py"
        if snapshot_script.exists():
            if framework.debug_logger:
                framework.debug_logger.debug(f"📸 Creating session end snapshot")

            subprocess.run([
                str(snapshot_script),
                "--action", "stop",
                "--session-id", session_id,
                "--quiet"
            ], timeout=10, check=False)

            if framework.debug_logger:
                framework.debug_logger.debug("Snapshot script executed")
    except Exception as e:
        if framework.debug_logger:
            framework.debug_logger.warning(f"⚠️ Snapshot creation failed: {type(e).__name__}")
        pass  # Don't fail session end if snapshot fails

def session_end_success_message(framework):
    """Custom success message for session end hook."""
    # Handle both typed input and raw dict for graceful degradation
    if hasattr(framework, 'typed_input') and framework.typed_input:
        typed_input = framework.typed_input
        if hasattr(typed_input, 'session_id'):
            session_id = typed_input.session_id
        elif isinstance(typed_input, dict):
            session_id = typed_input.get('session_id', 'unknown')
        else:
            session_id = 'unknown'
        reason = framework.raw_input_data.get('reason', 'unknown')
    else:
        session_id = framework.raw_input_data.get('session_id', 'unknown')
        reason = framework.raw_input_data.get('reason', 'unknown')

    session_short = session_id[:8] if len(session_id) >= 8 else session_id
    print(f"✅ Session ended ({reason}): {session_short}", file=sys.stderr)

if __name__ == "__main__":
    HookFramework("session_end", enable_analytics=True, enable_logging=True) \
        .with_custom_logic(session_end_logic) \
        .with_success_handler(session_end_success_message) \
        .execute()
