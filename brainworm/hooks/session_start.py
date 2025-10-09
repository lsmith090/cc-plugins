#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
# ]
# ///

"""
Session Start Hook - Framework Implementation

Initializes user config and cleans up session flags.
"""

from utils.hook_framework import HookFramework
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

def initialize_user_config(project_root: Path) -> None:
    """Initialize user config if it doesn't exist"""
    try:
        # Determine brainworm directory (.brainworm preferred, .claude fallback)
        brainworm_dir = project_root / ".brainworm"
        if not brainworm_dir.exists():
            brainworm_dir = project_root / ".claude"
        
        user_config_path = brainworm_dir / "user-config.json"
        template_path = brainworm_dir / "templates" / "user-config.json"
        
        # If user config doesn't exist but template does, create from template
        if not user_config_path.exists() and template_path.exists():
            import shutil
            
            # Copy template
            shutil.copy2(template_path, user_config_path)
            
            # Try to populate with git identity
            try:
                with open(user_config_path, 'r') as f:
                    config = json.load(f)
                
                # Get git identity if available
                name_result = subprocess.run(
                    ['git', 'config', 'user.name'],
                    capture_output=True, text=True, timeout=3, cwd=project_root
                )
                email_result = subprocess.run(
                    ['git', 'config', 'user.email'],
                    capture_output=True, text=True, timeout=3, cwd=project_root
                )
                
                if name_result.returncode == 0 and email_result.returncode == 0:
                    config['developer']['name'] = name_result.stdout.strip()
                    config['developer']['email'] = email_result.stdout.strip()
                    config['developer']['git_identity_source'] = 'auto'
                    config['created'] = datetime.now(timezone.utc).isoformat()
                    config['updated'] = datetime.now(timezone.utc).isoformat()
                    
                    with open(user_config_path, 'w') as f:
                        json.dump(config, f, indent=2)
                        
            except Exception:
                pass  # Continue with default template if git identity fails
                
    except Exception:
        pass  # Don't fail session start due to user config initialization issues

def cleanup_session_flags(project_root: Path) -> None:
    """Clean up flags from previous sessions based on cc-sessions logic"""
    try:
        state_dir = project_root / ".brainworm" / "state"
        
        # Clear context warning flags for new session
        warning_75_flag = state_dir / "context-warning-75.flag"
        warning_90_flag = state_dir / "context-warning-90.flag"
        
        if warning_75_flag.exists():
            warning_75_flag.unlink()
        if warning_90_flag.exists():
            warning_90_flag.unlink()
            
        # Also clean up any stale subagent context flag
        subagent_flag = state_dir / "in_subagent_context.flag"
        if subagent_flag.exists():
            subagent_flag.unlink()
    except Exception:
        pass  # Don't fail session start due to flag cleanup issues

def session_start_logic(framework, typed_input):
    """Custom logic for session start with user config and flag cleanup."""
    initialize_user_config(framework.project_root)
    cleanup_session_flags(framework.project_root)

    # Create session snapshot
    try:
        snapshot_script = framework.project_root / ".brainworm" / "scripts" / "snapshot_session.py"
        if snapshot_script.exists():
            subprocess.run([
                str(snapshot_script),
                "--action", "start",
                "--session-id", typed_input.session_id,
                "--quiet"
            ], timeout=10, check=False)
    except Exception:
        pass  # Don't fail session start if snapshot fails

def session_start_success_message(framework):
    """Custom success message for session start hook."""
    # Access typed input from framework if available, fallback to raw data
    if hasattr(framework, 'typed_input') and framework.typed_input:
        session_id = framework.typed_input.session_id
    else:
        session_id = framework.raw_input_data.get('session_id', 'unknown')
    session_short = session_id[:8] if len(session_id) >= 8 else session_id
    print(f"✅ Session started: {session_short}", file=sys.stderr)

if __name__ == "__main__":
    HookFramework("session_start").with_custom_logic(session_start_logic).with_success_handler(session_start_success_message).execute()