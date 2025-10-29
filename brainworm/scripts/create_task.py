#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["rich>=13.0.0", "tomli-w>=1.0.0"]
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

import argparse
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm

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
    from utils.config import load_config
    from utils.daic_state_manager import DAICStateManager
    from utils.git_submodule_manager import SubmoduleManager
    from utils.github_integration import (
        check_gh_available,
        create_github_issue,
        detect_github_repo,
        extract_issue_number_from_task_name,
        link_issue_to_task,
    )
    from utils.project import find_project_root
except ImportError as e:
    print(f"Error importing brainworm utilities: {e}")
    print(f"Tried plugin root: {plugin_root}")
    print(f"Python path: {sys.path[:3]}")
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
    interactive: bool = True,
    link_issue: int | None = None,
    create_issue: bool = False,
    no_github: bool = False
) -> bool:
    """
    Create task with submodule-aware branch management and GitHub integration.

    This orchestrates the complete task creation workflow:
    1. Detect submodules
    2. Determine target location (explicit, interactive, or main repo)
    3. Create task directory structure
    4. Populate task README from template
    5. GitHub integration (link/create issues if enabled)
    6. Smart branch detection (create new or use current)
    7. Create git branch in appropriate location
    8. Update DAIC state
    9. Provide next steps guidance

    Args:
        task_name: Task identifier (e.g., "implement-login-ui" or "fix-bug-#123")
        submodule: Target submodule name (or None for interactive/main repo)
        services: List of affected services/modules
        interactive: Whether to prompt for submodule selection
        link_issue: Explicit GitHub issue number to link (overrides auto-detection)
        create_issue: Create new GitHub issue for this task
        no_github: Skip GitHub integration completely

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
        console.print("\n[cyan]Creating task directory...[/cyan]")
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

        # 7. GitHub integration (if enabled and not disabled)
        if not no_github:
            try:
                # Load configuration
                config = load_config(project_root)
                github_config = config.get("github", {})
                github_enabled = github_config.get("enabled", False)

                if github_enabled and check_gh_available():
                    console.print("\n[cyan]GitHub integration enabled[/cyan]")

                    # Detect GitHub repository
                    repo = detect_github_repo(project_root, submodule)
                    if not repo:
                        console.print("[yellow]Could not detect GitHub repository, skipping integration[/yellow]")
                    else:
                        console.print(f"[cyan]Detected repository: {repo}[/cyan]")

                        # Determine issue number to link
                        issue_to_link = None

                        if link_issue:
                            # Explicit CLI flag
                            issue_to_link = link_issue
                            console.print(f"[cyan]Linking to issue #{issue_to_link} (explicit)[/cyan]")
                        elif github_config.get("auto_link_issues", True):
                            # Pattern matching in task name
                            detected_issue = extract_issue_number_from_task_name(task_name)
                            if detected_issue:
                                issue_to_link = detected_issue
                                console.print(f"[green]Auto-detected issue #{issue_to_link} from task name[/green]")

                        # Create new issue if requested
                        if create_issue or (not issue_to_link and github_config.get("create_issue_on_task", False)):
                            console.print("[cyan]Creating new GitHub issue...[/cyan]")
                            created_issue = create_github_issue(
                                repo=repo,
                                title=task_name,
                                body=f"Task: {task_name}\n\nCreated via brainworm task management."
                            )
                            if created_issue:
                                issue_to_link = created_issue
                                console.print(f"[green]✓ Created issue #{created_issue}[/green]")
                            else:
                                console.print("[yellow]Failed to create issue[/yellow]")

                        # Link issue to task
                        if issue_to_link:
                            if link_issue_to_task(task_readme, issue_to_link, repo):
                                console.print(f"[green]✓ Linked to GitHub issue #{issue_to_link}[/green]")
                                console.print(f"[dim]https://github.com/{repo}/issues/{issue_to_link}[/dim]")
                            else:
                                console.print("[yellow]Failed to link issue to task[/yellow]")

                elif github_enabled and not check_gh_available():
                    console.print("[yellow]GitHub integration enabled but gh CLI not available[/yellow]")
                    console.print("[dim]Install: https://cli.github.com/[/dim]")

            except Exception as e:
                console.print(f"[yellow]GitHub integration error (non-fatal): {e}[/yellow]")
                # Continue with task creation

        # 8. Smart branch detection - decide whether to create new branch or use current
        console.print("\n[cyan]Checking current branch...[/cyan]")

        # Get current branch in main repo (or submodule if specified)
        current_branch = sm.get_current_branch(submodule=submodule if submodule else None)
        stable_branches = ['main', 'master', 'develop', 'dev']

        # Decide: create new branch or use current?
        should_create_new_branch = False
        if current_branch in stable_branches:
            # On stable branch → create new feature branch
            should_create_new_branch = True
            console.print(f"[yellow]Currently on '{current_branch}' - will create new branch '{branch_name}'[/yellow]")
        elif current_branch:
            # Already on feature branch → use it (deterministic default)
            should_create_new_branch = False
            branch_name = current_branch  # Use existing branch instead
            console.print(f"[green]Currently on feature branch '{current_branch}' - using it for this task[/green]")
        else:
            # Detached HEAD or no branch → create new
            should_create_new_branch = True
            console.print(f"[yellow]Not on any branch - will create '{branch_name}'[/yellow]")

        # 9. Create git branch with smart monorepo handling
        # Determine branch creation strategy based on services
        active_submodule_branches = {}
        main_branch = branch_name  # Default: assume we're creating branch in main
        branch_created = False

        if services and sm.has_submodules():
            # NEW: Monorepo with services - create branches in submodules only
            console.print(f"[cyan]Detected {len(services)} services: {', '.join(services)}[/cyan]")

            # Validate that all services exist before attempting branch creation
            available_submodules = sm.list_submodules()
            invalid_services = [svc for svc in services if svc not in available_submodules]
            if invalid_services:
                console.print(f"[red]Error: Invalid service names: {', '.join(invalid_services)}[/red]")
                console.print(f"[yellow]Available services: {', '.join(available_submodules)}[/yellow]")
                sys.exit(1)

            if should_create_new_branch:
                # Confirm multi-service branch creation
                if interactive:
                    console.print(f"[yellow]This will create '{branch_name}' in: {', '.join(services)}[/yellow]")
                    console.print("[yellow]Main repo will stay on current branch[/yellow]")
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
            else:
                # Using current branches in services
                console.print("[green]Using current branches in services (no new branch creation)[/green]")
                # Track current branches for each service
                for svc in services:
                    svc_branch = sm.get_current_branch(submodule=svc)
                    if svc_branch:
                        active_submodule_branches[svc] = svc_branch
                branch_created = True

            # Get current main repo branch for tracking
            main_branch = sm.get_current_branch(submodule=None) or "main"

        elif submodule:
            # EXISTING: Single submodule specified
            location = f"submodule '{submodule}'"
            if should_create_new_branch:
                if interactive and not Confirm.ask(f"Create branch in {location}?", default=True):
                    console.print("[yellow]Skipping branch creation[/yellow]")
                else:
                    branch_created = sm.create_branch(branch_name, submodule)
                    if branch_created:
                        active_submodule_branches[submodule] = branch_name
                        main_branch = sm.get_current_branch(submodule=None) or "main"
            else:
                # Using current branch in submodule
                console.print(f"[green]Using current branch in {location}[/green]")
                active_submodule_branches[submodule] = branch_name
                main_branch = sm.get_current_branch(submodule=None) or "main"
                branch_created = True
        else:
            # EXISTING: No services, no submodule - create in main repo
            location = "main repository"
            if should_create_new_branch:
                if interactive and not Confirm.ask(f"Create branch in {location}?", default=True):
                    console.print("[yellow]Skipping branch creation[/yellow]")
                else:
                    branch_created = sm.create_branch(branch_name, submodule=None)
                    main_branch = branch_name
            else:
                # Using current branch in main repo
                console.print(f"[green]Using current branch '{branch_name}' in {location}[/green]")
                branch_created = True
                main_branch = branch_name

        if not branch_created:
            console.print("[yellow]Note: Branch not created, you'll need to create it manually[/yellow]")

        # 10. Update DAIC state with submodule branch tracking
        console.print("\n[cyan]Updating DAIC state...[/cyan]")
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

        # 11. Success message with next steps
        console.print(f"\n[bold green]✓ Task '{task_name}' created successfully![/bold green]")
        console.print("\n[cyan]Task Details:[/cyan]")
        console.print(f"  • Task file: .brainworm/tasks/{task_name}/README.md")
        console.print(f"  • Branch: {branch_name}")

        if active_submodule_branches:
            # Multi-service monorepo case
            console.print(f"  • Main repo: [yellow]{main_branch}[/yellow] (unchanged)")
            console.print("  • Service branches:")
            for svc, svc_branch in active_submodule_branches.items():
                console.print(f"    - {svc}: [green]{svc_branch}[/green]")
        elif submodule:
            # Single submodule case
            console.print(f"  • Submodule: {submodule}")
            console.print(f"  • Location: {sm.get_submodule_path(submodule)}")
        else:
            # Main repo case
            console.print("  • Location: main repository")

        console.print("\n[yellow]Next steps:[/yellow]")
        console.print("  1. Edit task file to add description and success criteria")
        console.print("  2. Invoke context-gathering agent for comprehensive context:")
        console.print("     [dim]Use Task tool with context-gathering agent, provide task file path[/dim]")
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
        description="Create a new brainworm task with submodule awareness and GitHub integration",
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

  # GitHub integration: auto-link from task name
  %(prog)s fix-bug-#123  # Auto-links to issue #123

  # GitHub integration: explicit link
  %(prog)s implement-feature --link-issue=456

  # GitHub integration: create new issue
  %(prog)s add-new-feature --create-issue

  # Skip GitHub integration
  %(prog)s task-name --no-github
        """
    )

    parser.add_argument(
        'task_name',
        help='Task identifier (e.g., implement-login-ui, fix-bug-#123)'
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
    parser.add_argument(
        '--link-issue',
        type=int,
        help='Link task to existing GitHub issue number'
    )
    parser.add_argument(
        '--create-issue',
        action='store_true',
        help='Create new GitHub issue for this task'
    )
    parser.add_argument(
        '--no-github',
        action='store_true',
        help='Skip GitHub integration completely'
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
        interactive=interactive,
        link_issue=args.link_issue,
        create_issue=args.create_issue,
        no_github=args.no_github
    )

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
