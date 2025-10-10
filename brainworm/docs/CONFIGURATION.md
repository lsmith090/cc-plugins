# Brainworm Configuration Reference - Core System Setup

## Overview

Brainworm uses `brainworm-config.toml` for system configuration and auto-generates `.claude/settings.json` during installation. The configuration covers implemented brainworm features: DAIC workflow enforcement, analytics intelligence, and multi-project data sources.

**Important**: This documentation covers only implemented features. Some advanced features shown in sample configurations are planned but not yet functional.

## Installation

See [`CLAUDE.md`](../CLAUDE.md) for installation commands. Configuration files are automatically generated during installation.

## Core Configuration Example

Here's a `brainworm-config.toml` with implemented system features:

```toml
# Multi-Project Data Sources
[[sources]]
name = "main-project"
type = "local"
path = "/Users/you/main-claude-project"
enabled = true

[sources.patterns]
jsonl = ".claude/logs/**/*.jsonl"
sessions = ".claude/sessions/**/*.md"
transcripts = ".claude/logs/transcript_backups/**/*.jsonl"

[sources.filters]
exclude_patterns = ["**/temp/**", "**/.tmp/**", "**/node_modules/**"]
min_file_age_minutes = 5
archive_originals = false

[[sources]]
name = "secondary-project"
type = "local"
path = "/Users/you/secondary-project"
enabled = true

[sources.patterns]
jsonl = ".claude/logs/**/*.jsonl"
sessions = ".claude/sessions/**/*.md"

[sources.filters]
exclude_patterns = ["**/test/**"]
min_file_age_minutes = 10

# Data Harvesting Configuration
[harvesting]
schedule = "*/15 * * * *"  # Every 15 minutes
enabled = true
max_concurrent_sources = 3

# Analytics Intelligence Configuration
[analytics]
real_time_processing = true
correlation_timeout_minutes = 60
success_rate_window_hours = 24

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

# Analytics Features (PLANNED - Limited Implementation)
[daic.analytics]
codebase_learning = true          # BASIC: Learn codebase patterns and conventions
pattern_recognition = true        # BASIC: Identify successful implementation patterns
smart_recommendations = true      # BASIC: Provide context-aware guidance
```

## Configuration Sections

### Data Sources (`[[sources]]`) ✅ IMPLEMENTED

Configure multiple Claude Code projects for central analytics:

```toml
[[sources]]
name = "unique-project-name"
type = "local"  # or "network" for mounted drives
path = "/absolute/path/to/claude-project"
enabled = true

[sources.patterns]
jsonl = ".claude/logs/**/*.jsonl"
sessions = ".claude/sessions/**/*.md"
transcripts = ".claude/logs/transcript_backups/**/*.jsonl"

[sources.filters]
exclude_patterns = ["**/temp/**", "**/.tmp/**"]
min_file_age_minutes = 5
archive_originals = false
```

**Options**:
- `name` - Unique identifier for the project
- `type` - `"local"` (filesystem) or `"network"` (mounted drives)
- `path` - Absolute path to the Claude Code project
- `enabled` - Whether to collect data from this source
- `patterns.jsonl` - Glob pattern for JSONL log files
- `patterns.sessions` - Glob pattern for session files
- `patterns.transcripts` - Glob pattern for transcript backups
- `filters.exclude_patterns` - Patterns to exclude from harvesting
- `filters.min_file_age_minutes` - Minimum file age before processing
- `filters.archive_originals` - Whether to archive original files after processing

### Data Harvesting (`[harvesting]`) ✅ IMPLEMENTED

Configure automatic data collection across projects:

```toml
[harvesting]
schedule = "*/15 * * * *"  # Cron expression
enabled = true
max_concurrent_sources = 3
```

**Options**:
- `schedule` - Cron expression for automatic collection frequency
- `enabled` - Enable/disable automatic harvesting
- `max_concurrent_sources` - Number of projects to process simultaneously

### Analytics Intelligence (`[analytics]`)

Basic analytics configuration for background intelligence. See [`docs/ANALYTICS.md`](ANALYTICS.md) for complete analytics configuration and capabilities.

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

### Branch Enforcement (`[daic.branch_enforcement]`) ✅ IMPLEMENTED

Configure automatic git branch management:

```toml
[daic.branch_enforcement]
enabled = true
task_prefixes = ["implement-", "fix-", "refactor-"]

[daic.branch_enforcement.branch_prefixes]
"implement-" = "feature/"
"fix-" = "fix/"
"refactor-" = "feature/"
```

**Options**:
- `enabled` - Enable automatic branch management
- `task_prefixes` - Task name prefixes that require specific branches
- `branch_prefixes` - Mapping of task prefixes to git branch prefixes

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

### Analytics Features (`[daic.analytics]`)

Analytics feature toggles. See [`docs/ANALYTICS.md`](ANALYTICS.md) for current implementation status and capabilities.

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
default_mode = "discussion"
trigger_phrases = ["make it so", "go ahead"]

# Enable discussion quality features
[daic.analytics] 
codebase_learning = true
pattern_recognition = true
smart_recommendations = true
```

### Production Environment  
```toml
[analytics]
real_time_processing = true

# Keep analytics features disabled until implemented
[daic.analytics]
smart_recommendations = true  # Only basic version available
```

### Team Environment
```toml
[harvesting]
enabled = true
schedule = "*/5 * * * *"  # More frequent harvesting

[analytics]
success_rate_window_hours = 168  # Weekly analytics window
```

## Migration and Upgrades

### Upgrading Existing Installations ✅ IMPLEMENTED

**Simple Upgrade Process** - Enhanced installer handles intelligent merging:

```bash
# Upgrade any existing installation with latest features
./install
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

## Known Limitations

### Unimplemented Features
- **Dashboard Configuration**: Dashboard runs with hardcoded settings, not config file settings
- **Metabase Integration**: Not implemented (files exist but no integration)
- **Advanced Intelligence**: ML-driven features are planned but not functional
- **Dynamic Configuration**: Some settings require system restart to take effect

### Workarounds
- **Dashboard Settings**: Modify hardcoded values in `src/analytics/realtime_dashboard.py`
- **Intelligence Features**: Keep disabled in configuration until implemented
- **Advanced Analytics**: Use existing analytics viewer and harvesting tools

This configuration system enables brainworm's implemented features while clearly marking planned capabilities for future development.