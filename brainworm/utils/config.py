#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "toml>=0.10.0",
# ]
# ///

"""
Configuration Utilities for Brainworm Hook System

Centralized configuration loading with canonical defaults.
"""

import sys
import toml
from pathlib import Path
from typing import Dict, Any


def get_canonical_default_config() -> Dict[str, Any]:
    """Get the canonical default configuration structure
    
    This represents the complete, authoritative default configuration
    that gets written to .brainworm/config.toml during installation.
    """
    return {
        "daic": {
            "enabled": True,
            "default_mode": "discussion",
            "trigger_phrases": ["make it so", "run that", "go ahead", "ship it"],
            "blocked_tools": ["Edit", "Write", "MultiEdit", "NotebookEdit"],
            "branch_enforcement": {
                "enabled": True
            },
            "intelligence": {
                "codebase_learning": True,
                "pattern_recognition": True,
                "smart_recommendations": True
            },
            "read_only_bash_commands": {
                "basic": [
                    "ls", "ll", "pwd", "cd", "echo", "cat", "head", "tail", 
                    "less", "more", "grep", "rg", "find", "which", "whereis", 
                    "type", "file", "stat"
                ],
                "git": [
                    "git status", "git log", "git diff", "git show", "git branch", 
                    "git remote", "git fetch", "git describe", "git rev-parse", 
                    "git blame"
                ],
                "docker": [
                    "docker ps", "docker images", "docker logs"
                ],
                "package_managers": [
                    "npm list", "npm ls", "pip list", "pip show", "yarn list"
                ],
                "network": [
                    "curl", "wget", "ping"
                ],
                "text_processing": [
                    "jq", "awk", "sed -n"
                ]
            }
        },
        "analytics": {
            "memory_capture": True,
            "correlation_timeout_minutes": 60
        }
    }


def write_default_config(config_file: Path) -> None:
    """Write the canonical default configuration to file"""
    from .file_manager import AtomicFileWriter
    
    config_file.parent.mkdir(parents=True, exist_ok=True)
    default_config = get_canonical_default_config()
    
    # Use atomic writer for safer file operations
    with AtomicFileWriter(config_file) as f:
        toml.dump(default_config, f)


def load_config(project_root: Path, verbose: bool = False) -> Dict[str, Any]:
    """Load brainworm configuration with canonical defaults
    
    Args:
        project_root: Project root directory
        verbose: Enable verbose error reporting
        
    Returns:
        Complete configuration dictionary
    """
    config_file = project_root / ".brainworm" / "config.toml"
    default_config = get_canonical_default_config()
    
    # If config file doesn't exist, create it with defaults
    if not config_file.exists():
        if verbose:
            print(f"Creating default config at {config_file}")
        write_default_config(config_file)
        return default_config
    
    # Load existing config
    try:
        config = toml.load(config_file)
        
        # Merge defaults with loaded config (preserves user customizations)
        merged_config = {}
        for section_name, section_defaults in default_config.items():
            if section_name in config:
                if isinstance(section_defaults, dict):
                    # Deep merge for dict sections
                    merged_config[section_name] = {**section_defaults, **config[section_name]}
                else:
                    # Use loaded value for non-dict sections
                    merged_config[section_name] = config[section_name]
            else:
                # Use defaults for missing sections
                merged_config[section_name] = section_defaults
        
        return merged_config
        
    except Exception as e:
        if verbose:
            print(f"Warning: Could not load config from {config_file}: {e}")
            print("Using default configuration")
        return default_config


def load_config_with_args() -> Dict[str, Any]:
    """Load configuration with automatic --verbose flag detection"""
    from utils.project import find_project_root
    
    project_root = find_project_root()
    verbose = '--verbose' in sys.argv
    return load_config(project_root, verbose=verbose)


def update_config_value(project_root: Path, key: str, value: Any, create_if_missing: bool = True) -> bool:
    """Update a configuration value safely with atomic write.
    
    Args:
        project_root: Project root directory
        key: Configuration key (e.g., 'api_mode' or 'daic.enabled')
        value: New value to set
        create_if_missing: Whether to create config file if it doesn't exist
        
    Returns:
        bool: True if update succeeded
    """
    config_file = project_root / ".brainworm" / "config.toml"
    
    try:
        # Load or create config
        if config_file.exists():
            config = toml.load(config_file)
        elif create_if_missing:
            config = get_canonical_default_config()
        else:
            return False
        
        # Handle nested keys (e.g., 'daic.enabled')
        keys = key.split('.')
        current = config
        for key_part in keys[:-1]:
            if key_part not in current:
                current[key_part] = {}
            current = current[key_part]
        
        # Set the value
        current[keys[-1]] = value
        
        # Use atomic writer for safer file operations  
        from .file_manager import AtomicFileWriter
        with AtomicFileWriter(config_file, create_backup=True) as f:
            toml.dump(config, f)
        
        return True
        
    except Exception:
        return False


def toggle_config_value(project_root: Path, key: str) -> tuple[bool, bool, bool]:
    """Toggle a boolean configuration value.
    
    Args:
        project_root: Project root directory
        key: Configuration key to toggle
        
    Returns:
        tuple: (success, old_value, new_value)
    """
    config_file = project_root / ".brainworm" / "config.toml"
    
    try:
        # Load current config
        if config_file.exists():
            config = toml.load(config_file)
        else:
            config = get_canonical_default_config()
        
        # Get current value (handle nested keys)
        keys = key.split('.')
        current = config
        for key_part in keys[:-1]:
            if key_part not in current:
                current[key_part] = {}
            current = current[key_part]
        
        # Get current value (default to False for boolean toggles)
        old_value = current.get(keys[-1], False)
        new_value = not old_value
        
        # Update value
        success = update_config_value(project_root, key, new_value)
        return success, old_value, new_value
        
    except Exception:
        return False, False, False


def get_config_value(project_root: Path, key: str, default: Any = None) -> Any:
    """Get a configuration value with optional default.
    
    Args:
        project_root: Project root directory
        key: Configuration key (e.g., 'api_mode' or 'daic.enabled')
        default: Default value if key not found
        
    Returns:
        Configuration value or default
    """
    try:
        config = load_config(project_root)
        
        # Handle nested keys
        keys = key.split('.')
        current = config
        for key_part in keys:
            if isinstance(current, dict) and key_part in current:
                current = current[key_part]
            else:
                return default
        
        return current
        
    except Exception:
        return default