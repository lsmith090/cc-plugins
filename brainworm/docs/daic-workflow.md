# DAIC Workflow

**DAIC (Discussion → Alignment → Implementation → Check)** is brainworm's core methodology for thoughtful, deliberate software development.

## Table of Contents

- [Overview](#overview)
- [The Two Modes](#the-two-modes)
- [Mode Switching](#mode-switching)
- [Tool Blocking](#tool-blocking)
- [The Philosophy](#the-philosophy)
- [Best Practices](#best-practices)
- [Customization](#customization)

## Overview

DAIC enforces a deliberate pause between planning and execution. Instead of immediately implementing changes, you first discuss and align on the approach.

**The DAIC Cycle:**

```
Discussion → Alignment → Implementation → Check
     ↓                         ↓
  [Plan & Explore]       [Execute & Verify]
     ↑_________________________↓
          (Return to Discussion)
```

**Benefits:**
- ✅ Reduces hasty, poorly-considered changes
- ✅ Encourages understanding before modifying
- ✅ Creates better architectural decisions
- ✅ Documents reasoning through discussion
- ✅ Builds institutional knowledge

## The Two Modes

### Discussion Mode 💭 (Purple)

**Purpose:** Plan, explore, understand

**What's Blocked:**
- `Edit` - Editing files
- `Write` - Creating files
- `MultiEdit` - Batch edits
- `NotebookEdit` - Notebook modifications

**What's Allowed:**
- `Read` - Reading any file
- `Bash` - Read-only commands (git status, ls, cat, grep, etc.)
- `Glob` - Finding files
- `Grep` - Searching code
- `Task` - Invoking specialized agents
- `./daic status`, `./tasks` - Brainworm commands

**When to Use:**
- Starting new features
- Understanding existing code
- Reviewing pull requests
- Architectural planning
- Debugging investigation
- After completing implementation

**Typical Activities:**
1. Read code to understand current implementation
2. Search for patterns and conventions
3. Ask clarifying questions
4. Use specialized agents for deep analysis
5. Discuss approach and trade-offs
6. Reach alignment on the plan

**Visual Indicator:**
Your statusline shows: `💭 Discussion`

### Implementation Mode ⚡ (Green)

**Purpose:** Execute agreed-upon changes

**What's Allowed:**
- All tools enabled
- Make file changes
- Run commands
- Create/modify files

**When to Use:**
- After discussion is complete
- When approach is clear
- Executing agreed-upon changes
- Following established patterns

**Typical Activities:**
1. Implement the discussed changes
2. Follow the agreed approach
3. Make only planned modifications
4. Run tests to verify
5. Commit changes
6. Return to discussion mode

**Visual Indicator:**
Your statusline shows: `⚡ Implementation`

## Mode Switching

### Using Trigger Phrases (Recommended)

The most natural way to switch to implementation mode is using trigger phrases:

**Default Trigger Phrases:**
- "make it so"
- "go ahead"
- "ship it"
- "let's do it"
- "execute"
- "implement it"

**Example Conversation:**

```
You: I need to add user authentication

Claude: [In discussion mode]
Let me explore the current authentication setup...
[Reads auth files, explains architecture]
Here's my proposed approach:
1. Add JWT token validation
2. Create middleware for protected routes
3. Update user model
What do you think?

You: That looks good, make it so

Claude: [Switches to implementation mode]
Great! I'll implement JWT authentication now.
[Makes the changes]
```

**How It Works:**

1. You include a trigger phrase in your message
2. `user_prompt_submit` hook detects the phrase
3. Mode switches from discussion → implementation
4. Claude confirms the switch
5. Implementation proceeds

**Case Insensitive:**
"GO AHEAD", "go ahead", "Go Ahead" all work.

**Substring Matching:**
"Okay, let's go ahead with that approach" triggers the switch.

### Manual Mode Switching

You can also switch modes manually:

```bash
# Switch to implementation (rarely needed - use trigger phrases!)
./daic implementation

# Switch back to discussion (common after completing work)
./daic discussion

# Toggle between modes
./daic toggle

# Check current mode
./daic status
```

**When to Use Manual Switching:**
- Returning to discussion after implementation
- Emergency mode corrections
- Automation/scripting

### Slash Commands

Available during the session:

```
/brainworm:daic implementation    # Switch to implementation
/brainworm:daic discussion        # Switch to discussion
/brainworm:daic toggle            # Toggle modes
/brainworm:daic status            # Check current mode
```

**Note:** Mode-switching slash commands are blocked in discussion mode (prevents accidental switches).

## Tool Blocking

### How Blocking Works

When in discussion mode:

1. Claude attempts to use a blocked tool (e.g., `Edit`)
2. `pre_tool_use` hook intercepts the request
3. Hook checks current DAIC mode
4. If discussion mode: returns `permission: denied`
5. Claude sees the denial and explains why

**Example:**

```
You: Go ahead and update the README

Claude: [Attempts to use Edit tool]
[Tool blocked by DAIC]

I'm currently in discussion mode, which blocks file editing tools.
To enable editing, use a trigger phrase like "make it so" or
run: ./daic implementation
```

### Read-Only Bash Commands

Not all Bash commands are blocked in discussion mode. Read-only commands are allowed:

**Allowed Commands:**
- `git status`, `git log`, `git diff`, `git show`, `git branch`
- `ls`, `cat`, `head`, `tail`, `less`, `more`
- `grep`, `find`, `locate`
- `ps`, `top`, `df`, `du`
- `npm list`, `pip list`, `cargo tree`
- `pytest`, `npm test` (running tests)
- `curl`, `wget` (read operations)
- All `./daic` and `./tasks` commands

**Blocked Commands:**
- `rm`, `mv`, `cp`, `mkdir`, `touch`
- `git commit`, `git push`, `git merge`
- Output redirection (`>`, `>>`)
- Package installation (`npm install`, `pip install`)
- Any command with dangerous flags (`-delete`, `-exec rm`)

**How It's Validated:**

1. Hook receives bash command
2. `bash_validator.py` parses the command
3. Checks against whitelist of read-only commands
4. Allows or blocks based on safety

**Quote-Aware Parsing:**
Commands like `grep "pattern with | pipe"` are parsed correctly - the pipe inside quotes doesn't split the command.

### Subagent Exception

DAIC blocking is disabled during subagent execution:

**Why:** Agents need full tool access to do their job (e.g., context-gathering agent needs to read files, logging agent needs to edit task files).

**How It Works:**
1. You invoke a subagent with `Task` tool
2. `transcript_processor` hook sets `in_subagent_context.flag`
3. `pre_tool_use` hook sees flag and allows all tools
4. Subagent executes with full access
5. `post_tool_use` hook cleans up flag when agent completes

**Impact:** You don't notice this - subagents just work normally.

## The Philosophy

### Why DAIC?

Traditional development often looks like:

```
Problem → Code → Debug → More Code → More Debug → Hope It Works
```

DAIC enforces:

```
Problem → Understand → Plan → Align → Implement → Verify
```

### Thoughtful Development

**Discussion Mode Forces:**
- Reading existing code before changing it
- Understanding patterns and conventions
- Considering multiple approaches
- Documenting reasoning through conversation
- Getting alignment before implementation

**Implementation Mode Ensures:**
- Changes are deliberate, not reactive
- Approach has been thought through
- Context is understood
- Reasoning is documented

### The Pause That Improves Quality

The "friction" of mode switching is intentional. That brief moment where you type "go ahead" is a decision point:

- ✅ Have I understood the problem?
- ✅ Is my approach sound?
- ✅ Have I considered edge cases?
- ✅ Am I following project conventions?

If the answer to any is "no", stay in discussion mode longer.

### Human-in-the-Loop

Only **you** can switch to implementation mode:
- Trigger phrases in your messages
- Manual `./daic implementation` command

Claude cannot switch modes unilaterally. This ensures:
- You remain in control
- Implementations happen when you're ready
- Changes align with your understanding

## Best Practices

### Start Every Session in Discussion

New tasks automatically start in discussion mode. This is intentional:
- First understand what needs to be done
- Then implement

Even for "simple" tasks, discussion mode helps:
- Verify you're editing the right file
- Check for related code that might need updating
- Consider test impacts
- Look for existing patterns to follow

### Use Trigger Phrases Naturally

Don't overthink it. When you're ready to implement:

```
"Looks good, go ahead"
"Perfect, make it so"
"Okay, ship it"
"Let's do it"
```

All work naturally in conversation.

### Return to Discussion After Implementing

After making changes:

```bash
./daic discussion
```

This helps you:
- Review what was done
- Verify the changes
- Discuss next steps
- Plan follow-up work

### Use Discussion for Code Review

When reviewing code (yours or others):
- Stay in discussion mode
- Read the changes thoroughly
- Ask questions about approach
- Suggest improvements
- Only switch to implementation when changes are agreed

### Respect the Workflow

If you find yourself frequently annoyed by tool blocking:

**Ask yourself:**
- Am I rushing to implement without understanding?
- Have I fully explored the existing code?
- Do I understand the implications of my changes?

DAIC's "friction" often reveals incomplete understanding.

## Customization

### Adding Custom Trigger Phrases

Add your own trigger phrases:

```bash
./add-trigger "do it"
```

Or via slash command:

```
/brainworm:add-trigger "execute now"
```

Or edit config directly:

```toml
# .brainworm/config.toml
[daic]
trigger_phrases = [
    "make it so",
    "go ahead",
    "ship it",
    "let's do it",
    "execute",
    "implement it",
    "do it",           # Your custom phrase
    "execute now"      # Another custom phrase
]
```

**Recommendations:**
- Keep phrases natural ("execute this" not "EXEC_MODE_ON")
- Use phrases you wouldn't say accidentally
- Avoid common words ("yes", "okay" would trigger constantly)

### Changing Blocked Tools

Edit which tools are blocked in discussion mode:

```toml
# .brainworm/config.toml
[daic]
blocked_tools = [
    "Edit",
    "Write",
    "MultiEdit",
    "NotebookEdit"
    # Add or remove tools as needed
]
```

**Warning:** Removing tools weakens DAIC enforcement. The defaults are carefully chosen.

### Changing Default Mode

Set which mode new sessions start in:

```toml
[daic]
default_mode = "discussion"  # or "implementation"
```

**Recommendation:** Keep "discussion" as default. Starting in implementation mode defeats DAIC's purpose.

### Disabling DAIC Entirely

If you want to disable DAIC temporarily:

```toml
[daic]
enabled = false
```

**When you might do this:**
- Urgent hotfixes where discussion isn't needed
- Purely exploratory sessions
- Testing brainworm itself

**Recommendation:** Don't disable DAIC permanently. The workflow improvements are worth the adjustment period.

## Troubleshooting

### DAIC Not Blocking Tools

**Symptom:** Edit/Write work in discussion mode

**Possible Causes:**

1. **DAIC disabled in config**
   ```bash
   cat .brainworm/config.toml | grep "enabled"
   ```
   Should show `enabled = true`

2. **Actually in implementation mode**
   ```bash
   ./daic status
   ```
   Check mode indicator

3. **Subagent context active**
   If a subagent is running, blocking is disabled (this is intentional)

4. **Hook not executing**
   Check `.brainworm/logs/debug.jsonl` for hook errors

### Trigger Phrases Not Working

**Symptom:** Saying "go ahead" doesn't switch modes

**Possible Causes:**

1. **Already in implementation mode**
   ```bash
   ./daic status
   ```

2. **Phrase not in config**
   ```bash
   cat .brainworm/config.toml | grep trigger_phrases
   ```

3. **Typo in phrase**
   Phrases are case-insensitive but must match exactly:
   - ✅ "go ahead"
   - ❌ "goahead" (no space)

### Accidentally Switched Modes

Switch back manually:

```bash
./daic discussion
```

Or toggle:

```bash
./daic toggle
```

### Want to Bypass DAIC for One Command

You can't selectively bypass DAIC (this is intentional). If you need to make a quick change:

1. **Switch to implementation:**
   ```bash
   ./daic implementation
   ```

2. **Make your change**

3. **Return to discussion:**
   ```bash
   ./daic discussion
   ```

This takes 5 seconds and maintains the workflow discipline.

## Advanced Topics

### DAIC State Persistence

Mode is persisted in `.brainworm/state/unified_session_state.json`:

```json
{
  "daic_mode": "discussion",
  "daic_timestamp": "2025-10-20T12:34:56+00:00",
  "previous_daic_mode": "implementation"
}
```

Mode persists across:
- Claude Code restarts
- Session interruptions
- Context compactions

### Mode Transition Events

Every mode change is logged to `.brainworm/events/hooks.db`:

```sql
SELECT * FROM hook_events
WHERE hook_name = 'user_prompt_submit'
  AND event_data LIKE '%mode_transition%';
```

This enables:
- Workflow analytics
- Time-in-mode metrics
- Pattern analysis

See [Reference](reference.md#event-schema) for event details.

### Coordination Flags

DAIC uses coordination flags for hook communication:

- `trigger_phrase_detected.flag` - Set when trigger phrase found
- `in_subagent_context.flag` - Set during subagent execution

These are cleaned up automatically and stored in `.brainworm/state/`.

## See Also

- **[Getting Started](getting-started.md)** - Basic DAIC usage examples
- **[Task Management](task-management.md)** - Using DAIC with tasks
- **[Configuration](configuration.md)** - Customizing DAIC settings
- **[CLI Reference](cli-reference.md)** - Complete command reference
- **[Troubleshooting](troubleshooting.md)** - Solving DAIC issues
- **[Architecture](architecture.md)** - How DAIC is implemented

---

**[← Back to Documentation Home](README.md)** | **[Next: Task Management →](task-management.md)**
