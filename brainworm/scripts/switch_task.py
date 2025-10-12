#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
#     "toml>=0.10.0",
# ]
# ///

"""
Switch Task Script - Atomic Task Switching

Provides atomic task switching by:
1. Validating task exists
2. Parsing task metadata for branch and services
3. Checking out git branch
4. Updating DAIC state atomically
5. Displaying task summary and next steps

Usage:
    ./tasks switch [task-name]
    ./tasks switch implement-feature
"""

# Add plugin root to sys.path before any utils imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import subprocess
from typing import Dict, Optional, List
from rich.console import Console

console = Console()


def parse_task_frontmatter(readme_path: Path) -> Optional[Dict[str, any]]:
    """Parse YAML frontmatter from task README.md"""
    try:
        content = readme_path.read_text()

        # Check for frontmatter
        if not content.startswith('---'):
            return None

        # Extract frontmatter (between first two ---)
        parts = content.split('---', 2)
        if len(parts) < 3:
            return None

        frontmatter = parts[1].strip()

        # Parse simple YAML (key: value format)
        metadata = {}
        for line in frontmatter.split('\n'):
            line = line.strip()
            if not line or ':' not in line:
                continue

            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()

            # Handle lists [item1, item2]
            if value.startswith('[') and value.endswith(']'):
                value = [v.strip() for v in value[1:-1].split(',')]

            metadata[key] = value

        return metadata

    except Exception as e:
        console.print(f"[red]Error parsing task frontmatter: {e}[/red]")
        return None


def check_context_manifest(task_dir: Path) -> bool:
    """Check if task has a context manifest section"""
    try:
        readme = task_dir / "README.md"
        content = readme.read_text()

        # Check for Context Manifest or Context Files section
        return "## Context Manifest" in content or "## Context Files" in content
    except Exception:
        return False


def switch_task(task_name: str) -> bool:
    """
    Switch to an existing task atomically.

    Args:
        task_name: Name of the task to switch to

    Returns:
        bool: True if successful
    """
    try:
        from utils.project import find_project_root
        from utils.daic_state_manager import DAICStateManager

        project_root = find_project_root()

        # 1. Validate task exists
        task_dir = project_root / ".brainworm" / "tasks" / task_name
        task_readme = task_dir / "README.md"

        if not task_dir.exists():
            console.print(f"[red]Error: Task '{task_name}' not found[/red]")
            console.print(f"[yellow]Task directory does not exist: {task_dir}[/yellow]")
            console.print("\n[cyan]Available tasks:[/cyan]")

            # Show available tasks
            tasks_dir = project_root / ".brainworm" / "tasks"
            if tasks_dir.exists():
                available = [d.name for d in tasks_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
                if available:
                    for task in sorted(available):
                        console.print(f"  • {task}")
                else:
                    console.print("  [yellow]No tasks found[/yellow]")

            return False

        if not task_readme.exists():
            console.print(f"[red]Error: Task README not found: {task_readme}[/red]")
            return False

        # 2. Parse task metadata
        console.print(f"[cyan]Switching to task: {task_name}[/cyan]")
        metadata = parse_task_frontmatter(task_readme)

        if not metadata:
            console.print("[red]Error: Could not parse task frontmatter[/red]")
            console.print("[yellow]Task README must have YAML frontmatter with task metadata[/yellow]")
            return False

        # Extract task info
        branch = metadata.get('branch', 'N/A')
        services_raw = metadata.get('modules', [])

        # Handle services/modules field
        if isinstance(services_raw, str):
            # Could be a string like "[service1, service2]" or "service1"
            if services_raw.startswith('[') and services_raw.endswith(']'):
                services = [s.strip() for s in services_raw[1:-1].split(',') if s.strip()]
            else:
                services = [services_raw] if services_raw and services_raw != 'none' else []
        elif isinstance(services_raw, list):
            services = [s for s in services_raw if s and s != 'none']
        else:
            services = []

        if branch == 'N/A' or not branch or branch == 'none':
            console.print("[yellow]Warning: No branch specified in task metadata[/yellow]")
            console.print("[yellow]Will update state but not checkout git branch[/yellow]")
            branch_checkout = False
        else:
            branch_checkout = True

        # 3. Check out git branch
        if branch_checkout:
            console.print(f"[yellow]Checking out branch: {branch}[/yellow]")
            try:
                result = subprocess.run(
                    ['git', 'checkout', branch],
                    cwd=project_root,
                    capture_output=True,
                    text=True,
                    check=False
                )

                if result.returncode != 0:
                    console.print(f"[red]Error: Git checkout failed[/red]")
                    console.print(f"[red]{result.stderr.strip()}[/red]")
                    return False

                console.print(f"[green]✓ Checked out branch: {branch}[/green]")
            except Exception as e:
                console.print(f"[red]Error executing git checkout: {e}[/red]")
                return False

        # 4. Update DAIC state
        console.print("[cyan]Updating DAIC state...[/cyan]")
        state_mgr = DAICStateManager(project_root)

        # Get current state for session/correlation IDs
        current_unified = state_mgr.get_unified_state()

        state_mgr.set_task_state(
            task=task_name,
            branch=branch if branch_checkout else None,
            services=services,
            correlation_id=current_unified.get("correlation_id"),
            session_id=current_unified.get("session_id")
        )

        console.print("[green]✓ DAIC state updated[/green]")

        # 5. Display task summary
        console.print(f"\n[bold green]✓ Switched to task: {task_name}[/bold green]\n")

        console.print("[cyan]Task Details:[/cyan]")
        console.print(f"  • Task file: .brainworm/tasks/{task_name}/README.md")
        if branch_checkout:
            console.print(f"  • Branch: {branch}")
        if services:
            console.print(f"  • Services: {', '.join(services)}")

        # Check for context manifest
        has_context = check_context_manifest(task_dir)
        if not has_context:
            console.print("\n[yellow]⚠ Warning: Task has no Context Manifest[/yellow]")
            console.print("[yellow]Consider invoking context-gathering agent for comprehensive context[/yellow]")

        # Next steps
        console.print("\n[cyan]Next steps:[/cyan]")
        console.print("  1. Review task README for goals and success criteria")
        if not has_context:
            console.print("  2. Invoke context-gathering agent if needed:")
            console.print("     [dim]Use Task tool with context-gathering agent, provide task file path[/dim]")
        console.print("  3. Begin work (currently in discussion mode)")

        return True

    except Exception as e:
        console.print(f"[red]Error switching task: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


def show_usage() -> None:
    """Show command usage"""
    console.print("\n[bold]Switch Task - Atomic Task Switching[/bold]")
    console.print("Usage:")
    console.print("  [green]./tasks switch[/green] [task-name]")
    console.print()
    console.print("Examples:")
    console.print("  [dim]./tasks switch implement-feature[/dim]")
    console.print("  [dim]./tasks switch fix-bug-123[/dim]")
    console.print()
    console.print("What it does:")
    console.print("  • Validates task exists")
    console.print("  • Checks out task's git branch")
    console.print("  • Updates DAIC state with task info")
    console.print("  • Displays task summary and next steps")
    console.print()


def main() -> None:
    """Main entry point"""
    try:
        # Parse arguments
        args = sys.argv[1:]

        if not args or args[0] in ['--help', '-h', 'help']:
            show_usage()
            return

        task_name = args[0]

        # Switch to task
        success = switch_task(task_name)
        sys.exit(0 if success else 1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main()
