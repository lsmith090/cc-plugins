# Getting Started with Brainworm

This guide will take you from installation through completing your first task with brainworm.

## What You'll Learn

- Installing brainworm from the marketplace
- Understanding DAIC modes
- Creating and completing your first task
- Using basic CLI commands

**Time required:** 10-15 minutes

## Prerequisites

- Claude Code installed and working
- Basic familiarity with git and command line
- A project directory where you want to use brainworm

## Installation

### Step 1: Add the Marketplace

In Claude Code, add the cc-plugins marketplace:

```bash
/plugin marketplace add https://github.com/lsmith090/cc-plugins
```

You should see:
```
✓ Marketplace added successfully
```

### Step 2: Install Brainworm

Install the brainworm plugin:

```bash
/plugin install brainworm@medicus-it
```

You should see:
```
✓ Plugin installed successfully
```

### Step 3: Verify Installation

On your next session start, brainworm will auto-configure. You'll see:

```
⚙️  Initializing brainworm...
✓ Brainworm initialized
```

Verify it's working:

```bash
./daic status
```

Expected output:
```
💭 Current DAIC Mode: Discussion
  Last changed: 2025-10-20T...

💡 In Discussion Mode:
  • Edit/Write tools are blocked
  • Focus on planning and alignment
  • Use trigger phrases like 'make it so' to enable implementation
```

## Understanding DAIC Workflow

Brainworm enforces **DAIC (Discussion → Alignment → Implementation → Check)** workflow:

### Discussion Mode (Purple 💭)

**What it does:**
- Blocks implementation tools (Edit, Write, MultiEdit)
- Allows reading code, exploring, and planning
- Encourages understanding before changing

**When to use:**
- Planning new features
- Understanding existing code
- Discussing architecture
- Reviewing changes

**What you can do:**
- Read files
- Run read-only commands (git status, ls, grep, etc.)
- Use specialized agents
- Ask questions and explore

### Implementation Mode (Green ⚡)

**What it does:**
- Enables all tools
- Allows making changes
- Execute agreed-upon work

**When to use:**
- After planning is complete
- When you're ready to implement
- When changes are well-defined

**How to switch:**

Use trigger phrases in your message:
- "make it so"
- "go ahead"
- "ship it"
- "let's do it"
- "execute"
- "implement it"

Or manually:
```bash
./daic implementation
```

**Example conversation:**
```
You: I want to add a new feature for user authentication.
Claude: [In discussion mode, explores code, explains approach]

You: That sounds good, go ahead and implement it
Claude: [Switches to implementation mode, makes changes]
```

## Your First Task

Let's create and complete a simple task to see the full workflow.

### Step 1: Create a Task

```bash
./tasks create fix-readme-typo
```

Expected output:
```
Creating task directory...
✓ Created task file: .brainworm/tasks/fix-readme-typo/README.md

Creating branch 'fix/fix-readme-typo'...
✓ Created branch 'fix/fix-readme-typo' in main repository

Updating DAIC state...
✓ DAIC state updated

✓ Task 'fix-readme-typo' created successfully!
```

What happened:
- ✅ Created `.brainworm/tasks/fix-readme-typo/README.md`
- ✅ Created git branch `fix/fix-readme-typo`
- ✅ Updated session state
- ✅ Set DAIC mode to discussion

### Step 2: Edit the Task File

Open the task file and customize it:

```bash
# The task file is at:
.brainworm/tasks/fix-readme-typo/README.md
```

Edit the Problem/Goal and Success Criteria sections:

```markdown
## Problem/Goal
Fix typo in README.md line 42 where "teh" should be "the"

## Success Criteria
- [ ] README.md line 42 corrected
- [ ] Changes committed
```

### Step 3: Discuss the Fix

In discussion mode, locate the typo:

**You:** "Can you find the typo in README.md around line 42?"

**Claude:** [Reads file, locates typo, explains the fix]

### Step 4: Switch to Implementation

When ready to fix it:

**You:** "Looks good, go ahead and fix it"

**Claude:** [Switches to implementation mode, makes the edit]

### Step 5: Verify the Fix

Check that the edit was made:

```bash
git diff
```

You should see the typo fix in the diff.

### Step 6: Complete the Task

Return to discussion mode:

```bash
./daic discussion
```

Clear the current task:

```bash
./tasks clear
```

Expected output:
```
✅ Task state cleared
```

**Congratulations!** You've completed your first brainworm task.

## What You Just Learned

✅ **Installation** - Added marketplace and installed plugin
✅ **DAIC Modes** - Worked in both discussion and implementation modes
✅ **Trigger Phrases** - Used "go ahead" to switch modes
✅ **Task Management** - Created, worked on, and completed a task
✅ **CLI Commands** - Used `./daic` and `./tasks` commands
✅ **Git Integration** - Saw how tasks create git branches

## Common Commands Reference

### DAIC Mode Commands

```bash
./daic status              # Check current mode
./daic discussion          # Switch to discussion
./daic implementation      # Switch to implementation (rarely needed)
./daic toggle              # Toggle between modes
```

### Task Commands

```bash
./tasks create <name>      # Create new task
./tasks status             # Show current task
./tasks list               # List all tasks
./tasks switch <name>      # Switch to existing task
./tasks clear              # Clear current task
```

### Slash Commands

```
/brainworm:daic status            # Check DAIC mode
/brainworm:daic toggle            # Toggle mode
/brainworm:add-trigger "phrase"   # Add custom trigger phrase
/brainworm:api-mode               # Toggle API mode
```

## Next Steps

### Learn More About DAIC

Read [DAIC Workflow](daic-workflow.md) to understand:
- When to use each mode
- How trigger phrases work
- Customizing trigger phrases
- Tool blocking behavior

### Master Task Management

Read [Task Management](task-management.md) to learn:
- Task organization best practices
- Using task templates effectively
- Session correlation
- Context management

### Use Protocols & Agents

Read [Protocols & Agents](protocols-and-agents.md) to discover:
- 4 workflow protocols for common operations
- 6 specialized agents for advanced tasks
- When to use each agent
- Protocol best practices

### Customize Your Setup

Read [Configuration](configuration.md) to customize:
- Trigger phrases
- Blocked tools
- Default DAIC mode
- Event capture settings

## Troubleshooting

### Brainworm Didn't Auto-Initialize

If you don't see the initialization message:

1. Check plugin is installed:
   ```bash
   /plugin list
   ```

2. Restart Claude Code

3. Check for errors:
   ```bash
   ls .brainworm/
   ```

If `.brainworm/` directory doesn't exist, see [Troubleshooting](troubleshooting.md#installation-issues).

### Commands Not Found

If `./daic` or `./tasks` commands don't work:

1. Check they exist:
   ```bash
   ls daic tasks
   ```

2. Make them executable:
   ```bash
   chmod +x daic tasks
   ```

3. Try running directly:
   ```bash
   bash daic status
   ```

See [Troubleshooting](troubleshooting.md#cli-commands-not-working) for more help.

### Tool Blocking Not Working

If Edit/Write work in discussion mode:

1. Check DAIC is enabled in config:
   ```bash
   cat .brainworm/config.toml | grep "enabled"
   ```

2. Check current mode:
   ```bash
   ./daic status
   ```

3. See [Troubleshooting](troubleshooting.md#daic-not-blocking-tools)

## Getting Help

- [Troubleshooting Guide](troubleshooting.md) - Common issues and solutions
- [CLI Reference](cli-reference.md) - Complete command documentation
- [GitHub Issues](https://github.com/lsmith090/cc-plugins/issues) - Report bugs

## What's Next?

You now know the basics of brainworm! Explore the other documentation:

- **[DAIC Workflow](daic-workflow.md)** - Deep dive on discussion and implementation modes
- **[Task Management](task-management.md)** - Advanced task organization
- **[Protocols & Agents](protocols-and-agents.md)** - Powerful workflow automation
- **[Configuration](configuration.md)** - Customize brainworm to your workflow

---

**[← Back to Documentation Home](README.md)** | **[Next: DAIC Workflow →](daic-workflow.md)**
