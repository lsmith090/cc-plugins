# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
#     "filelock>=3.13.0",
# ]
# ///

"""
Subagent Stop Hook - Hooks Framework

Captures subagent stop events with specialized event logging.
"""

# Add plugin root to sys.path before any utils imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Dict, Any
from utils.hook_framework import HookFramework


def subagent_stop_logic(framework, input_data: Dict[str, Any]):
    """Custom logic for subagent stop processing.

    Args:
        framework: HookFramework instance
        input_data: Raw input dict (always dict, typed input used for validation only)
    """
    # Extract data from dict - simple and direct
    session_id = input_data.get('session_id', 'unknown')

    # Debug logging - INFO level
    if framework.debug_logger:
        session_short = session_id[:8] if len(session_id) >= 8 else session_id
        framework.debug_logger.info(f"🤖 Subagent stopped: {session_short}")
        framework.debug_logger.debug("Event marked as subagent context")

    # Event data will be automatically logged by framework with agent_type metadata
    # No additional processing needed - hook just observes the subagent stop


def subagent_stop_success_message(framework):
    """Generate success message for subagent stop"""
    # Direct dict access - simple and clear
    session_id = framework.raw_input_data.get('session_id', 'unknown')
    session_short = session_id[:8] if len(session_id) >= 8 else session_id
    print(f"✅ Subagent stopped: {session_short}", file=sys.stderr)


def main() -> None:
    """Main entry point for subagent stop hook"""
    HookFramework("subagent_stop", enable_event_logging=True) \
        .with_custom_logic(subagent_stop_logic) \
        .with_success_handler(subagent_stop_success_message) \
        .execute()


if __name__ == '__main__':
    main()