#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
# ]
# ///

"""
Brainworm Plugin Project Installation Script

Installs brainworm into a project directory when invoked from the plugin.
Creates .brainworm directory structure, initializes database, and generates wrapper scripts.
"""

import os
import shutil
import stat
import subprocess
import argparse
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.prompt import Confirm
from rich.panel import Panel

console = Console()

# Database schema for hooks.db
HOOKS_DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS "hook_events" (
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
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    tool_name TEXT,
    file_path TEXT,
    change_summary TEXT,
    original_data_size INTEGER
);

CREATE INDEX IF NOT EXISTS idx_hook_events_created_at ON hook_events(created_at);
CREATE INDEX IF NOT EXISTS idx_hook_events_correlation ON hook_events(correlation_id);
CREATE INDEX IF NOT EXISTS idx_hook_events_tool_name ON hook_events(tool_name);
CREATE INDEX IF NOT EXISTS idx_hook_events_file_path ON hook_events(file_path);

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
);

CREATE INDEX IF NOT EXISTS idx_tool_outputs_hook_id ON tool_outputs(hook_event_id);
"""

def detect_project_root() -> Path:
    """
    Detect project root directory.

    Tries:
    1. CLAUDE_PROJECT_DIR environment variable
    2. Git root via git command
    3. Current working directory
    """
    # Try environment variable first
    if env_root := os.environ.get('CLAUDE_PROJECT_DIR'):
        root = Path(env_root).resolve()
        if root.exists() and root.is_dir():
            return root

    # Try git root
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )
        git_root = Path(result.stdout.strip()).resolve()
        if git_root.exists():
            return git_root
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Fallback to current directory
    return Path.cwd()

def get_plugin_root() -> Path:
    """
    Get the plugin root directory.
    Uses CLAUDE_PLUGIN_ROOT environment variable or falls back to __file__ location.
    """
    if plugin_root := os.environ.get('CLAUDE_PLUGIN_ROOT'):
        return Path(plugin_root).resolve()

    # Fallback: assume we're in brainworm-plugin/scripts/
    return Path(__file__).parent.parent.resolve()

def create_directory_structure(project_root: Path) -> bool:
    """Create .brainworm directory structure"""
    console.print("[dim]Creating .brainworm directory structure...[/dim]")

    directories = [
        ".brainworm",
        ".brainworm/state",
        ".brainworm/analytics",
        ".brainworm/logs",
        ".brainworm/timing",
        ".brainworm/memory",
        ".brainworm/templates",
        ".brainworm/protocols",
        ".brainworm/scripts",
    ]

    try:
        for dir_path in directories:
            (project_root / dir_path).mkdir(parents=True, exist_ok=True)

        console.print("[green]✅ Created directory structure[/green]")
        return True
    except Exception as e:
        console.print(f"[red]❌ Failed to create directories: {e}[/red]")
        return False

def initialize_database(project_root: Path) -> bool:
    """Initialize hooks.db with schema"""
    console.print("[dim]Initializing analytics database...[/dim]")

    db_path = project_root / ".brainworm" / "analytics" / "hooks.db"

    try:
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        conn.executescript(HOOKS_DB_SCHEMA)
        conn.commit()
        conn.close()

        console.print("[green]✅ Initialized database with schema[/green]")
        return True
    except Exception as e:
        console.print(f"[red]❌ Failed to initialize database: {e}[/red]")
        return False

def copy_templates(project_root: Path, plugin_root: Path) -> bool:
    """Copy configuration templates from plugin"""
    console.print("[dim]Copying configuration templates...[/dim]")

    templates_source = plugin_root / "templates"

    if not templates_source.exists():
        console.print(f"[yellow]⚠️  Templates directory not found at {templates_source}[/yellow]")
        return False

    try:
        # Copy config template
        config_template = templates_source / "config.toml.template"
        config_target = project_root / ".brainworm" / "config.toml"

        if config_template.exists() and not config_target.exists():
            shutil.copy2(config_template, config_target)
            console.print("[green]  ✓ Copied config.toml[/green]")

        # Copy user-config template
        user_config_template = templates_source / "user-config.json"
        user_config_target = project_root / ".brainworm" / "templates" / "user-config.json"

        if user_config_template.exists():
            shutil.copy2(user_config_template, user_config_target)
            console.print("[green]  ✓ Copied user-config.json[/green]")

        # Copy task template
        task_template = templates_source / "TEMPLATE.md"
        task_target = project_root / ".brainworm" / "templates" / "TEMPLATE.md"

        if task_template.exists():
            shutil.copy2(task_template, task_target)
            console.print("[green]  ✓ Copied TEMPLATE.md[/green]")

        # Copy protocols
        protocols_source = templates_source / "protocols"
        protocols_target = project_root / ".brainworm" / "protocols"

        if protocols_source.exists():
            for protocol_file in protocols_source.glob("*.md"):
                shutil.copy2(protocol_file, protocols_target / protocol_file.name)
            console.print(f"[green]  ✓ Copied {len(list(protocols_source.glob('*.md')))} protocol files[/green]")

        # Copy CLAUDE.sessions.md to project root
        claude_sessions = templates_source / "CLAUDE.sessions.md"
        if claude_sessions.exists():
            shutil.copy2(claude_sessions, project_root / "CLAUDE.sessions.md")
            console.print("[green]  ✓ Copied CLAUDE.sessions.md to project root[/green]")

        console.print("[green]✅ Templates copied successfully[/green]")
        return True

    except Exception as e:
        console.print(f"[red]❌ Failed to copy templates: {e}[/red]")
        return False

def copy_utility_scripts(project_root: Path, plugin_root: Path) -> bool:
    """Copy utility scripts and utils module needed by commands"""
    console.print("[dim]Copying utility scripts...[/dim]")

    scripts_source = plugin_root / "hooks"
    scripts_target = project_root / ".brainworm" / "scripts"

    required_scripts = [
        "update_task_state.py",
        "update_session_correlation.py",
        "update_daic_mode.py",
        "create_task.py"
    ]

    try:
        # Copy scripts
        copied_count = 0
        for script_name in required_scripts:
            source_file = scripts_source / script_name
            if source_file.exists():
                shutil.copy2(source_file, scripts_target / script_name)
                copied_count += 1

        # Copy statusline-script.py from plugin scripts
        statusline_source = plugin_root / "scripts" / "statusline-script.py"
        if statusline_source.exists():
            shutil.copy2(statusline_source, scripts_target / "statusline-script.py")
            console.print(f"[green]  ✓ Copied statusline-script.py[/green]")
            copied_count += 1

        # Copy utils directory for script imports
        utils_source = scripts_source / "utils"
        utils_target = scripts_target / "utils"

        if utils_source.exists():
            if utils_target.exists():
                shutil.rmtree(utils_target)
            shutil.copytree(utils_source, utils_target)
            console.print(f"[green]  ✓ Copied utils module[/green]")

        console.print(f"[green]✅ Copied {copied_count} utility scripts[/green]")
        return True

    except Exception as e:
        console.print(f"[red]❌ Failed to copy utility scripts: {e}[/red]")
        return False

def create_wrapper_scripts(project_root: Path, plugin_root: Path) -> bool:
    """Generate ./daic and ./tasks wrapper scripts"""
    console.print("[dim]Generating wrapper scripts...[/dim]")

    try:
        # Create ./daic wrapper
        daic_wrapper = project_root / "daic"
        daic_content = f"""#!/usr/bin/env bash
# Generated by brainworm plugin v1.0.0
# Plugin root: {plugin_root}

PLUGIN_ROOT="{plugin_root}"

if [ -z "$PLUGIN_ROOT" ] || [ ! -d "$PLUGIN_ROOT" ]; then
    echo "Error: brainworm plugin not found at $PLUGIN_ROOT"
    echo "Plugin may have been moved or uninstalled"
    echo "Run /install-brainworm to regenerate wrapper"
    exit 1
fi

exec uv run "${{PLUGIN_ROOT}}/hooks/daic_command.py" "$@"
"""

        with open(daic_wrapper, 'w') as f:
            f.write(daic_content)
        daic_wrapper.chmod(daic_wrapper.stat().st_mode | stat.S_IEXEC)
        console.print("[green]  ✓ Created ./daic wrapper[/green]")

        # Create ./tasks wrapper
        tasks_wrapper = project_root / "tasks"
        tasks_content = f"""#!/usr/bin/env bash
# Generated by brainworm plugin v1.0.0
# Plugin root: {plugin_root}

PLUGIN_ROOT="{plugin_root}"

if [ -z "$PLUGIN_ROOT" ] || [ ! -d "$PLUGIN_ROOT" ]; then
    echo "Error: brainworm plugin not found at $PLUGIN_ROOT"
    echo "Plugin may have been moved or uninstalled"
    echo "Run /install-brainworm to regenerate wrapper"
    exit 1
fi

exec uv run "${{PLUGIN_ROOT}}/hooks/tasks_command.py" "$@"
"""

        with open(tasks_wrapper, 'w') as f:
            f.write(tasks_content)
        tasks_wrapper.chmod(tasks_wrapper.stat().st_mode | stat.S_IEXEC)
        console.print("[green]  ✓ Created ./tasks wrapper[/green]")

        console.print("[green]✅ Wrapper scripts created[/green]")
        return True

    except Exception as e:
        console.print(f"[red]❌ Failed to create wrapper scripts: {e}[/red]")
        return False

def update_gitignore(project_root: Path) -> bool:
    """Add brainworm patterns to .gitignore"""
    console.print("[dim]Updating .gitignore...[/dim]")

    gitignore_path = project_root / ".gitignore"
    required_patterns = [".brainworm/", "daic", "tasks"]

    try:
        # Read existing or create new
        if gitignore_path.exists():
            content = gitignore_path.read_text()
            lines = content.splitlines()
        else:
            lines = []

        # Check what's missing
        existing_patterns = set(line.strip() for line in lines)
        missing_patterns = [p for p in required_patterns if p not in existing_patterns]

        if missing_patterns:
            # Add brainworm section
            if lines and lines[-1].strip():
                lines.append("")
            lines.append("#brainworm")
            for pattern in missing_patterns:
                lines.append(pattern)

            # Write back
            new_content = "\n".join(lines) + "\n"
            gitignore_path.write_text(new_content)

            console.print(f"[green]✅ Added {len(missing_patterns)} patterns to .gitignore[/green]")
        else:
            console.print("[blue]ℹ️  .gitignore already configured[/blue]")

        return True

    except Exception as e:
        console.print(f"[yellow]⚠️  Could not update .gitignore: {e}[/yellow]")
        return False

def initialize_state_files(project_root: Path) -> bool:
    """Initialize essential state files"""
    console.print("[dim]Initializing state files...[/dim]")

    try:
        # Create unified_session_state.json
        state_file = project_root / ".brainworm" / "state" / "unified_session_state.json"
        if not state_file.exists():
            import json
            initial_state = {
                "daic_mode": "discussion",
                "daic_timestamp": None,
                "current_task": None,
                "current_branch": None,
                "session_id": None,
                "correlation_id": None
            }
            with open(state_file, 'w') as f:
                json.dump(initial_state, f, indent=2)
            console.print("[green]  ✓ Created unified_session_state.json[/green]")

        console.print("[green]✅ State files initialized[/green]")
        return True

    except Exception as e:
        console.print(f"[yellow]⚠️  Could not initialize state files: {e}[/yellow]")
        return False

def show_completion_message(project_root: Path):
    """Show installation completion message"""
    message = f"""[bold green]✅ Brainworm Successfully Installed![/bold green]

[bold]Project:[/bold] {project_root.name}
[bold]Location:[/bold] {project_root}

[bold]📁 Created:[/bold]
  • .brainworm/ directory structure
  • analytics/hooks.db database
  • Configuration files
  • ./daic and ./tasks wrapper scripts

[bold]🔧 Next Steps:[/bold]
  1. Restart your Claude Code session
  2. Run [cyan]./daic status[/cyan] to check system
  3. Use trigger phrases like [cyan]'make it so'[/cyan] to enable tools
  4. Check your statusline for DAIC mode

[bold]📚 Documentation:[/bold]
  • DAIC workflow: Run [cyan]./daic --help[/cyan]
  • Task management: Run [cyan]./tasks --help[/cyan]
  • Protocols: See .brainworm/protocols/

[dim]Hooks will activate automatically on next Claude Code session.[/dim]
"""

    console.print(Panel.fit(message, border_style="green", title="🧠 Installation Complete"))

def main():
    """Main installation function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Install brainworm in the current project")
    parser.add_argument('-y', '--yes', action='store_true', help='Skip confirmation prompts')
    args = parser.parse_args()

    console.print(Panel.fit(
        "[bold]🧠 Brainworm Project Installation[/bold]\n\n"
        "This will set up brainworm in your current project.",
        border_style="blue",
        title="Brainworm Plugin Installer"
    ))

    # Detect project root
    project_root = detect_project_root()
    console.print(f"\n📍 Detected project: [cyan]{project_root}[/cyan]")

    # Get plugin root
    plugin_root = get_plugin_root()
    console.print(f"🔌 Plugin location: [dim]{plugin_root}[/dim]\n")

    # Check if already installed
    brainworm_dir = project_root / ".brainworm"
    if brainworm_dir.exists():
        console.print("[yellow]⚠️  .brainworm directory already exists[/yellow]")
        if not args.yes and not Confirm.ask("Proceed with installation (will update existing)?"):
            console.print("Installation cancelled")
            return 1

    # Confirm installation
    if not args.yes and not Confirm.ask(f"\nInstall brainworm to {project_root.name}?", default=True):
        console.print("Installation cancelled")
        return 1

    console.print("\n[bold blue]🚀 Starting installation...[/bold blue]\n")

    # Run installation steps
    steps = [
        ("Creating directory structure", lambda: create_directory_structure(project_root)),
        ("Initializing database", lambda: initialize_database(project_root)),
        ("Copying templates", lambda: copy_templates(project_root, plugin_root)),
        ("Copying utility scripts", lambda: copy_utility_scripts(project_root, plugin_root)),
        ("Creating wrapper scripts", lambda: create_wrapper_scripts(project_root, plugin_root)),
        ("Updating .gitignore", lambda: update_gitignore(project_root)),
        ("Initializing state files", lambda: initialize_state_files(project_root)),
    ]

    failed = False
    for step_name, step_func in steps:
        if not step_func():
            failed = True
            break

    if failed:
        console.print("\n[red]❌ Installation failed[/red]")
        return 1

    # Show completion message
    console.print()
    show_completion_message(project_root)

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
