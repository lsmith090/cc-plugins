# Technical Reference

Complete technical reference for brainworm schemas, APIs, and configuration.

## Table of Contents

- [Hook Schemas](#hook-schemas)
- [Event Schemas](#event-schemas)
- [Configuration Reference](#configuration-reference)
- [State File Schemas](#state-file-schemas)
- [Task File Schema](#task-file-schema)
- [CLI Command Reference](#cli-command-reference)
- [Event Database Queries](#event-database-queries)
- [File Locations](#file-locations)

## Hook Schemas

### PreToolUse Hook

**Input Schema:**
```json
{
  "tool_name": "Edit|Write|MultiEdit|NotebookEdit|...",
  "tool_input": {
    "file_path": "/path/to/file",
    // Tool-specific parameters
  }
}
```

**Output Schema:**
```json
{
  "permission": "allow|deny",
  "user_message": "Message to display if denied (optional)"
}
```

**Example:**
```json
{
  "permission": "deny",
  "user_message": "[DAIC: Tool Blocked] You're in discussion mode. The Edit tool is not allowed."
}
```

### PostToolUse Hook

**Input Schema:**
```json
{
  "tool_name": "Edit|Write|...",
  "tool_input": {
    "file_path": "/path/to/file"
  },
  "tool_output": {
    "success": true,
    "message": "File edited successfully"
  }
}
```

**Output Schema:**
```json
{
  "continue": true
}
```

### UserPromptSubmit Hook

**Input Schema:**
```json
{
  "user_message": "User's input text",
  "conversation_history": [
    {
      "role": "user|assistant",
      "content": "Message content"
    }
  ]
}
```

**Output Schema:**
```json
{
  "additional_context": "Text to inject into prompt (optional)",
  "block_submission": false
}
```

### SessionStart Hook

**Input Schema:**
```json
{
  "session_id": "unique-session-identifier",
  "project_root": "/path/to/project"
}
```

**Output Schema:**
```json
{
  "success": true
}
```

### SessionEnd Hook

**Input Schema:**
```json
{
  "session_id": "unique-session-identifier"
}
```

**Output Schema:**
```json
{
  "success": true
}
```

### TranscriptProcessor Hook

**Input Schema:**
```json
{
  "conversation_history": [
    {
      "role": "user|assistant",
      "content": "Message content"
    }
  ],
  "agent_name": "context-gathering|logging|...",
  "additional_context": {}
}
```

**Output Schema:**
```json
{
  "processed_transcript": "Cleaned conversation text"
}
```

## Event Schemas

### Event Schema v2.0

All events stored in SQLite follow this schema:

**Database Schema:**
```sql
CREATE TABLE hook_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    correlation_id TEXT,
    hook_name TEXT NOT NULL,
    timestamp_ns INTEGER NOT NULL,
    execution_id TEXT,
    event_data TEXT,  -- JSON blob
    duration_ms INTEGER
);

CREATE INDEX idx_session ON hook_events(session_id);
CREATE INDEX idx_correlation ON hook_events(correlation_id);
CREATE INDEX idx_timestamp ON hook_events(timestamp_ns);
CREATE INDEX idx_hook ON hook_events(hook_name);
```

**Event Data JSON Schema:**
```json
{
  "hook_name": "pre_tool_use",
  "session_id": "abc12345",
  "correlation_id": "task-name_correlation",
  "timestamp_ns": 1234567890123456789,
  "execution_id": "exec-123",
  "event_data": {
    "tool_name": "Edit",
    "file_path": "/path/to/file",
    "daic_mode": "discussion",
    "permission": "deny",
    // Hook-specific data
  },
  "duration_ms": 150
}
```

### DAIC Mode Transition Event

```json
{
  "hook_name": "user_prompt_submit",
  "event_data": {
    "event_type": "mode_transition",
    "previous_mode": "discussion",
    "new_mode": "implementation",
    "trigger": "user_phrase",
    "trigger_phrase": "go ahead",
    "timestamp": "2025-10-20T12:34:56+00:00"
  }
}
```

### Tool Execution Event

```json
{
  "hook_name": "post_tool_use",
  "execution_id": "exec-abc123",
  "event_data": {
    "tool_name": "Edit",
    "file_path": "/path/to/file.py",
    "success": true,
    "daic_mode": "implementation"
  },
  "duration_ms": 235
}
```

### Task Event

```json
{
  "hook_name": "session_start",
  "event_data": {
    "event_type": "task_created",
    "task_name": "implement-feature-x",
    "branch": "feature/implement-feature-x",
    "services": ["backend", "frontend"],
    "correlation_id": "implement-feature-x_correlation"
  }
}
```

## Configuration Reference

### Complete config.toml Schema

```toml
[daic]
# Enable/disable DAIC workflow enforcement
enabled = true

# Default mode for new sessions
default_mode = "discussion"  # or "implementation"

# Tools blocked in discussion mode
blocked_tools = [
    "Edit",
    "Write",
    "MultiEdit",
    "NotebookEdit"
]

# Trigger phrases for mode switching
trigger_phrases = [
    "make it so",
    "go ahead",
    "ship it",
    "let's do it",
    "execute",
    "implement it"
]

[daic.read_only_bash_commands]
# Read-only bash commands allowed in discussion mode

basic = [
    "ls", "cat", "head", "tail", "less", "more",
    "grep", "find", "locate", "which", "whereis",
    "pwd", "echo", "printf", "wc", "sort", "uniq"
]

git = [
    "git status", "git log", "git diff", "git show",
    "git branch", "git remote", "git config --get",
    "git rev-parse", "git describe"
]

system = [
    "ps", "top", "df", "du", "free", "uptime",
    "uname", "hostname", "whoami", "id"
]

package_managers = [
    "npm list", "pip list", "pip show",
    "cargo tree", "bundle list"
]

testing = [
    "pytest", "npm test", "cargo test",
    "python -m pytest", "python -m unittest"
]

network = [
    "curl", "wget", "ping", "nslookup", "dig"
]

[debug]
# Debug output settings
enabled = false
level = "INFO"  # ERROR, WARNING, INFO, DEBUG, TRACE
format = "text"  # text or json

[debug.outputs]
stderr = true
file = false
framework = false
```

### Configuration Defaults

**DAIC Defaults:**
- `enabled`: `true`
- `default_mode`: `"discussion"`
- `blocked_tools`: `["Edit", "Write", "MultiEdit", "NotebookEdit"]`
- 6 default trigger phrases

**Debug Defaults:**
- `enabled`: `false`
- `level`: `"INFO"`
- `format`: `"text"`
- `outputs.stderr`: `true`
- `outputs.file`: `false`
- `outputs.framework`: `false`

## State File Schemas

### Unified Session State

**File:** `.brainworm/state/unified_session_state.json`

**Schema:**
```json
{
  "daic_mode": "discussion",
  "daic_timestamp": "2025-10-20T12:34:56+00:00",
  "previous_daic_mode": "implementation",
  "current_task": "implement-feature-x",
  "current_branch": "feature/implement-feature-x",
  "task_services": ["backend", "frontend"],
  "session_id": "abc12345",
  "correlation_id": "implement-feature-x_correlation",
  "plugin_root": "/path/to/plugin",
  "developer": {
    "name": "Developer Name",
    "email": "developer@example.com"
  }
}
```

**Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `daic_mode` | string | Current DAIC mode ("discussion" or "implementation") |
| `daic_timestamp` | string | ISO 8601 timestamp of last mode change |
| `previous_daic_mode` | string | Previous DAIC mode |
| `current_task` | string | Name of current task (or null) |
| `current_branch` | string | Current git branch (or null) |
| `task_services` | array | List of services affected by task |
| `session_id` | string | Claude Code session identifier |
| `correlation_id` | string | Task correlation identifier |
| `plugin_root` | string | Absolute path to plugin installation |
| `developer` | object | Developer information from git config |

### Coordination Flags

**Location:** `.brainworm/state/`

**Flag Files:**
- `trigger_phrase_detected.flag` - Created when trigger phrase found
- `in_subagent_context.flag` - Created when subagent executing

**Format:** Empty file (existence is the signal)

**Lifecycle:**
1. Created by hook
2. Read by another hook
3. Deleted after use
4. Never persisted

## Task File Schema

**File:** `.brainworm/tasks/[task-name]/README.md`

**YAML Frontmatter:**
```yaml
---
task: implement-feature-x
branch: feature/implement-feature-x
submodule: none
status: pending|in-progress|completed|blocked
created: 2025-10-20
modules: [backend, frontend]
session_id: abc12345
correlation_id: implement-feature-x_correlation
---
```

**Markdown Structure:**
```markdown
# [Task Title]

## Problem/Goal
[Clear description of what needs to be done]

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Context Manifest
[Added by context-gathering agent]

### How This Currently Works
[Verbose narrative...]

### For New Feature Implementation
[What needs to connect...]

### Technical Reference Details
[Signatures, data structures, etc.]

## User Notes
- Note 1
- Note 2

## Work Log

### 2025-10-20

#### Completed
- Item 1
- Item 2

#### Decisions
- Decision 1
- Decision 2

#### Discovered
- Discovery 1

#### Next Steps
- Next step 1
- Next step 2
```

**Status Values:**
- `pending` - Not yet started
- `in-progress` - Actively working
- `completed` - Finished
- `blocked` - Waiting on external dependency

## CLI Command Reference

### DAIC Commands

**`./daic status`**
- Shows current DAIC mode
- Exit code: Always 0

**`./daic discussion`**
- Switches to discussion mode
- Exit code: 0 on success, 1 on error

**`./daic implementation`**
- Switches to implementation mode
- Exit code: 0 on success, 1 on error

**`./daic toggle`**
- Toggles between modes
- Exit code: 0 on success, 1 on error

### Task Commands

**`./tasks create <name> [--services=SVC1,SVC2] [--submodule=NAME]`**
- Creates new task with branch
- Exit code: 0 on success, 1-4 on error

**`./tasks status`**
- Shows current task
- Exit code: 0 if task set, 1 if no task

**`./tasks list [--status=STATUS]`**
- Lists all tasks
- Exit code: Always 0

**`./tasks switch <name>`**
- Switches to existing task
- Exit code: 0 on success, 3 if not found, 4 if precondition failed

**`./tasks clear`**
- Clears current task
- Exit code: Always 0

**`./tasks set --task=NAME --branch=BRANCH [--services=SVC1,SVC2]`**
- Manually updates task state
- Exit code: 0 on success, 2 on invalid arguments

**Exit Codes:**
- `0` - Success
- `1` - General error
- `2` - Invalid arguments
- `3` - Not found (task/branch)
- `4` - Precondition failed (uncommitted changes, etc.)

## Event Database Queries

### Common Queries

**All events for a task:**
```sql
SELECT * FROM hook_events
WHERE correlation_id = 'task-name_correlation'
ORDER BY timestamp_ns;
```

**DAIC mode transitions:**
```sql
SELECT
    timestamp_ns,
    json_extract(event_data, '$.previous_mode') as from_mode,
    json_extract(event_data, '$.new_mode') as to_mode,
    json_extract(event_data, '$.trigger') as trigger
FROM hook_events
WHERE hook_name = 'user_prompt_submit'
  AND event_data LIKE '%mode_transition%'
ORDER BY timestamp_ns;
```

**Tool usage by mode:**
```sql
SELECT
    json_extract(event_data, '$.tool_name') as tool,
    json_extract(event_data, '$.daic_mode') as mode,
    COUNT(*) as count,
    AVG(duration_ms) as avg_duration_ms
FROM hook_events
WHERE hook_name = 'post_tool_use'
  AND correlation_id = 'task-name_correlation'
GROUP BY tool, mode;
```

**Session timeline:**
```sql
SELECT
    datetime(timestamp_ns / 1000000000, 'unixepoch') as timestamp,
    hook_name,
    json_extract(event_data, '$.event_type') as event_type,
    json_extract(event_data, '$.tool_name') as tool_name
FROM hook_events
WHERE session_id = 'abc12345'
ORDER BY timestamp_ns;
```

**Time in each mode:**
```sql
WITH mode_changes AS (
    SELECT
        timestamp_ns,
        json_extract(event_data, '$.new_mode') as mode,
        LEAD(timestamp_ns) OVER (ORDER BY timestamp_ns) as next_timestamp
    FROM hook_events
    WHERE hook_name = 'user_prompt_submit'
      AND event_data LIKE '%mode_transition%'
      AND correlation_id = 'task-name_correlation'
)
SELECT
    mode,
    SUM((next_timestamp - timestamp_ns) / 1000000000.0) as seconds_in_mode
FROM mode_changes
WHERE next_timestamp IS NOT NULL
GROUP BY mode;
```

**Tool blocking frequency:**
```sql
SELECT
    json_extract(event_data, '$.tool_name') as tool,
    json_extract(event_data, '$.permission') as permission,
    COUNT(*) as count
FROM hook_events
WHERE hook_name = 'pre_tool_use'
  AND correlation_id = 'task-name_correlation'
GROUP BY tool, permission
ORDER BY count DESC;
```

## File Locations

### Plugin Installation

**Plugin Source:**
```
.claude/plugins/brainworm@medicus-it/
├── .claude-plugin/
│   └── plugin.json
├── hooks/
│   ├── hooks.json
│   └── *.py
├── agents/
│   └── *.md
├── commands/
│   └── *.md
├── scripts/
│   └── *.py
├── utils/
│   └── *.py
├── templates/
│   ├── TEMPLATE.md
│   ├── CLAUDE.sessions.md
│   └── protocols/
└── docs/
    └── *.md
```

### Project Files

**User Project:**
```
your-project/
├── .brainworm/
│   ├── config.toml
│   ├── state/
│   │   ├── unified_session_state.json
│   │   └── *.flag
│   ├── tasks/
│   │   └── task-name/
│   │       └── README.md
│   ├── events/
│   │   └── hooks.db
│   ├── protocols/
│   │   ├── task-creation.md
│   │   ├── task-startup.md
│   │   ├── task-completion.md
│   │   └── context-compaction.md
│   ├── logs/
│   │   ├── debug.jsonl (optional)
│   │   └── timing/ (optional)
│   ├── memory/ (optional)
│   │   └── YYYY-MM-DD-HHMM-focus.md
│   └── plugin-launcher
├── daic
└── tasks
```

### State Files

| File | Purpose | Format | Persistence |
|------|---------|--------|-------------|
| `unified_session_state.json` | Single source of truth | JSON | Persistent |
| `*.flag` | Inter-hook coordination | Empty file | Ephemeral |
| `hooks.db` | Event storage | SQLite | Persistent |
| `config.toml` | User configuration | TOML | Persistent |
| `debug.jsonl` | Debug logs (optional) | JSONL | Persistent |

### Temporary Files

**Agent Delivery:**
- `.brainworm/state/[agent-name]/current_transcript_*.json`
- `.brainworm/state/[agent-name]/service_context.json`

**Lifecycle:** Created before agent invocation, consumed by agent, deleted after use.

## Environment Variables

**CLAUDE_PLUGIN_ROOT**
- Plugin installation directory
- Set by Claude Code automatically
- Used by hook scripts

**BRAINWORM_DEBUG**
- Enable debug output
- Set to `1` or `true`
- Shows detailed execution info

**Example:**
```bash
BRAINWORM_DEBUG=1 ./daic status
```

## Python API

### DAICStateManager

```python
from pathlib import Path
from brainworm.utils.daic_state_manager import DAICStateManager

manager = DAICStateManager(Path("."))

# Get current unified state
state = manager.get_unified_state()

# Get DAIC mode
mode = manager.get_daic_mode()

# Set DAIC mode
manager.set_daic_mode("implementation")

# Toggle DAIC mode
new_mode = manager.toggle_daic_mode()

# Get task state
task_state = manager.get_task_state()

# Set task state
manager.set_task_state(
    task="my-task",
    branch="feature/my-task",
    services=["backend", "frontend"],
    updated=str(datetime.now().date())
)

# Update session correlation
manager.update_session_correlation(
    session_id="abc123",
    correlation_id="my-task_correlation"
)

# Check if tool should be blocked
result = manager.should_block_tool("Edit", {"file_path": "/test.py"})
```

### EventStore

```python
from brainworm.utils.event_store import EventStore

store = EventStore()

# Log event
store.log_event(
    hook_name="pre_tool_use",
    session_id="abc123",
    correlation_id="task_correlation",
    event_data={
        "tool_name": "Edit",
        "permission": "deny"
    }
)

# Query events
events = store.get_events_by_session("abc123")
```

### BashValidator

```python
from brainworm.utils.bash_validator import BashValidator

validator = BashValidator()

# Check if command is read-only
is_safe = validator.is_read_only("git status")  # True
is_safe = validator.is_read_only("rm -rf /")    # False

# Get command type
cmd_type = validator.get_command_type("git status")  # "git"
```

## Version History

**Current Version:** 1.0.0

**Schema Versions:**
- Event Schema: v2.0
- State Schema: v1.0
- Task File Schema: v1.0

**Breaking Changes:**
- v2.0: Migrated from fragmented state files to unified state
- v2.0: Event schema updated with correlation tracking

## See Also

- **[Architecture](architecture.md)** - System design and implementation
- **[Contributing](contributing.md)** - Development guidelines
- **[Configuration](configuration.md)** - Configuration guide
- **[CLI Reference](cli-reference.md)** - Command-line interface

---

**[← Back to Documentation Home](README.md)**
