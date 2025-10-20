#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
#     "tomli-w>=1.0.0",
# ]
# ///

"""
Task State Update Hook - Programmatic Task State Management

Provides safe, atomic task state updates for agents and scripts instead of direct file editing.
Eliminates race conditions and ensures consistency across all state files.

Usage:
    uv run update_task_state.py --task="new-feature" --branch="feature/xyz"
    uv run update_task_state.py --task="new-feature" --services="hooks,analytics"
    uv run update_task_state.py --clear-task
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from rich.console import Console

# Add plugin root to path for utils access
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.project import find_project_root

console = Console()


def validate_branch_exists(project_root: Path, branch: str) -> bool:
    """Validate that the branch exists in git"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", branch],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def update_task_state(
    project_root: Path,
    task: Optional[str] = None,
    branch: Optional[str] = None,
    services: Optional[List[str]] = None,
    clear_task: bool = False
) -> dict:
    """Update task state using DAICStateManager for atomic updates

    Note: This updates state only. It does NOT run git commands.
    To actually switch branches, use git checkout manually.
    This is useful for fixing state mismatches or updating metadata.
    """

    try:
        # Import DAICStateManager
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from utils.daic_state_manager import DAICStateManager

        state_manager = DAICStateManager(project_root)

        if clear_task:
            # Clear current task
            result = state_manager.set_task_state(
                task=None,
                branch=None,
                services=[],
                correlation_id=state_manager.get_unified_state().get("correlation_id"),
                session_id=state_manager.get_unified_state().get("session_id")
            )
            console.print("✅ [green]Task state cleared[/green]")
            return result

        # Get current state for partial updates
        current_state = state_manager.get_task_state()
        current_unified = state_manager.get_unified_state()

        # Use provided values or keep existing ones
        final_task = task if task is not None else current_state.get("current_task")
        final_branch = branch if branch is not None else current_state.get("current_branch")
        final_services = services if services is not None else current_state.get("task_services", [])

        # Validate branch exists if a new branch was provided
        if branch is not None and final_branch:
            if not validate_branch_exists(project_root, final_branch):
                console.print(f"⚠️  [yellow]Warning:[/yellow] Branch '{final_branch}' does not exist in git")
                console.print("   State will be updated, but you may want to create the branch first")

        # Update task state atomically
        result = state_manager.set_task_state(
            task=final_task,
            branch=final_branch,
            services=final_services,
            correlation_id=current_unified.get("correlation_id"),
            session_id=current_unified.get("session_id")
        )

        # Success feedback
        if task:
            console.print(f"✅ [green]Task updated:[/green] {task}")
        if branch:
            console.print(f"✅ [green]Branch updated:[/green] {branch}")
        if services:
            console.print(f"✅ [green]Services updated:[/green] {', '.join(services)}")

        return result

    except Exception as e:
        console.print(f"❌ [red]Error updating task state:[/red] {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point for task state updates"""
    parser = argparse.ArgumentParser(
        description="Update task state programmatically",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run update_task_state.py --task="consolidate-state" --branch="feature/state"
  uv run update_task_state.py --services="hooks,analytics"
  uv run update_task_state.py --clear-task
        """
    )

    parser.add_argument("--task", help="Task name to set")
    parser.add_argument("--branch", help="Git branch to set in state (does not run git checkout)")
    parser.add_argument("--services", help="Comma-separated list of services")
    parser.add_argument("--clear-task", action="store_true", help="Clear current task")
    parser.add_argument("--show-current", action="store_true", help="Show current task state")

    args = parser.parse_args()

    # Parse services if provided
    services = None
    if args.services:
        services = [s.strip() for s in args.services.split(",") if s.strip()]

    # Find project root
    try:
        project_root = find_project_root()
    except Exception as e:
        console.print(f"❌ [red]Error finding project root:[/red] {e}")
        sys.exit(1)

    # Show current state if requested
    if args.show_current:
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from utils.daic_state_manager import DAICStateManager

            state_manager = DAICStateManager(project_root)
            task_state = state_manager.get_task_state()

            console.print("\n[green]Current Task State:[/green]")
            console.print(f"  Task: {task_state.get('current_task', 'None')}")

            # Show task file path if task is set
            current_task = task_state.get('current_task')
            if current_task and current_task != 'None':
                task_file = f".brainworm/tasks/{current_task}/README.md"
                console.print(f"  Task File: {task_file}")

            console.print(f"  Branch: {task_state.get('current_branch', 'None')}")
            console.print(f"  Services: {', '.join(task_state.get('task_services', []))}")
            console.print(f"  Updated: {task_state.get('updated', 'None')}")
            console.print(f"  Session ID: {task_state.get('session_id', 'None')}")
            console.print(f"  Correlation ID: {task_state.get('correlation_id', 'None')}")
            console.print()
        except Exception as e:
            console.print(f"❌ [red]Error showing current state:[/red] {e}")
            sys.exit(1)
        return

    # Update task state
    update_task_state(
        project_root=project_root,
        task=args.task,
        branch=args.branch,
        services=services,
        clear_task=args.clear_task
    )


if __name__ == "__main__":
    main()
