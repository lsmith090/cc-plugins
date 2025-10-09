#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "toml>=0.10.0",
# ]
# ///
"""API mode control script for brainworm."""
import sys
import toml
from pathlib import Path
from utils.project import find_project_root


def toggle_api_mode() -> None:
    project_root = find_project_root()
    config_file = project_root / ".brainworm" / "config.toml"
    
    if not config_file.exists():
        print(f"Error: {config_file} not found", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Load existing config
        with open(config_file, 'r') as f:
            config = toml.load(f)
        
        # Get current API mode setting (default False)
        current_api_mode = config.get("api_mode", False)
        new_api_mode = not current_api_mode
        
        # Update config
        config["api_mode"] = new_api_mode
        
        # Write back to file
        with open(config_file, 'w') as f:
            toml.dump(config, f)
        
        print(f"API mode toggled: {current_api_mode} → {new_api_mode}")
        
    except Exception as e:
        print(f"Error: Failed to update config: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    toggle_api_mode()