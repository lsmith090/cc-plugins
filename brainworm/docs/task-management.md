# Task Management

Tasks are brainworm's fundamental unit of work, providing structure, context, and continuity for your development sessions.

## Table of Contents

- [Overview](#overview)
- [Creating Tasks](#creating-tasks)
- [Working with Tasks](#working-with-tasks)
- [Task File Structure](#task-file-structure)
- [Switching Tasks](#switching-tasks)
- [Completing Tasks](#completing-tasks)
- [Git Integration](#git-integration)
- [Session Correlation](#session-correlation)
- [Best Practices](#best-practices)

## Overview

**What is a Task?**

A task is a structured unit of work with:
- **Dedicated directory**: `.brainworm/tasks/[task-name]/`
- **README file**: Problem statement, success criteria, context, work log
- **Git branch**: Isolated development environment
- **Session correlation**: All events tagged with task correlation_id
- **State tracking**: Current task tracked in unified state

**Why Use Tasks?**

✅ **Focus** - One task at a time, clear scope
✅ **Context** - Dedicated documentation and notes
✅ **Continuity** - Resume work across sessions
✅ **Isolation** - Separate git branch per task
✅ **History** - Complete work log and event correlation
✅ **Knowledge** - Institutional memory through documentation

## Creating Tasks

### Basic Creation

Create a new task:

```bash
./tasks create implement-user-auth
```

**What happens:**
1. Creates `.brainworm/tasks/implement-user-auth/README.md`
2. Creates git branch `feature/implement-user-auth`
3. Updates `unified_session_state.json`
4. Sets DAIC mode to discussion
5. Initializes correlation tracking

**Output:**
```
Creating task directory...
✓ Created task file: .brainworm/tasks/implement-user-auth/README.md

Creating branch 'feature/implement-user-auth'...
✓ Created branch 'feature/implement-user-auth' in main repository

Updating DAIC state...
✓ DAIC state updated

✓ Task 'implement-user-auth' created successfully!
```

### Task Naming Conventions

Task names determine the git branch prefix:

| Name Pattern | Branch Type | Example |
|--------------|-------------|---------|
| `fix-*` | `fix/` | `fix-login-bug` → `fix/fix-login-bug` |
| `refactor-*` | `refactor/` | `refactor-auth` → `refactor/refactor-auth` |
| `test-*` | `test/` | `test-coverage` → `test/test-coverage` |
| `docs-*` | `docs/` | `docs-api` → `docs/docs-api` |
| `migrate-*` | `migrate/` | `migrate-db` → `migrate/migrate-db` |
| (default) | `feature/` | `user-auth` → `feature/user-auth` |

**Naming Tips:**
- Use lowercase with hyphens: `implement-feature-x`
- Be descriptive but concise: `fix-payment-webhook-timeout`
- Include key component: `refactor-database-connection`

### Multi-Service Tasks

For tasks affecting multiple services:

```bash
./tasks create implement-api --services=backend,frontend
```

This tracks which services are involved, useful for:
- Context gathering
- Code review scope
- Documentation updates

### Submodule Tasks

For monorepo projects with git submodules:

```bash
./tasks create fix-ui-bug --submodule=frontend-service
```

Creates branch in the specified submodule instead of main repo.

## Working with Tasks

### Viewing Current Task

Check which task is active:

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

### Listing All Tasks

See all tasks:

```bash
./tasks list
```

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

Filter by status:

```bash
./tasks list --status=pending
./tasks list --status=in-progress
./tasks list --status=completed
```

## Task File Structure

Each task has a README.md file with this structure:

```markdown
---
task: implement-user-auth
branch: feature/implement-user-auth
submodule: none
status: pending|in-progress|completed|blocked
created: 2025-10-20
modules: [backend, database]
session_id: abc123...
correlation_id: implement-user-auth_correlation
---

# Implement User Authentication

## Problem/Goal
[Clear description of what needs to be done]

## Success Criteria
- [ ] JWT token generation working
- [ ] Login endpoint returns valid tokens
- [ ] Protected routes verify tokens
- [ ] Tests pass

## Context Files
<!-- Added by context-gathering agent -->
- @backend/auth.py - Current auth implementation
- @backend/middleware/auth.py:45-89 - Token validation
- @database/models/user.py - User model

## User Notes
- Use bcrypt for password hashing
- Token expiry: 24 hours
- Follow existing auth patterns in codebase

## Work Log
- [2025-10-20 14:30] Created task, reviewed existing auth
- [2025-10-20 15:15] Implemented JWT generation
- [2025-10-20 16:00] Added token validation middleware
```

### YAML Frontmatter

The frontmatter tracks metadata:

- **task**: Task identifier
- **branch**: Associated git branch
- **submodule**: Git submodule path (or "none")
- **status**: pending, in-progress, completed, blocked
- **created**: Creation date
- **modules**: Services/components involved
- **session_id**: Claude Code session ID
- **correlation_id**: Event correlation identifier

### Problem/Goal Section

Clear statement of:
- What needs to be built/fixed
- Why it's important
- Any constraints or requirements

**Keep it concise:** 2-4 sentences

### Success Criteria

Specific, measurable outcomes:
- Use checkboxes: `- [ ]`
- Be concrete: "Tests pass" not "Good code quality"
- Include verification: "Endpoints return 200 OK"

### Context Files

Added by the context-gathering agent:
- File paths with line ranges
- Key functions and classes
- Related patterns to follow

You can also add manually:
```markdown
- @service/file.py:123-145 - Specific function
- @other/file.py - Whole file reference
- patterns/auth-flow - Pattern documentation
```

### User Notes

Your own notes:
- Requirements clarifications
- Design decisions
- Things to remember
- Constraints or gotchas

### Work Log

Chronological record of work:
- Date and time
- What was done
- Decisions made
- Blockers encountered

**Updated by:**
- You manually during work
- Logging agent at session end

## Switching Tasks

### Switch to Existing Task

```bash
./tasks switch implement-user-auth
```

**What happens:**
1. Verifies task exists
2. Checks out task's git branch
3. Updates unified session state
4. Sets DAIC mode to discussion
5. Warns if context manifest missing

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

### Resume After Break

When returning to a task after time away:

1. **Switch to task:**
   ```bash
   ./tasks switch my-task
   ```

2. **Read task file** to reload context

3. **Check work log** to see what's been done

4. **Review DAIC mode:**
   ```bash
   ./daic status
   ```

5. **Continue in discussion mode** to re-familiarize

### Multi-Task Workflow

Working on multiple tasks:

```bash
# Work on task A
./tasks switch task-a
# ... do some work ...

# Switch to task B
./tasks switch task-b
# ... do some work ...

# Back to task A
./tasks switch task-a
# State and branch automatically restored
```

Each switch:
- Changes git branch
- Updates session state
- Resets DAIC to discussion
- Changes correlation_id

## Completing Tasks

### Completion Checklist

Before completing a task:

1. **Verify success criteria**
   - All checkboxes marked?
   - All requirements met?

2. **Run tests**
   ```bash
   # Your test command
   pytest tests/
   ```

3. **Update work log**
   - Final state documented
   - Decisions recorded

4. **Code review** (optional but recommended)
   - Use code-review agent
   - Check pattern consistency
   - Verify error handling

### Using the Completion Protocol

For structured completion:

1. **Run logging agent** to clean work log
2. **Run service-documentation agent** if service changed
3. **Commit changes** if not already done
4. **Clear task**:
   ```bash
   ./tasks clear
   ```

5. **Return to discussion**:
   ```bash
   ./daic discussion
   ```

See [Protocols & Agents](protocols-and-agents.md#task-completion) for details.

### Quick Clear

For simple tasks or mid-work switching:

```bash
./tasks clear
```

This just removes the current task from state. The task file and branch remain for reference.

## Git Integration

### Automatic Branch Creation

Task creation automatically creates git branches:

```bash
./tasks create fix-bug-123
```

Creates branch: `fix/fix-bug-123`

### Branch Types

| Task Prefix | Branch Type | When to Use |
|-------------|-------------|-------------|
| `implement-*` | `feature/` | New features |
| `fix-*` | `fix/` | Bug fixes |
| `refactor-*` | `refactor/` | Code improvements |
| `test-*` | `test/` | Test additions |
| `docs-*` | `docs/` | Documentation |
| `migrate-*` | `migrate/` | Migrations |

### Branch Naming

Branch names are derived from task names:

```bash
./tasks create implement-user-authentication
# Branch: feature/implement-user-authentication

./tasks create fix-payment-timeout-issue
# Branch: fix/fix-payment-timeout-issue
```

### Manual Branch Management

You can work with branches normally:

```bash
# See current branch
git branch

# Make commits
git add .
git commit -m "Add JWT validation"

# Push to remote
git push origin feature/implement-user-auth
```

**Task switching automatically handles branch checkout.**

### Submodule Support

For monorepo projects:

```bash
./tasks create fix-frontend-bug --submodule=frontend
```

Creates branch in `frontend/` submodule, not main repo.

Main repo stays on its current branch.

## Session Correlation

### What is Correlation?

Every task gets a `correlation_id` that tags all related events:

```json
{
  "correlation_id": "implement-user-auth_correlation"
}
```

All hook events during this task are tagged with this ID.

### Why It Matters

**Continuity:**
- Resume work after context compaction
- Pick up where you left off
- Review full history of task

**Analytics:**
- Query all events for a task
- Calculate time in discussion vs implementation
- Identify patterns and bottlenecks

**Learning:**
- Review past tasks
- Understand decision-making process
- Improve estimates

### Event Queries

Query events for a task:

```sql
-- All events for this task
SELECT * FROM hook_events
WHERE correlation_id = 'implement-user-auth_correlation'
ORDER BY timestamp;

-- Time per mode
SELECT
  JSON_EXTRACT(event_data, '$.daic_mode') as mode,
  COUNT(*) as event_count,
  SUM(duration_ms) as total_time_ms
FROM hook_events
WHERE correlation_id = 'implement-user-auth_correlation'
GROUP BY mode;
```

See [Reference](reference.md#querying-events) for more queries.

## Best Practices

### One Task at a Time

Focus on single task:
- Clearer scope
- Better context management
- Easier to complete

If you need to work on multiple things:
- Create separate tasks
- Use `./tasks switch` to change between them

### Descriptive Task Names

Good names help you remember what the task is about:

✅ `fix-payment-webhook-timeout`
✅ `implement-user-profile-api`
✅ `refactor-database-connection-pooling`

❌ `fix-bug`
❌ `new-feature`
❌ `task1`

### Update Work Logs Regularly

Add entries as you work:

```markdown
## Work Log
- [2025-10-20 14:30] Started task, reviewed auth code
- [2025-10-20 15:15] Implemented JWT generation
- [2025-10-20 15:45] Added validation middleware
- [2025-10-20 16:30] Tests passing, ready for review
```

**Why:**
- Helps you remember what was done
- Useful when resuming after break
- Creates institutional knowledge
- Helps with estimates

### Use Context-Gathering Agent

After creating a task, use the context-gathering agent:

```
Use the context-gathering agent to analyze requirements
and create a comprehensive context manifest. The task file
is at .brainworm/tasks/my-task/README.md
```

This adds detailed context to the Context Files section.

### Small, Focused Tasks

Better to have:
- 5 small, focused tasks
- Each completable in 1-2 sessions
- Clear scope and success criteria

Than:
- 1 large, vague task
- Takes weeks
- Unclear when "done"

### Task Hierarchy

For large features, create a hierarchy:

```bash
./tasks create implement-user-auth         # Parent
./tasks create implement-user-auth-jwt     # Subtask 1
./tasks create implement-user-auth-api     # Subtask 2
./tasks create implement-user-auth-tests   # Subtask 3
```

Reference parent in subtask descriptions.

### Status Updates

Keep status current:

Edit task frontmatter:
```yaml
status: pending       # Not started
status: in-progress   # Actively working
status: blocked       # Waiting on something
status: completed     # Done
```

Helps when running `./tasks list`.

## Troubleshooting

### Task File Not Found

```bash
./tasks switch my-task
# Error: Task not found
```

**Check:**
```bash
./tasks list              # See all tasks
ls .brainworm/tasks/      # List task directories
```

Task names must match directory names exactly.

### Branch Checkout Failed

```bash
./tasks switch my-task
# Error: Branch checkout failed
```

**Possible causes:**
1. Uncommitted changes in current branch
2. Branch doesn't exist
3. Git conflict

**Solutions:**
```bash
git status                # Check for uncommitted changes
git stash                 # Stash changes temporarily
./tasks switch my-task    # Try again
git stash pop             # Restore changes if needed
```

### Wrong Branch After Switch

**Check current branch:**
```bash
git branch
```

**Should match task:**
```bash
./tasks status
```

If mismatch, manually checkout:
```bash
git checkout feature/my-task
```

### Context Manifest Missing

After switching tasks:
```
⚠️  Warning: Task file has no Context Manifest section
```

**Solution:** Run context-gathering agent to build context.

### Lost Work Log

Work log accidentally deleted?

**Check event database:**
```bash
sqlite3 .brainworm/events/hooks.db

SELECT timestamp, event_data
FROM hook_events
WHERE correlation_id = 'my-task_correlation'
ORDER BY timestamp;
```

Events contain tool use history you can reconstruct from.

## Advanced Usage

### Manual State Updates

Rarely needed, but you can manually update task state:

```bash
./tasks set --task=my-task --branch=feature/my-task
```

**When to use:**
- Recovering from errors
- Importing existing work
- Testing/debugging

### Task Without Git Branch

Create task without branch (not recommended):

Edit task after creation:
```yaml
branch: none
```

**Why you might:** Working in detached HEAD, experimental work

**Downside:** No git isolation, harder to manage

### Correlation ID Customization

Correlation IDs default to `{task-name}_correlation`.

Can be changed in task frontmatter:
```yaml
correlation_id: custom-identifier-123
```

**Useful for:** Grouping related tasks under one correlation.

## See Also

- **[Getting Started](getting-started.md)** - Basic task creation walkthrough
- **[DAIC Workflow](daic-workflow.md)** - How tasks integrate with DAIC
- **[Protocols & Agents](protocols-and-agents.md)** - Task protocols and context-gathering
- **[CLI Reference](cli-reference.md)** - Complete `./tasks` command reference
- **[Reference](reference.md)** - Task file schema and event correlation

---

**[← Back to Documentation Home](README.md)** | **[Next: CLI Reference →](cli-reference.md)**
