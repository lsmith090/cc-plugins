#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
# ]
# ///

"""
Session Start Hook - Framework Implementation

Initializes user config, cleans up session flags, and auto-sets up .brainworm/ structure.
"""

# Add plugin root to sys.path before any utils imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.hook_framework import HookFramework
import json
import subprocess
import shutil
import sqlite3
import os
from datetime import datetime, timezone
from rich.console import Console

console = Console(stderr=True)

def auto_setup_minimal_brainworm(project_root: Path) -> None:
    """
    Auto-create minimal .brainworm/ structure if needed.
    This runs on every session start to ensure structure exists and plugin_root is current.
    """
    try:
        # Try to get plugin root from environment first
        plugin_root_str = os.environ.get('CLAUDE_PLUGIN_ROOT', '')

        # If not set, derive from script location (hook is in plugin/hooks/)
        if not plugin_root_str:
            script_path = Path(__file__).resolve()
            # Check if we're running from a plugin directory
            if '.claude/plugins/marketplaces' in str(script_path):
                # script_path is like: ~/.claude/plugins/marketplaces/xxx/brainworm/hooks/session_start.py
                plugin_root_str = str(script_path.parent.parent)  # Go up to brainworm/
            else:
                # Not running from plugin, skip auto-setup
                return

        plugin_root = Path(plugin_root_str)
        if not plugin_root.exists():
            return  # Can't auto-setup without valid plugin

        brainworm_dir = project_root / '.brainworm'
        state_file = brainworm_dir / 'state' / 'unified_session_state.json'

        # Quick check - if state exists with valid plugin_root, just update if needed
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                current_plugin = state.get('plugin_root')

                # Update plugin_root if changed (plugin moved/updated)
                if current_plugin != str(plugin_root):
                    state['plugin_root'] = str(plugin_root)
                    from utils.file_manager import AtomicFileWriter
                    with AtomicFileWriter(state_file) as f:
                        json.dump(state, f, indent=2)

                # Always regenerate wrappers to ensure new wrappers are created
                generate_wrappers(project_root, plugin_root)

                # Always configure statusline to ensure it's up to date
                configure_statusline(project_root, plugin_root)

                # Always ensure CLAUDE.sessions.md exists and is referenced
                setup_claude_sessions_docs(project_root, plugin_root)
                return
            except Exception:
                pass  # If state file is corrupt, recreate it below

        # First-time setup
        console.print("[dim]⚙️  Initializing brainworm...[/dim]")

        # 1. Create minimal directory structure
        (brainworm_dir / 'state').mkdir(parents=True, exist_ok=True)
        (brainworm_dir / 'analytics').mkdir(parents=True, exist_ok=True)
        (brainworm_dir / 'tasks').mkdir(parents=True, exist_ok=True)
        (brainworm_dir / 'timing').mkdir(parents=True, exist_ok=True)

        # 2. Copy config.toml from plugin template (if not exists)
        config_file = brainworm_dir / 'config.toml'
        if not config_file.exists():
            template = plugin_root / 'templates' / 'config.toml.template'
            if template.exists():
                shutil.copy(template, config_file)

        # 3. Initialize unified session state with plugin_root
        initial_state = {
            "daic_mode": "discussion",
            "task": None,
            "branch": None,
            "services": [],
            "correlation_id": None,
            "session_id": None,
            "plugin_root": str(plugin_root),
            "developer": {
                "name": "",
                "email": ""
            }
        }

        # Try to get git identity
        try:
            name_result = subprocess.run(
                ['git', 'config', 'user.name'],
                capture_output=True, text=True, timeout=3, cwd=project_root
            )
            email_result = subprocess.run(
                ['git', 'config', 'user.email'],
                capture_output=True, text=True, timeout=3, cwd=project_root
            )
            if name_result.returncode == 0:
                initial_state['developer']['name'] = name_result.stdout.strip()
            if email_result.returncode == 0:
                initial_state['developer']['email'] = email_result.stdout.strip()
        except Exception:
            pass

        # Write initial state
        from utils.file_manager import AtomicFileWriter
        with AtomicFileWriter(state_file) as f:
            json.dump(initial_state, f, indent=2)

        # 4. Initialize analytics database with schema
        init_analytics_database(brainworm_dir / 'analytics' / 'hooks.db')

        # 5. Generate wrapper scripts
        generate_wrappers(project_root, plugin_root)

        # 6. Update .gitignore
        update_gitignore(project_root)

        # 7. Configure statusline
        configure_statusline(project_root, plugin_root)

        # 8. Setup CLAUDE.sessions.md
        setup_claude_sessions_docs(project_root, plugin_root)

        console.print("[dim green]✓ Brainworm initialized[/dim green]")

    except Exception as e:
        # Don't fail session start if auto-setup fails
        console.print(f"[dim yellow]⚠️  Auto-setup warning: {e}[/dim yellow]")

def init_analytics_database(db_path: Path) -> None:
    """Initialize analytics database with schema"""
    if db_path.exists():
        return  # Don't overwrite existing database

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create hook_events table with enhanced schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hook_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hook_name TEXT NOT NULL,
                event_type TEXT NOT NULL,
                correlation_id TEXT,
                session_id TEXT,
                success BOOLEAN,
                duration_ms REAL,
                data TEXT,
                developer_name TEXT,
                developer_email TEXT,
                tool_name TEXT,
                file_path TEXT,
                change_summary TEXT,
                original_data_size INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hook_events_created_at ON hook_events(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hook_events_correlation ON hook_events(correlation_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hook_events_tool_name ON hook_events(tool_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hook_events_file_path ON hook_events(file_path)')

        # Create tool_outputs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tool_outputs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hook_event_id INTEGER NOT NULL,
                tool_name TEXT,
                input_data TEXT,
                output_data TEXT,
                full_content TEXT,
                is_compressed BOOLEAN DEFAULT 0,
                content_size INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hook_event_id) REFERENCES hook_events(id)
            )
        ''')

        conn.commit()
        conn.close()
    except Exception:
        pass  # Don't fail if database init fails

def generate_wrappers(project_root: Path, plugin_root: Path) -> None:
    """Generate ./daic and ./tasks wrapper scripts"""
    try:
        # DAIC wrapper
        daic_wrapper = f'''#!/usr/bin/env bash
# Generated by brainworm session_start hook
# Uses plugin-launcher to execute daic_command.py

exec .brainworm/plugin-launcher daic_command.py "$@"
'''

        daic_path = project_root / 'daic'
        daic_path.write_text(daic_wrapper)
        daic_path.chmod(0o755)

        # Tasks wrapper
        tasks_wrapper = f'''#!/usr/bin/env bash
# Generated by brainworm session_start hook
# Uses plugin-launcher to execute tasks_command.py

exec .brainworm/plugin-launcher tasks_command.py "$@"
'''

        tasks_path = project_root / 'tasks'
        tasks_path.write_text(tasks_wrapper)
        tasks_path.chmod(0o755)

        # Plugin launcher wrapper (for slash commands and statusline)
        plugin_launcher_wrapper = f'''#!/usr/bin/env bash
# Generated by brainworm session_start hook
# Generic plugin script launcher for slash commands and statusline

STATE_FILE=".brainworm/state/unified_session_state.json"

if [ ! -f "$STATE_FILE" ]; then
    echo "Error: Brainworm not initialized" >&2
    exit 1
fi

# Extract plugin_root using jq (fallback to python if jq not available)
if command -v jq &> /dev/null; then
    PLUGIN_ROOT=$(jq -r '.plugin_root // empty' "$STATE_FILE" 2>/dev/null)
else
    PLUGIN_ROOT=$(python3 -c "import json; print(json.load(open('$STATE_FILE')).get('plugin_root', ''))" 2>/dev/null)
fi

if [ -z "$PLUGIN_ROOT" ]; then
    echo "Error: Plugin path not found in state" >&2
    exit 1
fi

if [ ! -d "$PLUGIN_ROOT" ]; then
    echo "Error: Plugin not found at $PLUGIN_ROOT" >&2
    exit 1
fi

# First arg is script name, rest are arguments to pass through
SCRIPT_NAME="$1"
shift

# Check scripts/ directory first, then fall back to hooks/
if [ -f "${{PLUGIN_ROOT}}/scripts/${{SCRIPT_NAME}}" ]; then
    exec uv run "${{PLUGIN_ROOT}}/scripts/${{SCRIPT_NAME}}" "$@"
elif [ -f "${{PLUGIN_ROOT}}/hooks/${{SCRIPT_NAME}}" ]; then
    exec uv run "${{PLUGIN_ROOT}}/hooks/${{SCRIPT_NAME}}" "$@"
else
    echo "Error: Script ${{SCRIPT_NAME}} not found in plugin" >&2
    exit 1
fi
'''

        plugin_launcher_path = project_root / '.brainworm' / 'plugin-launcher'
        plugin_launcher_path.write_text(plugin_launcher_wrapper)
        plugin_launcher_path.chmod(0o755)

    except Exception:
        pass  # Don't fail if wrapper generation fails

def update_gitignore(project_root: Path) -> None:
    """Update .gitignore with brainworm patterns"""
    try:
        gitignore_path = project_root / '.gitignore'

        patterns = [
            '# Brainworm',
            '.brainworm/',
            'CLAUDE.sessions.md',
            'daic',
            'tasks',
            ''
        ]

        # Read existing gitignore
        existing = gitignore_path.read_text() if gitignore_path.exists() else ''

        # Check if patterns already exist
        if '.brainworm/' in existing or 'Brainworm' in existing:
            return  # Already configured

        # Append patterns
        with open(gitignore_path, 'a') as f:
            f.write('\n' + '\n'.join(patterns))
    except Exception:
        pass  # Don't fail if gitignore update fails

def configure_statusline(project_root: Path, plugin_root: Path) -> None:
    """Configure statusLine in .claude/settings.json"""
    try:
        claude_dir = project_root / '.claude'
        claude_dir.mkdir(exist_ok=True)

        settings_file = claude_dir / 'settings.json'

        # Read existing settings or create new
        if settings_file.exists():
            with open(settings_file, 'r') as f:
                settings = json.load(f)
        else:
            settings = {}

        # Add statusLine configuration
        settings['statusLine'] = {
            'type': 'command',
            'command': '.brainworm/plugin-launcher statusline-script.py',
            'padding': 0
        }

        # Ensure env section exists with CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR
        if 'env' not in settings:
            settings['env'] = {}
        if 'CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR' not in settings['env']:
            settings['env']['CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR'] = 'true'

        # Write back
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)

    except Exception:
        pass  # Don't fail session start

def setup_claude_sessions_docs(project_root: Path, plugin_root: Path) -> None:
    """Setup CLAUDE.sessions.md and ensure it's referenced in CLAUDE.md"""
    try:
        # 1. Copy CLAUDE.sessions.md from plugin templates if needed
        sessions_file = project_root / 'CLAUDE.sessions.md'
        template_file = plugin_root / 'templates' / 'CLAUDE.sessions.md'

        if template_file.exists():
            # Always copy to ensure latest version (it's documentation, not state)
            shutil.copy(template_file, sessions_file)

        # 2. Ensure CLAUDE.md exists and has the @CLAUDE.sessions.md reference
        claude_md = project_root / 'CLAUDE.md'

        if claude_md.exists():
            content = claude_md.read_text()

            # Check if reference already exists
            if '@CLAUDE.sessions.md' not in content:
                # Add reference at the end
                if not content.endswith('\n'):
                    content += '\n'
                content += '\n## Brainworm System Behaviors\n\n@CLAUDE.sessions.md\n'
                claude_md.write_text(content)
        else:
            # Create minimal CLAUDE.md with reference
            claude_md.write_text('''# CLAUDE.md

Guidance for Claude Code when working with this project.

## Brainworm System Behaviors

@CLAUDE.sessions.md
''')

    except Exception:
        pass  # Don't fail session start if docs setup fails

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
    """Custom logic for session start with auto-setup, user config, and flag cleanup."""
    # Auto-setup minimal .brainworm/ structure if needed
    auto_setup_minimal_brainworm(framework.project_root)

    # Initialize user config and cleanup flags
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