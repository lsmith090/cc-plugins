#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["rich>=13.0.0", "toml>=0.10.0"]
# ///

"""
Unified Task Creation Script - Creates tasks with submodule awareness

This is brainworm's FIRST automated task creation system. Previously, task creation
was entirely manual following documented protocols. This script orchestrates:
- Submodule detection and selection
- Task directory and README creation
- Branch creation in correct location (main repo OR submodule)
- DAIC state updates with submodule tracking
- Analytics correlation initialization
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.prompt import Prompt, Confirm

# Import brainworm utilities - add plugin root to path
script_path = Path(__file__).resolve()

# Determine plugin root based on location
if '.claude/plugins' in str(script_path):
    # Running from installed location: ~/.claude/plugins/.../brainworm/scripts/
    plugin_root = script_path.parent.parent
else:
    # Running from source: ~/repos/cc-plugins/brainworm/scripts/
    plugin_root = script_path.parent.parent

# Add plugin root to path for utils access
sys.path.insert(0, str(plugin_root))

try:
    # Import with utils. prefix to help with relative imports
    from utils.project import find_project_root
    from utils.git_submodule_manager import SubmoduleManager
    from utils.daic_state_manager import DAICStateManager
except ImportError as e:
    print(f"Error importing brainworm utilities: {e}")
    print(f"Tried utils path: {utils_path}")
    print(f"Tried parent path: {utils_path.parent}")
    print("Make sure you're running create_task.py from an installed brainworm system")
    print("Install brainworm via: /plugin install brainworm@<marketplace>")
    sys.exit(1)


console = Console()


def should_be_interactive() -> bool:
    """
    Auto-detect if we should run in interactive mode.

    Returns False (non-interactive) when:
    - Not running in a TTY (e.g., called by Claude Code, CI/CD)
    - Running in CI environment

    Returns True (interactive) when:
    - Running in a terminal by a human user

    Returns:
        bool: True if interactive prompts should be shown
    """
    import os

    # Check if running in a TTY (terminal)
    # When Claude Code calls this, stdin won't be a TTY
    if not sys.stdin.isatty():
        return False

    # Check for CI environment variables
    if os.getenv('CI') or os.getenv('GITHUB_ACTIONS'):
        return False

    # Default to interactive for terminal use
    return True


def determine_branch_prefix(task_name: str) -> str:
    """
    Determine git branch prefix based on task name.

    Args:
        task_name: Task identifier

    Returns:
        Branch prefix (feature, fix, refactor, etc.)
    """
    if task_name.startswith('fix-'):
        return 'fix'
    elif task_name.startswith('refactor-'):
        return 'refactor'
    elif task_name.startswith('test-'):
        return 'test'
    elif task_name.startswith('docs-'):
        return 'docs'
    elif task_name.startswith('migrate-'):
        return 'migrate'
    else:
        return 'feature'


def create_task(
    task_name: str,
    submodule: str | None = None,
    services: list[str] | None = None,
    interactive: bool = True
) -> bool:
    """
    Create task with submodule-aware branch management.

    This orchestrates the complete task creation workflow:
    1. Detect submodules
    2. Determine target location (explicit, interactive, or main repo)
    3. Create task directory structure
    4. Populate task README from template
    5. Create git branch in appropriate location
    6. Update DAIC state
    7. Provide next steps guidance

    Args:
        task_name: Task identifier (e.g., "implement-login-ui")
        submodule: Target submodule name (or None for interactive/main repo)
        services: List of affected services/modules
        interactive: Whether to prompt for submodule selection

    Returns:
        bool: True if successful
    """
    try:
        # 1. Find project root and detect submodules
        console.print("[cyan]Initializing task creation...[/cyan]")
        project_root = find_project_root()
        sm = SubmoduleManager(project_root)

        # 2. Determine submodule (explicit, interactive, or None)
        if submodule is None and interactive and sm.has_submodules():
            console.print(f"\n[yellow]Detected {len(sm.list_submodules())} submodules[/yellow]")
            submodule = sm.prompt_submodule_selection()

        # 3. Validate submodule if specified
        if submodule and not sm.validate_submodule(submodule):
            console.print(f"[red]Error: Submodule '{submodule}' not found[/red]")
            available = ', '.join(sm.list_submodules())
            console.print(f"[yellow]Available submodules: {available}[/yellow]")
            return False

        # 4. Determine branch name based on task prefix
        branch_prefix = determine_branch_prefix(task_name)
        branch_name = f"{branch_prefix}/{task_name}"

        # 5. Create task directory structure
        console.print(f"\n[cyan]Creating task directory...[/cyan]")
        task_dir = project_root / ".brainworm" / "tasks" / task_name
        task_dir.mkdir(parents=True, exist_ok=True)

        # 6. Copy and populate template
        task_readme = task_dir / "README.md"

        # Template always lives in the plugin directory (not copied locally)
        template_path = plugin_root / "templates" / "TEMPLATE.md"

        if not template_path.exists():
            console.print(f"[red]Error: Template not found at {template_path}[/red]")
            console.print(f"[yellow]Plugin root: {plugin_root}[/yellow]")
            return False

        with open(template_path, 'r') as f:
            template = f.read()

        # Replace template placeholders
        content = template.replace('[prefix]-[descriptive-name]', task_name)
        content = content.replace('feature/[name]|fix/[name]|experiment/[name]|none', branch_name)
        content = content.replace('[submodule-path]|none', submodule or 'none')
        content = content.replace('YYYY-MM-DD', datetime.now().strftime('%Y-%m-%d'))
        content = content.replace('[current-session-id]', 'pending')
        content = content.replace('[brainworm-correlation-id]', f'{task_name}_correlation')

        # Write task README
        task_readme.write_text(content)
        console.print(f"[green]✓ Created task file: .brainworm/tasks/{task_name}/README.md[/green]")

        # 7. Create git branch with smart monorepo handling
        console.print(f"\n[yellow]Creating branch '{branch_name}'...[/yellow]")

        # Determine branch creation strategy based on services
        active_submodule_branches = {}
        main_branch = branch_name  # Default: assume we're creating branch in main
        branch_created = False

        if services and sm.has_submodules():
            # NEW: Monorepo with services - create branches in submodules only
            console.print(f"[cyan]Detected {len(services)} services: {', '.join(services)}[/cyan]")

            # Confirm multi-service branch creation
            if interactive:
                console.print(f"[yellow]This will create '{branch_name}' in: {', '.join(services)}[/yellow]")
                console.print(f"[yellow]Main repo will stay on current branch[/yellow]")
                if not Confirm.ask("Proceed?", default=True):
                    console.print("[yellow]Skipping branch creation[/yellow]")
                else:
                    # Create branches in all specified services
                    branch_results = sm.create_branches_for_services(
                        branch_name=branch_name,
                        services=services,
                        create_main_branch=False  # Keep main on current branch
                    )

                    # Track successful branch creations
                    active_submodule_branches = {
                        svc: branch_name for svc, success in branch_results.items() if success
                    }
                    branch_created = len(active_submodule_branches) > 0
            else:
                # Non-interactive: create without prompting
                branch_results = sm.create_branches_for_services(
                    branch_name=branch_name,
                    services=services,
                    create_main_branch=False
                )
                active_submodule_branches = {
                    svc: branch_name for svc, success in branch_results.items() if success
                }
                branch_created = len(active_submodule_branches) > 0

            # Get current main repo branch for tracking
            main_branch = sm.get_current_branch(submodule=None) or "main"

        elif submodule:
            # EXISTING: Single submodule specified
            location = f"submodule '{submodule}'"
            if interactive and not Confirm.ask(f"Create branch in {location}?", default=True):
                console.print("[yellow]Skipping branch creation[/yellow]")
            else:
                branch_created = sm.create_branch(branch_name, submodule)
                if branch_created:
                    active_submodule_branches[submodule] = branch_name
                    main_branch = sm.get_current_branch(submodule=None) or "main"
        else:
            # EXISTING: No services, no submodule - create in main repo
            location = "main repository"
            if interactive and not Confirm.ask(f"Create branch in {location}?", default=True):
                console.print("[yellow]Skipping branch creation[/yellow]")
            else:
                branch_created = sm.create_branch(branch_name, submodule=None)
                main_branch = branch_name

        if not branch_created:
            console.print("[yellow]Note: Branch not created, you'll need to create it manually[/yellow]")

        # 8. Update DAIC state with submodule branch tracking
        console.print(f"\n[cyan]Updating DAIC state...[/cyan]")
        state_mgr = DAICStateManager(project_root)

        # Get current state to preserve session/correlation IDs
        current_unified = state_mgr.get_unified_state()

        state_mgr.set_task_state(
            task=task_name,
            branch=main_branch,  # Main repo's actual branch
            services=services or [],
            correlation_id=current_unified.get("correlation_id"),
            session_id=current_unified.get("session_id"),
            active_submodule_branches=active_submodule_branches
        )
        console.print("[green]✓ DAIC state updated[/green]")

        # 9. Success message with next steps
        console.print(f"\n[bold green]✓ Task '{task_name}' created successfully![/bold green]")
        console.print(f"\n[cyan]Task Details:[/cyan]")
        console.print(f"  • Task file: .brainworm/tasks/{task_name}/README.md")
        console.print(f"  • Branch: {branch_name}")

        if active_submodule_branches:
            # Multi-service monorepo case
            console.print(f"  • Main repo: [yellow]{main_branch}[/yellow] (unchanged)")
            console.print(f"  • Service branches:")
            for svc, svc_branch in active_submodule_branches.items():
                svc_path = sm.get_submodule_path(svc)
                console.print(f"    - {svc}: [green]{svc_branch}[/green]")
        elif submodule:
            # Single submodule case
            console.print(f"  • Submodule: {submodule}")
            console.print(f"  • Location: {sm.get_submodule_path(submodule)}")
        else:
            # Main repo case
            console.print(f"  • Location: main repository")

        console.print(f"\n[yellow]Next steps:[/yellow]")
        console.print("  1. Edit task file to add description and success criteria")
        console.print("  2. Invoke context-gathering agent for comprehensive context:")
        console.print(f"     [dim]Use Task tool with context-gathering agent, provide task file path[/dim]")
        console.print("  3. Start work in discussion mode (already active)")

        if active_submodule_branches:
            console.print(f"\n[yellow]Note:[/yellow] Your work spans multiple services: {', '.join(active_submodule_branches.keys())}")
            console.print("Work in each service will be on its feature branch.")
            console.print(f"Main repo stays on [cyan]{main_branch}[/cyan]")
        elif submodule:
            console.print(f"\n[yellow]Note:[/yellow] Your work is scoped to the '{submodule}' submodule.")
            console.print("File edits outside this submodule may be blocked by DAIC enforcement.")

        return True

    except Exception as e:
        console.print(f"[red]Error creating task: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


def main():
    """CLI interface for task creation."""
    parser = argparse.ArgumentParser(
        description="Create a new brainworm task with submodule awareness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (prompts for submodule if available)
  %(prog)s implement-login-ui

  # Explicit submodule
  %(prog)s implement-login-ui --submodule=one-mit

  # Main repo task (no submodule)
  %(prog)s fix-database-connection --no-interactive

  # With services
  %(prog)s refactor-api-layer --services=backend,api
        """
    )

    parser.add_argument(
        'task_name',
        help='Task identifier (e.g., implement-login-ui, fix-auth-bug)'
    )
    parser.add_argument(
        '--submodule',
        help='Target submodule name (e.g., one-mit, one-mit-backend)'
    )
    parser.add_argument(
        '--services',
        help='Comma-separated list of affected services/modules'
    )
    parser.add_argument(
        '--no-interactive',
        action='store_true',
        help='Force non-interactive mode (auto-detected by default)'
    )

    args = parser.parse_args()

    # Parse services
    services = args.services.split(',') if args.services else None

    # Auto-detect interactive mode if not explicitly set
    if args.no_interactive:
        interactive = False
    else:
        # Auto-detect based on environment (TTY detection)
        interactive = should_be_interactive()

    # Create task
    success = create_task(
        task_name=args.task_name,
        submodule=args.submodule,
        services=services,
        interactive=interactive
    )

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
