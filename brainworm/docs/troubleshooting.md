# Troubleshooting

Common issues and solutions when using brainworm.

## Table of Contents

- [Installation Issues](#installation-issues)
- [DAIC Workflow Issues](#daic-workflow-issues)
- [Task Management Issues](#task-management-issues)
- [CLI Command Issues](#cli-command-issues)
- [Agent Issues](#agent-issues)
- [State Synchronization Issues](#state-synchronization-issues)
- [Git and Branch Issues](#git-and-branch-issues)
- [Hook Execution Issues](#hook-execution-issues)
- [Configuration Issues](#configuration-issues)
- [Getting Help](#getting-help)

## Installation Issues

### Brainworm Didn't Auto-Initialize

**Symptom:**
- No initialization message when starting Claude Code
- `.brainworm/` directory doesn't exist
- Commands like `./daic` and `./tasks` not available

**Possible Causes:**
1. Plugin not installed correctly
2. Session start hook not executing
3. Permissions issues

**Solutions:**

1. **Verify plugin is installed:**
   ```bash
   /plugin list
   ```
   Should show `brainworm@medicus-it`

2. **Restart Claude Code:**
   - Close and reopen your Claude Code session
   - Plugin initialization happens on session start

3. **Check for error messages:**
   - Look for errors in Claude Code output
   - Check if any system messages mention brainworm

4. **Manual initialization check:**
   ```bash
   ls .brainworm/
   ```
   If directory doesn't exist, plugin hasn't initialized

5. **Reinstall plugin:**
   ```bash
   /plugin uninstall brainworm@medicus-it
   /plugin install brainworm@medicus-it
   ```

### Plugin Installation Failed

**Symptom:**
```
Error: Failed to install plugin
```

**Solutions:**

1. **Check marketplace is added:**
   ```bash
   /plugin marketplace add https://github.com/lsmith090/cc-plugins
   ```

2. **Verify network connectivity:**
   - Ensure you can access GitHub
   - Check firewall settings

3. **Try local installation:**
   ```bash
   /plugin install brainworm@file:///absolute/path/to/cc-plugins/brainworm
   ```

4. **Check Claude Code version:**
   - Ensure Claude Code is up to date
   - Brainworm requires recent Claude Code features

### Wrapper Scripts Not Created

**Symptom:**
- `./daic` and `./tasks` commands don't exist
- `.brainworm/` directory exists but wrapper scripts missing

**Solutions:**

1. **Check if wrappers exist:**
   ```bash
   ls daic tasks
   ```

2. **Regenerate wrappers:**
   - Start new Claude Code session
   - Wrappers regenerate automatically on session start

3. **Make scripts executable:**
   ```bash
   chmod +x daic tasks
   ```

4. **Run commands via bash:**
   ```bash
   bash daic status
   bash tasks status
   ```

## DAIC Workflow Issues

### DAIC Not Blocking Tools

**Symptom:**
- Edit/Write tools work in discussion mode
- No tool blocking enforcement

**Possible Causes:**
1. DAIC disabled in configuration
2. Actually in implementation mode
3. Subagent context active
4. Hook not executing

**Solutions:**

1. **Check DAIC is enabled:**
   ```bash
   cat .brainworm/config.toml | grep "enabled"
   ```
   Should show `enabled = true` under `[daic]`

2. **Verify current mode:**
   ```bash
   ./daic status
   ```
   Check mode indicator (Discussion or Implementation)

3. **Check for subagent context:**
   - If a subagent is running, blocking is disabled (intentional)
   - Wait for subagent to complete

4. **Check hook execution:**
   ```bash
   cat .brainworm/logs/debug.jsonl | tail -20
   ```
   Look for `pre_tool_use` hook entries

5. **Reset DAIC mode:**
   ```bash
   ./daic discussion
   ```

### Trigger Phrases Not Working

**Symptom:**
- Saying "go ahead" or "make it so" doesn't switch modes
- Mode stays in discussion

**Possible Causes:**
1. Already in implementation mode
2. Phrase not in configuration
3. Typo in phrase

**Solutions:**

1. **Check current mode:**
   ```bash
   ./daic status
   ```
   If already in implementation, triggers won't fire

2. **Verify trigger phrases:**
   ```bash
   cat .brainworm/config.toml | grep -A 10 "trigger_phrases"
   ```

3. **Check phrase matching:**
   - Phrases are case-insensitive
   - Must match exactly (with proper spacing)
   - ✅ "go ahead"
   - ❌ "goahead" (no space)

4. **Add custom trigger:**
   ```bash
   /brainworm:add-trigger "execute now"
   ```

5. **Manual mode switch:**
   ```bash
   ./daic implementation
   ```

### Accidentally Switched Modes

**Symptom:**
- In wrong mode for current work
- Switched to implementation when meant to stay in discussion

**Solutions:**

1. **Switch back to discussion:**
   ```bash
   ./daic discussion
   ```

2. **Toggle mode:**
   ```bash
   ./daic toggle
   ```

3. **Verify mode after switch:**
   ```bash
   ./daic status
   ```

### Want to Bypass DAIC for One Command

**Problem:**
DAIC intentionally cannot be bypassed selectively (workflow discipline).

**Solution:**

1. **Switch to implementation:**
   ```bash
   ./daic implementation
   ```

2. **Make your change**

3. **Return to discussion:**
   ```bash
   ./daic discussion
   ```

This takes 5 seconds and maintains workflow discipline.

**Alternative:**
If you frequently need quick changes, consider if you're starting in the right mode. Maybe you should be in implementation mode for this work session.

## Task Management Issues

### Task File Not Found

**Symptom:**
```bash
./tasks switch my-task
# Error: Task not found
```

**Solutions:**

1. **List all tasks:**
   ```bash
   ./tasks list
   ls .brainworm/tasks/
   ```

2. **Check exact task name:**
   - Task names must match directory names exactly
   - Case sensitive

3. **Verify task directory exists:**
   ```bash
   ls .brainworm/tasks/my-task/
   ```

4. **Check task file exists:**
   ```bash
   ls .brainworm/tasks/my-task/README.md
   ```

### Branch Checkout Failed

**Symptom:**
```bash
./tasks switch my-task
# Error: Branch checkout failed
```

**Possible Causes:**
1. Uncommitted changes in current branch
2. Branch doesn't exist
3. Git conflict

**Solutions:**

1. **Check git status:**
   ```bash
   git status
   ```

2. **Stash uncommitted changes:**
   ```bash
   git stash
   ./tasks switch my-task
   git stash pop  # If needed later
   ```

3. **Commit changes first:**
   ```bash
   git add .
   git commit -m "Work in progress"
   ./tasks switch my-task
   ```

4. **Verify branch exists:**
   ```bash
   git branch -a | grep my-task
   ```

5. **Manual branch checkout:**
   ```bash
   git checkout feature/my-task
   ./tasks set --task=my-task --branch=feature/my-task
   ```

### Wrong Branch After Switch

**Symptom:**
- `git branch` shows different branch than expected
- Task status shows wrong branch

**Solutions:**

1. **Check current branch:**
   ```bash
   git branch
   ```

2. **Check task status:**
   ```bash
   ./tasks status
   ```

3. **Manually checkout correct branch:**
   ```bash
   git checkout feature/my-task
   ```

4. **Sync state:**
   ```bash
   ./tasks set --task=my-task --branch=feature/my-task
   ```

### Context Manifest Missing Warning

**Symptom:**
```bash
./tasks switch my-task
# ⚠️  Warning: Task file has no Context Manifest section
```

**Solution:**

This is expected for new tasks. Run the context-gathering agent:

```
Use the context-gathering agent to create a context manifest for this task.
Task file: .brainworm/tasks/my-task/README.md
```

### Task Creation Fails

**Symptom:**
```bash
./tasks create my-task
# Error: Task creation failed
```

**Possible Causes:**
1. `.brainworm/` directory doesn't exist
2. Git repository not initialized
3. Uncommitted changes prevent branch creation
4. Task already exists

**Solutions:**

1. **Check brainworm initialized:**
   ```bash
   ls .brainworm/
   ```

2. **Verify git repository:**
   ```bash
   git status
   ```
   If "not a git repository", run `git init`

3. **Check for existing task:**
   ```bash
   ./tasks list
   ls .brainworm/tasks/
   ```

4. **Use different task name:**
   ```bash
   ./tasks create my-task-v2
   ```

## CLI Command Issues

### Commands Not Found

**Symptom:**
```bash
./daic status
# bash: ./daic: No such file or directory
```

**Solutions:**

1. **Verify files exist:**
   ```bash
   ls daic tasks
   ```

2. **Make executable:**
   ```bash
   chmod +x daic tasks
   ```

3. **Run via bash:**
   ```bash
   bash daic status
   bash tasks status
   ```

4. **Regenerate wrappers:**
   - Start new Claude Code session
   - Wrappers regenerate automatically

### Permission Denied

**Symptom:**
```bash
./daic status
# -bash: ./daic: Permission denied
```

**Solution:**

```bash
chmod +x daic tasks
./daic status
```

### Command Fails Silently

**Symptom:**
- Command runs but produces no output
- No error message displayed

**Solutions:**

1. **Check for errors:**
   ```bash
   ./daic status 2>&1 | tee error.log
   cat error.log
   ```

2. **Enable debug mode:**
   ```bash
   BRAINWORM_DEBUG=1 ./daic status
   ```

3. **Check logs:**
   ```bash
   cat .brainworm/logs/debug.jsonl | tail -20
   ```

4. **Verify state file exists:**
   ```bash
   cat .brainworm/state/unified_session_state.json
   ```

### Invalid Arguments Error

**Symptom:**
```bash
./tasks create
# Error: Missing required argument: task-name
```

**Solutions:**

1. **Check command syntax:**
   ```bash
   ./tasks --help
   ./tasks create --help
   ```

2. **Provide required arguments:**
   ```bash
   ./tasks create my-task-name
   ```

3. **Check for typos:**
   ```bash
   # Wrong
   ./tasks creat my-task

   # Correct
   ./tasks create my-task
   ```

## Agent Issues

### Agent Doesn't Update Task File

**Symptom:**
- Agent reports success but task file unchanged
- No Context Manifest added

**Possible Causes:**
1. Wrong task file path provided
2. Agent lacks Edit/MultiEdit tools
3. Task file doesn't exist

**Solutions:**

1. **Verify task file path:**
   ```bash
   ls .brainworm/tasks/my-task/README.md
   ```
   Use absolute path or correct relative path

2. **Check agent has edit tools:**
   - Context-gathering: Has Edit, MultiEdit
   - Logging: Has Edit, MultiEdit
   - Code-review: Read-only, no edit tools

3. **Verify task file exists:**
   ```bash
   cat .brainworm/tasks/my-task/README.md
   ```

4. **Re-run agent with correct path:**
   ```
   Use the context-gathering agent for my-task.
   Task file: .brainworm/tasks/my-task/README.md
   ```

### Context-Gathering Adds Too Much

**Symptom:**
- Context manifest is very long (1000+ lines)
- Too much detail in task file

**This is Intentional:**
- Agent is designed to be comprehensive
- Better to over-include context than miss something

**Solutions:**

1. **Edit down after if needed:**
   - Remove sections that are truly irrelevant
   - Keep architectural understanding intact

2. **Accept comprehensive context:**
   - Detailed context prevents bugs
   - Can skim what you don't need
   - Future developers benefit

### Code-Review Finds Nothing

**Symptom:**
- Agent reports "No critical issues"
- Expected some feedback

**This is Good News:**
- Agent found no security vulnerabilities
- Code follows existing patterns
- No obvious bugs

**If You Expected Issues:**
1. Code may actually be good
2. Agent respects existing project patterns
3. Agent focuses on correctness, not style preferences

### Logging Agent Removes Too Much

**Symptom:**
- Important information removed from task file
- Work log entries deleted

**This is Intentional:**
- Agent consolidates redundant entries
- Removes completed Next Steps
- Cleans up obsolete context

**If Critical Info Lost:**
1. Check agent looked at correct transcript
2. Re-add critical information manually
3. Agent focuses on "current state" not history

### Context-Refinement Says "No Updates Needed"

**Symptom:**
```
No context updates needed. Context remains accurate.
```

**This is Normal:**
- Agent only updates if significant drift found
- No update means context is still correct

**When This Happens:**
- Implementation was straightforward
- No surprising discoveries
- Original context was comprehensive

### Agent Invocation Failed

**Symptom:**
- Agent doesn't respond
- Error during agent execution

**Solutions:**

1. **Check agent name is correct:**
   - context-gathering
   - code-review
   - logging
   - context-refinement
   - service-documentation
   - session-docs

2. **Provide task file path:**
   ```
   Use the logging agent to clean up work log.
   Task file: .brainworm/tasks/my-task/README.md
   ```

3. **Check task file exists:**
   ```bash
   cat .brainworm/tasks/my-task/README.md
   ```

4. **Be specific in prompt:**
   Include all necessary information (task file, files modified, etc.)

## State Synchronization Issues

### State Out of Sync

**Symptom:**
- `./tasks status` shows different task than actual work
- Git branch doesn't match task state

**Solutions:**

1. **Check current state:**
   ```bash
   ./tasks status
   git branch
   ```

2. **Check state file:**
   ```bash
   cat .brainworm/state/unified_session_state.json | jq
   ```

3. **Manually sync state:**
   ```bash
   ./tasks set --task=my-task --branch=feature/my-task
   ```

4. **Verify after sync:**
   ```bash
   ./tasks status
   ```

### DAIC Mode Stuck

**Symptom:**
- Can't change DAIC mode
- Mode doesn't match expected state

**Solutions:**

1. **Force mode change:**
   ```bash
   ./daic discussion
   ```
   or
   ```bash
   ./daic implementation
   ```

2. **Check state file:**
   ```bash
   cat .brainworm/state/unified_session_state.json | jq .daic_mode
   ```

3. **Verify mode after change:**
   ```bash
   ./daic status
   ```

4. **Toggle mode:**
   ```bash
   ./daic toggle
   ```

### Session ID Issues

**Symptom:**
- Session correlation not working
- Events not properly correlated

**Solutions:**

1. **Check session ID:**
   ```bash
   cat .brainworm/state/unified_session_state.json | jq .session_id
   ```

2. **Check correlation ID:**
   ```bash
   cat .brainworm/state/unified_session_state.json | jq .correlation_id
   ```

3. **Session IDs set automatically:**
   - Should not need manual intervention
   - Regenerated on session start

4. **If manual update needed:**
   ```bash
   ./tasks session set --session-id=<id> --correlation-id=<id>
   ```

## Git and Branch Issues

### Branch Already Exists

**Symptom:**
```bash
./tasks create my-task
# Error: Branch feature/my-task already exists
```

**Solutions:**

1. **Use different task name:**
   ```bash
   ./tasks create my-task-v2
   ```

2. **Delete old branch:**
   ```bash
   git branch -d feature/my-task
   ./tasks create my-task
   ```

3. **Switch to existing task:**
   ```bash
   ./tasks switch my-task
   ```

### Uncommitted Changes Block Switch

**Symptom:**
```bash
./tasks switch other-task
# Error: Uncommitted changes prevent checkout
```

**Solutions:**

1. **Commit changes:**
   ```bash
   git add .
   git commit -m "Work in progress"
   ./tasks switch other-task
   ```

2. **Stash changes:**
   ```bash
   git stash
   ./tasks switch other-task
   ```

3. **Check what changed:**
   ```bash
   git status
   git diff
   ```

### Branch Name Mismatch

**Symptom:**
- Task expects `feature/my-task`
- Branch is actually `main` or something else

**Solutions:**

1. **Check branch:**
   ```bash
   git branch
   ```

2. **Checkout correct branch:**
   ```bash
   git checkout feature/my-task
   ```

3. **Update task state:**
   ```bash
   ./tasks set --task=my-task --branch=feature/my-task
   ```

### Submodule Issues

**Symptom:**
- Task in submodule not working
- Branch created in wrong repository

**Solutions:**

1. **Specify submodule:**
   ```bash
   ./tasks create my-task --submodule=frontend
   ```

2. **Check submodule status:**
   ```bash
   git submodule status
   cd frontend/
   git status
   ```

3. **Verify branch location:**
   ```bash
   # Should be in submodule
   cd frontend/
   git branch
   ```

## Hook Execution Issues

### Hooks Not Executing

**Symptom:**
- DAIC not enforcing tool blocking
- Events not being captured
- No hook activity

**Solutions:**

1. **Check hooks installed:**
   ```bash
   ls .brainworm/hooks/
   ```

2. **Check plugin initialized:**
   ```bash
   ls .brainworm/
   ```

3. **Restart Claude Code session:**
   - Hooks registered on session start

4. **Check debug logs:**
   ```bash
   cat .brainworm/logs/debug.jsonl | tail -20
   ```

### Hook Permission Errors

**Symptom:**
- Hook fails with permission error
- Tools blocked unexpectedly

**Solutions:**

1. **Check file permissions:**
   ```bash
   ls -la .brainworm/hooks/
   ```

2. **Make hooks executable:**
   ```bash
   chmod +x .brainworm/hooks/*.py
   ```

3. **Check Python available:**
   ```bash
   python3 --version
   ```

### Pre-Tool-Use Hook Errors

**Symptom:**
- Tool use blocked with error
- Hook returning errors

**Solutions:**

1. **Check hook logs:**
   ```bash
   cat .brainworm/logs/debug.jsonl | grep pre_tool_use | tail -5
   ```

2. **Verify DAIC state:**
   ```bash
   ./daic status
   ```

3. **Check blocked tools config:**
   ```bash
   cat .brainworm/config.toml | grep -A 5 "blocked_tools"
   ```

## Configuration Issues

### Configuration Not Loading

**Symptom:**
- Custom trigger phrases not working
- DAIC settings not applied
- Configuration changes ignored

**Solutions:**

1. **Check config file exists:**
   ```bash
   cat .brainworm/config.toml
   ```

2. **Verify TOML syntax:**
   - Check for syntax errors
   - Ensure proper formatting
   - Strings in quotes

3. **Restart Claude Code:**
   - Configuration loaded on session start

4. **Check config location:**
   ```bash
   ls .brainworm/config.toml
   ```
   Should be at project root

### Invalid Configuration

**Symptom:**
- Config file has errors
- Brainworm not initializing properly

**Solutions:**

1. **Validate TOML syntax:**
   - Use online TOML validator
   - Check for missing quotes
   - Check for invalid characters

2. **Restore default config:**
   ```bash
   # Backup current config
   cp .brainworm/config.toml .brainworm/config.toml.backup

   # Plugin will regenerate on next session start
   rm .brainworm/config.toml
   ```

3. **Check for common errors:**
   ```toml
   # Wrong - missing quotes
   trigger_phrases = [make it so]

   # Correct - strings in quotes
   trigger_phrases = ["make it so"]
   ```

### Custom Trigger Not Working

**Symptom:**
- Added custom trigger phrase
- Phrase doesn't switch modes

**Solutions:**

1. **Verify phrase in config:**
   ```bash
   cat .brainworm/config.toml | grep -A 10 "trigger_phrases"
   ```

2. **Check syntax:**
   ```toml
   [daic]
   trigger_phrases = [
       "make it so",
       "go ahead",
       "my custom phrase"  # Correct
   ]
   ```

3. **Restart Claude Code:**
   - Config loaded on session start

4. **Use exact phrase:**
   - Case insensitive but must match
   - "my custom phrase" not "mycustomphrase"

## Getting Help

### Debug Mode

Enable detailed logging:

```bash
BRAINWORM_DEBUG=1 ./daic status
BRAINWORM_DEBUG=1 ./tasks status
```

### Check Logs

View recent hook activity:

```bash
# Debug logs
cat .brainworm/logs/debug.jsonl | tail -20

# Timing logs
cat .brainworm/logs/timing/*.jsonl | tail -10

# Event database
sqlite3 .brainworm/events/hooks.db "SELECT * FROM hook_events ORDER BY timestamp DESC LIMIT 10"
```

### State Inspection

Check current system state:

```bash
# Unified session state
cat .brainworm/state/unified_session_state.json | jq

# DAIC mode
./daic status

# Current task
./tasks status

# Git state
git status
git branch
```

### Report Issues

If you've tried troubleshooting and still have issues:

1. **Gather information:**
   ```bash
   # System info
   ./daic status
   ./tasks status
   git status

   # Recent logs
   cat .brainworm/logs/debug.jsonl | tail -50 > debug-output.txt

   # Configuration
   cat .brainworm/config.toml > config-output.txt
   ```

2. **Report at GitHub:**
   - Repository: https://github.com/lsmith090/cc-plugins/issues
   - Include system information
   - Include debug logs (if not sensitive)
   - Describe expected vs actual behavior
   - Steps to reproduce

3. **Check existing issues:**
   - Someone may have encountered same problem
   - Solution may already be documented

### Community Support

- **GitHub Discussions:** Ask questions, share tips
- **GitHub Issues:** Report bugs, request features
- **Plugin Documentation:** Review docs for guidance

## Quick Reference

**Common Solutions:**

```bash
# Restart everything
# 1. Close Claude Code
# 2. Reopen in project directory
# 3. Check status
./daic status
./tasks status

# Reset DAIC mode
./daic discussion

# Sync task state
./tasks set --task=<name> --branch=<branch>

# Make wrappers executable
chmod +x daic tasks

# View recent logs
cat .brainworm/logs/debug.jsonl | tail -20

# Check configuration
cat .brainworm/config.toml

# Verify brainworm initialized
ls .brainworm/
```

## See Also

- **[Getting Started](getting-started.md)** - Installation and setup
- **[DAIC Workflow](daic-workflow.md)** - Understanding DAIC behavior
- **[Task Management](task-management.md)** - Task lifecycle details
- **[CLI Reference](cli-reference.md)** - Complete command documentation
- **[Configuration](configuration.md)** - Configuration options

---

**[← Back to Documentation Home](README.md)** | **[Next: Architecture →](architecture.md)**
