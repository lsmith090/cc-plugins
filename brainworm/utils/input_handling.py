#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""
Hook Input Processing Utilities
Standardized JSON input handling and validation for Claude Code hooks
"""

import json
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

# Add parent to path for hook_types
# Import type definitions with fallback
try:
    from .hook_types import (
        BaseHookInput,
        PostToolUseInput,
        PreToolUseInput,
        ToolInputVariant,
        UserPromptSubmitInput,
        parse_tool_input,
    )
except ImportError:
    BaseHookInput = None
    PreToolUseInput = None
    PostToolUseInput = None
    UserPromptSubmitInput = None
    parse_tool_input = None
    ToolInputVariant = None


def read_hook_input(debug: bool = False) -> Dict[str, Any]:
    """
    Read and parse JSON input from stdin for Claude Code hooks.

    This function implements the proven pattern for reading hook input
    with proper error handling and debug output.

    Args:
        debug: Whether to print debug information to stderr

    Returns:
        Dict containing the parsed JSON input

    Raises:
        json.JSONDecodeError: If input is not valid JSON
        ValueError: If input is empty or invalid
    """
    if debug:
        print("[DEBUG] Reading JSON input from stdin", file=sys.stderr)

    try:
        # Read from stdin
        raw_input = sys.stdin.read().strip()

        if not raw_input:
            raise ValueError("Empty input received")

        # Parse JSON
        input_data = json.loads(raw_input)

        if debug:
            # Don't print full data as it might be large, just show keys
            keys = list(input_data.keys()) if isinstance(input_data, dict) else "non-dict"
            print(f"[DEBUG] Received input with keys: {keys}", file=sys.stderr)

        return input_data

    except json.JSONDecodeError as e:
        if debug:
            print(f"[DEBUG] JSON decode error: {e}", file=sys.stderr)
        raise
    except Exception as e:
        if debug:
            print(f"[DEBUG] Input reading error: {e}", file=sys.stderr)
        raise


def read_typed_hook_input(debug: bool = False, hook_type: str = None) -> Union[BaseHookInput, Dict[str, Any]]:
    """
    Read and parse hook input using type-safe approach with fallback.

    Args:
        debug: Whether to print debug information
        hook_type: Expected hook type ('pre_tool_use', 'post_tool_use', etc.)

    Returns:
        Typed hook input object or fallback dict
    """
    raw_input = read_hook_input(debug=debug)

    # Try typed parsing based on hook type
    if hook_type and BaseHookInput:
        try:
            if hook_type == 'pre_tool_use' and PreToolUseInput:
                return PreToolUseInput.parse(raw_input)
            elif hook_type == 'post_tool_use' and PostToolUseInput:
                return PostToolUseInput.parse(raw_input)
            elif hook_type == 'user_prompt_submit' and UserPromptSubmitInput:
                return UserPromptSubmitInput.parse(raw_input)
            else:
                return BaseHookInput.parse(raw_input)
        except Exception as e:
            if debug:
                print(f"[DEBUG] Typed parsing failed, using fallback: {e}", file=sys.stderr)
            return raw_input

    return raw_input


def validate_hook_input(input_data: Dict[str, Any],
                       required_fields: Optional[List[str]] = None,
                       debug: bool = False) -> bool:
    """
    Validate hook input data has required fields.

    Args:
        input_data: The input data to validate
        required_fields: List of required field names (default: basic hook fields)
        debug: Whether to print debug information

    Returns:
        bool: True if validation passes

    Raises:
        ValueError: If validation fails
    """
    if required_fields is None:
        required_fields = ['session_id', 'transcript_path', 'hook_event_name']

    if debug:
        print(f"[DEBUG] Validating input for required fields: {required_fields}", file=sys.stderr)

    if not isinstance(input_data, dict):
        raise ValueError("Input data must be a dictionary")

    missing_fields = []
    for field in required_fields:
        if field not in input_data:
            missing_fields.append(field)

    if missing_fields:
        error_msg = f"Missing required fields: {', '.join(missing_fields)}"
        if debug:
            print(f"[DEBUG] Validation failed: {error_msg}", file=sys.stderr)
        raise ValueError(error_msg)

    if debug:
        print("[DEBUG] Input validation passed", file=sys.stderr)

    return True


def extract_tool_info(input_data: Union[Dict[str, Any], BaseHookInput], debug: bool = False) -> Dict[str, Any]:
    """
    Extract tool-specific information from hook input using type-safe approach.

    Args:
        input_data: The hook input data (typed or untyped)
        debug: Whether to print debug information

    Returns:
        Dict containing extracted tool information
    """
    if debug:
        print("[DEBUG] Extracting tool information", file=sys.stderr)

    # Handle typed input
    if hasattr(input_data, '__class__') and hasattr(input_data, 'tool_name'):
        tool_name = getattr(input_data, 'tool_name', 'unknown')
        session_id = getattr(input_data, 'session_id', 'unknown')
        hook_event = getattr(input_data, 'hook_event_name', 'unknown')
        tool_input = getattr(input_data, 'tool_input', None)
        tool_response = getattr(input_data, 'tool_response', None)

        tool_info = {
            'tool_name': tool_name,
            'has_tool_input': tool_input is not None,
            'has_tool_response': tool_response is not None,
            'session_id': session_id,
            'hook_event': hook_event
        }

        # Extract typed tool input details
        if tool_input:
            if hasattr(tool_input, 'file_path'):
                tool_info['file_path'] = tool_input.file_path
            if hasattr(tool_input, 'command'):
                tool_info['command'] = tool_input.command
            if hasattr(tool_input, 'content'):
                tool_info['has_content'] = True
                tool_info['content_length'] = len(str(tool_input.content))

        # Extract typed tool response details
        if tool_response:
            if hasattr(tool_response, 'success'):
                tool_info['success'] = tool_response.success
            # Add more typed response fields as needed

    else:
        # Handle untyped input (fallback)
        tool_info = {
            'tool_name': input_data.get('tool_name', 'unknown'),
            'has_tool_input': 'tool_input' in input_data,
            'has_tool_response': 'tool_response' in input_data,
            'session_id': input_data.get('session_id', 'unknown'),
            'hook_event': input_data.get('hook_event_name', 'unknown')
        }

        # Extract tool input details if present
        if tool_input := input_data.get('tool_input', {}):
            tool_info['tool_input_keys'] = list(tool_input.keys())

            # Common tool input fields
            if 'file_path' in tool_input:
                tool_info['file_path'] = tool_input['file_path']
            if 'command' in tool_input:
                tool_info['command'] = tool_input['command']
            if 'content' in tool_input:
                tool_info['has_content'] = True
                tool_info['content_length'] = len(str(tool_input['content']))

        # Extract tool response details if present
        if tool_response := input_data.get('tool_response', {}):
            tool_info['tool_response_keys'] = list(tool_response.keys())

            # Common response fields
            if 'success' in tool_response:
                tool_info['success'] = tool_response['success']
            if 'error' in tool_response:
                tool_info['has_error'] = True

    if debug:
        print(f"[DEBUG] Extracted tool info: {list(tool_info.keys())}", file=sys.stderr)

    return tool_info


def extract_file_info(input_data: Union[Dict[str, Any], BaseHookInput], debug: bool = False) -> Optional[Dict[str, Any]]:
    """
    Extract file-related information from tool input using type-safe approach.

    Args:
        input_data: The hook input data (typed or untyped)
        debug: Whether to print debug information

    Returns:
        Dict with file information, or None if not a file-related tool
    """
    # Handle typed input
    if hasattr(input_data, '__class__') and hasattr(input_data, 'tool_name'):
        tool_name = getattr(input_data, 'tool_name', '')
        tool_input = getattr(input_data, 'tool_input', None)

        if debug:
            print(f"[DEBUG] Checking for file info in typed tool: {tool_name}", file=sys.stderr)

        # File-related tools
        file_tools = ['Edit', 'Write', 'MultiEdit', 'Read']

        if tool_name not in file_tools:
            if debug:
                print("[DEBUG] Not a file-related tool", file=sys.stderr)
            return None

        # Extract file path from typed tool input
        file_path = None
        if tool_input and hasattr(tool_input, 'file_path'):
            file_path = tool_input.file_path

        if not file_path:
            if debug:
                print("[DEBUG] No file_path in typed tool input", file=sys.stderr)
            return None

        file_info = {
            'file_path': file_path,
            'tool_name': tool_name,
            'is_documentation': _is_documentation_file(file_path),
            'is_code': _is_code_file(file_path),
            'is_config': _is_config_file(file_path)
        }

        # Add content information for write operations
        if tool_name in ['Write', 'Edit', 'MultiEdit'] and hasattr(tool_input, 'content'):
            content = str(tool_input.content)
            file_info.update({
                'has_content': True,
                'content_length': len(content),
                'line_count': content.count('\n') + 1 if content else 0
            })

    else:
        # Handle untyped input (fallback)
        tool_name = input_data.get('tool_name', '')
        tool_input = input_data.get('tool_input', {})

        if debug:
            print(f"[DEBUG] Checking for file info in tool: {tool_name}", file=sys.stderr)

        # File-related tools
        file_tools = ['Edit', 'Write', 'MultiEdit', 'Read']

        if tool_name not in file_tools:
            if debug:
                print("[DEBUG] Not a file-related tool", file=sys.stderr)
            return None

        file_path = tool_input.get('file_path')
        if not file_path:
            if debug:
                print("[DEBUG] No file_path in tool input", file=sys.stderr)
            return None

        file_info = {
            'file_path': file_path,
            'tool_name': tool_name,
            'is_documentation': _is_documentation_file(file_path),
            'is_code': _is_code_file(file_path),
            'is_config': _is_config_file(file_path)
        }

        # Add content information for write operations
        if tool_name in ['Write', 'Edit', 'MultiEdit'] and 'content' in tool_input:
            content = str(tool_input['content'])
            file_info.update({
                'has_content': True,
                'content_length': len(content),
                'line_count': content.count('\n') + 1 if content else 0
            })

    if debug:
        print(f"[DEBUG] Extracted file info for: {file_path}", file=sys.stderr)

    return file_info


def _is_documentation_file(file_path: str) -> bool:
    """Check if file is documentation-related."""
    if not file_path:
        return False

    doc_indicators = ['/docs/', '/documentation/', 'README.md', 'CLAUDE.md', '.md']
    return any(indicator in file_path for indicator in doc_indicators)


def _is_code_file(file_path: str) -> bool:
    """Check if file is code-related."""
    if not file_path:
        return False

    code_extensions = ['.py', '.js', '.jsx', '.ts', '.tsx', '.ps1', '.sh', '.css', '.html']
    return any(file_path.endswith(ext) for ext in code_extensions)


def _is_config_file(file_path: str) -> bool:
    """Check if file is configuration-related."""
    if not file_path:
        return False

    config_indicators = [
        '.json', '.yaml', '.yml', '.toml', '.ini', '.conf', '.config',
        'package.json', 'pyproject.toml', 'requirements.txt'
    ]
    return any(indicator in file_path for indicator in config_indicators)


def get_hook_args() -> Tuple[List[str], Dict[str, str]]:
    """
    Parse command line arguments for hooks.

    Returns:
        Tuple of (flags, key_value_args)
        - flags: List of flag arguments (starting with --)
        - key_value_args: Dict of key=value arguments
    """
    args = sys.argv[1:]  # Skip script name

    flags = []
    key_value_args = {}

    for arg in args:
        if arg.startswith('--'):
            if '=' in arg:
                key, value = arg[2:].split('=', 1)
                key_value_args[key] = value
            else:
                flags.append(arg[2:])  # Remove --
        elif '=' in arg:
            key, value = arg.split('=', 1)
            key_value_args[key] = value

    return flags, key_value_args


def should_process_tool(tool_name: str, matchers: Optional[List[str]] = None) -> bool:
    """
    Check if a tool should be processed based on matchers.

    Args:
        tool_name: Name of the tool
        matchers: List of matcher patterns (None means process all)

    Returns:
        bool: True if tool should be processed
    """
    if not matchers:
        return True

    for matcher in matchers:
        if matcher == '*' or matcher == '':
            return True
        if matcher == tool_name:
            return True
        # Simple regex-like matching
        if '|' in matcher:
            patterns = matcher.split('|')
            if tool_name in patterns:
                return True

    return False


if __name__ == '__main__':
    # Test the input handling utilities
    print("Testing input handling utilities...")

    # Test argument parsing
    flags, kv_args = get_hook_args()
    print(f"Flags: {flags}")
    print(f"Key-value args: {kv_args}")

    # Test tool matching
    test_cases = [
        ('Write', ['Write'], True),
        ('Edit', ['Write|Edit'], True),
        ('Read', ['Write|Edit'], False),
        ('Bash', ['*'], True),
        ('Anything', [], True)
    ]

    for tool, matchers, expected in test_cases:
        result = should_process_tool(tool, matchers)
        status = "✓" if result == expected else "✗"
        print(f"{status} Tool '{tool}' with matchers {matchers}: {result}")

    print("Test completed.")
