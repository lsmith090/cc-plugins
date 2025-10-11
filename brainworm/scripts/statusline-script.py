#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "toml>=0.10.0",
# ]
# ///

"""
Brainworm StatusLine Script (Python Version)
Provides comprehensive session information with DAIC workflow and analytics integration
Converted from bash version for better maintainability and consistent output
"""

import sys
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Import DAICMode enum if available
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))  # Add plugin root for utils access
    from utils.hook_types import DAICMode
except ImportError:
    # Fallback if not available - define enum values as constants
    class DAICMode:
        DISCUSSION = "discussion"
        IMPLEMENTATION = "implementation"

# Context limits based on model and mode
SONNET_API_MODE_USABLE_TOKENS = 800000    # 1M Sonnet models in API mode
STANDARD_USABLE_TOKENS = 160000           # Ultrathink mode or non-Sonnet models
DEFAULT_STARTUP_TOKENS = 17900            # Typical conversation startup size (from /context)

def read_input() -> Dict[str, Any]:
    """Read and parse JSON input from stdin"""
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}

def get_project_root(cwd: str) -> Path:
    """Find project root directory"""
    return Path(cwd) if cwd else Path.cwd()

def calculate_context(input_data: Dict[str, Any], project_root: Path) -> str:
    """Calculate context breakdown and progress with colored progress bar"""
    
    # Get basic info from input
    cwd = input_data.get('workspace', {}).get('current_dir') or input_data.get('cwd', '')
    model_name = input_data.get('model', {}).get('display_name', 'Claude')
    transcript_path = input_data.get('transcript_path', '')
    
    # Determine usable context limit based on API mode and model
    api_mode_enabled = False
    config_path = project_root / ".brainworm" / "config.toml"
    
    if config_path.exists():
        try:
            import toml
            with open(config_path, 'r') as f:
                config = toml.load(f)
                api_mode_enabled = config.get('api_mode', False)
        except:
            pass
    
    # Set context limit based on API mode and model
    if api_mode_enabled and "Sonnet" in model_name:
        context_limit = SONNET_API_MODE_USABLE_TOKENS
    else:
        context_limit = STANDARD_USABLE_TOKENS
    
    # Parse transcript to get real token usage
    total_tokens = 0
    if transcript_path and Path(transcript_path).exists():
        try:
            with open(transcript_path, 'r') as f:
                lines = f.readlines()[-100:]
            
            most_recent_usage = None
            most_recent_timestamp = None
            
            for line in lines:
                try:
                    data = json.loads(line.strip())
                    # Skip sidechain entries (subagent calls)
                    if data.get('isSidechain', False):
                        continue
                    
                    # Check for usage data in main-chain messages
                    if data.get('message', {}).get('usage'):
                        timestamp = data.get('timestamp')
                        if timestamp and (not most_recent_timestamp or timestamp > most_recent_timestamp):
                            most_recent_timestamp = timestamp
                            most_recent_usage = data['message']['usage']
                except:
                    continue
            
            # Calculate context length (input + cache tokens only, NOT output)
            if most_recent_usage:
                total_tokens = (
                    most_recent_usage.get('input_tokens', 0) +
                    most_recent_usage.get('cache_read_input_tokens', 0) +
                    most_recent_usage.get('cache_creation_input_tokens', 0)
                )
        except:
            pass
    
    # Default values when no transcript available - still add default context
    if total_tokens == 0:
        total_tokens = DEFAULT_STARTUP_TOKENS
    
    # Calculate progress percentage
    progress_pct = min(100.0, total_tokens * 100 / context_limit)
    progress_pct_int = int(progress_pct)
    
    # Format token count in 'k' format
    formatted_tokens = f"{total_tokens // 1000}k"
    formatted_limit = f"{context_limit // 1000}k"
    
    # Create progress bar (capped at 100%) with Ayu Dark colors
    filled_blocks = min(10, progress_pct_int // 10)
    empty_blocks = 10 - filled_blocks
    
    # Ayu Dark colors (converted to closest ANSI 256)
    if progress_pct_int < 50:
        bar_color = "\033[38;5;114m"  # AAD94C green
    elif progress_pct_int < 80:
        bar_color = "\033[38;5;215m"  # FFB454 orange
    else:
        bar_color = "\033[38;5;203m"  # F26D78 red
    
    gray_color = "\033[38;5;242m"     # Dim for empty blocks
    text_color = "\033[38;5;250m"     # BFBDB6 light gray
    reset = "\033[0m"
    
    # Build progress bar
    progress_bar = bar_color + "█" * filled_blocks
    progress_bar += gray_color + "░" * empty_blocks
    progress_bar += f"{reset} {text_color}{progress_pct:.1f}% ({formatted_tokens}/{formatted_limit}){reset}"
    
    return progress_bar

def get_task_display(project_root: Path) -> str:
    """Get current task and open task count display"""
    blue = "\033[38;5;111m"    # 73B8FF modified blue for Tasks label
    cyan = "\033[38;5;117m"    # Light cyan for task name
    reset = "\033[0m"
    
    task_name = "None"
    
    # Get current task from unified state
    unified_state_file = project_root / ".brainworm" / "state" / "unified_session_state.json"

    if unified_state_file.exists():
        try:
            with open(unified_state_file, 'r') as f:
                data = json.load(f)
                task_name = data.get('current_task', 'None')
                if task_name is None or task_name == '':
                    task_name = 'None'
        except:
            pass

    # Always scan filesystem for accurate open task count
    open_count = _count_open_tasks(project_root)

    return f"{blue}Active Task: {cyan}{task_name}{reset} {blue}[{open_count} open]{reset}"

def _count_open_tasks(project_root: Path) -> int:
    """Count open tasks by scanning filesystem (fallback method)"""
    open_count = 0
    tasks_dir = project_root / ".brainworm" / "tasks"
    
    if tasks_dir.exists():
        for task_path in tasks_dir.iterdir():
            if task_path.is_dir():
                readme_file = task_path / "README.md"
                if readme_file.exists():
                    try:
                        with open(readme_file, 'r') as f:
                            content = f.read()
                            if not re.search(r'status:\s*(done|completed)', content, re.IGNORECASE):
                                open_count += 1
                    except:
                        pass
            elif task_path.is_file() and task_path.suffix == '.md':
                try:
                    with open(task_path, 'r') as f:
                        content = f.read()
                        if not re.search(r'status:\s*(done|completed)', content, re.IGNORECASE):
                            open_count += 1
                except:
                    pass
    
    return open_count

def get_daic_mode(project_root: Path) -> str:
    """Get DAIC mode with color from unified state"""
    # Use unified state as single source of truth
    unified_state_file = project_root / ".brainworm" / "state" / "unified_session_state.json"
    
    mode = DAICMode.DISCUSSION  # default
    
    if unified_state_file.exists():
        try:
            with open(unified_state_file, 'r') as f:
                data = json.load(f)
                mode_str = data.get('daic_mode', 'discussion')
                mode = DAICMode.from_string(mode_str)
        except:
            pass
    
    if mode == DAICMode.DISCUSSION:
        purple = "\033[38;5;183m"  # D2A6FF constant purple
        reset = "\033[0m"
        return f"{purple}DAIC: Discussion{reset}"
    else:
        green = "\033[38;5;114m"   # AAD94C string green
        reset = "\033[0m"
        return f"{green}DAIC: Implementation{reset}"

def get_git_display(project_root: Path) -> str:
    """Get git branch and file count display with submodule branch awareness"""
    green = "\033[38;5;114m"   # AAD94C string green for Git label and branch
    yellow = "\033[38;5;215m"  # FFB454 func orange for file count
    cyan = "\033[38;5;117m"    # Light cyan for repo name
    reset = "\033[0m"

    modified_count = 0
    branch_name = "none"
    repo_name = "main"  # default to main repo
    git_dir = project_root / ".git"

    # Get active submodule branches from unified state
    active_submodule_branches = {}
    unified_state_file = project_root / ".brainworm" / "state" / "unified_session_state.json"
    if unified_state_file.exists():
        try:
            with open(unified_state_file, 'r') as f:
                data = json.load(f)
                active_submodule_branches = data.get('active_submodule_branches', {})
        except:
            pass

    if git_dir.exists():
        try:
            # Detect if we're in a submodule
            superproject_result = subprocess.run(
                ["git", "rev-parse", "--show-superproject-working-tree"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=5
            )

            if superproject_result.returncode == 0 and superproject_result.stdout.strip():
                # We're in a submodule - extract submodule name from path
                superproject_root = Path(superproject_result.stdout.strip())
                try:
                    # The submodule name is the relative path from superproject to current
                    relative = project_root.relative_to(superproject_root)
                    repo_name = str(relative)
                except ValueError:
                    # Fallback if relative path calculation fails
                    repo_name = project_root.name

            # Get current branch
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=True
            )
            branch_name = branch_result.stdout.strip() or "detached"

            # Count modified and staged files
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=True
            )

            # Count lines that match modified/added pattern
            for line in status_result.stdout.strip().split('\n'):
                if line and re.match(r'^[AM]|^.[AM]', line):
                    modified_count += 1
        except:
            pass

    # Build branch display with submodule awareness
    if active_submodule_branches:
        # Monorepo mode: show main branch + active submodule branches
        branch_display = f"{cyan}[{branch_name}]{reset}"
        for submodule, sub_branch in active_submodule_branches.items():
            branch_display += f" {green}{submodule}:{sub_branch}{reset}"
        return f"{yellow}Git: {branch_display} ✎ {modified_count} files{reset}"
    else:
        # Standard mode: show repo name + branch
        return f"{yellow}Git: {cyan}[{repo_name}]{yellow} | {branch_name} ✎ {modified_count} files{reset}"


def get_working_directory(input_data: Dict[str, Any]) -> str:
    """Get current working directory with color"""
    cyan = "\033[38;5;117m"    # Light cyan for directory
    reset = "\033[0m"
    
    cwd = input_data.get('workspace', {}).get('current_dir') or input_data.get('cwd', '')
    
    if cwd:
        return f"{cyan}{cwd}{reset}"
    else:
        return f"{cyan}--{reset}"

def get_user_preferences(project_root: Path) -> Dict[str, Any]:
    """Get user preferences from user-config.json"""
    default_prefs = {
        "statusline_format": "full",
        "context_warning_threshold": 75
    }
    
    user_config_file = project_root / ".brainworm" / "user-config.json"
    
    if user_config_file.exists():
        try:
            with open(user_config_file, 'r') as f:
                config = json.load(f)
                preferences = config.get('preferences', {})
                return {**default_prefs, **preferences}
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    
    return default_prefs

def main() -> None:
    """Main function to build and output the complete statusline"""
    
    # Read JSON input from stdin
    input_data = read_input()
    
    # Get project root
    cwd = input_data.get('workspace', {}).get('current_dir') or input_data.get('cwd', '')
    project_root = get_project_root(cwd)
    
    # Get user preferences
    prefs = get_user_preferences(project_root)
    statusline_format = prefs.get('statusline_format', 'full')
    
    # Build all components
    progress_info = calculate_context(input_data, project_root)
    working_dir_info = get_working_directory(input_data)
    daic_info = get_daic_mode(project_root)
    git_info = get_git_display(project_root)
    task_info = get_task_display(project_root)
    
    # Output based on user preference
    if statusline_format == "minimal":
        # Single line with essential info only
        print(f"{progress_info} | {daic_info}")
    elif statusline_format == "compact":
        # Two lines with condensed info
        print(f"{progress_info} | {working_dir_info}")
        print(f"{daic_info} | {git_info} | {task_info}")
    else:  # full format (default)
        # Original three lines with complete info
        print(f"{progress_info} | {working_dir_info}")
        print(f"{daic_info} | {git_info}")
        print(f"{task_info}")

if __name__ == "__main__":
    main()