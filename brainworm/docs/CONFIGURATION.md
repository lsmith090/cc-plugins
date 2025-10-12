# Brainworm Configuration Reference - Core System Setup

## Overview

Brainworm uses `.brainworm/config.toml` for system configuration and auto-generates `.claude/settings.json` during installation. The configuration covers DAIC workflow enforcement, branch management, and local analytics capture.

**Important**: Multi-project analytics aggregation (sources, harvesting, dashboards) is handled by the separate **nautiloid** project, not brainworm. This documentation covers only brainworm's single-project features.

## Installation

See [`CLAUDE.md`](../CLAUDE.md) for installation commands. Configuration files are automatically generated during installation.

## Core Configuration Example

Here's a `.brainworm/config.toml` with brainworm's core features:

```toml
# DAIC Workflow Configuration
[daic]
enabled = true
default_mode = "discussion"  # Start sessions in discussion mode

# Trigger phrases that switch from discussion to implementation mode
trigger_phrases = [
    "make it so",
    "run that", 
    "go ahead",
    "ship it",
    "let's do it",
    "execute",
    "implement it"
]

# Tools blocked in discussion mode (require user alignment first)
blocked_tools = [
    "Edit",
    "Write", 
    "MultiEdit",
    "NotebookEdit"
]

# Branch Enforcement Settings
[daic.branch_enforcement]
enabled = true
task_prefixes = ["implement-", "fix-", "refactor-", "migrate-", "test-", "docs-"]

[daic.branch_enforcement.branch_prefixes]
"implement-" = "feature/"
"fix-" = "fix/"
"refactor-" = "feature/"
"migrate-" = "feature/"
"test-" = "feature/"
"docs-" = "feature/"

# Read-Only Commands (allowed in discussion mode)
[daic.read_only_bash_commands]
basic = [
    "ls", "ll", "pwd", "cd", "echo", "cat", "head", "tail", "less", "more",
    "grep", "rg", "find", "which", "whereis", "type", "file", "stat",
    "du", "df", "tree", "basename", "dirname", "realpath", "readlink",
    "whoami", "env", "printenv", "date", "cal", "uptime", "wc", "cut", 
    "sort", "uniq", "comm", "diff", "cmp", "md5sum", "sha256sum"
]
git = [
    "git status", "git log", "git diff", "git show", "git branch", 
    "git remote", "git fetch", "git describe", "git rev-parse", "git blame"
]
docker = ["docker ps", "docker images", "docker logs"]
package_managers = ["npm list", "npm ls", "pip list", "pip show", "yarn list"]
network = ["curl", "wget", "ping", "nslookup", "dig"]
text_processing = ["jq", "awk", "sed -n"]

```

## Configuration Sections

### Multi-Project Analytics

**Note**: Multi-project data sources, harvesting schedules, and cross-project analytics aggregation are managed by the separate **nautiloid** project. Nautiloid reads brainworm's local analytics database (`.brainworm/analytics/hooks.db`) but configuration for multi-project features belongs in nautiloid's config, not here.

For nautiloid documentation, see: https://github.com/lsmith090/nautiloid

### DAIC Workflow Configuration (`[daic]`) ✅ IMPLEMENTED

Configure Discussion → Alignment → Implementation → Check workflow:

```toml
[daic]
enabled = true
default_mode = "discussion"
trigger_phrases = ["make it so", "ship it", "go ahead"]
blocked_tools = ["Edit", "Write", "MultiEdit", "NotebookEdit"]
```

**Core Options**:
- `enabled` - Enable DAIC workflow enforcement
- `default_mode` - Starting mode (`"discussion"` or `"implementation"`)
- `trigger_phrases` - Phrases that activate implementation mode
- `blocked_tools` - Tools blocked in discussion mode

### Read-Only Commands (`[daic.read_only_bash_commands]`) ✅ IMPLEMENTED

Configure commands allowed in discussion mode:

```toml
[daic.read_only_bash_commands]
basic = ["ls", "pwd", "cat", "grep", "find"]
git = ["git status", "git log", "git diff"]
docker = ["docker ps", "docker images"]
```

**Command Categories**:
- `basic` - Fundamental filesystem and text commands
- `git` - Git repository inspection commands
- `docker` - Docker container inspection commands
- `package_managers` - Package manager listing commands
- `network` - Network diagnostic commands
- `text_processing` - Text processing utilities

### Debug Logging Configuration (`[debug]`) ✅ IMPLEMENTED

Configure centralized debug output behavior for all brainworm hooks and utilities:

```toml
[debug]
enabled = false
level = "INFO"

[debug.outputs]
stderr = true
file = false
framework = false
```

**Core Options**:
- `enabled` - Master switch for debug output (default: `false`)
  - Set to `true` to enable debug logging
  - Can be temporarily overridden with `--verbose` CLI flag
- `level` - Debug verbosity level (default: `"INFO"`)
  - `"ERROR"` - Only errors
  - `"WARNING"` - Errors + warnings
  - `"INFO"` - Normal operations (recommended default)
  - `"DEBUG"` - Detailed debugging information
  - `"TRACE"` - Everything including internal state

**Output Destinations** (`[debug.outputs]`):
- `stderr` - Print debug messages to stderr (default: `true`)
  - Recommended for immediate feedback during development
  - Integrates with Claude Code terminal output
- `file` - Write debug messages to `.brainworm/logs/debug.log` (default: `false`)
  - Useful for offline analysis or when stderr is too noisy
  - Persists across sessions for debugging patterns
- `framework` - Write framework-specific debug to `.brainworm/debug_framework_output.log` (default: `false`)
  - Captures JSON communication between hooks and Claude Code
  - Useful for debugging hook/Claude integration issues

**CLI Flag Override**:

The `--verbose` flag provides temporary debug override:
```bash
# Temporarily enable debug output at DEBUG level
claude --verbose
```

When `--verbose` is detected:
- Debug is automatically enabled (regardless of config)
- Debug level is set to `DEBUG`
- Output follows configured destinations
- Only affects current session (doesn't modify config file)

**Usage Examples**:

**Development debugging** (verbose stderr output):
```toml
[debug]
enabled = true
level = "DEBUG"

[debug.outputs]
stderr = true
file = false
framework = false
```

**Production troubleshooting** (minimal file logging):
```toml
[debug]
enabled = true
level = "WARNING"

[debug.outputs]
stderr = false
file = true
framework = false
```

**Framework integration debugging** (capture Claude Code communication):
```toml
[debug]
enabled = true
level = "TRACE"

[debug.outputs]
stderr = true
file = true
framework = true
```

**Debugging Double Logging Issues**:

If you observe duplicate log entries:
1. Set `debug.enabled = true` and `debug.level = "TRACE"`
2. Enable `debug.outputs.file = true` for persistent logs
3. Review `.brainworm/logs/debug.log` to identify duplicate sources
4. Report findings to brainworm issue tracker

**Note**: The centralized debug system eliminates ad-hoc debug statements that previously caused double logging. All hooks and utilities now use the unified debug logger configured here.

## Configuration Management

### Interactive Configuration Tool ✅ IMPLEMENTED

Use the interactive tool for guided setup:

```bash
uv run src/hooks/configure_analytics.py
```

This tool provides:
- Project source configuration
- DAIC workflow setup
- Analytics settings
- Configuration validation

### Manual Configuration ✅ IMPLEMENTED

1. **Create** `brainworm-config.toml` in project root
2. **Configure** required sections based on your needs
3. **Validate** configuration with:
   ```bash
   uv run src/hooks/verify_installation.py
   ```

### Configuration Validation ✅ IMPLEMENTED

Test your configuration:

```bash
# Verify complete system
uv run src/hooks/verify_installation.py

# Test DAIC workflow
./daic status

# Test analytics processing
uv run .brainworm/hooks/view_analytics.py

# Test real-time dashboard (basic version)
uv run src/analytics/realtime_dashboard.py --metrics
```

## Auto-Generated Settings

### `.claude/settings.json` ✅ IMPLEMENTED

Individual project settings use Claude Code's native hook configuration format:

```json
{
  "hooks": {
    "PreCompact": [{"hooks": [{"type": "command", "command": "uv run .brainworm/hooks/pre_compact.py"}]}],
    "SessionStart": [{"hooks": [{"type": "command", "command": "uv run .brainworm/hooks/session_start.py"}]}],
    "Stop": [{"hooks": [{"type": "command", "command": "uv run .brainworm/hooks/stop.py"}]}],
    "UserMessages": [{"hooks": [{"type": "command", "command": "uv run .brainworm/hooks/user_messages.py"}]}],
    "PostToolUse": [{"hooks": [{"type": "command", "command": "uv run .brainworm/hooks/post_tool_use.py"}]}],
    "PreToolUse": [
      {"matcher": {"tools": ["Edit", "MultiEdit", "Write", "NotebookEdit"]}, "hooks": [{"type": "command", "command": "uv run .brainworm/hooks/daic_pre_tool_use.py"}]},
      {"matcher": {"tools": ["Task"]}, "hooks": [{"type": "command", "command": "uv run .brainworm/hooks/transcript_processor.py"}]}
    ]
  },
  "statusLine": {
    "type": "command", 
    "command": ".brainworm/statusline-script.sh"
  }
}
```

**Critical Requirements:**
- **Task Hook Configuration**: The PreToolUse hook for "Task" tools is essential for transcript processing to work
- **DAIC Hook Configuration**: The PreToolUse hook for implementation tools enables workflow enforcement
- Missing either hook configuration prevents core system functionality

Manual editing is rarely needed as installation handles proper setup, but existing installations may need upgrade.

## Environment-Specific Configuration

### Development Environment
```toml
[daic]
enabled = true
default_mode = "discussion"
trigger_phrases = ["make it so", "go ahead", "ship it"]
blocked_tools = ["Edit", "Write", "MultiEdit", "NotebookEdit"]
```

### Production Environment
```toml
[daic]
enabled = true
default_mode = "discussion"
trigger_phrases = ["make it so", "ship it", "let's do it", "execute"]
blocked_tools = ["Edit", "Write", "MultiEdit", "NotebookEdit"]
```

### Minimal Environment
```toml
[daic]
enabled = true
default_mode = "discussion"
trigger_phrases = ["go ahead"]
blocked_tools = ["Edit", "Write"]
```

## Migration and Upgrades

### Upgrading Existing Installations ✅ IMPLEMENTED

**Simple Upgrade Process** - Plugin marketplace handles intelligent updates:

```bash
# Upgrade to latest version
/plugin upgrade brainworm
```

The enhanced installer automatically:
- ✅ **Detects missing hook configurations** (like Task → transcript_processor)
- ✅ **Adds new functionality** to existing settings.json
- ✅ **Preserves custom configurations** and user modifications
- ✅ **Creates automatic backups** before making changes
- ✅ **Reports changes made** ("Added Task matcher to PreToolUse hooks")

### Critical Hook Requirements Validation

**Transcript Processing Requirements:**
Ensure `.claude/settings.json` contains Task hook configuration:
```json
{"matcher": {"tools": ["Task"]}, "hooks": [{"type": "command", "command": "uv run .brainworm/hooks/transcript_processor.py"}]}
```

**DAIC Workflow Requirements:**
Ensure PreToolUse hooks include DAIC enforcement:
```json
{"matcher": {"tools": ["Edit", "MultiEdit", "Write", "NotebookEdit"]}, "hooks": [{"type": "command", "command": "uv run .brainworm/hooks/daic_pre_tool_use.py"}]}
```

### Manual Configuration Backup
```bash
# Backup configuration
cp brainworm-config.toml brainworm-config.toml.backup

# Restore if needed
cp brainworm-config.toml.backup brainworm-config.toml
```

### Troubleshooting Upgrade Issues

**If transcript processing isn't working after upgrade:**
1. Check for Task hook in `.claude/settings.json` PreToolUse array
2. Restart Claude Code for settings to take effect
3. Test with: Task invocation should create 5 transcript chunks in `.brainworm/state/{subagent_type}/`

**If DAIC workflow isn't enforcing:**
1. Verify DAIC hook matcher in `.claude/settings.json`
2. Check `./daic status` shows current mode
3. Validate with blocked tool attempt in discussion mode

## Brainworm vs Nautiloid Separation

### Brainworm (This Plugin)
- **Single-project DAIC enforcement**: Discussion → Implementation workflow
- **Local analytics capture**: Captures hook events to `.brainworm/analytics/hooks.db`
- **Branch management**: Automatic git branch enforcement
- **Task management**: Task tracking and correlation
- **Configuration**: `.brainworm/config.toml` (DAIC settings only)

### Nautiloid (Separate Project)
- **Multi-project aggregation**: Harvests data from multiple brainworm installations
- **Cross-project analytics**: Success patterns, developer insights, trends
- **Dashboards**: Grafana, Metabase, real-time dashboards
- **Data harvesting**: Scheduled collection across projects
- **Configuration**: Nautiloid's own config (sources, harvesting, dashboards)

See nautiloid documentation for multi-project analytics: https://github.com/lsmith090/nautiloid

## Known Limitations

### Brainworm Scope
- **Single-project focus**: Only manages the current project's workflow
- **Local analytics only**: Analytics database is local to each project
- **No cross-project insights**: Use nautiloid for aggregated analytics
- **Dynamic Configuration**: Some settings require Claude Code restart

### Configuration Best Practices
- **Keep it simple**: Brainworm config should only contain DAIC workflow settings
- **No orphaned sections**: Remove sources/harvesting if copied from old configs
- **Use defaults**: Most users only need to customize trigger phrases and blocked tools

This configuration system enables brainworm's core DAIC workflow enforcement while maintaining clear separation from multi-project analytics capabilities.