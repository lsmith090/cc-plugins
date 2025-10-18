#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "tomli-w>=1.0.0",
#     "filelock>=3.13.0",
# ]
# ///
# Add plugin root to sys.path before any utils imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import tomllib  # Python 3.12+ built-in (read-only)
import tomli_w  # For writing TOML files
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
        # Use file locking to prevent race conditions in read-modify-write
        try:
            from filelock import FileLock
            lock_file = config_file.parent / '.config.lock'
            lock = FileLock(str(lock_file), timeout=10)

            with lock:
                # Load existing config while holding lock
                with open(config_file, 'rb') as f:
                    config = tomllib.load(f)

                # Ensure daic section exists
                if "daic" not in config:
                    config["daic"] = {}

                # Ensure trigger_phrases exists
                if "trigger_phrases" not in config["daic"]:
                    config["daic"]["trigger_phrases"] = []

                # Add new phrase if not already present
                if phrase not in config["daic"]["trigger_phrases"]:
                    config["daic"]["trigger_phrases"].append(phrase)

                    # Write back to file while still holding lock
                    with open(config_file, 'wb') as f:
                        tomli_w.dump(config, f)

                    print(f"✅ Added trigger phrase: '{phrase}'")
                else:
                    print(f"⚠️  Trigger phrase '{phrase}' already exists")
        except ImportError:
            # Fallback without locking (race condition possible but rare)
            with open(config_file, 'rb') as f:
                config = tomllib.load(f)

            if "daic" not in config:
                config["daic"] = {}

            if "trigger_phrases" not in config["daic"]:
                config["daic"]["trigger_phrases"] = []

            if phrase not in config["daic"]["trigger_phrases"]:
                config["daic"]["trigger_phrases"].append(phrase)

                with open(config_file, 'wb') as f:
                    tomli_w.dump(config, f)

                print(f"✅ Added trigger phrase: '{phrase}'")
            else:
                print(f"⚠️  Trigger phrase '{phrase}' already exists")

    except Exception as e:
        print(f"Error: Failed to update config: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    add_trigger_phrase()