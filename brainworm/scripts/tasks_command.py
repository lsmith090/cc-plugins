#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
# ]
# ///

"""
Tasks Command - Unified Task State Management Interface

Provides a clean command-line interface for task state management,
similar to the DAIC command but focused on task tracking and session state.

Works in both discussion and implementation modes.
"""

import sys
import subprocess
from pathlib import Path
from typing import List, Optional
from rich.console import Console
from utils.project import find_project_root

console = Console()


def run_script(project_root: Path, script_name: str, args: List[str]) -> int:
    """Run a script using plugin-launcher"""
    try:
        plugin_launcher = project_root / ".brainworm" / "plugin-launcher"
        cmd = [str(plugin_launcher), script_name] + args
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except Exception as e:
        console.print(f"❌ [red]Error running script:[/red] {e}")
        return 1


def show_usage() -> None:
    """Show command usage"""
    console.print("\n[bold]Tasks Command - Task State Management[/bold]")
    console.print("Usage:")
    console.print("  [green]tasks status[/green]              - Show current task state")  
    console.print("  [green]tasks set[/green] [options]       - Update task state")
    console.print("    [dim]--task=NAME[/dim]                 Set task name")
    console.print("    [dim]--branch=BRANCH[/dim]             Set git branch")
    console.print("    [dim]--services=LIST[/dim]             Set comma-separated services")
    console.print("  [green]tasks clear[/green]               - Clear current task")
    console.print("  [green]tasks session[/green]             - Show session correlation info")
    console.print("  [green]tasks help[/green]                - Show this help")
    console.print()
    console.print("Examples:")
    console.print("  [dim]tasks set --task=\"feature-work\" --branch=\"feature/new\"[/dim]")
    console.print("  [dim]tasks set --services=\"hooks,analytics\"[/dim]")
    console.print("  [dim]tasks status[/dim]")
    console.print("  [dim]tasks clear[/dim]")
    console.print()


def main() -> None:
    """Tasks command main entry point"""
    try:
        project_root = find_project_root()
        
        # Parse command line arguments
        args = sys.argv[1:] if len(sys.argv) > 1 else []
        
        if not args or args[0] in ["help", "h", "--help", "-h"]:
            show_usage()
            return
            
        command = args[0]
        remaining_args = args[1:]

        if command in ["status", "s"]:
            # Show current task state
            return_code = run_script(project_root, "update_task_state.py", ["--show-current"])
            sys.exit(return_code)

        elif command in ["set", "update"]:
            # Update task state with provided arguments
            return_code = run_script(project_root, "update_task_state.py", remaining_args)
            sys.exit(return_code)

        elif command in ["clear", "c"]:
            # Clear current task
            return_code = run_script(project_root, "update_task_state.py", ["--clear-task"])
            sys.exit(return_code)

        elif command in ["session", "sess"]:
            # Show session correlation info
            if remaining_args and remaining_args[0] == "set":
                # Set session correlation
                return_code = run_script(project_root, "update_session_correlation.py", remaining_args[1:])
            else:
                # Show current session correlation
                return_code = run_script(project_root, "update_session_correlation.py", ["--show-current"])
            sys.exit(return_code)
            
        else:
            console.print(f"[red]Unknown command: {command}[/red]")
            console.print("Run [green]tasks help[/green] for available commands.")
            sys.exit(1)
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main()