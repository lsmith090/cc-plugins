#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""
Git Utilities for Brainworm Hook System

Centralized git context and operations for consistent behavior across hooks.
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, Any


def get_basic_git_context(project_root: Path) -> Dict[str, Any]:
    """Get basic git context - no analysis, just raw data"""
    context = {}
    try:
        # Current branch
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            capture_output=True, text=True, timeout=3, cwd=project_root
        )
        if result.returncode == 0:
            context['branch'] = result.stdout.strip()
        
        # Current commit
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True, text=True, timeout=3, cwd=project_root
        )
        if result.returncode == 0:
            context['commit'] = result.stdout.strip()
        
        # Uncommitted file count
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True, text=True, timeout=3, cwd=project_root
        )
        if result.returncode == 0:
            context['uncommitted_files'] = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
    except Exception as e:
        # Git commands failed - continue with partial context
        print(f"Debug: Failed to get git context: {e}", file=sys.stderr)
    return context