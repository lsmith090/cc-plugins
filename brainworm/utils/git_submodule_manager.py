#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["rich>=13.0.0"]
# ///

"""
Git Submodule Manager - Submodule-aware git operations for task/branch management

Provides clean abstractions for:
- Submodule detection and mapping
- Branch creation in specific submodules
- Working directory management for git operations
- Interactive submodule selection
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, List
from rich.console import Console
from rich.prompt import Prompt

# Import existing project utilities for submodule detection
try:
    from .project import get_project_context, find_project_root
except (ImportError, ValueError):
    # Fallback for direct execution or when used as standalone
    import sys
    import os
    current_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
    sys.path.insert(0, str(current_dir))
    from project import get_project_context, find_project_root


class SubmoduleManager:
    """
    Manages git operations within submodules for task/branch management.

    This class provides submodule-aware git operations that correctly handle
    working directory management when creating branches in submodules vs main repo.

    Key Insight: Each submodule is an independent git repository. Git operations
    performed in a submodule directory only affect that submodule's repository.
    The critical requirement is using the correct `cwd` parameter in subprocess calls.
    """

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize SubmoduleManager with submodule detection.

        Args:
            project_root: Path to project root. If None, uses find_project_root()
        """
        self.project_root = project_root or find_project_root()
        self.submodules = self._detect_submodules()
        self.console = Console()

    def _detect_submodules(self) -> Dict[str, Path]:
        """
        Detect all submodules and return {name: absolute_path} mapping.

        Leverages existing get_project_context() from project.py which already
        implements robust submodule detection via `git submodule status`.

        Returns:
            Dict mapping submodule names to their absolute paths
        """
        context = get_project_context(self.project_root)
        submodule_map = {}

        for name, info in context.get('submodules', {}).items():
            # Validate submodule name to prevent path traversal
            # Git submodule names should not contain ".." or start with "/"
            if ".." in name or name.startswith("/") or "\\" in name:
                self.console.print(
                    f"[yellow]Warning: Skipping potentially unsafe submodule name: {name}[/yellow]"
                )
                continue

            submodule_path = self.project_root / name

            # Verify resolved path is within project root (additional safety check)
            try:
                resolved = submodule_path.resolve()
                if not resolved.is_relative_to(self.project_root.resolve()):
                    self.console.print(
                        f"[yellow]Warning: Submodule path escapes project root: {name}[/yellow]"
                    )
                    continue
            except (ValueError, OSError):
                # Path resolution failed
                continue

            # Only include if directory actually exists
            if submodule_path.is_dir():
                submodule_map[name] = submodule_path

        return submodule_map

    def has_submodules(self) -> bool:
        """Check if project has any submodules."""
        return len(self.submodules) > 0

    def validate_submodule(self, submodule: str) -> bool:
        """
        Validate that a submodule exists.

        Args:
            submodule: Submodule name to validate

        Returns:
            bool: True if submodule exists
        """
        return submodule in self.submodules

    def get_submodule_path(self, submodule: str) -> Optional[Path]:
        """
        Get absolute path for a submodule.

        Args:
            submodule: Submodule name

        Returns:
            Path to submodule directory, or None if not found
        """
        return self.submodules.get(submodule)

    def create_branch(self, branch_name: str, submodule: Optional[str] = None) -> bool:
        """
        Create git branch in specified location.

        This is the core operation - creates a branch in either the main repo
        or a specific submodule by setting the correct working directory.

        Critical Implementation Detail:
        - Uses subprocess `cwd` parameter to control WHERE git operations happen
        - Submodule operations MUST run with cwd set to submodule directory
        - Main repo operations run with cwd set to project root

        Args:
            branch_name: Name of branch (e.g., "feature/login")
            submodule: Submodule path (e.g., "one-mit") or None for main repo

        Returns:
            bool: True if successful

        Raises:
            ValueError: If specified submodule doesn't exist or branch name is invalid
        """
        # Security: Validate branch name to prevent command injection
        try:
            from .security_validators import validate_branch_name
            branch_name = validate_branch_name(branch_name)
        except ImportError:
            # Fallback validation without security_validators
            if not branch_name or any(c in branch_name for c in [';', '&', '|', '$', '`', '(', ')', '\n', '\\']):
                raise ValueError(f"Invalid branch name: {branch_name}")

        # Determine working directory for git operation
        if submodule:
            if submodule not in self.submodules:
                available = ', '.join(self.submodules.keys()) if self.submodules else 'none'
                raise ValueError(
                    f"Submodule '{submodule}' not found. "
                    f"Available submodules: {available}"
                )
            cwd = self.submodules[submodule]
            location = f"submodule '{submodule}'"
        else:
            cwd = self.project_root
            location = "main repository"

        # Check if branch already exists
        # Security: branch_name is validated above, safe to use in subprocess
        check_result = subprocess.run(
            ['git', 'rev-parse', '--verify', branch_name],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5
        )

        if check_result.returncode == 0:
            self.console.print(
                f"[yellow]Branch '{branch_name}' already exists in {location}[/yellow]"
            )

            # Check if we're in an interactive environment
            is_interactive = sys.stdin.isatty()

            if is_interactive:
                # Ask if user wants to checkout existing branch
                if Prompt.ask(
                    f"Checkout existing branch?",
                    choices=["y", "n"],
                    default="y"
                ) == "y":
                    checkout_result = subprocess.run(
                        ['git', 'checkout', branch_name],
                        cwd=cwd,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    return checkout_result.returncode == 0
                return False
            else:
                # Non-interactive: automatically checkout existing branch
                self.console.print(f"[cyan]Non-interactive mode: checking out existing branch[/cyan]")
                checkout_result = subprocess.run(
                    ['git', 'checkout', branch_name],
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return checkout_result.returncode == 0

        # Ensure submodule is not in detached HEAD state
        if submodule:
            if not self._ensure_submodule_on_branch(cwd):
                self.console.print(
                    f"[red]Error: Submodule '{submodule}' is in detached HEAD state "
                    "and couldn't be checked out to a default branch[/red]"
                )
                return False

        # Create the branch
        result = subprocess.run(
            ['git', 'checkout', '-b', branch_name],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            self.console.print(f"[green]✓ Created branch '{branch_name}' in {location}[/green]")
            return True
        else:
            self.console.print(f"[red]✗ Failed to create branch: {result.stderr}[/red]")
            return False

    def _ensure_submodule_on_branch(self, submodule_path: Path) -> bool:
        """
        Ensure submodule is on a branch, not detached HEAD.

        Submodules frequently end up in "detached HEAD" state where they're not
        on any branch. This prevents branch creation. This method attempts to
        checkout a default branch if HEAD is detached.

        Args:
            submodule_path: Path to submodule directory

        Returns:
            bool: True if submodule is on a branch (or was successfully checked out to one)
        """
        # Check if HEAD is detached
        result = subprocess.run(
            ['git', 'symbolic-ref', '-q', 'HEAD'],
            cwd=submodule_path,
            capture_output=True,
            timeout=5
        )

        if result.returncode == 0:
            # Already on a branch
            return True

        # Detached HEAD - try to checkout a default branch
        self.console.print(
            f"[yellow]Submodule is in detached HEAD state, "
            "attempting to checkout default branch...[/yellow]"
        )

        for default_branch in ['main', 'master', 'develop']:
            result = subprocess.run(
                ['git', 'checkout', default_branch],
                cwd=submodule_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                self.console.print(f"[green]✓ Checked out '{default_branch}' branch[/green]")
                return True

        return False

    def create_branches_for_services(
        self,
        branch_name: str,
        services: List[str],
        create_main_branch: bool = False
    ) -> Dict[str, bool]:
        """
        Create branches in specified submodules, optionally in main repo.

        This is the key method for monorepo task management. It creates feature
        branches in multiple submodules simultaneously while optionally leaving
        the main repo on its current branch.

        Args:
            branch_name: Branch name to create (e.g., "feature/task-name")
            services: List of submodule names to create branches in
            create_main_branch: Whether to also create branch in main repo
                               (default False to preserve main repo's current branch)

        Returns:
            Dict mapping location names to success status
            Example: {"frontend": True, "backend": True}

        Example Usage:
            # Create branches in frontend and backend, leave main untouched
            results = manager.create_branches_for_services(
                "feature/add-auth",
                ["frontend", "backend"],
                create_main_branch=False
            )

            # Create branches in main + services
            results = manager.create_branches_for_services(
                "feature/update-all",
                ["frontend", "backend"],
                create_main_branch=True
            )
        """
        results = {}

        # Validate service names to prevent path traversal
        invalid_services = []
        for service in services:
            if service != "main" and (".." in service or service.startswith("/") or "\\" in service):
                invalid_services.append(service)
                results[service] = False

        if invalid_services:
            self.console.print(
                f"[red]Error: Invalid service names detected (path traversal attempt): {', '.join(invalid_services)}[/red]"
            )

        # Only create main repo branch if explicitly requested or "main" in services
        if create_main_branch or "main" in services:
            try:
                results['main'] = self.create_branch(branch_name, submodule=None)
            except Exception as e:
                self.console.print(f"[red]Error creating branch in main repo: {e}[/red]")
                results['main'] = False

        # Create in each submodule (skip "main" as it's handled above)
        for service in services:
            if service == "main":
                continue  # Already handled above

            if service not in self.submodules:
                self.console.print(
                    f"[yellow]Warning: Service '{service}' not found in submodules, skipping[/yellow]"
                )
                results[service] = False
                continue

            try:
                results[service] = self.create_branch(branch_name, submodule=service)
            except ValueError as e:
                self.console.print(f"[yellow]Warning: {e}[/yellow]")
                results[service] = False
            except Exception as e:
                self.console.print(f"[red]Error creating branch in {service}: {e}[/red]")
                results[service] = False

        return results

    def get_current_branch(self, submodule: Optional[str] = None) -> Optional[str]:
        """
        Get current branch in main repo or specified submodule.

        Args:
            submodule: Submodule name, or None for main repo

        Returns:
            Branch name, or None if in detached HEAD state or error
        """
        cwd = self.submodules.get(submodule) if submodule else self.project_root

        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5
        )

        return result.stdout.strip() if result.returncode == 0 else None

    def prompt_submodule_selection(self) -> Optional[str]:
        """
        Interactive prompt for submodule selection.

        Presents user with a menu of available submodules plus main repo option.
        Uses rich for colorful, clear UI.

        Returns:
            Selected submodule name, or None for main repo
        """
        if not self.submodules:
            return None

        self.console.print("\n[yellow]This project has submodules. Where should this task work?[/yellow]")

        options = ["main-repo"] + list(self.submodules.keys())
        for i, option in enumerate(options, 1):
            self.console.print(f"  {i}. {option}")

        choice = Prompt.ask(
            "Select location",
            choices=[str(i) for i in range(1, len(options) + 1)],
            default="1"
        )

        selected = options[int(choice) - 1]
        return None if selected == "main-repo" else selected

    def list_submodules(self) -> List[str]:
        """
        Get list of all submodule names.

        Returns:
            List of submodule names
        """
        return list(self.submodules.keys())


def main():
    """CLI interface for testing submodule operations."""
    import argparse

    parser = argparse.ArgumentParser(description="Git submodule management utilities")
    parser.add_argument('--list', action='store_true', help='List all submodules')
    parser.add_argument('--create-branch', help='Create branch in submodule')
    parser.add_argument('--submodule', help='Target submodule (or omit for main repo)')
    parser.add_argument('--current-branch', action='store_true', help='Show current branch')

    args = parser.parse_args()

    sm = SubmoduleManager()
    console = Console()

    if args.list:
        if sm.has_submodules():
            console.print("\n[cyan]Detected submodules:[/cyan]")
            for name, path in sm.submodules.items():
                console.print(f"  • {name} → {path}")
        else:
            console.print("[yellow]No submodules detected[/yellow]")

    elif args.create_branch:
        try:
            success = sm.create_branch(args.create_branch, args.submodule)
            if not success:
                sys.exit(1)
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)

    elif args.current_branch:
        branch = sm.get_current_branch(args.submodule)
        if branch:
            location = f"submodule '{args.submodule}'" if args.submodule else "main repo"
            console.print(f"[green]Current branch in {location}: {branch}[/green]")
        else:
            console.print("[yellow]Not on any branch (detached HEAD)[/yellow]")

    else:
        parser.print_help()


if __name__ == '__main__':
    import sys
    main()
