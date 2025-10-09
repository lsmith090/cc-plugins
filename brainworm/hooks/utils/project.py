#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""
Generic Project Detection Utilities
Handles project root detection and context for Claude Code hooks
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional


def find_project_root() -> Path:
    """
    Find the project root directory using multiple strategies.
    
    This function implements the battle-tested project detection logic
    extracted from existing hooks, with optimizations for performance.
    
    Returns:
        Path: The project root directory
        
    Raises:
        RuntimeError: If the project root cannot be found
    """
    # Strategy 1: Check for CLAUDE_PROJECT_DIR environment variable (most reliable)
    if env_root := os.environ.get('CLAUDE_PROJECT_DIR'):
        root_path = Path(env_root).resolve()
        if root_path.exists() and is_valid_project_root(root_path):
            return root_path
    
    # Strategy 2: Use git to find the root of the repository
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            check=True,
            timeout=5  # Add timeout for performance
        )
        git_root = Path(result.stdout.strip()).resolve()
        
        # Verify this is a valid project using basic validation
        if is_valid_project_root(git_root):
            return git_root
    
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        # Git not available or not in git repository
        pass
    
    # Strategy 3: Walk up from current directory looking for project markers
    current = Path.cwd()
    while current != current.parent:
        # Check if current directory is a valid project root
        if is_valid_project_root(current):
            return current
        current = current.parent
    
    # Strategy 4: Use current working directory as fallback if it has basic project markers
    if is_valid_project_root(Path.cwd()):
        return Path.cwd()
    
    # Strategy 5: Use parent directory if current doesn't qualify
    parent = Path.cwd().parent
    if parent.exists() and is_valid_project_root(parent):
        return parent
    
    raise RuntimeError(
        "Could not find project root. "
        "Ensure you're running from within a project directory with .git, .brainworm, .claude, or other markers."
    )


def is_valid_project_root(path: Path) -> bool:
    """
    Check if path is a valid project root using generic validation.
    
    Args:
        path: Path to check
        
    Returns:
        bool: True if path is a valid project root
    """
    if not (path.exists() and path.is_dir()):
        return False
    
    # Prioritize git root, but check if it's a submodule
    git_path = path / '.git'
    if git_path.exists():
        # If .git is a file (submodule), prefer the main repository root
        if git_path.is_file():
            try:
                git_content = git_path.read_text().strip()
                if git_content.startswith('gitdir:'):
                    # This is a submodule, look for main repo root with hooks
                    current = path.parent
                    while current != current.parent:
                        if (current / '.git').is_dir() and ((current / '.brainworm' / 'hooks').exists() or (current / '.claude' / 'hooks').exists()):
                            return False  # Let the main repo be found instead
                        current = current.parent
            except Exception:
                pass
        return True
    
    # For .brainworm directories, prefer ones with hooks installed (main project)
    if (path / '.brainworm').exists():
        brainworm_dir = path / '.brainworm'
        # Check if this .brainworm directory has hooks installed (indicates main project)
        if (brainworm_dir / 'hooks').exists():
            return True
        # If no hooks, only consider it valid if there's no git root above
        current = path.parent
        while current != current.parent:
            if (current / '.git').exists():
                return False  # Prefer git root over submodule .brainworm
            current = current.parent
    
    # Fallback: For .claude directories, prefer ones with hooks installed (main project)
    if (path / '.claude').exists():
        claude_dir = path / '.claude'
        # Check if this .claude directory has hooks installed (indicates main project)
        if (claude_dir / 'hooks').exists() and (claude_dir / 'settings.json').exists():
            return True
        # If no hooks, only consider it valid if there's no git root above
        current = path.parent
        while current != current.parent:
            if (current / '.git').exists():
                return False  # Prefer git root over submodule .claude
            current = current.parent
    
    # Common project markers
    return (
        (path / 'package.json').exists() or
        (path / 'pyproject.toml').exists() or
        (path / 'Cargo.toml').exists() or
        (path / 'composer.json').exists()
    )


def get_project_context(project_root: Path) -> Dict[str, Any]:
    """
    Get project context information for hooks.
    
    Args:
        project_root: Path to project root
        
    Returns:
        Dict containing project context information
    """
    context = {
        'project_root': str(project_root),
        'git_info': {},
        'submodules': {}
    }
    
    # Git information
    try:
        # Get current branch
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            capture_output=True, text=True, timeout=3, cwd=project_root
        )
        if result.returncode == 0:
            context['git_info']['branch'] = result.stdout.strip()
        
        # Get latest commit
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True, text=True, timeout=3, cwd=project_root
        )
        if result.returncode == 0:
            context['git_info']['commit'] = result.stdout.strip()
        
        # Check for submodules
        result = subprocess.run(
            ['git', 'submodule', 'status'],
            capture_output=True, text=True, timeout=5, cwd=project_root
        )
        if result.returncode == 0 and result.stdout.strip():
            submodules = {}
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        submodules[parts[1]] = {'commit': parts[0]}
            context['submodules'] = submodules
    
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    return context


def get_project_context_with_details(project_root: Path) -> Dict[str, Any]:
    """
    Get project context with development-specific information.
    
    Args:
        project_root: Path to project root
        
    Returns:
        Dict containing enhanced project context
    """
    context = get_project_context(project_root)
    
    # Detect project type
    project_type = 'unknown'
    if (project_root / 'package.json').exists():
        project_type = 'node'
    elif (project_root / 'pyproject.toml').exists() or (project_root / 'requirements.txt').exists():
        project_type = 'python'
    elif (project_root / 'Cargo.toml').exists():
        project_type = 'rust'
    elif (project_root / 'composer.json').exists():
        project_type = 'php'
    elif (project_root / '.brainworm').exists() or (project_root / '.claude').exists():
        project_type = 'claude_code'
    
    context['project_type'] = project_type
    
    # Check for common development files
    dev_files = []
    common_files = ['README.md', 'CLAUDE.md', '.gitignore', 'LICENSE', 'CHANGELOG.md']
    for file_name in common_files:
        if (project_root / file_name).exists():
            dev_files.append(file_name)
    
    context['dev_files'] = dev_files
    
    return context