#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
# ]
# ///

"""
List Tasks Script - Display All Tasks

Shows all tasks in .brainworm/tasks/ directory with their status,
branch, and other metadata. Highlights the current active task.
"""

# Add plugin root to sys.path before any utils imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from datetime import datetime
from typing import Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich.text import Text

console = Console()


def parse_task_frontmatter(readme_path: Path) -> Optional[Dict[str, any]]:
    """Parse YAML frontmatter from task README.md with robust edge case handling"""
    try:
        content = readme_path.read_text()

        # Check for frontmatter (strip leading whitespace)
        content_stripped = content.lstrip()
        if not content_stripped.startswith('---'):
            return None

        # Extract frontmatter (between first two --- markers)
        # Use lstrip() content to handle indented frontmatter
        parts = content_stripped.split('---', 2)
        if len(parts) < 3:
            return None

        frontmatter = parts[1].strip()
        if not frontmatter:  # Empty frontmatter
            return {}

        # Parse simple YAML (key: value format)
        metadata = {}
        for line in frontmatter.split('\n'):
            line = line.strip()
            if not line or ':' not in line:
                continue

            # Split on first colon only (handles values with colons)
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()

            # Skip entries with empty keys
            if not key:
                continue

            # Strip YAML comments (everything after #, but not inside lists)
            if '#' in value and not (value.startswith('[') and value.endswith(']')):
                value = value.split('#')[0].strip()

            # Handle lists [item1, item2]
            if value.startswith('[') and value.endswith(']'):
                inner = value[1:-1].strip()
                # Handle empty lists
                if not inner:
                    value = []
                else:
                    value = [v.strip() for v in inner.split(',') if v.strip()]

            # Store non-empty values
            if value or value == []:  # Allow empty lists but not empty strings
                metadata[key] = value

        return metadata

    except Exception as e:
        console.print(f"[yellow]Warning: Could not parse {readme_path}: {e}[/yellow]")
        return None


def get_current_task(project_root: Path) -> Optional[str]:
    """Get current task from unified session state"""
    try:
        state_file = project_root / ".brainworm" / "state" / "unified_session_state.json"
        if not state_file.exists():
            return None

        with open(state_file, 'r') as f:
            data = json.load(f)
            return data.get('current_task')

    except Exception:
        return None


def format_date(date_str: str) -> str:
    """Format date string for display"""
    try:
        # Parse YYYY-MM-DD format
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%b %d, %Y')
    except Exception:
        return date_str


def get_status_style(status: str) -> tuple[str, str]:
    """Get color and symbol for task status"""
    status_lower = status.lower()

    if status_lower == 'completed':
        return 'green', '✓'
    elif status_lower == 'in_progress' or status_lower == 'active':
        return 'yellow', '◉'
    elif status_lower == 'pending':
        return 'blue', '○'
    elif status_lower == 'blocked':
        return 'red', '✗'
    else:
        return 'white', '·'


def list_tasks(project_root: Path, filter_status: Optional[str] = None, show_all: bool = False) -> None:
    """List all tasks in .brainworm/tasks directory"""

    tasks_dir = project_root / ".brainworm" / "tasks"

    if not tasks_dir.exists():
        console.print("[yellow]No tasks directory found.[/yellow]")
        console.print(f"Expected location: {tasks_dir}")
        return

    # Get current task
    current_task = get_current_task(project_root)

    # Find all task directories
    task_dirs = [d for d in tasks_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]

    if not task_dirs:
        console.print("[yellow]No tasks found.[/yellow]")
        return

    # Parse task metadata
    tasks = []
    for task_dir in task_dirs:
        readme = task_dir / "README.md"
        if not readme.exists():
            continue

        metadata = parse_task_frontmatter(readme)
        if not metadata:
            continue

        # Apply status filter if specified
        if filter_status:
            task_status = metadata.get('status', '').lower()
            if task_status != filter_status.lower():
                continue

        tasks.append({
            'name': metadata.get('task', task_dir.name),
            'status': metadata.get('status', 'unknown'),
            'branch': metadata.get('branch', 'N/A'),
            'created': metadata.get('created', 'N/A'),
            'completed': metadata.get('completed', ''),
            'modules': metadata.get('modules', []),
            'is_current': metadata.get('task', task_dir.name) == current_task
        })

    if not tasks:
        if filter_status:
            console.print(f"[yellow]No tasks found with status: {filter_status}[/yellow]")
        else:
            console.print("[yellow]No tasks with valid metadata found.[/yellow]")
        return

    # Sort tasks: current first, then by status (in_progress, pending, completed), then by created date
    def sort_key(task):
        if task['is_current']:
            return (0, task['created'])
        status_order = {'in_progress': 1, 'active': 1, 'pending': 2, 'blocked': 3, 'completed': 4}
        return (status_order.get(task['status'].lower(), 5), task['created'])

    tasks.sort(key=sort_key)

    # Create table
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Status", width=10)
    table.add_column("Task", style="white")
    table.add_column("Branch", style="dim")
    table.add_column("Created", style="dim")

    if show_all:
        table.add_column("Completed", style="dim")
        table.add_column("Modules", style="dim")

    # Add rows
    for task in tasks:
        status_style, status_symbol = get_status_style(task['status'])

        # Format status
        status_text = Text()
        status_text.append(f"{status_symbol} ", style=status_style)
        status_text.append(task['status'].capitalize()[:8], style=status_style)

        # Format task name (highlight current task)
        task_name = task['name']
        if task['is_current']:
            task_text = Text(f"→ {task_name}", style="bold yellow")
        else:
            task_text = Text(task_name)

        # Format dates
        created = format_date(task['created']) if task['created'] != 'N/A' else 'N/A'

        # Add row
        row = [
            status_text,
            task_text,
            task['branch'],
            created,
        ]

        if show_all:
            completed = format_date(task['completed']) if task['completed'] else '-'
            modules = ', '.join(task['modules']) if isinstance(task['modules'], list) else str(task['modules'])
            row.extend([completed, modules])

        table.add_row(*row)

    # Display table
    console.print()
    console.print(table)
    console.print()

    # Summary
    total = len(tasks)
    completed = sum(1 for t in tasks if t['status'].lower() == 'completed')
    in_progress = sum(1 for t in tasks if t['status'].lower() in ['in_progress', 'active'])
    pending = sum(1 for t in tasks if t['status'].lower() == 'pending')

    summary_parts = [f"Total: {total} tasks"]
    if in_progress > 0:
        summary_parts.append(f"[yellow]In Progress: {in_progress}[/yellow]")
    if pending > 0:
        summary_parts.append(f"[blue]Pending: {pending}[/blue]")
    summary_parts.append(f"[green]Completed: {completed}[/green]")

    console.print(f"[dim]{' | '.join(summary_parts)}[/dim]")
    console.print()


def show_usage() -> None:
    """Show command usage"""
    console.print("\n[bold]List Tasks - Display All Tasks[/bold]")
    console.print("Usage:")
    console.print("  [green]list_tasks.py[/green]                    - List all tasks")
    console.print("  [green]list_tasks.py[/green] [dim]--status=STATUS[/dim]   - Filter by status")
    console.print("  [green]list_tasks.py[/green] [dim]--all[/dim]             - Show all columns")
    console.print()
    console.print("Options:")
    console.print("  [dim]--status=completed[/dim]   Show only completed tasks")
    console.print("  [dim]--status=pending[/dim]     Show only pending tasks")
    console.print("  [dim]--status=in_progress[/dim] Show only in-progress tasks")
    console.print("  [dim]--all[/dim]                Show additional columns (completed date, modules)")
    console.print()


def main() -> None:
    """Main entry point"""
    try:
        # Find project root
        from utils.project import find_project_root
        project_root = find_project_root()

        # Parse arguments
        filter_status = None
        show_all = False

        for arg in sys.argv[1:]:
            if arg in ['--help', '-h', 'help']:
                show_usage()
                return
            elif arg.startswith('--status='):
                filter_status = arg.split('=', 1)[1]
            elif arg == '--all':
                show_all = True

        # List tasks
        list_tasks(project_root, filter_status, show_all)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main()
