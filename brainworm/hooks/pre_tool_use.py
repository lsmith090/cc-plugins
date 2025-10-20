# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
#     "tomli-w>=1.0.0",
#     "filelock>=3.13.0",
# ]
# ///

"""
Pre-Tool Use Hook - Hooks Framework

DAIC workflow enforcement with intelligent subagent coordination.
Critical tool blocking functionality for Claude Code integration.
"""

# Add plugin root to sys.path before any utils imports
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import re
from typing import Any, Dict

from utils.bash_validator import is_read_only_bash_command, split_command_respecting_quotes
from utils.business_controllers import create_daic_controller, create_subagent_manager
from utils.hook_framework import HookFramework
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


# Removed - now using shared functions from utils.bash_validator


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
        r'(\./)?daic\s+discussion$',  # Discussion mode is always safe (noop in discussion mode)
        r'\.brainworm/plugin-launcher\s+daic_command\.py\s+status$',  # Slash command status
        r'\.brainworm/plugin-launcher\s+daic_command\.py\s+discussion$',  # Slash command discussion
        r'uv run \.brainworm/scripts/update_.*\.py\s+--show-current$',  # Only --show-current queries
        r'(\./)?tasks(\s+.*)?$',  # All tasks commands allowed in discussion mode
        r'uv run \.brainworm/scripts/create_task\.py(\s+.*)?$',  # Task creation allowed in discussion mode
    ]

    return any(re.search(pattern, command) for pattern in read_only_system_patterns)


def should_block_tool_daic(raw_input_data: Dict[str, Any], config: Dict[str, Any],
                          daic_state: Dict[str, Any], project_root: Path, debug_logger=None) -> ToolBlockingResult:
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

        # FIRST: Block daic mode-switching commands in discussion mode (check before system commands)
        if is_discussion_mode:
            command_parts = split_command_respecting_quotes(command)
            if command_parts:
                # Get the first part of the first command (before any pipes)
                first_command = command_parts[0].strip().split()[0] if command_parts[0].strip() else ""

                # DEBUG: Log command analysis for slash command investigation
                if debug_logger:
                    debug_logger.debug(f"Slash command check - Full command: {command}")
                    debug_logger.debug(f"Slash command check - First command: '{first_command}'")
                    debug_logger.debug(f"Slash command check - Has 'plugin-launcher': {'plugin-launcher' in first_command}")
                    debug_logger.debug(f"Slash command check - Has 'daic_command.py': {'daic_command.py' in command}")
                    debug_logger.debug(f"Slash command check - Has 'implementation': {'implementation' in command}")

                # Check for direct daic mode-switching command: 'daic' or './daic'
                # Only block mode-switching subcommands, not read-only queries like 'status'
                if first_command in ('daic', './daic'):
                    # Extract the subcommand (first argument after daic)
                    parts = command.split()
                    if len(parts) > 1:
                        subcommand = parts[1]
                        # Only block implementation and toggle subcommands
                        if subcommand in ['implementation', 'toggle']:
                            return ToolBlockingResult.command_block(
                                command,
                                "DAIC mode switching to implementation is not allowed in discussion mode. Use trigger phrases or let the user invoke the command directly."
                            )

                # Check for slash command via plugin-launcher: '.brainworm/plugin-launcher daic_command.py'
                if 'plugin-launcher' in first_command and 'daic_command.py' in command:
                    # Extract arguments to check for mode-switching subcommands
                    # Only block implementation and toggle, not status or discussion
                    parts = command.split()
                    # Find the index after daic_command.py to get the subcommand
                    try:
                        daic_idx = next(i for i, p in enumerate(parts) if 'daic_command.py' in p)
                        if daic_idx + 1 < len(parts):
                            subcommand = parts[daic_idx + 1]
                            if subcommand in ['implementation', 'toggle']:
                                return ToolBlockingResult.command_block(
                                    command,
                                    "DAIC mode switching to implementation is not allowed. Use trigger phrases or let the user invoke the command directly."
                                )
                    except StopIteration:
                        pass  # daic_command.py not found in parts, allow it through

        # SECOND: Allow brainworm system management commands even in discussion mode (after mode-switching check)
        if is_discussion_mode and is_brainworm_system_command(command, config, project_root):
            return ToolBlockingResult.allow_tool("Brainworm system command allowed")

        # THIRD: Check if command is read-only in discussion mode
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
            try:
                # Security: Resolve path to normalize and prevent traversal attacks
                # Must resolve BEFORE checking relationship to state_dir
                file_path = Path(file_path_str).resolve()
                resolved_state_dir = state_dir.resolve()

                # Check if file_path is under the state directory
                # This will properly detect paths like ".brainworm/state/../state/file.txt"
                file_path.relative_to(resolved_state_dir)
                # If we get here, the file is under .brainworm/state
                return ToolBlockingResult.block_tool(
                    "[Subagent Boundary Violation] Subagents are NOT allowed to modify .brainworm/state files.",
                    "SUBAGENT_BOUNDARY_VIOLATION"
                )
            except ValueError:
                # Not under .brainworm/state, which is fine
                pass
            except Exception:
                # Path resolution failed - could be malicious, block to be safe
                return ToolBlockingResult.block_tool(
                    "[Subagent Boundary Violation] Invalid file path",
                    "INVALID_PATH"
                )

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


def pre_tool_use_framework_logic(framework, input_data: Dict[str, Any]):
    """Custom logic for pre-tool use using pure framework approach.

    Args:
        framework: HookFramework instance
        input_data: Raw input dict (always dict, typed input used for validation only)
    """
    project_root = framework.project_root

    # Handle case where project_root might be None
    if not project_root:
        framework.set_exit_decision(0, "Error: Could not determine project root")
        return

    # Load configuration and DAIC state
    from utils.config import load_config
    config = load_config(project_root)
    daic_state = get_daic_state(project_root)

    # Extract data from dict - simple and direct
    tool_name = input_data.get('tool_name', 'unknown')
    tool_input = input_data.get('tool_input', {})

    # Debug logging - INFO level
    if framework.debug_logger:
        daic_mode = daic_state.get('mode', 'unknown')
        framework.debug_logger.info(f"DAIC pre-validation: {tool_name} in {daic_mode} mode")

    # PHASE 1: Basic security check
    passes_security = basic_security_check(framework.raw_input_data)

    if framework.debug_logger and not passes_security:
        framework.debug_logger.warning(f"Security check FAILED for {tool_name}")

    # PHASE 2: DAIC enforcement check
    daic_result = should_block_tool_daic(
        framework.raw_input_data, config, daic_state, project_root, framework.debug_logger
    )

    # Determine final blocking decision
    should_block = not passes_security or daic_result.should_block
    block_reason = daic_result.reason if daic_result.should_block else ("Security check failed" if not passes_security else "")

    # Debug logging - decision details
    if framework.debug_logger:
        if should_block:
            framework.debug_logger.info(f"🚫 BLOCKED: {tool_name} - {block_reason}")
            # DEBUG level: log more details
            framework.debug_logger.debug(f"Block reason: {block_reason}")
            if tool_name == "Bash" and isinstance(tool_input, dict):
                command = tool_input.get("command", "")
                framework.debug_logger.debug(f"Bash command: {command[:100]}")
            elif isinstance(tool_input, dict) and "file_path" in tool_input:
                framework.debug_logger.debug(f"File path: {tool_input.get('file_path')}")
        else:
            framework.debug_logger.info(f"✅ ALLOWED: {tool_name}")
            framework.debug_logger.debug(f"Allow reason: {daic_result.reason}")

    # Use typed decision methods for framework to handle
    if should_block:
        framework.block_tool(block_reason, [block_reason])  # Block tool execution
    else:
        framework.approve_tool()  # Allow tool execution


def main() -> None:
    """Main entry point for pre-tool use hook - Pure Framework Approach"""
    try:
        HookFramework("daic_pre_tool_use", enable_event_logging=True, security_critical=True) \
            .with_custom_logic(pre_tool_use_framework_logic) \
            .execute()

    except Exception:
        # Non-blocking error - allow tool to proceed
        sys.exit(0)


if __name__ == '__main__':
    main()
