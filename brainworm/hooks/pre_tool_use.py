#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
#     "toml>=0.10.0",
# ]
# ///

"""
Pre-Tool Use Hook - Hooks Framework

DAIC workflow enforcement with intelligent subagent coordination.
Critical tool blocking functionality for Claude Code integration.
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Tuple
from utils.hook_framework import HookFramework
from utils.business_controllers import create_daic_controller, create_subagent_manager
from utils.hook_types import DAICMode, ToolBlockingResult


# Removed - now using shared function from utils.git


# Removed - now using shared function from utils.project


# Removed - now using shared function from utils.config


def get_daic_state(project_root: Path) -> Dict[str, Any]:
    """Get current DAIC state using business controllers"""
    try:
        controller = create_daic_controller(project_root)
        mode_info = controller.get_mode_with_display()
        
        return {
            "mode": mode_info.mode,
            "timestamp": None,
            "previous_mode": None
        }
    except Exception:
        return {
            "mode": str(DAICMode.DISCUSSION),
            "timestamp": None,
            "previous_mode": None
        }


def split_command_respecting_quotes(command: str) -> list:
    """
    Split command on operators (&&, ||, ;, |) while respecting quoted strings
    
    Examples:
    - 'ls | grep "test|pattern"' → ['ls', 'grep "test|pattern"']
    - 'ls && pwd' → ['ls', 'pwd']
    """
    parts = []
    current_part = []
    in_single_quote = False
    in_double_quote = False
    i = 0
    
    while i < len(command):
        char = command[i]
        
        # Handle quotes
        if char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            current_part.append(char)
        elif char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            current_part.append(char)
        # Handle operators only when not in quotes
        elif not in_single_quote and not in_double_quote:
            # Check for multi-character operators
            if i < len(command) - 1:
                two_char = command[i:i+2]
                if two_char in ['&&', '||', '>>']:
                    # End current part and start new one
                    if current_part:
                        parts.append(''.join(current_part))
                        current_part = []
                    i += 2  # Skip both characters
                    continue
            
            # Check for single-character operators  
            if char in [';', '|']:
                # End current part and start new one
                if current_part:
                    parts.append(''.join(current_part))
                    current_part = []
            else:
                current_part.append(char)
        else:
            current_part.append(char)
        
        i += 1
    
    # Add final part
    if current_part:
        parts.append(''.join(current_part))
    
    return [part.strip() for part in parts if part.strip()]


def is_read_only_bash_command(command: str, config: Dict[str, Any]) -> bool:
    """Check if a bash command is read-only and safe in discussion mode"""
    import re
    
    daic_config = config.get("daic", {})
    read_only_commands = daic_config.get("read_only_bash_commands", {})
    
    # Flatten all read-only command categories
    all_read_only = []
    for category_commands in read_only_commands.values():
        all_read_only.extend(category_commands)
    
    # Check for write patterns first
    write_patterns = [
        r'>\s*[^>]',  # Output redirection
        r'>>',         # Append redirection
        r'\btee\b',    # tee command
        r'\bmv\b',     # move/rename
        r'\bcp\b',     # copy
        r'\brm\b',     # remove
        r'\bmkdir\b',  # make directory
        r'\btouch\b',  # create/update file
        r'\bsed\s+(?!-n)',  # sed without -n flag
        r'\bnpm\s+install',  # npm install
        r'\bpip\s+install',  # pip install
        r'-delete\b',  # find -delete flag (SECURITY FIX)
        r'-exec\s+.*rm\b',  # find -exec with rm (SECURITY FIX)
    ]
    
    # If command has write patterns, it's not read-only
    if any(re.search(pattern, command) for pattern in write_patterns):
        return False
    
    # Check if ALL commands in chain are read-only (FIXED: use quote-aware splitting)
    command_parts = split_command_respecting_quotes(command)
    for part in command_parts:
        part = part.strip()
        if not part:
            continue
        
        # Check against configured read-only commands
        is_part_read_only = any(
            part.startswith(prefix) 
            for prefix in all_read_only
        )
        
        if not is_part_read_only:
            return False
    
    return True


def is_brainworm_system_command(command: str, config: Dict[str, Any], project_root: Path = None) -> bool:
    """Check if command is a brainworm system management operation"""
    # Check for trigger phrase exception flag
    if project_root:
        trigger_flag = project_root / '.brainworm' / 'state' / 'trigger_phrase_detected.flag'
        if trigger_flag.exists():
            # Allow all DAIC state management operations when trigger phrase detected
            trigger_exception_patterns = [
                r'(\./)?daic\s+(status|toggle)$',  # All daic commands during trigger
                r'uv run \.brainworm/scripts/update_.*\.py',  # All update scripts during trigger
            ]
            if any(re.search(pattern, command) for pattern in trigger_exception_patterns):
                return True
    
    # Normal restrictive patterns when no trigger phrase
    read_only_system_patterns = [
        r'(\./)?daic\s+status$',  # Only status command, NOT toggle
        r'uv run \.brainworm/scripts/update_.*\.py\s+--show-current$',  # Only --show-current queries
        r'(\./)?tasks(\s+.*)?$',  # All tasks commands allowed in discussion mode
        r'uv run \.brainworm/scripts/create_task\.py(\s+.*)?$',  # Task creation allowed in discussion mode
    ]
    
    return any(re.search(pattern, command) for pattern in read_only_system_patterns)


def should_block_tool_daic(raw_input_data: Dict[str, Any], config: Dict[str, Any], 
                          daic_state: Dict[str, Any], project_root: Path) -> ToolBlockingResult:
    """
    DAIC enforcement logic - determine if tool should be blocked
    Returns ToolBlockingResult with blocking decision and reason
    """
    daic_config = config.get("daic", {})
    
    # Check if DAIC is enabled
    if not daic_config.get("enabled", True):
        return ToolBlockingResult.allow_tool("DAIC enforcement disabled")
    
    # Check for subagent context - disable DAIC enforcement during subagent execution
    try:
        subagent_manager = create_subagent_manager(project_root)
        if subagent_manager.is_in_subagent_context():
            return ToolBlockingResult.allow_tool("DAIC enforcement disabled during subagent execution")
    except Exception:
        # Fallback to direct flag check if business controller fails
        state_dir = project_root / '.brainworm' / 'state'
        subagent_flag = state_dir / 'in_subagent_context.flag'
        if subagent_flag.exists():
            return ToolBlockingResult.allow_tool("DAIC enforcement disabled during subagent execution")
    
    tool_name = raw_input_data.get("tool_name", "")
    tool_input = raw_input_data.get("tool_input", {})
    is_discussion_mode = daic_state.get("mode", str(DAICMode.DISCUSSION)) == str(DAICMode.DISCUSSION)
    
    # Block configured tools in discussion mode
    blocked_tools = daic_config.get("blocked_tools", [])
    if is_discussion_mode and tool_name in blocked_tools:
        return ToolBlockingResult.discussion_mode_block(tool_name)
    
    # Handle Bash commands specially
    if tool_name == "Bash":
        command = tool_input.get("command", "").strip()
        
        # Allow brainworm system management commands even in discussion mode
        if is_discussion_mode and is_brainworm_system_command(command, config, project_root):
            return ToolBlockingResult.allow_tool("Brainworm system command allowed")
        
        # Block other daic commands in discussion mode (they should be handled by user-messages hook)
        if is_discussion_mode and 'daic' in command:
            return ToolBlockingResult.command_block(command, "The 'daic' command is not allowed in discussion mode. You're already in discussion mode.")
        
        # Check if command is read-only in discussion mode
        if is_discussion_mode and not is_read_only_bash_command(command, config):
            return ToolBlockingResult.command_block(command[:50] + "...", "Potentially modifying Bash command blocked in discussion mode")
    
    # Check for subagent boundary violations
    try:
        subagent_manager = create_subagent_manager(project_root)
        in_subagent_context = subagent_manager.is_in_subagent_context()
    except Exception:
        # Fallback to direct flag check
        state_dir = project_root / '.brainworm' / 'state'
        subagent_flag = state_dir / 'in_subagent_context.flag'
        in_subagent_context = subagent_flag.exists()
    
    if in_subagent_context and tool_name in ["Write", "Edit", "MultiEdit"]:
        file_path_str = tool_input.get("file_path", "")
        if file_path_str:
            file_path = Path(file_path_str)
            try:
                # Check if file_path is under the state directory
                file_path.resolve().relative_to(state_dir.resolve())
                # If we get here, the file is under .brainworm/state
                return ToolBlockingResult.block_tool("[Subagent Boundary Violation] Subagents are NOT allowed to modify .brainworm/state files.", "SUBAGENT_BOUNDARY_VIOLATION")
            except ValueError:
                # Not under .brainworm/state, which is fine
                pass
    
    return ToolBlockingResult.allow_tool("Tool allowed by DAIC")


def basic_security_check(raw_input_data: Dict[str, Any]) -> bool:
    """Basic security check - only block obviously dangerous operations"""
    tool_name = raw_input_data.get('tool_name', '')
    
    if tool_name == 'Bash':
        command = raw_input_data.get('tool_input', {}).get('command', '')
        # Only block obviously destructive commands
        dangerous_patterns = ['rm -rf /', 'format c:', 'del /s /q C:\\']
        return not any(pattern in command for pattern in dangerous_patterns)
    
    return True  # Allow all other operations


def extract_metadata(raw_input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract relevant metadata from tool input"""
    metadata = {}
    tool_input = raw_input_data.get('tool_input', {})
    
    # Extract file path if available
    if file_path := tool_input.get('file_path'):
        metadata['file_path'] = file_path
    
    # Extract command if it's a Bash operation
    if command := tool_input.get('command'):
        metadata['command'] = command
    
    return metadata


def pre_tool_use_framework_logic(framework, typed_input):
    """Custom logic for pre-tool use using pure framework approach"""
    project_root = framework.project_root
    
    # Handle case where project_root might be None
    if not project_root:
        framework.set_exit_decision(0, "Error: Could not determine project root")
        return
    
    # Load configuration and DAIC state
    from utils.config import load_config
    config = load_config(project_root)
    daic_state = get_daic_state(project_root)
    
    # Extract basic info from typed input
    session_id = typed_input.session_id
    tool_name = typed_input.tool_name
    tool_input = typed_input.tool_input
    
    # PHASE 1: Basic security check
    passes_security = basic_security_check(framework.raw_input_data)
    
    # PHASE 2: DAIC enforcement check
    daic_result = should_block_tool_daic(
        framework.raw_input_data, config, daic_state, project_root
    )
    
    # Determine final blocking decision
    should_block = not passes_security or daic_result.should_block
    block_reason = daic_result.reason if daic_result.should_block else ("Security check failed" if not passes_security else "")
    
    # Display debug info
    if '--verbose' in sys.argv:
        block_status = "🚫" if should_block else "✅"
        mode_indicator = "💭" if daic_state.get('mode') == 'discussion' else "⚡"
        print(f"{block_status} {mode_indicator} DAIC Pre-validation: {tool_name} (Session: {session_id[:8]})", file=sys.stderr)
        if should_block:
            print(f"Tool execution blocked: {block_reason}", file=sys.stderr)
    
    # Use typed decision methods for framework to handle
    if should_block:
        framework.block_tool(block_reason, [block_reason])  # Block tool execution
    else:
        framework.approve_tool()  # Allow tool execution


def main() -> None:
    """Main entry point for pre-tool use hook - Pure Framework Approach"""
    try:
        HookFramework("daic_pre_tool_use", enable_analytics=True, enable_logging=True, security_critical=True) \
            .with_custom_logic(pre_tool_use_framework_logic) \
            .execute()
            
    except Exception as e:
        # Non-blocking error - allow tool to proceed
        if '--verbose' in sys.argv:
            print(f"Hook error (non-blocking): {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == '__main__':
    main()