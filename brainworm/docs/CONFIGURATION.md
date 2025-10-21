# Configuration

Customize brainworm behavior via `.brainworm/config.toml`.

## Configuration File

**Location:** `.brainworm/config.toml`

Created automatically on first session. Edit with any text editor.

## Complete Reference

```toml
[daic]
# Enable/disable DAIC enforcement
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
# Read-only commands allowed in discussion mode
basic = ["ls", "cat", "head", "tail", "less", "more", "pwd", "cd", "echo", "env"]
git = ["git status", "git log", "git diff", "git show", "git branch"]
docker = ["docker ps", "docker images", "docker logs"]
package_managers = ["npm list", "pip list", "cargo tree"]
network = ["curl", "wget", "ping"]
text_processing = ["jq", "awk", "sed -n"]
testing = ["pytest", "npm test", "cargo test"]

[debug]
# Debug output settings
enabled = false
level = "INFO"  # ERROR, WARNING, INFO, DEBUG, TRACE
format = "text"  # text or json
outputs = { stderr = true, file = false, framework = false }
```

## Common Customizations

### Add Custom Trigger Phrases

**Via command:**
```bash
/brainworm:add-trigger "do the thing"
```

**Via config:**
```toml
[daic]
trigger_phrases = [
    "make it so",
    "go ahead",
    "do the thing"  # Your addition
]
```

### Change Default Mode

Start sessions in implementation mode:

```toml
[daic]
default_mode = "implementation"
```

**Not recommended** - defeats DAIC purpose.

### Disable DAIC Temporarily

```toml
[daic]
enabled = false
```

All tools work normally. Re-enable when ready:

```toml
[daic]
enabled = true
```

### Add Read-Only Commands

Allow custom read-only bash commands:

```toml
[daic.read_only_bash_commands]
custom = ["mycommand status", "mycli info"]
```

### Enable Debug Logging

For troubleshooting:

```toml
[debug]
enabled = true
level = "DEBUG"
outputs = { stderr = true, file = true }
```

Logs to: `.brainworm/logs/debug.jsonl`

## Configuration Sections

### [daic]

Core DAIC workflow settings.

**enabled** (boolean)
- Default: `true`
- Set to `false` to disable DAIC entirely

**default_mode** (string)
- Default: `"discussion"`
- Options: `"discussion"` or `"implementation"`
- Mode for new sessions

**blocked_tools** (array)
- Default: `["Edit", "Write", "MultiEdit", "NotebookEdit"]`
- Tools blocked in discussion mode

**trigger_phrases** (array)
- Default: See above
- Phrases that switch to implementation mode
- Case insensitive
- Substring matching

### [daic.read_only_bash_commands]

Bash commands allowed in discussion mode.

Each key is a category with array of commands:

```toml
[daic.read_only_bash_commands]
basic = ["ls", "cat", ...]
git = ["git status", "git log", ...]
custom = ["mycommand", ...]
```

**How validation works:**
1. Bash command parsed
2. Checked against all arrays
3. Allowed if matches any entry
4. Exact match OR command + space + args

### [debug]

Debug output configuration.

**enabled** (boolean)
- Default: `false`
- Enable debug logging

**level** (string)
- Default: `"INFO"`
- Options: `"ERROR"`, `"WARNING"`, `"INFO"`, `"DEBUG"`, `"TRACE"`

**format** (string)
- Default: `"text"`
- Options: `"text"` or `"json"`

**outputs** (table)
- `stderr`: Console output
- `file`: `.brainworm/logs/debug.jsonl`
- `framework`: Framework logging

## User Configuration

Additional settings in `.brainworm/user-config.json`:

```json
{
  "developer": {
    "name": "Your Name",
    "email": "you@example.com"
  },
  "preferences": {
    "daic_default_mode": "discussion",
    "context_warning_threshold": 75
  }
}
```

**Auto-populated from:**
- Git config (`git config user.name`, `git config user.email`)
- Can be edited manually

## Reloading Configuration

Config changes take effect:
- **Next hook execution** - Most settings
- **Next session** - Some settings (like blocked tools)

Force reload by restarting Claude Code session.

## See Also

- [DAIC Workflow](daic-workflow.md) - Understanding modes
- [CLI Reference](cli-reference.md) - Commands affected by config
- [Troubleshooting](troubleshooting.md) - Config issues

---

**[← Back to Documentation Home](README.md)** | **[Next: Protocols & Agents →](protocols-and-agents.md)**
