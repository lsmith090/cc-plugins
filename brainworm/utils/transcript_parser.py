#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""
Claude Code Transcript Parser

Parses Claude Code transcript files to extract tool execution data
for analytics and hook processing.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def parse_transcript_for_tool_data(transcript_path: str, debug: bool = False) -> List[Dict[str, Any]]:
    """
    Parse Claude Code transcript to extract tool execution events.

    Args:
        transcript_path: Path to the Claude Code transcript file
        debug: Whether to print debug information

    Returns:
        List of tool execution events with standardized structure
    """
    if debug:
        print(f"[DEBUG] Parsing transcript: {transcript_path}", file=sys.stderr)

    try:
        transcript_file = Path(transcript_path)
        if not transcript_file.exists():
            if debug:
                print(f"[DEBUG] Transcript file not found: {transcript_path}", file=sys.stderr)
            return []

        tool_events = []

        with open(transcript_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)

                    # Look for tool invocation events
                    if is_tool_event(event):
                        tool_data = extract_tool_data(event, line_num, debug)
                        if tool_data:
                            tool_events.append(tool_data)

                except json.JSONDecodeError as e:
                    if debug:
                        print(f"[DEBUG] JSON decode error on line {line_num}: {e}", file=sys.stderr)
                    continue

        if debug:
            print(f"[DEBUG] Found {len(tool_events)} tool events", file=sys.stderr)

        return tool_events

    except Exception as e:
        if debug:
            print(f"[DEBUG] Transcript parsing error: {e}", file=sys.stderr)
        return []


def is_tool_event(event: Dict[str, Any]) -> bool:
    """Check if an event represents tool execution."""
    # Look for tool invocation patterns in Claude Code transcripts

    # Check for function calls with tool names
    if event.get('type') == 'function_calls':
        return True

    # Check for tool results
    if event.get('type') == 'function_results':
        return True

    # Check for message with tool usage
    if event.get('type') == 'message':
        content = event.get('content', [])
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    if item.get('type') == 'tool_use':
                        return True
                    if item.get('type') == 'tool_result':
                        return True

    return False


def extract_tool_data(event: Dict[str, Any], line_num: int, debug: bool = False) -> Optional[Dict[str, Any]]:
    """Extract standardized tool data from a transcript event."""

    try:
        # Handle different event structures
        if event.get('type') == 'function_calls':
            return extract_from_function_calls(event, line_num, debug)

        elif event.get('type') == 'function_results':
            return extract_from_function_results(event, line_num, debug)

        elif event.get('type') == 'message':
            return extract_from_message(event, line_num, debug)

    except Exception as e:
        if debug:
            print(f"[DEBUG] Tool data extraction error on line {line_num}: {e}", file=sys.stderr)

    return None


def extract_from_function_calls(event: Dict[str, Any], line_num: int, debug: bool = False) -> Optional[Dict[str, Any]]:
    """Extract tool data from function_calls event."""

    if 'function_calls' not in event:
        return None

    # Claude Code typically has an array of function calls
    calls = event['function_calls']
    if not isinstance(calls, list) or not calls:
        return None

    # Take the first call (most common case)
    call = calls[0]

    tool_data = {
        'event_type': 'tool_invocation',
        'transcript_line': line_num,
        'timestamp': event.get('timestamp'),
        'tool_name': call.get('name', 'unknown'),
        'tool_input': call.get('parameters', {}),
        'tool_id': call.get('id'),
        'raw_event': event
    }

    if debug:
        print(f"[DEBUG] Extracted tool invocation: {tool_data['tool_name']}", file=sys.stderr)

    return tool_data


def extract_from_function_results(event: Dict[str, Any], line_num: int, debug: bool = False) -> Optional[Dict[str, Any]]:
    """Extract tool data from function_results event."""

    if 'function_results' not in event:
        return None

    results = event['function_results']
    if not isinstance(results, list) or not results:
        return None

    # Take the first result
    result = results[0]

    tool_data = {
        'event_type': 'tool_result',
        'transcript_line': line_num,
        'timestamp': event.get('timestamp'),
        'tool_id': result.get('call_id'),
        'success': not result.get('is_error', False),
        'tool_result': result.get('content'),
        'error': result.get('content') if result.get('is_error') else None,
        'raw_event': event
    }

    if debug:
        print(f"[DEBUG] Extracted tool result: success={tool_data['success']}", file=sys.stderr)

    return tool_data


def extract_from_message(event: Dict[str, Any], line_num: int, debug: bool = False) -> Optional[Dict[str, Any]]:
    """Extract tool data from message event."""

    content = event.get('content', [])
    if not isinstance(content, list):
        return None

    for item in content:
        if not isinstance(item, dict):
            continue

        if item.get('type') == 'tool_use':
            tool_data = {
                'event_type': 'tool_invocation',
                'transcript_line': line_num,
                'timestamp': event.get('timestamp'),
                'tool_name': item.get('name', 'unknown'),
                'tool_input': item.get('input', {}),
                'tool_id': item.get('id'),
                'raw_event': event
            }

            if debug:
                print(f"[DEBUG] Extracted tool use: {tool_data['tool_name']}", file=sys.stderr)

            return tool_data

        elif item.get('type') == 'tool_result':
            tool_data = {
                'event_type': 'tool_result',
                'transcript_line': line_num,
                'timestamp': event.get('timestamp'),
                'tool_id': item.get('tool_use_id'),
                'success': not item.get('is_error', False),
                'tool_result': item.get('content'),
                'error': item.get('content') if item.get('is_error') else None,
                'raw_event': event
            }

            if debug:
                print(f"[DEBUG] Extracted tool result: success={tool_data['success']}", file=sys.stderr)

            return tool_data

    return None


def correlate_tool_events(tool_events: List[Dict[str, Any]], debug: bool = False) -> List[Dict[str, Any]]:
    """Correlate tool invocations with their results."""

    if debug:
        print(f"[DEBUG] Correlating {len(tool_events)} tool events", file=sys.stderr)

    # Group by tool_id
    invocations = {}
    results = {}

    for event in tool_events:
        tool_id = event.get('tool_id')
        if not tool_id:
            continue

        if event.get('event_type') == 'tool_invocation':
            invocations[tool_id] = event
        elif event.get('event_type') == 'tool_result':
            results[tool_id] = event

    # Combine invocations with results
    correlated_events = []

    for tool_id, invocation in invocations.items():
        result = results.get(tool_id)

        combined_event = {
            **invocation,
            'event_type': 'tool_execution',
            'has_result': result is not None
        }

        if result:
            combined_event.update({
                'success': result.get('success', False),
                'tool_result': result.get('tool_result'),
                'error': result.get('error'),
                'result_timestamp': result.get('timestamp'),
                'execution_duration_ms': calculate_duration(
                    invocation.get('timestamp'),
                    result.get('timestamp')
                )
            })

        correlated_events.append(combined_event)

        if debug:
            status = "with result" if result else "no result"
            print(f"[DEBUG] Correlated {invocation.get('tool_name')} {status}", file=sys.stderr)

    return correlated_events


def calculate_duration(start_timestamp: Optional[str], end_timestamp: Optional[str]) -> Optional[float]:
    """Calculate duration between two ISO timestamps in milliseconds."""

    if not start_timestamp or not end_timestamp:
        return None

    try:
        from datetime import datetime
        start = datetime.fromisoformat(start_timestamp.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_timestamp.replace('Z', '+00:00'))
        duration_seconds = (end - start).total_seconds()
        return duration_seconds * 1000  # Convert to milliseconds
    except Exception:
        return None


def get_latest_tool_execution(transcript_path: str, debug: bool = False) -> Optional[Dict[str, Any]]:
    """Get the most recent tool execution from the transcript."""

    tool_events = parse_transcript_for_tool_data(transcript_path, debug)
    if not tool_events:
        return None

    correlated_events = correlate_tool_events(tool_events, debug)
    if not correlated_events:
        return None

    # Return the last tool execution
    return correlated_events[-1]


if __name__ == '__main__':
    # Test the transcript parser
    import argparse

    parser = argparse.ArgumentParser(description='Test transcript parser')
    parser.add_argument('transcript_path', help='Path to transcript file')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--latest-only', action='store_true', help='Show only latest tool execution')

    args = parser.parse_args()

    if args.latest_only:
        latest = get_latest_tool_execution(args.transcript_path, args.debug)
        if latest:
            print(json.dumps(latest, indent=2))
        else:
            print("No tool executions found")
    else:
        tool_events = parse_transcript_for_tool_data(args.transcript_path, args.debug)
        correlated = correlate_tool_events(tool_events, args.debug)

        print(f"Found {len(correlated)} tool executions:")
        for event in correlated:
            print(json.dumps(event, indent=2))
