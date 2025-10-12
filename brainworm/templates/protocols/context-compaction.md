# Context Compaction Protocol

## Overview
This protocol manages context window limits in the DAIC-enhanced brainworm workflow system. When the context approaches capacity, this protocol ensures work continuity while preserving institutional knowledge and task progress.

## When to Use This Protocol
- Context window reaches 75% capacity (warning threshold)
- Context window reaches 90% capacity (urgent threshold)
- User explicitly requests context compaction
- Before switching to a different major task or focus area
- At natural breakpoints in complex work sessions

## Context Compaction Process

### Step 1: Assess Current State

**Check context usage:**
- Current token count and percentage of limit
- Identify largest contributors to context usage
- Assess what information is still actively needed

**Evaluate work progress:**
- Review current task status and what's been accomplished
- Identify natural stopping points in current work
- Assess if current work can be cleanly paused

**Check DAIC state:**
- Current mode (discussion vs implementation)
- Any pending decisions or alignments needed
- Implementation work that's partially complete

### Step 2: Preserve Critical Context

**Use logging agent to consolidate work progress:**
```
Use the logging agent to consolidate and clean up the work log for the current task, 
removing redundant information while preserving important progress and decisions.
Task file: .brainworm/tasks/[current-task-name]/README.md
```

**Use context-refinement agent for ongoing tasks:**
```
Use the context-refinement agent to update the task context with any new discoveries 
or insights from this work session before compaction.
Task file: .brainworm/tasks/[current-task-name]/README.md
```

**Document current implementation state:**
- What's partially complete and in what state
- Any temporary code or configurations that need explanation
- Decisions made that aren't yet reflected in code
- Next immediate steps to continue work

### Step 3: Verify Current State

**Check DAIC mode before compaction:**
```bash
./daic status    # Note current mode and task
./tasks status   # Verify task state
```

**State is automatically preserved:**
- Session correlation continues across compaction
- Analytics data is maintained automatically
- Task association persists in unified_session_state.json
- No manual state updates needed

### Step 4: Knowledge Extraction and Storage

**Extract key insights:**
- Technical discoveries not yet documented
- Successful approaches worth replicating
- Problems encountered and solutions found
- Integration insights or architectural learnings

**Update service documentation if significant discoveries:**
```
Use the service-documentation agent to update relevant CLAUDE.md files 
with any significant patterns or insights discovered during this session.
```

**Create continuation notes:**
```markdown
## Context Compaction Notes - [Date]

### Work Session Summary
[Brief overview of what was accomplished]

### Current Implementation State
- **Files modified:** [List of changed files and their state]
- **Partial work:** [Description of any incomplete implementations]
- **Temporary changes:** [Any debugging code or temporary modifications]

### Immediate Next Steps
1. [First thing to do when resuming]
2. [Second priority item]
3. [Third priority item]

### Key Decisions Made
- [Decision 1]: [Rationale]
- [Decision 2]: [Rationale]

### Analytics Insights
- **Session effectiveness:** [DAIC workflow patterns observed]
- **Success factors:** [What worked well this session]
- **Risk factors:** [Potential issues to watch for]

### Context for Resumption
[Any information that will be important when work resumes]
```

### Step 5: Coordinate Transition

**If switching tasks after compaction:**
```bash
./tasks switch [new-task-name]    # Atomic task switch
./daic discussion                  # Reset to discussion mode
```

**If continuing same task:**
- Ensure task file contains all necessary context for resumption
- Verify implementation state is clearly documented
- Check that analytics correlation will continue properly
- Current task remains active in state automatically

**Manage DAIC mode for resumption:**
```bash
./daic discussion       # If resuming needs planning
./daic implementation   # If continuing focused work
./daic status           # Verify mode is correct
```

### Step 6: Final Validation

**Review compaction completeness:**
- Task file contains complete current context
- Work progress is accurately documented
- Implementation state is clearly described
- Next steps are specific and actionable

**Verify continuity preparation:**
- Someone else could pick up this work from the documentation
- No critical information exists only in current context
- Analytics tracking will resume correctly
- Branch and development environment state is documented

## Compaction Quality Levels

### Minimal Compaction (75% threshold)
**Focus on:** Removing redundant conversation, preserving core context
- Clean up repetitive discussions
- Consolidate similar technical explanations
- Remove debugging artifacts from context
- Keep all current task context intact

### Standard Compaction (85% threshold)
**Focus on:** Significant context reduction while preserving work continuity
- Run logging agent to consolidate work progress
- Update task context with session discoveries
- Preserve only actively relevant technical context
- Document current state thoroughly for resumption

### Deep Compaction (95% threshold)
**Focus on:** Maximum context reduction, full work preservation
- Complete logging agent cleanup
- Run context refinement to update task understanding
- Update service documentation with discoveries
- Create comprehensive resumption notes
- Preserve only essential context for immediate continuation

## Resumption After Compaction

### Automatic Context Loading
**When resuming work:**
- Current task file should provide complete context
- Analytics correlation should continue seamlessly
- DAIC state should reflect actual work status
- Development environment state should be documented

### Validation Steps
**Check that compaction was effective:**
- Task context contains all necessary information
- Work progress accurately reflects current state
- Next steps are clear and actionable
- No critical information was lost

## Analytics Integration Benefits

### Session Continuity Tracking
- Measure effectiveness of compaction strategies
- Track work continuity across context boundaries
- Identify optimal compaction timing patterns
- Analyze impact on task completion success rates

### Context Quality Metrics
- Monitor how well compacted context supports work resumption
- Track correlation between context quality and subsequent productivity
- Identify patterns in context usage that predict compaction needs
- Optimize context preservation strategies based on outcomes

### Workflow Pattern Learning
- Analyze DAIC workflow effectiveness across compaction boundaries
- Learn optimal break points for different types of work
- Identify context preservation strategies that work best for each task type
- Develop predictive models for compaction timing

## Common Compaction Scenarios

### Mid-Implementation Compaction
**Special considerations:**
- Document exact state of partial implementations
- Preserve temporary debugging code explanations
- Note any assumptions made that aren't yet codified
- Ensure branch state and uncommitted changes are documented

### Research-Heavy Task Compaction
**Focus areas:**
- Consolidate research findings into actionable insights
- Update context manifest with new understanding
- Preserve investigation approaches that were effective
- Document research dead-ends to avoid repetition

### Multi-Service Integration Compaction
**Key elements:**
- Document current state of each service involved
- Preserve integration testing approaches and results
- Note any coordination needed with other teams
- Update service documentation with integration insights

## Emergency Compaction

### Context Window Full (99%+)
**Immediate actions:**
1. Save current work state immediately
2. Run minimal logging agent cleanup
3. Document critical next steps in task file
4. Clear context and reload task context only
5. Resume work with reduced context

**Recovery steps:**
- Verify task continuity after emergency compaction
- Check for any lost context that needs reconstruction
- Update compaction protocols to prevent similar situations

## Remember

Effective context compaction:
- Preserves work continuity without losing institutional knowledge
- Leverages analytics for continuous improvement of compaction strategies
- Maintains DAIC workflow effectiveness across context boundaries
- Enables seamless work resumption with full context preservation
- Contributes to organizational learning about optimal work patterns

Context compaction is not just about managing technical limitations - it's an opportunity to consolidate learning and improve future work effectiveness.

---

## Reference: State Management During Compaction

**What wrappers preserve automatically:**

State files remain intact across compaction:
- `unified_session_state.json` preserves task, branch, services
- Session and correlation IDs persist
- DAIC mode settings maintained
- Analytics tracking continues seamlessly

**Manual state inspection** (for understanding):
```bash
# View current state
cat .brainworm/state/unified_session_state.json | jq

# Check task status
./tasks status

# Verify DAIC mode
./daic status
```

**Note:** Compaction is a context window operation, not a state operation. State persists automatically.