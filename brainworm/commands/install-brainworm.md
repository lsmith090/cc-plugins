---
description: Set up brainworm in the current project
---

Install brainworm in the current project:

1. Find the brainworm plugin directory in `~/.claude/plugins/marketplaces/brainworm-marketplace/brainworm/`
2. Execute the installation script at `scripts/install_project.py` using `uv run`
3. The script will prompt for confirmation before creating the `.brainworm` structure

This will:
- Create `.brainworm` directory with state, analytics, and configuration
- Initialize analytics database with proper schema
- Generate `./daic` and `./tasks` wrapper scripts
- Copy protocol templates for task management
- Set up project-specific configuration
- Update `.gitignore` with brainworm patterns

## What Gets Installed

**Directory Structure:**
- `.brainworm/state/` - Session and workflow state
- `.brainworm/analytics/` - Local analytics database
- `.brainworm/logs/` - Hook execution logs
- `.brainworm/templates/` - Task and config templates
- `.brainworm/protocols/` - Workflow protocols

**Wrapper Scripts:**
- `./daic` - DAIC mode control (`./daic status`, `./daic toggle`)
- `./tasks` - Task management (`./tasks status`, `./tasks create`)

**Configuration:**
- `config.toml` - DAIC and analytics settings
- `user-config.json` - User preferences template
- `unified_session_state.json` - Initial state

## After Installation

1. Restart your Claude Code session
2. Hooks will activate automatically
3. Run `./daic status` to check DAIC mode
4. Use trigger phrases like "make it so" to enable tools
5. Check your statusline for real-time brainworm awareness

## Multiple Projects

You can install brainworm in multiple projects. Each project gets:
- Independent `.brainworm/` directory
- Separate analytics database
- Own DAIC mode state
- Project-specific configuration

All projects share the same plugin installation.
