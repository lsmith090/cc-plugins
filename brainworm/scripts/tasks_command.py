#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
#     "typer>=0.9.0",
# ]
# ///

"""
Tasks Command - Unified Task State Management Interface

Provides a clean command-line interface for task state management,
similar to the DAIC command but focused on task tracking and session state.

Works in both discussion and implementation modes.
"""

# Add plugin root to sys.path before any utils imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import subprocess
from typing import List, Optional
from rich.console import Console
import typer
from utils.project import find_project_root

console = Console()
app = typer.Typer(
    name="tasks",
    help="Task State Management - Track and manage development tasks",
    no_args_is_help=True,
    add_completion=False,
)


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


@app.command(name="create", help="Create a new task")
def create(
    task_name: Optional[str] = typer.Argument(None, help="Name of the task to create"),
    submodule: Optional[str] = typer.Option(None, "--submodule", help="Target submodule"),
    services: Optional[str] = typer.Option(None, "--services", help="Comma-separated services"),
    no_interactive: bool = typer.Option(False, "--no-interactive", help="Skip interactive prompts"),
) -> None:
    """Create a new task"""
    project_root = find_project_root()
    args = []
    if task_name:
        args.append(task_name)
    if submodule:
        args.append(f"--submodule={submodule}")
    if services:
        args.append(f"--services={services}")
    if no_interactive:
        args.append("--no-interactive")

    return_code = run_script(project_root, "create_task.py", args)
    raise typer.Exit(code=return_code)


@app.command(name="status", help="Show current task state")
def status() -> None:
    """Show current task state"""
    project_root = find_project_root()
    return_code = run_script(project_root, "update_task_state.py", ["--show-current"])
    raise typer.Exit(code=return_code)


@app.command(name="list", help="List all tasks")
def list_tasks(
    status_filter: Optional[str] = typer.Option(None, "--status", help="Filter by status (completed, pending, in_progress)"),
    show_all: bool = typer.Option(False, "--all", help="Show all columns"),
) -> None:
    """List all tasks"""
    project_root = find_project_root()
    args = []
    if status_filter:
        args.append(f"--status={status_filter}")
    if show_all:
        args.append("--all")

    return_code = run_script(project_root, "list_tasks.py", args)
    raise typer.Exit(code=return_code)


@app.command(name="switch", help="Switch to an existing task")
def switch(
    task_name: Optional[str] = typer.Argument(None, help="Name of the task to switch to"),
) -> None:
    """Switch to a different task"""
    project_root = find_project_root()
    args = [task_name] if task_name else []
    return_code = run_script(project_root, "switch_task.py", args)
    raise typer.Exit(code=return_code)


@app.command(name="set", help="Update task state")
def set_state(
    task: Optional[str] = typer.Option(None, "--task", help="Set task name"),
    branch: Optional[str] = typer.Option(None, "--branch", help="Set git branch"),
    services: Optional[str] = typer.Option(None, "--services", help="Set comma-separated services"),
) -> None:
    """Update task state with provided arguments"""
    project_root = find_project_root()
    args = []
    if task:
        args.append(f"--task={task}")
    if branch:
        args.append(f"--branch={branch}")
    if services:
        args.append(f"--services={services}")

    return_code = run_script(project_root, "update_task_state.py", args)
    raise typer.Exit(code=return_code)


@app.command(name="clear", help="Clear current task")
def clear() -> None:
    """Clear current task"""
    project_root = find_project_root()
    return_code = run_script(project_root, "update_task_state.py", ["--clear-task"])
    raise typer.Exit(code=return_code)


@app.command(name="session", help="Show or set session correlation info")
def session(
    subcommand: Optional[str] = typer.Argument(None, help="Subcommand: 'set' to update session"),
    session_id: Optional[str] = typer.Option(None, "--session-id", help="Session ID to set"),
    correlation_id: Optional[str] = typer.Option(None, "--correlation-id", help="Correlation ID to set"),
) -> None:
    """Show or set session correlation info"""
    project_root = find_project_root()

    if subcommand == "set":
        args = ["set"]
        if session_id:
            args.append(f"--session-id={session_id}")
        if correlation_id:
            args.append(f"--correlation-id={correlation_id}")
        return_code = run_script(project_root, "update_session_correlation.py", args)
    else:
        return_code = run_script(project_root, "update_session_correlation.py", ["--show-current"])

    raise typer.Exit(code=return_code)


def main() -> None:
    """Tasks command main entry point"""
    try:
        app()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main()
