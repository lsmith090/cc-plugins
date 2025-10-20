#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
# ]
# ///

"""
Claude Code Hooks Utilities
Shared utilities for eliminating code duplication across hooks
"""

from .hook_logging import HookLogger
from .input_handling import extract_tool_info, read_hook_input, validate_hook_input
from .project import find_project_root, get_project_context, is_valid_project_root

__all__ = [
    'find_project_root',
    'is_valid_project_root',
    'get_project_context',
    'HookLogger',
    'read_hook_input',
    'validate_hook_input',
    'extract_tool_info'
]
