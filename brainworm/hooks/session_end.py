# /// script
# requires-python = ">=3.12"
# dependencies = ["rich>=13.0.0", "filelock>=3.13.0"]
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
from typing import Dict, Any
from utils.hook_framework import HookFramework

def session_end_logic(framework, input_data: Dict[str, Any]):
    """Custom logic for session end with snapshot creation.

    Args:
        framework: HookFramework instance
        input_data: Raw input dict (always dict, typed input used for validation only)
    """
    # Extract data from dict - simple and direct
    session_id = input_data.get('session_id', 'unknown')

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
    # Direct dict access - simple and clear
    session_id = framework.raw_input_data.get('session_id', 'unknown')
    reason = framework.raw_input_data.get('reason', 'unknown')
    session_short = session_id[:8] if len(session_id) >= 8 else session_id
    print(f"✅ Session ended ({reason}): {session_short}", file=sys.stderr)

if __name__ == "__main__":
    HookFramework("session_end", enable_event_logging=True) \
        .with_custom_logic(session_end_logic) \
        .with_success_handler(session_end_success_message) \
        .execute()
