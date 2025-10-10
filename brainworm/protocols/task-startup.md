# THIS FILE IS AUTO-GENERATED - DO NOT EDIT DIRECTLY
# Generated from: /Users/logansmith/brainworm/src/hooks/templates/task-startup.md
# Generation time: 2025-10-08T17:06:54.727412Z
# Template checksum: daf8c4c085f6cdf9...
# 
# To modify this file, edit the source template and run: ./install
# For questions about this file, see: docs/GOVERNANCE.md
#
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

### Step 1: Identify and Load Task Context

**Locate the task:**
- Find the task file in `.brainworm/tasks/[task-name]/README.md`
- Verify this is the intended task to work on
- Check task priority and current status

**Read the complete task file:**
- Understand the task description and goals
- Review all success criteria
- Read the Context Manifest thoroughly
- Check the current Work Log for recent progress
- Note any Next Steps from previous sessions

### Step 2: Validate Task State

**Check task metadata:**
```markdown
**Status:** [Should be 'planned' or 'in-progress']
**Priority:** [Verify this aligns with current priorities]
**Services/Components Affected:** [Note which areas you'll be working in]
```

**If task is new (status: planned):**
- Verify context manifest exists and is comprehensive
- If no context manifest, use context-gathering agent first
- Update status to 'in-progress' when ready to begin

**If resuming existing task (status: in-progress):**
- Review recent work log entries
- Check if context manifest needs updates based on recent discoveries
- Identify where previous session left off

### Step 3: Set Up Development Environment

**Update DAIC state:**
```json
{
  "task": "[task-name]",
  "branch": "[appropriate-branch-name]",
  "services": ["affected-service-1", "affected-service-2"],
  "updated": "[current-date]",
  "session_id": "[current-session-id]",
  "correlation_id": "[correlation-id]"
}
```

**Branch management:**
```bash
# Check current branch
git branch --show-current

# Switch to task branch (create if needed)
git checkout -b feature/[task-name]

# Or switch to existing task branch
git checkout feature/[task-name]

# Verify branch is up to date
git pull origin feature/[task-name]
```

**DAIC mode setup:**
- Ensure starting in discussion mode
- Review what needs to be discussed/planned before implementation
- Identify any open questions or decisions needed

### Step 4: Context Validation and Updates

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

### Step 5: Analytics and Success Pattern Integration

**Load relevant analytics insights:**
- Review similar completed tasks for success patterns
- Check brainworm analytics for relevant performance data
- Note any workflow patterns that have proven effective
- Consider complexity estimates based on historical data

**Update analytics tracking:**
- Record task startup event with session correlation
- Associate current session with task progression
- Enable success pattern matching for discussion quality enhancement
- Initialize performance tracking for this task session

### Step 6: Plan the Work Session

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

### Step 7: Service Environment Preparation

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
- Confirm context matches current implementation state
- Verify no significant changes occurred during compaction
- Check that branch state matches task expectations

### After Team Handoff
**Additional steps:**
- Schedule knowledge transfer session if needed
- Review any informal notes or communications
- Understand decision rationale from previous developer
- Identify any concerns or potential issues noted

### After Extended Break
**Catch-up process:**
- Review related changes in codebase since last work
- Check for relevant team discussions or decisions
- Verify dependencies haven't changed significantly
- Test current implementation state matches expectations

## Common Startup Patterns

### Research-Heavy Tasks
For tasks requiring significant investigation:
1. Start with thorough context gathering
2. Plan multiple discussion sessions before implementation
3. Use analytics to estimate research vs implementation time
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

## Analytics-Driven Optimizations

### Session Timing
- Use analytics to identify optimal work session lengths for task types
- Consider historical patterns for discussion vs implementation time ratios
- Plan breaks and context preservation based on complexity estimates

### Success Factors
- Apply learned success patterns from similar historical tasks
- Avoid approaches that analytics show have high failure rates
- Use team performance patterns to optimize collaboration approaches

### Risk Mitigation
- Identify early warning signs of potential task difficulties
- Apply preventive measures for common failure patterns
- Set up monitoring for factors that correlate with task success

## Quality Checklist

Before beginning substantive work, verify:

**Task Understanding:**
- [ ] Task goals and success criteria are clear
- [ ] Context manifest provides adequate technical background
- [ ] Dependencies and integration points are mapped
- [ ] Current implementation state is understood

**Environment Setup:**
- [ ] Correct git branch checked out and current
- [ ] Development environment is functional
- [ ] All required services and dependencies are available
- [ ] DAIC state properly configured

**Analytics Integration:**
- [ ] Session correlation tracking is active
- [ ] Relevant success patterns have been reviewed
- [ ] Performance baselines established for comparison
- [ ] Risk factors identified and mitigation planned

**Work Planning:**
- [ ] Session goals are realistic and specific
- [ ] Discussion vs implementation balance planned
- [ ] Good stopping points identified
- [ ] Knowledge preservation strategy in place

## Remember

Effective task startup:
- Prevents wasted effort from insufficient context
- Leverages organizational learning for better outcomes
- Establishes proper workflow patterns from the beginning
- Enables smooth handoffs and continuations
- Contributes to continuous improvement through analytics

The investment in proper startup pays dividends throughout the task lifecycle and contributes to overall team effectiveness.