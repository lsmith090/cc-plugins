# CLI Reference

Complete reference for all brainworm command-line tools.

## Quick Reference

**DAIC Commands:**
```bash
./daic status          # Check current mode
./daic discussion      # Switch to discussion mode
./daic implementation  # Switch to implementation mode
./daic toggle          # Toggle between modes
```

**Task Commands:**
```bash
./tasks create <name>            # Create new task
./tasks status                   # Show current task
./tasks list [--status=STATUS]   # List tasks
./tasks switch <name>            # Switch to task
./tasks clear                    # Clear current task
```

**Slash Commands:**
```
/brainworm:daic <subcommand>     # DAIC mode control
/brainworm:add-trigger <phrase>  # Add custom trigger phrase
/brainworm:api-mode              # Toggle API mode
```

## DAIC Commands (`./daic`)

All DAIC mode management commands.

### `./daic status`

Show current DAIC mode and state.

**Usage:**
```bash
./daic status
```

**Output:**
```
💭 Current DAIC Mode: Discussion
  Last changed: 2025-10-20T12:34:56+00:00
  Previous mode: implementation
  Trigger: user_phrase

💡 In Discussion Mode:
  • Edit/Write tools are blocked
  • Focus on planning and alignment
  • Use trigger phrases like 'make it so' to enable implementation
```

**Returns:**
- Current mode (discussion/implementation)
- Last change timestamp
- Previous mode
- How mode was changed (trigger/manual/default)

### `./daic discussion`

Switch to discussion mode.

**Usage:**
```bash
./daic discussion
```

**Output:**
```
Switching to discussion mode...
✓ DAIC mode set to: discussion
```

**Effect:**
- Blocks Edit, Write, MultiEdit, NotebookEdit tools
- Allows read-only operations
- Enables planning and exploration

**When to use:**
- After completing implementation
- Starting new work
- Reviewing code
- Planning changes

### `./daic implementation`

Switch to implementation mode.

**Usage:**
```bash
./daic implementation
```

**Output:**
```
Switching to implementation mode...
✓ DAIC mode set to: implementation
```

**Effect:**
- Enables all tools
- Allows file changes
- Executes changes

**Note:** Rarely needed - use trigger phrases instead!

**When to use:**
- Manual mode switching (rare)
- Scripting/automation
- Emergency override

### `./daic toggle`

Toggle between discussion and implementation modes.

**Usage:**
```bash
./daic toggle
```

**Output:**
```
Current mode: discussion
Toggling to: implementation
✓ DAIC mode set to: implementation
```

**Effect:** Switches to opposite mode

**When to use:**
- Quick mode switching
- Testing mode behavior
- Keyboard shortcuts

## Task Commands (`./tasks`)

All task management commands.

### `./tasks create`

Create a new task.

**Usage:**
```bash
./tasks create <task-name> [options]
```

**Options:**
- `--submodule=NAME` - Create branch in specific submodule
- `--services=SVC1,SVC2` - Track affected services
- `--no-interactive` - Skip prompts (for automation)

**Examples:**
```bash
# Basic task
./tasks create implement-user-auth

# With services
./tasks create fix-api --services=backend,database

# In submodule
./tasks create fix-ui-bug --submodule=frontend
```

**Effect:**
- Creates `.brainworm/tasks/<task-name>/README.md`
- Creates git branch (feature/, fix/, etc.)
- Updates unified session state
- Sets DAIC to discussion mode
- Initializes correlation tracking

**Branch naming:**
- `fix-*` → `fix/...`
- `refactor-*` → `refactor/...`
- `test-*` → `test/...`
- `docs-*` → `docs/...`
- (default) → `feature/...`

### `./tasks status`

Show current task state.

**Usage:**
```bash
./tasks status
```

**Output:**
```
Current Task State:
  Task: implement-user-auth
  Task File: .brainworm/tasks/implement-user-auth/README.md
  Branch: feature/implement-user-auth
  Services: backend, database
  Updated: 2025-10-20
  Session ID: abc123...
  Correlation ID: def456...
```

**Returns:**
- Current task name
- Task file location
- Associated git branch
- Affected services
- Last update timestamp
- Session and correlation IDs

**Exit codes:**
- `0` - Task is set
- `1` - No current task

### `./tasks list`

List all tasks.

**Usage:**
```bash
./tasks list [--status=STATUS]
```

**Options:**
- `--status=pending` - Show only pending tasks
- `--status=in-progress` - Show only in-progress tasks
- `--status=completed` - Show only completed tasks
- `--status=blocked` - Show only blocked tasks
- (no option) - Show all tasks

**Output:**
```
┌──────────────────────────┬──────────────┬─────────────┬────────────┐
│ Task                     │ Branch       │ Status      │ Created    │
├──────────────────────────┼──────────────┼─────────────┼────────────┤
│ implement-user-auth      │ feature/...  │ in-progress │ 2025-10-18 │
│ fix-payment-bug          │ fix/...      │ pending     │ 2025-10-19 │
│ refactor-database        │ refactor/... │ completed   │ 2025-10-15 │
└──────────────────────────┴──────────────┴─────────────┴────────────┘
```

**Columns:**
- Task name
- Git branch
- Status (from task frontmatter)
- Creation date

### `./tasks switch`

Switch to an existing task.

**Usage:**
```bash
./tasks switch <task-name>
```

**Example:**
```bash
./tasks switch implement-user-auth
```

**Effect:**
- Checks out task's git branch
- Updates unified session state
- Sets DAIC to discussion mode
- Updates correlation tracking

**Output:**
```
Switching to task: implement-user-auth

Checking out branch...
✓ Checked out branch: feature/implement-user-auth

Updating state...
✓ State updated

Current task: implement-user-auth
Task file: .brainworm/tasks/implement-user-auth/README.md

⚠️  Tip: Read the task file to load context
```

**Prerequisites:**
- Task must exist
- No uncommitted changes (or use `git stash`)

### `./tasks clear`

Clear the current task from state.

**Usage:**
```bash
./tasks clear
```

**Effect:**
- Removes task from unified session state
- Keeps task file and branch intact
- Resets correlation tracking

**Output:**
```
✅ Task state cleared
```

**Note:** Task file and branch remain for reference.

**When to use:**
- Completing a task
- Switching context
- Cleaning up state

### `./tasks set`

Manually update task state (advanced).

**Usage:**
```bash
./tasks set --task=NAME --branch=BRANCH [--services=SVC1,SVC2]
```

**Options:**
- `--task=NAME` - Set current task
- `--branch=BRANCH` - Set current branch
- `--services=SVC1,SVC2` - Set affected services

**Example:**
```bash
./tasks set --task=my-task --branch=feature/my-task
```

**When to use:**
- Recovering from errors
- Importing existing work
- Testing/debugging

**Caution:** Manual state updates can cause inconsistencies. Use with care.

### `./tasks session`

Manage session correlation (advanced).

**Usage:**
```bash
./tasks session set --session-id=ID --correlation-id=ID
./tasks session show
```

**Subcommands:**
- `set` - Manually set IDs
- `show` - Display current IDs

**Example:**
```bash
./tasks session show
```

**When to use:**
- Debugging correlation issues
- Custom correlation schemes
- Session analysis

## Slash Commands

Commands available during Claude Code sessions.

### `/brainworm:daic`

DAIC mode control via slash command.

**Usage:**
```
/brainworm:daic status
/brainworm:daic discussion
/brainworm:daic implementation
/brainworm:daic toggle
```

**Same as `./daic` but available inline:**
- During conversation
- Without bash tool
- When command-line unavailable

**Note:** Mode-switching commands blocked in discussion mode (prevents accidental switches).

### `/brainworm:add-trigger`

Add custom trigger phrase.

**Usage:**
```
/brainworm:add-trigger "do it"
```

**Effect:**
- Adds phrase to `.brainworm/config.toml`
- Phrase becomes active immediately

**Example:**
```
/brainworm:add-trigger "execute now"

✓ Added trigger phrase: execute now
Updated config: .brainworm/config.toml
```

**Phrase guidelines:**
- Use natural language
- Avoid common words ("yes", "ok")
- 2-4 words recommended
- Case insensitive

### `/brainworm:api-mode`

Toggle API mode (disables ultrathink).

**Usage:**
```
/brainworm:api-mode
```

**Effect:**
- Toggles API mode on/off
- When on: Disables automatic ultrathink injection
- When off: Re-enables ultrathink

**Output:**
```
API mode: enabled
  • Ultrathink disabled
  • For programmatic usage
```

**When to use:**
- API integrations
- Programmatic workflows
- Disabling ultrathink injection

## Common Workflows

### Start New Task Workflow

```bash
# 1. Create task
./tasks create implement-feature-x

# 2. Edit task file
# (Define problem, success criteria)

# 3. Verify state
./tasks status
./daic status

# 4. Start work in discussion mode
# (Read code, plan approach)

# 5. Switch to implementation when ready
# (Use trigger phrase: "go ahead")

# 6. Complete and clear
./daic discussion
./tasks clear
```

### Switch Between Tasks Workflow

```bash
# Currently on task A
./tasks status

# Switch to task B
./tasks switch task-b

# Work on task B
# ...

# Switch back to task A
./tasks switch task-a

# Git branch and state restored automatically
```

### Check Status Workflow

```bash
# What am I working on?
./tasks status

# What mode am I in?
./daic status

# What other tasks exist?
./tasks list

# Complete picture in 3 commands
```

## Exit Codes

All commands return standard exit codes:

- `0` - Success
- `1` - General error
- `2` - Invalid arguments
- `3` - Not found (task/branch)
- `4` - Precondition failed (uncommitted changes, etc.)

**Use in scripts:**
```bash
if ./tasks status > /dev/null 2>&1; then
    echo "Task is set"
else
    echo "No current task"
fi
```

## Output Formats

### Standard Output

Human-readable with colors and formatting (when terminal supports it).

### JSON Output (Future)

Not yet implemented, but planned:
```bash
./tasks status --json
./daic status --json
```

## Environment Variables

**CLAUDE_PLUGIN_ROOT**
- Plugin installation directory
- Set automatically by Claude Code
- Used by wrapper scripts

**BRAINWORM_DEBUG**
- Enable debug output
- Set to `1` or `true`
- Shows detailed execution info

**Example:**
```bash
BRAINWORM_DEBUG=1 ./daic status
```

## Troubleshooting

### Commands Not Found

**Symptom:**
```bash
./daic status
bash: ./daic: No such file or directory
```

**Solutions:**
1. Check files exist:
   ```bash
   ls daic tasks
   ```

2. Make executable:
   ```bash
   chmod +x daic tasks
   ```

3. Run via bash:
   ```bash
   bash daic status
   ```

### Permission Denied

**Symptom:**
```bash
./daic status
-bash: ./daic: Permission denied
```

**Solution:**
```bash
chmod +x daic tasks
```

### Command Fails Silently

**Check for errors:**
```bash
./daic status 2>&1 | tee error.log
```

**Enable debug:**
```bash
BRAINWORM_DEBUG=1 ./daic status
```

**Check logs:**
```bash
cat .brainworm/logs/debug.jsonl | tail -20
```

### Wrapper Script Issues

If wrappers aren't working, they may need regeneration:

1. Start new Claude Code session (wrappers regenerate automatically)
2. Or manually regenerate (advanced):
   ```bash
   uv run .brainworm/plugin-launcher session_start.py
   ```

## See Also

- **[Getting Started](getting-started.md)** - CLI usage examples
- **[DAIC Workflow](daic-workflow.md)** - DAIC mode concepts
- **[Task Management](task-management.md)** - Task lifecycle
- **[Configuration](configuration.md)** - Configuring brainworm
- **[Troubleshooting](troubleshooting.md)** - Solving CLI issues

---

**[← Back to Documentation Home](README.md)** | **[Next: Configuration →](configuration.md)**
