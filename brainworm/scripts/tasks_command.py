#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
#     "typer>=0.9.0",
#     "tomli-w>=1.0.0",
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

import typer
from rich.console import Console
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


@app.command(name="create", help="Create a new task with optional GitHub integration")
def create(
    task_name: Optional[str] = typer.Argument(None, help="Name of the task to create (e.g., fix-bug-#123)"),
    submodule: Optional[str] = typer.Option(None, "--submodule", help="Target submodule"),
    services: Optional[str] = typer.Option(None, "--services", help="Comma-separated services"),
    no_interactive: bool = typer.Option(False, "--no-interactive", help="Skip interactive prompts"),
    link_issue: Optional[int] = typer.Option(None, "--link-issue", help="Link to existing GitHub issue number"),
    create_issue: bool = typer.Option(False, "--create-issue", help="Create new GitHub issue for this task"),
    no_github: bool = typer.Option(False, "--no-github", help="Skip GitHub integration completely"),
) -> None:
    """
    Create a new task with optional GitHub integration.

    Examples:
      tasks create implement-feature
      tasks create fix-bug-#123  # Auto-links to issue #123
      tasks create add-auth --link-issue=456
      tasks create new-feature --create-issue
    """
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
    if link_issue:
        args.append(f"--link-issue={link_issue}")
    if create_issue:
        args.append("--create-issue")
    if no_github:
        args.append("--no-github")

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


@app.command(name="summarize", help="Generate and post session summary to GitHub")
def summarize(
    session_id: Optional[str] = typer.Option(None, "--session-id", help="Session ID to summarize (default: current)"),
) -> None:
    """
    Generate session summary from memory file and post to linked GitHub issue.

    Requires:
    - Session memory file created by session-docs agent
    - Task with linked GitHub issue (github_issue and github_repo in frontmatter)
    - gh CLI authenticated

    Examples:
      tasks summarize                    # Summarize current session
      tasks summarize --session-id=abc   # Summarize specific session
    """
    import json

    from utils.config import load_config
    from utils.github_integration import (
        check_gh_available,
        find_session_memory,
        generate_github_summary_from_memory,
        post_issue_comment,
    )

    project_root = find_project_root()

    # Get session_id (from arg or unified state)
    if not session_id:
        state_file = project_root / ".brainworm" / "state" / "unified_session_state.json"
        if not state_file.exists():
            console.print("[red]No unified state file found. Cannot determine session ID.[/red]")
            raise typer.Exit(code=1)

        try:
            state = json.loads(state_file.read_text())
            session_id = state.get("session_id")
            if not session_id:
                console.print("[red]No session_id in unified state.[/red]")
                raise typer.Exit(code=1)
        except Exception as e:
            console.print(f"[red]Error reading unified state: {e}[/red]")
            raise typer.Exit(code=1)

    # Find memory file
    console.print(f"[cyan]Looking for session memory: {session_id[:8]}...[/cyan]")
    memory_file = find_session_memory(project_root, session_id)

    if not memory_file:
        console.print(f"[red]No memory file found for session {session_id[:8]}[/red]")
        console.print("[yellow]Tip: Use the session-docs agent to create a memory file first[/yellow]")
        raise typer.Exit(code=1)

    console.print(f"[green]Found memory file: {memory_file.name}[/green]")

    # Get current task state
    state_file = project_root / ".brainworm" / "state" / "unified_session_state.json"
    try:
        state = json.loads(state_file.read_text())
        current_task = state.get("current_task")
        current_branch = state.get("current_branch", "unknown")

        if not current_task:
            console.print("[red]No current task set.[/red]")
            raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error reading task state: {e}[/red]")
        raise typer.Exit(code=1)

    # Get GitHub issue from task frontmatter
    task_file = project_root / ".brainworm" / "tasks" / current_task / "README.md"
    if not task_file.exists():
        console.print(f"[red]Task file not found: {task_file}[/red]")
        raise typer.Exit(code=1)

    # Parse frontmatter for github_issue and github_repo
    try:
        content = task_file.read_text()
        lines = content.split('\n')
        if not (lines and lines[0] == '---'):
            console.print("[red]Task file has invalid frontmatter[/red]")
            raise typer.Exit(code=1)

        github_issue = None
        github_repo = None

        for i in range(1, min(20, len(lines))):
            if lines[i] == '---':
                break
            if lines[i].startswith('github_issue:'):
                issue_str = lines[i].split(':', 1)[1].strip()
                if issue_str and issue_str != 'null':
                    try:
                        github_issue = int(issue_str)
                    except ValueError:
                        pass
            elif lines[i].startswith('github_repo:'):
                repo_str = lines[i].split(':', 1)[1].strip()
                if repo_str and repo_str != 'null':
                    github_repo = repo_str

        if not github_issue or not github_repo:
            console.print("[red]Task is not linked to a GitHub issue[/red]")
            console.print("[yellow]Use --link-issue or include #123 in task name to link[/yellow]")
            raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"[red]Error parsing task file: {e}[/red]")
        raise typer.Exit(code=1)

    # Check GitHub configuration
    config = load_config(project_root)
    github_config = config.get("github", {})
    github_enabled = github_config.get("enabled", False)

    if not github_enabled:
        console.print("[red]GitHub integration is disabled in config.toml[/red]")
        console.print("[yellow]Set [github] enabled = true to use this feature[/yellow]")
        raise typer.Exit(code=1)

    if not check_gh_available():
        console.print("[red]gh CLI is not available or not authenticated[/red]")
        console.print("[yellow]Install and authenticate: gh auth login[/yellow]")
        raise typer.Exit(code=1)

    # Generate summary
    console.print("[cyan]Generating summary from memory file...[/cyan]")
    summary = generate_github_summary_from_memory(
        memory_file,
        session_id,
        current_task,
        current_branch
    )

    # Show preview
    console.print("\n[bold]Summary Preview:[/bold]")
    console.print("─" * 80)
    console.print(summary)
    console.print("─" * 80)

    # Post to GitHub
    console.print(f"\n[cyan]Posting summary to {github_repo}#{github_issue}...[/cyan]")
    success = post_issue_comment(github_repo, github_issue, summary)

    if success:
        console.print(f"[green]✓ Summary posted to GitHub issue #{github_issue}[/green]")
        raise typer.Exit(code=0)
    else:
        console.print("[red]✗ Failed to post summary to GitHub[/red]")
        raise typer.Exit(code=1)


def main() -> None:
    """Tasks command main entry point"""
    try:
        app()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main()
