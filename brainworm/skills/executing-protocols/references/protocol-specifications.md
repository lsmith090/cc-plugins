# Protocol Specifications Technical Reference

Complete technical documentation for all brainworm protocols and their execution requirements.

## Protocol Overview

Brainworm protocols are structured workflows for complex, multi-step operations that require coordination between agents, state management, and careful sequencing. They exist to prevent errors in critical workflows like task completion and context compaction.

## Protocol Architecture

### Protocol File Structure

Location: `.brainworm/protocols/<protocol-name>.md`

Each protocol file contains:
1. **Purpose**: What the protocol achieves
2. **When to Use**: Trigger conditions and user scenarios
3. **Prerequisites**: Required state or conditions
4. **Steps**: Ordered list of actions
5. **Verification**: How to confirm success
6. **Troubleshooting**: Common issues and solutions

### Protocol Template Format

```markdown
# Protocol Name

## Purpose
[What this protocol achieves]

## When to Use
[Conditions that trigger this protocol]

## Prerequisites
[Required state or setup]

## Steps

### Step 1: [Action Name]
[Detailed instructions]
[Commands to run]
[Expected outcomes]

### Step 2: [Next Action]
...

## Verification
[How to confirm protocol succeeded]

## Troubleshooting
[Common issues and fixes]
```

## Core Protocols

### 1. Context Compaction Protocol

**File**: `context-compaction.md` (may not exist in all installations)

**Purpose**: Preserve work and state when approaching context window limits, enabling session continuity.

**When to Use**:
- Token usage approaching limit (visible in statusline)
- Long complex session needs to continue
- User explicitly requests compaction

**Prerequisites**:
- Current task identified (or none)
- Current mode known
- Work to be preserved exists

**Critical Steps**:

1. **State Verification**
   ```bash
   ./tasks status
   ./daic status
   cat .brainworm/state/unified_session_state.json
   ```
   Record: current_task, daic_mode, correlation_id

2. **User Confirmation**
   Ask: "Are you continuing this task or switching?"
   - Continuing: Proceed with compaction
   - Switching: May need task completion first

3. **Logging Agent Invocation**
   ```
   Task tool:
   - subagent_type: brainworm:logging
   - Task file: absolute path to current task README
   - Focus: Consolidate work logs, clean up redundant entries
   ```

4. **Context Refinement Agent** (if discoveries were made)
   ```
   Task tool:
   - subagent_type: brainworm:context-refinement
   - Task file: absolute path to current task README
   - Focus: Update context manifest with session discoveries
   ```

5. **Service Documentation Agent** (if services modified)
   ```
   Task tool:
   - subagent_type: brainworm:service-documentation
   - Services: list of modified services
   - Focus: Update CLAUDE.md files with changes
   ```

6. **State Preservation Verification**
   ```bash
   ./tasks status  # Should show same task
   ./daic status   # Should show same mode
   ```

7. **User Handoff**
   Inform user:
   - What was preserved
   - Current state (task, mode)
   - That they can continue in new session
   - No git changes were made

**State Changes**: None (state is preserved)

**Agent Dependencies**: logging (required), context-refinement (optional), service-documentation (optional)

**Failure Modes**:
- Agent invocation fails: Retry or skip optional agents
- State read fails: Cannot proceed safely
- File write fails: Work may not be preserved

### 2. Task Completion Protocol

**File**: `task-completion.md` (may not exist in all installations)

**Purpose**: Properly close out completed tasks with documentation updates and state cleanup.

**When to Use**:
- User declares task complete
- All success criteria met
- Ready to move to next work

**Prerequisites**:
- Active task exists
- Task work is actually complete
- Success criteria verified

**Critical Steps**:

1. **Completion Verification**
   Check:
   - All success criteria checked off?
   - Tests passing?
   - Code reviewed?
   - Work documented?

   If not complete: Tell user what remains

2. **Final Logging Agent Invocation**
   ```
   Task tool:
   - subagent_type: brainworm:logging
   - Task file: absolute path to task README
   - Focus: Final consolidation, mark task complete
   - Note: This is the last update
   ```

3. **Service Documentation Agent**
   ```
   Task tool:
   - subagent_type: brainworm:service-documentation
   - Services: all services touched during task
   - Focus: Update CLAUDE.md files with all changes
   ```

4. **GitHub Summary** (if GitHub integrated)
   ```bash
   ./tasks summarize
   ```
   Posts session summary to linked issue

5. **State Cleanup**
   ```bash
   ./tasks clear
   ```
   Removes task from active state

6. **Mode Reset**
   ```bash
   ./daic discussion
   ```
   Return to discussion for next work

7. **Git Guidance** (informational only)
   Suggest to user (DO NOT execute):
   - Merge or archive branch
   - Delete local/remote branch
   - Update tracking systems

**State Changes**:
- `current_task`: null
- `current_branch`: null
- `daic_mode`: "discussion"

**Agent Dependencies**: logging (required), service-documentation (required), session-docs (optional)

**Failure Modes**:
- Task not actually complete: Stop protocol, inform user
- Agent failures: Complete what you can, note failures
- State clear fails: May leave inconsistent state

### 3. Task Startup Protocol

**File**: `task-startup.md` (may not exist in all installations)

**Purpose**: Properly initialize work on an existing task with full context.

**When to Use**:
- Beginning work on existing task
- Resuming paused task
- Picking up task from another session

**Prerequisites**:
- Task exists in `.brainworm/tasks/`
- Task has valid frontmatter
- Git branch exists

**Critical Steps**:

1. **Task Switch**
   ```bash
   ./tasks switch <task-name>
   ```
   Handles: git checkout, state update, service coordination

2. **Verify Switch Success**
   ```bash
   ./tasks status
   ```
   Confirm: correct task, branch, services

3. **Context Verification**
   Check if Context Manifest exists:
   ```bash
   grep -q "## Context Manifest" .brainworm/tasks/<task>/README.md
   echo $?  # 0 = exists, 1 = missing
   ```

4. **Context Gathering** (if missing)
   ```
   Task tool:
   - subagent_type: brainworm:context-gathering
   - Task file: absolute path to task README
   - Focus: Build comprehensive context for existing task
   ```

5. **Mode Verification**
   ```bash
   ./daic status
   ```
   Should be in discussion mode for task start

6. **Mode Correction** (if needed)
   ```bash
   ./daic discussion
   ```

7. **Task Review with User**
   - Read task README
   - Review success criteria
   - Check if requirements changed
   - Confirm understanding before implementing

**State Changes**:
- `current_task`: set to task name
- `current_branch`: set to task branch
- `task_services`: set if multi-service
- `daic_mode`: should be "discussion"

**Agent Dependencies**: context-gathering (conditional)

**Failure Modes**:
- Task doesn't exist: List available tasks
- Git checkout fails: Check for uncommitted changes
- Context gathering fails: Proceed with warning

### 4. Task Creation Protocol

**File**: `task-creation.md` (may not exist in all installations)

**Purpose**: Create new tasks with proper setup and context.

**When to Use**:
- User wants to create new task
- Starting new feature/fix/refactor

**Note**: This protocol is largely automated by `./tasks create` command. The skill focuses on proper invocation and follow-up.

**Critical Steps**:

1. **Task Creation Command**
   ```bash
   ./tasks create <task-name> [options]
   ```

   Options:
   - `--link-issue=N`: Link to existing GitHub issue
   - `--create-issue`: Create new GitHub issue
   - `--services=svc1,svc2`: Specify services (multi-service projects)
   - `--submodule=name`: Target specific submodule

2. **Verify Creation**
   Check:
   - Task directory created
   - Task README exists with valid frontmatter
   - Git branch created
   - State updated

3. **Context Gathering Agent** (ALWAYS)
   ```
   Task tool:
   - subagent_type: brainworm:context-gathering
   - Task file: absolute path to new task README
   - Focus: Build comprehensive context for new task
   - Include: What user wants to build, relevant systems
   ```

4. **Task File Customization**
   User should:
   - Fill in Problem/Goal
   - Define Success Criteria
   - Add any specific notes

5. **Begin in Discussion Mode**
   Verify:
   ```bash
   ./daic status  # Should be discussion
   ```

**State Changes**:
- `current_task`: set to new task
- `current_branch`: set to new branch
- `task_services`: set if specified

**Agent Dependencies**: context-gathering (required)

**Automation Note**: `./tasks create` handles most heavy lifting. Skill ensures proper follow-up.

## Protocol Execution Framework

### Agent Invocation Standards

All protocol agent invocations must follow this pattern:

```
Use Task tool with:
- subagent_type: "brainworm:<agent-name>"
- description: "<brief-description>"
- prompt: "<detailed-instructions>

          File: <absolute-path>

          Focus: <specific-focus>

          Context: <relevant-context>"
```

**Required elements**:
- Absolute file paths (use project root + relative path)
- Clear focus statement
- Relevant context about what changed
- Specific deliverables expected

**Agent-specific requirements**:

**logging agent**:
- Task file path (absolute)
- Current timestamp
- Whether this is mid-session or completion

**context-gathering agent**:
- Task file path (absolute)
- Description of what task involves
- What systems are relevant

**context-refinement agent**:
- Task file path (absolute)
- What discoveries were made
- What changed during session

**service-documentation agent**:
- List of services modified
- What changed in each service
- New patterns or approaches used

**code-review agent**:
- Files and line ranges to review
- Task file for context
- Focus areas (security, performance, etc.)

### State Management Standards

Protocols that modify state must:

1. **Read state before modifications**
   ```bash
   cat .brainworm/state/unified_session_state.json
   ```

2. **Use atomic operations**
   - Use CLI commands (`./tasks`, `./daic`)
   - Don't manually edit state files
   - One state change per command

3. **Verify state after modifications**
   ```bash
   ./tasks status
   ./daic status
   ```

4. **Handle state errors**
   - Check exit codes
   - Read error messages
   - Don't proceed if state is inconsistent

### Verification Standards

Every protocol must include verification steps:

1. **Immediate verification**: Check command succeeded
   ```bash
   echo $?  # 0 = success, non-zero = failure
   ```

2. **State verification**: Confirm state is as expected
   ```bash
   ./tasks status  # Current task/branch correct?
   ./daic status   # Mode correct?
   ```

3. **File verification**: Check files were created/updated
   ```bash
   ls -la .brainworm/tasks/<task>/
   grep -q "expected content" file
   ```

4. **User confirmation**: Tell user what was done
   - What succeeded
   - What was preserved
   - What they should verify manually

## Custom Protocol Development

Users can create custom protocols for project-specific workflows.

### Custom Protocol Guidelines

**File naming**: `<workflow-name>.md` in `.brainworm/protocols/`

**Must include**:
1. Clear purpose statement
2. When to use conditions
3. Step-by-step instructions
4. Verification steps
5. Troubleshooting guidance

**Best practices**:
- Keep steps atomic and sequential
- Include command examples
- Specify absolute paths
- Handle failure cases
- Verify each step

**Agent invocation**: Follow standard invocation pattern

**State management**: Use CLI commands only

### Example Custom Protocol

```markdown
# Deploy to Staging Protocol

## Purpose
Deploy current branch to staging environment with proper verification.

## When to Use
- Feature branch ready for staging test
- All tests passing locally
- Code review complete

## Prerequisites
- On feature branch
- All changes committed
- Tests passing

## Steps

### Step 1: Run Full Test Suite
\`\`\`bash
pytest tests/ -v
\`\`\`
Verify: All tests pass

### Step 2: Build Docker Image
\`\`\`bash
docker build -t myapp:staging .
\`\`\`
Verify: Build succeeds

### Step 3: Push to Registry
\`\`\`bash
docker push myapp:staging
\`\`\`
Verify: Push succeeds

### Step 4: Deploy to Staging
\`\`\`bash
kubectl apply -f k8s/staging/
\`\`\`
Verify: Pods are running

### Step 5: Run Smoke Tests
\`\`\`bash
./scripts/smoke-test.sh staging
\`\`\`
Verify: Smoke tests pass

## Verification
- Staging environment is healthy
- Application responding correctly
- No errors in logs

## Troubleshooting
- Build fails: Check Dockerfile syntax
- Push fails: Verify registry credentials
- Deploy fails: Check k8s resources
- Smoke tests fail: Check application logs
```

## Protocol Error Handling

### Common Errors and Recovery

**Agent Invocation Fails**:
- Verify agent name is correct
- Check Task tool syntax
- Ensure file paths are absolute
- Retry if transient failure

**State Update Fails**:
- Check file permissions
- Verify paths are correct
- Check for file locks
- Manually verify state file

**Git Operation Fails**:
- Check for uncommitted changes
- Verify branch exists
- Check for merge conflicts
- Stash or commit as needed

**Command Not Found**:
- Verify command is in PATH
- Check spelling
- Ensure dependencies installed
- Try absolute path

### Protocol Rollback

If protocol execution fails mid-way:

1. **Stop immediately** - Don't continue with incomplete state
2. **Assess damage** - What succeeded, what failed
3. **Manual recovery** - Reverse successful steps if needed
4. **State correction** - Ensure state is consistent
5. **User notification** - Explain what happened and what's needed

**No automatic rollback** - Protocols don't have transactions. Manual recovery required.

## Protocol Best Practices

1. **Always read protocol file** - Don't execute from memory
2. **Execute in order** - Don't skip or reorder steps
3. **Verify each step** - Don't assume success
4. **Use absolute paths** - Avoid path ambiguity
5. **Preserve state** - Be explicit about state changes
6. **Inform user** - Keep them aware of progress
7. **Handle errors gracefully** - Stop on failure, don't proceed
8. **Document deviations** - If you must improvise, explain why

## Performance Considerations

**Agent invocations are expensive**:
- Each agent runs in separate context
- Full conversation history provided
- Can take 30-60 seconds each

**Minimize agent calls**:
- Only invoke required agents
- Skip optional agents if not needed
- Combine agent work when possible

**State operations are cheap**:
- CLI commands are fast (< 1 second)
- File reads are instant
- No network operations

**Optimize protocols**:
- Group state operations
- Invoke agents in parallel when possible (future)
- Skip verification steps only if confident

## Testing Protocols

Protocol execution should be tested:

**Unit level**: Test individual steps work
**Integration level**: Test full protocol execution
**End-to-end level**: Test protocol in real scenarios

**Test categories**:
- Happy path (all steps succeed)
- Failure modes (steps fail gracefully)
- State consistency (state correct after execution)
- Idempotency (running twice is safe)

## Future Enhancements

Potential protocol system improvements:

- **Protocol versioning**: Track protocol changes over time
- **Protocol validation**: Lint protocols for correctness
- **Parallel agent invocation**: Speed up multi-agent protocols
- **Protocol composition**: Build protocols from smaller protocols
- **Automatic rollback**: Transaction-like protocol execution
- **Protocol templates**: Generate protocols from templates
- **Visual protocol editor**: GUI for creating/editing protocols
