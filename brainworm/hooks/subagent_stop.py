#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
# ]
# ///

"""
Subagent Stop Hook - Hooks Framework

Captures subagent stop events with specialized analytics marking.
"""

from pathlib import Path
from typing import Dict, Any
from utils.hook_framework import HookFramework


def subagent_stop_logic(framework, typed_input):
    """Custom logic for subagent stop processing"""
    
    # Configure analytics for subagent context
    analytics_config = {
        'agent_type': 'subagent',  # Mark as subagent for filtering
        'hook_name': 'subagent_stop',
        'event_type': 'raw_execution'
    }
    
    # Process subagent-specific analytics using typed input
    return framework.process_analytics(framework.raw_input_data, analytics_config)


def subagent_stop_success_message(framework):
    """Generate success message for subagent stop"""
    # Access typed input from framework if available, fallback to raw data
    if hasattr(framework, 'typed_input') and framework.typed_input:
        session_id = framework.typed_input.session_id
    else:
        session_id = framework.raw_input_data.get('session_id', 'unknown')
    session_short = session_id[:8] if len(session_id) >= 8 else session_id
    print(f"✅ Subagent stopped: {session_short}", file=sys.stderr)


def main() -> None:
    """Main entry point for subagent stop hook"""
    HookFramework("subagent_stop") \
        .with_custom_logic(subagent_stop_logic) \
        .with_success_handler(subagent_stop_success_message) \
        .execute()


if __name__ == '__main__':
    main()