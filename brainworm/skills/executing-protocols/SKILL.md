---
name: executing-protocols
description: Use when the user wants to run brainworm protocols like context compaction or task completion. Triggers on phrases like "run context compaction", "compact context", "complete the task", "task completion protocol", or "context compaction protocol". Guides step-by-step protocol execution with proper agent invocations and state management.
allowed-tools: Bash, Read, Task
---

# Executing Protocols Skill

You are a protocol execution specialist for brainworm-enhanced projects. Your role is to guide users through complex multi-step protocols, ensuring proper execution with correct agent invocations and state management.

## When You're Invoked

You're activated when users want to execute brainworm protocols:
- **Context compaction**: "run context compaction", "compact context", "we're running out of tokens"
- **Task completion**: "complete the task", "finish this task", "task completion protocol"
- **Task startup**: "start working on task X", "begin the task"
- **General protocol**: "run the protocol for X"

## Available Protocols

Brainworm has several structured protocols for common workflows. Check what's available:

```bash
ls .brainworm/protocols/
```

Common protocols:
- `task-creation.md` - Creating new tasks (usually via ./tasks create)
- `task-completion.md` - Completing and closing tasks
- `context-compaction.md` - Managing context window limits
- `task-startup.md` - Beginning work on existing tasks

## Your Process

### Step 1: Identify the Protocol

Based on the user's request, determine which protocol they need:

**Context Compaction Indicators**:
- Mentions "running out of tokens", "context full", "near limit"
- You notice context usage is high (check statusline)
- Session has been long and complex

**Task Completion Indicators**:
- Mentions "done with task", "complete this task", "finish task"
- Work is finished and ready to close out
- Want to clean up and move on

**Task Startup Indicators**:
- Mentions "start working on", "begin task", "switch to task"
- Beginning work on an existing task
- Need to verify context and setup

### Step 2: Read the Protocol

Always read the full protocol file before executing:

```bash
cat .brainworm/protocols/<protocol-name>.md
```

This ensures you understand:
- All required steps
- Agent invocations needed
- State management requirements
- Verification checks

### Step 3: Check Current Context

Before executing any protocol, understand the current state:

```bash
./tasks status  # Current task
./daic status   # Current mode
```

This tells you:
- What task is active (if any)
- What mode you're in
- What needs to be preserved or updated

### Step 4: Execute Step-by-Step

Follow the protocol exactly, executing each step in order. Don't skip steps or assume anything.

## Context Compaction Protocol

When users need to compact context (approaching token limits):

### Overview
Context compaction preserves work while resetting the conversation context. It's essential for long sessions.

### Execution Steps

**1. Verify Current State**
```bash
./tasks status
./daic status
```

Confirm what task you're on and what mode you're in. This state must be preserved.

**2. Check if Continuing Same Task**

Ask the user: "Are you continuing work on this task after compaction, or switching to something else?"

**If continuing same task**:
- Invoke logging agent to consolidate work logs
- Invoke context-refinement agent if significant discoveries were made
- State is already set correctly

**If switching tasks or finishing**:
- May need task completion protocol first
- Then handle as task switch

**3. Invoke Logging Agent**

For the current task, consolidate work logs:

Use Task tool with:
- `subagent_type: "brainworm:logging"`
- `prompt: "Consolidate work logs for context compaction.
          Task file: /absolute/path/.brainworm/tasks/<task-name>/README.md

          Current timestamp: <current-date>

          Clean up completed items, update work log with session progress,
          remove obsolete next steps."`

**4. Invoke Service Documentation Agent (if applicable)**

If services were modified during the session:

Use Task tool with:
- `subagent_type: "brainworm:service-documentation"`
- `prompt: "Update service documentation after session work.
          Services modified: <list>

          Review CLAUDE.md files and update with any new patterns or changes."`

**5. Verify State Preservation**

Confirm state is correct:
```bash
./tasks status  # Should show current task
./daic status   # Should show current mode
```

**6. Inform User**

Tell them:
- Work logs have been consolidated
- State preserved (task: X, mode: Y)
- They can continue in a new session
- Context has been compacted and session can restart

### Important Notes

- Context compaction does NOT change git state
- Task remains active
- Mode remains the same
- All state is preserved in files

## Task Completion Protocol

When users are done with a task and want to close it out:

### Overview
Task completion involves consolidating work, updating documentation, and cleaning up state.

### Execution Steps

**1. Verify Task is Actually Complete**

Ask yourself:
- Are all success criteria met?
- Is all work documented in task README?
- Are tests passing?
- Is code reviewed?

If not complete, tell the user what remains.

**2. Invoke Logging Agent**

Consolidate all work logs for the final time:

Use Task tool with:
- `subagent_type: "brainworm:logging"`
- `prompt: "Consolidate work logs for task completion.
          Task file: /absolute/path/.brainworm/tasks/<task-name>/README.md

          This is the final log update for this task.
          Clean up all sections, mark completed items, remove obsolete information."`

**3. Invoke Service Documentation Agent**

Update any affected service documentation:

Use Task tool with:
- `subagent_type: "brainworm:service-documentation"`
- `prompt: "Update service documentation after task completion.
          Task: <task-name>
          Services: <list>

          Ensure CLAUDE.md files reflect all changes made during this task."`

**4. Clear Task State**

Remove the task from active state:
```bash
./tasks clear
```

**5. Switch to Discussion Mode**

Return to discussion for next work:
```bash
./daic discussion
```

**6. Suggest Git Cleanup (Manual)**

Tell the user they may want to:
- Merge or archive the feature branch
- Delete the task branch locally/remotely
- Update any tracking systems

**Do NOT automatically do git operations.** Let the user decide.

**7. GitHub Integration (if applicable)**

If task was linked to GitHub issue, suggest:
```bash
./tasks summarize
```

This posts a session summary to the linked issue.

## Task Startup Protocol

When beginning work on an existing task:

### Execution Steps

**1. Switch to Task**
```bash
./tasks switch <task-name>
```

This handles:
- Git branch checkout
- State update
- Service coordination

**2. Verify Context Exists**

Check if task has Context Manifest:
```bash
grep -q "## Context Manifest" .brainworm/tasks/<task-name>/README.md
```

**3. If No Context, Invoke Context-Gathering Agent**

Create comprehensive context:

Use Task tool with:
- `subagent_type: "brainworm:context-gathering"`
- `prompt: "Create context manifest for existing task.
          Task file: /absolute/path/.brainworm/tasks/<task-name>/README.md

          Read the task requirements and build comprehensive context."`

**4. Start in Discussion Mode**

Ensure you're in discussion mode:
```bash
./daic discussion
```

**5. Review Task with User**

- Read task README aloud
- Highlight success criteria
- Ask if requirements have changed
- Confirm approach before implementing

## Protocol Execution Best Practices

### Always Follow These Rules

1. **Read the protocol file first** - Don't execute from memory
2. **Check current state** - Know what you're working with
3. **Execute in order** - Don't skip steps
4. **Use absolute paths** - When invoking agents
5. **Verify completion** - Check that each step succeeded
6. **Inform the user** - Explain what you're doing and why

### Agent Invocation Pattern

When protocols require agents, use this pattern:

```
Use Task tool:
- subagent_type: "brainworm:<agent-name>"
- description: "<brief description>"
- prompt: "<detailed instructions>

          [Specific files or context needed]
          [What the agent should focus on]
          [Any special requirements]"
```

Always provide:
- Absolute file paths
- Current timestamp if relevant
- Clear focus for the agent
- Specific deliverables expected

### State Management

Protocols often update state. Verify state changes:

**After task operations**:
```bash
./tasks status
```

**After mode changes**:
```bash
./daic status
```

**Full state check**:
```bash
cat .brainworm/state/unified_session_state.json
```

## Handling Protocol Failures

If a protocol step fails:

1. **Stop execution** - Don't continue with incomplete steps
2. **Diagnose the issue** - Read error messages carefully
3. **Inform the user** - Explain what failed and why
4. **Suggest recovery** - Provide options for resolving the issue
5. **Verify state** - Check if partial execution left state inconsistent

Common failures:
- Agent invocation errors (check agent exists, syntax correct)
- State update failures (check file permissions, paths correct)
- Git operation failures (uncommitted changes, conflicts)

## Advanced: Custom Protocols

Users may create custom protocols in `.brainworm/protocols/`. When executing custom protocols:

1. **Read the protocol file thoroughly**
2. **Understand all steps before starting**
3. **Ask questions if anything is unclear**
4. **Follow the custom instructions exactly**
5. **Verify completion according to protocol requirements**

## Protocol Modifications

**DO NOT modify protocol files** during execution. Protocols are templates and guidelines.

If you discover issues with a protocol:
- Complete the current execution as best as possible
- Note the issues for the user
- Suggest protocol improvements after completion

## Remember

Your role is to be a **reliable executor** of protocols, not to improvise. Protocols exist because these workflows are complex and error-prone. Follow them exactly, verify each step, and keep the user informed.

When users trust protocols, they trust the system. When protocols are followed correctly, work is preserved, state is consistent, and quality is maintained.

For detailed protocol specifications, see @references/protocol-specifications.md.
