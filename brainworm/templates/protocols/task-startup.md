# Task Startup Protocol

## Overview
This protocol guides the proper startup and resumption of tasks in the DAIC-enhanced brainworm workflow system. Effective task startup ensures context continuity, proper branch management, and optimal workflow patterns.

## When to Use This Protocol
- Beginning work on a new task
- Resuming work on an existing task after interruption
- Switching between different tasks
- After context compaction when continuing task work
- When team members hand off tasks

## Task Startup Process

### Step 1: Find and Switch to Your Task

**List available tasks:**
```bash
./tasks list                    # All tasks
./tasks list --status=pending   # Pending tasks only
./tasks list --status=in_progress  # Active tasks
```

**Switch to the task atomically:**
```bash
./tasks switch [task-name]
```

**The wrapper automatically:**
- Checks out the task's git branch
- Updates DAIC state with task, branch, and services
- Shows task summary and next steps
- Warns if context manifest is missing

**Verify the switch:**
```bash
./tasks status    # Shows current task state
./daic status     # Shows DAIC mode
```

### Step 2: Review Task Context

**Read the task file thoroughly:**
- `.brainworm/tasks/[task-name]/README.md`
- Understand the task description and goals
- Review all success criteria
- Read the Context Manifest section
- Check the Work Log for recent progress
- Note any Next Steps from previous sessions

**Check task status:**
- If **new task** (status: pending/planned):
  - Verify context manifest exists and is comprehensive
  - If no context manifest, invoke context-gathering agent
  - Update status to 'in-progress' when ready

- If **resuming task** (status: in-progress):
  - Review recent work log entries
  - Check if context needs updates based on discoveries
  - Identify where previous session left off

### Step 3: Context Validation

**If context manifest is missing or incomplete:**
```
Use the context-gathering agent to analyze and create/update the context manifest for [task-name].
Task file: .brainworm/tasks/[task-name]/README.md
```

**If context exists but may be outdated:**
- Check if any referenced systems have changed
- Verify integration points are still accurate
- Update any configuration or API changes discovered

**Review dependencies:**
- Check if dependent tasks are complete
- Verify external dependencies are available
- Confirm any blocking issues have been resolved

### Step 4: Verify DAIC Mode

**Check current mode:**
```bash
./daic status
```

**Ensure proper mode for work:**
- Start in discussion mode for planning
- Review what needs to be discussed before implementation
- Identify any open questions or decisions needed
- Use trigger phrases when ready for implementation mode

### Step 5: Plan the Work Session

**Review current session context:**
- Understand available time and focus areas
- Identify specific goals for this session
- Note any constraints (deployments, dependencies, meetings)

**Plan discussion vs implementation:**
- If significant unknowns exist, plan discussion time first
- If context is clear, identify implementation priorities
- Consider using trigger phrases when ready for implementation mode

**Set session expectations:**
- Define what "done for this session" looks like
- Identify good stopping points if interrupted
- Plan knowledge preservation for future sessions

### Step 6: Environment Preparation

**For each affected service:**
- Verify local development environment is working
- Check that dependencies are available and current
- Confirm database/cache connections if needed
- Verify test suite is passing before making changes

**Configuration checks:**
- Verify environment variables are set correctly
- Check that feature flags are in expected states
- Confirm external service integrations are working
- Test any authentication or API tokens needed

## Resumption Scenarios

### After Context Compaction
**Expected state:**
- Task file should have comprehensive context
- Work log should be clean and current
- Next steps should be clearly defined
- Any discoveries should be integrated into context

**Validation steps:**
- Use `./tasks switch [task-name]` to resume
- Confirm context matches current implementation state
- Verify no significant changes occurred during compaction
- Check that branch state matches task expectations

### After Team Handoff
**Additional steps:**
- Schedule knowledge transfer session if needed
- Review any informal notes or communications
- Understand decision rationale from previous developer
- Identify any concerns or potential issues noted
- Use `./tasks switch [task-name]` to activate task

### After Extended Break
**Catch-up process:**
- Review related changes in codebase since last work
- Check for relevant team discussions or decisions
- Verify dependencies haven't changed significantly
- Test current implementation state matches expectations
- Use `./tasks switch [task-name]` to reactivate

## Common Startup Patterns

### Research-Heavy Tasks
For tasks requiring significant investigation:
1. Start with thorough context gathering
2. Plan multiple discussion sessions before implementation
3. Estimate research vs implementation time needs
4. Document findings continuously for future reference

### Integration Tasks
For tasks involving multiple services:
1. Map all integration points before starting
2. Plan service-by-service implementation approach
3. Consider impact on other teams and coordinate accordingly
4. Set up comprehensive testing strategy early

### Bug Fix Tasks
For fixing existing issues:
1. Reproduce the issue reliably first
2. Understand root cause before implementing fixes
3. Consider prevention strategies, not just immediate fixes
4. Plan regression testing to prevent reoccurrence

## Quality Checklist

Before beginning substantive work, verify:

**Task Understanding:**
- [ ] Task goals and success criteria are clear
- [ ] Context manifest provides adequate technical background
- [ ] Dependencies and integration points are mapped
- [ ] Current implementation state is understood

**Environment Setup:**
- [ ] Correct git branch checked out (via `./tasks switch`)
- [ ] Development environment is functional
- [ ] All required services and dependencies are available
- [ ] DAIC state properly configured (via `./tasks status`)

**Work Planning:**
- [ ] Session goals are realistic and specific
- [ ] Discussion vs implementation balance planned
- [ ] Good stopping points identified
- [ ] Knowledge preservation strategy in place

## Remember

Effective task startup:
- Prevents wasted effort from insufficient context
- Leverages documented learnings for better outcomes
- Establishes proper workflow patterns from the beginning
- Enables smooth handoffs and continuations
- Contributes to continuous improvement through documentation

The investment in proper startup pays dividends throughout the task lifecycle and contributes to overall team effectiveness.

---

## Reference: Manual Task Switching

**Understanding how `./tasks switch` works internally:**

The switch command performs these operations atomically:
1. Validates task exists in `.brainworm/tasks/`
2. Parses task README frontmatter for branch and services
3. Executes `git checkout [branch]`
4. Updates `unified_session_state.json` via DAICStateManager
5. Displays task summary and warnings

**If wrapper is unavailable, manual process:**
1. List tasks: `ls .brainworm/tasks/`
2. Check out branch: `git checkout feature/[task-name]`
3. Update state: `./tasks set --task=[task-name] --branch=[branch]`
4. Verify: `./tasks status`

**Note:** Manual process is error-prone. Use `./tasks switch` whenever possible.
