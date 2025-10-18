#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
#     "tomli-w>=1.0.0",
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
from utils.git_submodule_manager import SubmoduleManager
from utils.debug_logger import create_debug_logger, get_default_debug_config

console = Console()
debug_logger = None  # Will be initialized in switch_task()


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
        from utils.config import load_config

        project_root = find_project_root()

        # Initialize debug logger
        from utils.debug_logger import DebugConfig
        config = load_config(project_root)
        debug_dict = config.get('debug', {})
        debug_config = DebugConfig.from_dict(debug_dict) if debug_dict else get_default_debug_config()
        debug_logger = create_debug_logger('switch_task', project_root, debug_config)

        debug_logger.info(f"Task switch initiated: {task_name}")

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

        # Extract submodule field
        submodule = metadata.get('submodule', 'none')
        # Normalize values
        if submodule in ['none', 'N/A', '', 'null']:
            submodule = None

        debug_logger.debug(f"Task metadata: branch={branch}, submodule={submodule}, services={services}")

        if branch == 'N/A' or not branch or branch == 'none':
            console.print("[yellow]Warning: No branch specified in task metadata[/yellow]")
            console.print("[yellow]Will update state but not checkout git branch[/yellow]")
            branch_checkout = False
        else:
            branch_checkout = True

        # 3. Check out git branch(es)
        if branch_checkout:
            # Determine if this is a submodule-scoped task
            if submodule:
                # Single submodule task
                debug_logger.info(f"Detected submodule-scoped task: submodule='{submodule}', branch='{branch}'")
                console.print(f"[yellow]Switching submodule '{submodule}' to branch: {branch}[/yellow]")

                sm = SubmoduleManager(project_root)

                # Validate submodule exists
                if not sm.validate_submodule(submodule):
                    console.print(f"[red]Error: Submodule '{submodule}' not found[/red]")
                    available = sm.list_submodules()
                    if available:
                        console.print(f"[yellow]Available submodules: {', '.join(available)}[/yellow]")
                    return False

                submodule_path = sm.get_submodule_path(submodule)

                # Check and fix detached HEAD state
                if not sm._ensure_submodule_on_branch(submodule_path):
                    console.print(f"[red]Error: Submodule '{submodule}' is in detached HEAD state[/red]")
                    console.print("[red]Could not checkout to a default branch (tried: main, master, develop)[/red]")
                    return False

                # Checkout branch in submodule
                try:
                    debug_logger.debug(f"Executing git checkout in submodule: cwd={submodule_path}, branch={branch}")
                    result = subprocess.run(
                        ['git', 'checkout', branch],
                        cwd=submodule_path,  # ← This is the fix!
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=10  # Prevent hanging on slow git operations
                    )

                    if result.returncode != 0:
                        debug_logger.error(f"Git checkout failed in submodule '{submodule}': {result.stderr.strip()}")
                        console.print(f"[red]Error: Git checkout failed in submodule '{submodule}'[/red]")
                        console.print(f"[red]{result.stderr.strip()}[/red]")
                        return False

                    debug_logger.info(f"Successfully checked out branch '{branch}' in submodule '{submodule}'")
                    console.print(f"[green]✓ Checked out branch '{branch}' in submodule '{submodule}'[/green]")

                    # Verify the checkout succeeded
                    actual_branch = sm.get_current_branch(submodule)
                    debug_logger.debug(f"Verification: expected_branch='{branch}', actual_branch='{actual_branch}'")
                    if actual_branch != branch:
                        debug_logger.error(f"Branch verification failed: expected '{branch}', got '{actual_branch}'")
                        console.print(f"[red]Error: Branch verification failed in submodule '{submodule}'[/red]")
                        console.print(f"[red]Expected '{branch}', but got '{actual_branch}'[/red]")
                        return False

                except Exception as e:
                    console.print(f"[red]Error executing git checkout: {e}[/red]")
                    return False

            elif services:
                # Multi-service task - checkout branches in multiple submodules
                debug_logger.info(f"Detected multi-service task: services={services}")
                console.print(f"[yellow]Switching multiple services to their task branches...[/yellow]")

                sm = SubmoduleManager(project_root)
                state_mgr_temp = DAICStateManager(project_root)
                current_unified = state_mgr_temp.get_unified_state()
                active_branches = current_unified.get('active_submodule_branches', {})

                if not active_branches:
                    debug_logger.warning("No active_submodule_branches in state, skipping submodule checkout")
                else:
                    for service, service_branch in active_branches.items():
                        console.print(f"[cyan]  • {service} → {service_branch}[/cyan]")

                        if not sm.validate_submodule(service):
                            console.print(f"[yellow]    Warning: Submodule '{service}' not found, skipping[/yellow]")
                            continue

                        submodule_path = sm.get_submodule_path(service)

                        # Fix detached HEAD if needed
                        sm._ensure_submodule_on_branch(submodule_path)

                        # Checkout branch
                        result = subprocess.run(
                            ['git', 'checkout', service_branch],
                            cwd=submodule_path,
                            capture_output=True,
                            text=True,
                            check=False,
                            timeout=10  # Prevent hanging on slow git operations
                        )

                        if result.returncode != 0:
                            console.print(f"[red]    Error: Failed to checkout '{service_branch}' in '{service}'[/red]")
                            console.print(f"[red]    {result.stderr.strip()}[/red]")
                            return False
                        else:
                            console.print(f"[green]    ✓ Checked out '{service_branch}'[/green]")
            else:
                # Main repo task - original behavior
                debug_logger.info(f"Detected main repo task: branch='{branch}'")
                console.print(f"[yellow]Checking out branch: {branch}[/yellow]")
                try:
                    debug_logger.debug(f"Executing git checkout in main repo: cwd={project_root}, branch={branch}")
                    result = subprocess.run(
                        ['git', 'checkout', branch],
                        cwd=project_root,
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=10  # Prevent hanging on slow git operations
                    )

                    if result.returncode != 0:
                        debug_logger.error(f"Git checkout failed in main repo: {result.stderr.strip()}")
                        console.print(f"[red]Error: Git checkout failed[/red]")
                        console.print(f"[red]{result.stderr.strip()}[/red]")
                        return False

                    debug_logger.info(f"Successfully checked out branch '{branch}' in main repo")
                    console.print(f"[green]✓ Checked out branch: {branch}[/green]")
                except Exception as e:
                    debug_logger.error(f"Exception during git checkout: {e}")
                    console.print(f"[red]Error executing git checkout: {e}[/red]")
                    return False

        # 4. Update DAIC state
        debug_logger.debug("Updating DAIC state")
        state_mgr = DAICStateManager(project_root)

        # Get current state for session/correlation IDs
        current_unified = state_mgr.get_unified_state()

        # Build active_submodule_branches mapping based on task type
        active_submodule_branches = {}
        if submodule and branch_checkout:
            # Single submodule task: map submodule to its branch
            active_submodule_branches = {submodule: branch}
            debug_logger.debug(f"Built active_submodule_branches for single submodule: {active_submodule_branches}")
        elif services and branch_checkout:
            # Multi-service task: preserve existing mapping from state
            active_submodule_branches = current_unified.get('active_submodule_branches', {})
            debug_logger.debug(f"Preserved active_submodule_branches for multi-service task: {active_submodule_branches}")
        else:
            # Main repo task: no submodule branches
            debug_logger.debug("Main repo task: active_submodule_branches empty")

        state_mgr.set_task_state(
            task=task_name,
            branch=branch if branch_checkout else None,
            services=services,
            correlation_id=current_unified.get("correlation_id"),
            session_id=current_unified.get("session_id"),
            active_submodule_branches=active_submodule_branches
        )

        debug_logger.debug("DAIC state updated successfully")

        # 5. Display task summary
        console.print(f"\n[bold green]✓ Switched to task: {task_name}[/bold green]\n")

        console.print("[cyan]Task Details:[/cyan]")
        console.print(f"  • Task file: .brainworm/tasks/{task_name}/README.md")
        if branch_checkout:
            if submodule:
                console.print(f"  • Submodule: {submodule}")
                console.print(f"  • Branch: {branch} (in submodule)")
                # Show main repo stayed on its branch
                main_result = subprocess.run(
                    ['git', 'branch', '--show-current'],
                    cwd=project_root,
                    capture_output=True,
                    text=True,
                    timeout=5  # Quick operation, shorter timeout
                )
                main_branch = main_result.stdout.strip()
                if main_branch:
                    console.print(f"  • Main repo: {main_branch} (unchanged)")
            elif services:
                console.print(f"  • Services switched: {', '.join(services)}")
                console.print(f"  • Branch: {branch}")
            else:
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

        debug_logger.info(f"Task switch completed successfully: {task_name}")
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
