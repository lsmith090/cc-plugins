#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "toml>=0.10.0",
# ]
# ///
# Add plugin root to sys.path before any utils imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import toml
from utils.project import find_project_root

def add_trigger_phrase() -> None:
    if len(sys.argv) < 2:
        print("Error: No trigger phrase provided", file=sys.stderr)
        print("Usage: add_trigger.py 'phrase'", file=sys.stderr)
        sys.exit(1)
    
    phrase = " ".join(sys.argv[1:]).strip()
    if not phrase:
        print("Error: No trigger phrase provided", file=sys.stderr)
        sys.exit(1)
    
    project_root = find_project_root()
    config_file = project_root / ".brainworm" / "config.toml"
    
    if not config_file.exists():
        print(f"Error: {config_file} not found", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Load existing config
        with open(config_file, 'r') as f:
            config = toml.load(f)
        
        # Ensure daic section exists
        if "daic" not in config:
            config["daic"] = {}
        
        # Ensure trigger_phrases exists
        if "trigger_phrases" not in config["daic"]:
            config["daic"]["trigger_phrases"] = []
        
        # Add new phrase if not already present
        if phrase not in config["daic"]["trigger_phrases"]:
            config["daic"]["trigger_phrases"].append(phrase)
            
            # Write back to file
            with open(config_file, 'w') as f:
                toml.dump(config, f)
            
            print(f"✅ Added trigger phrase: '{phrase}'")
        else:
            print(f"⚠️  Trigger phrase '{phrase}' already exists")
            
    except Exception as e:
        print(f"Error: Failed to update config: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    add_trigger_phrase()