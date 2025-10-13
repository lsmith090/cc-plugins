# Task Completion Protocol

## Overview
This protocol guides the proper completion and archiving of tasks in the DAIC-enhanced brainworm workflow system. Proper task completion ensures knowledge retention, analytics learning, and clean project state.

## When to Use This Protocol
- All success criteria have been met
- User explicitly requests task completion
- Task is no longer relevant or has been superseded
- Work has been deployed and verified successful
- Task has been blocked permanently and alternatives pursued

## Task Completion Process

### Step 1: Verify Completion Readiness

**Check Success Criteria:**
- Review each success criterion in the task file
- Verify all checkboxes can be honestly marked complete
- Ensure any testing requirements are met
- Confirm documentation updates are complete

**Code Quality Verification:**
- Use the code-review agent to review all changes
- Ensure all code follows established patterns
- Verify security and performance standards are met
- Check that error handling is appropriate

**Integration Testing:**
- Verify changes work in intended environment
- Test integration points with other services
- Confirm no regressions were introduced
- Validate with actual use cases where possible

### Step 2: Update Task File

**Mark Success Criteria Complete:**
```markdown
## Success Criteria
- [x] Feature implemented and tested
- [x] Integration with authentication service working
- [x] Error handling covers edge cases
- [x] Documentation updated
- [x] Code reviewed and approved
```

**Update Task Status:**
Change task status in metadata:
```markdown
**Status:** completed
**Completed:** [Date]
**Final Outcome:** [Brief description of what was accomplished]
```

### Step 3: Run Logging Agent

**Invoke logging agent for final cleanup:**
```
Use the logging agent to consolidate and clean up the work log for this completed task. 
Remove any redundant entries and provide a clear summary of what was accomplished.
Task file: .brainworm/tasks/[task-name]/README.md
```

**The logging agent will:**
- Consolidate all work entries into clean final log
- Remove outdated "Next Steps" (since task is complete)
- Clean up redundant or obsolete information
- Provide clear summary of accomplishments
- Archive temporary notes and debugging information

### Step 4: Service Documentation Updates

**Update relevant service documentation:**
- Use service-documentation agent to update CLAUDE.md files
- Document any new patterns or configurations discovered
- Add troubleshooting information for future developers
- Update API documentation if endpoints were modified

**Service updates should include:**
- New configuration patterns learned
- Integration patterns that worked well
- Performance characteristics discovered
- Security considerations found
- Common pitfalls and how to avoid them

### Step 5: Completion Documentation

**Record completion information:**
- Final task duration and outcome
- DAIC workflow adherence notes
- Key decisions and approach taken
- Blockers encountered and resolution strategies
- Code quality observations

**Document learnings:**
- Identify what made this task successful
- Note effective workflow patterns
- Document reusable approaches for similar future tasks
- Record collaboration patterns that worked well

### Step 6: Branch and Git Management

**Clean up development artifacts:**
```bash
# Ensure all changes are committed
git status

# Switch back to main branch
git checkout main

# Optional: Delete feature branch if work is merged
git branch -d feature/[task-name]

# Optional: Delete remote branch if appropriate
git push origin --delete feature/[task-name]
```

**Verify deployment status:**
- Confirm changes are deployed to appropriate environments
- Verify monitoring and logging are capturing expected metrics
- Check that feature flags are configured correctly if applicable

### Step 7: Task State Cleanup

**Use wrappers to clean up state:**
```bash
./tasks clear         # Clears current task from state
./daic discussion     # Reset to discussion mode for next task
```

**Verify clean state:**
```bash
./tasks status    # Should show "No active task"
./daic status     # Should show "Discussion mode"
```

**Archive task artifacts:**
- Task file remains in `.brainworm/tasks/[task-name]/` for reference
- Event correlation data is preserved automatically
- Branch cleanup is optional (keep for reference or delete)

### Step 8: Team Communication

**Communicate completion:**
- Notify relevant team members of completion
- Share key learnings or insights discovered
- Update project tracking systems (Jira, GitHub issues, etc.)
- Document any follow-up tasks that were identified

## Completion Outcomes

### Successful Completion
**Status:** `completed-success`
- All success criteria met
- Code reviewed and merged
- Documentation updated
- No known issues or technical debt introduced

### Partial Completion
**Status:** `completed-partial`
- Core functionality complete but some criteria unmet
- Acceptable tradeoffs were made
- Document what was deferred and why
- Create follow-up tasks for unmet criteria

### Abandoned/Superseded
**Status:** `completed-abandoned`
- Task no longer relevant due to changing requirements
- Alternative approach was chosen
- Document why task was abandoned for future reference
- Preserve learnings even if work wasn't used

### Blocked/Deferred
**Status:** `completed-blocked`
- External dependencies prevent completion
- Technical blockers cannot be resolved currently
- Document blocking factors and potential future approaches
- Create monitoring tasks for when blockers are resolved

## Knowledge Retention

### Document Key Learnings
**Technical Insights:**
- Architectural patterns that worked well
- Performance optimizations discovered
- Integration challenges and solutions
- Testing strategies that were effective

**Process Insights:**
- DAIC workflow effectiveness for this task type
- Communication patterns that helped
- Tools or techniques that improved productivity
- Time estimation accuracy and adjustment factors

### Create Reference Materials
**For Future Similar Tasks:**
- Template code or configurations
- Testing approaches and data sets
- Integration patterns and examples
- Common pitfalls and avoidance strategies

**For Team Knowledge:**
- Update team documentation with new patterns
- Share reusable components or utilities created
- Document process improvements discovered
- Update coding standards if new patterns emerged

## Event Storage Integration

### Session Correlation
- Task completion events are captured with full context
- Session IDs link all work within the completed task
- Workflow data preserved for future reference

### Knowledge Preservation
- Task documentation remains accessible
- Work logs provide chronological record
- Context files enable understanding of decisions made
- Event data maintains workflow continuity records

## Quality Checklist

Before marking a task complete, verify:

**Technical Quality:**
- [ ] All code follows established patterns and standards
- [ ] Security review completed (use code-review agent)
- [ ] Performance impact assessed and acceptable
- [ ] Error handling covers identified edge cases
- [ ] Integration points tested and documented

**Documentation Quality:**
- [ ] README or service documentation updated
- [ ] API documentation reflects changes
- [ ] Configuration examples are current
- [ ] Troubleshooting information added

**Process Quality:**
- [ ] Success criteria honestly assessed
- [ ] Work log provides clear record of accomplishments
- [ ] Analytics data captured for learning
- [ ] Follow-up tasks identified and created
- [ ] Team communication completed

## Remember

Proper task completion:
- Ensures institutional knowledge is retained
- Provides documentation for future reference
- Maintains clean project state for future work
- Creates foundation for similar future work
- Demonstrates professional development practices

The completion process is as important as the implementation - it's where individual work becomes team knowledge through thorough documentation.

---

## Reference: State Management

**Understanding how `./tasks clear` works:**

The clear command:
1. Reads current unified_session_state.json
2. Clears current_task field
3. Preserves session and correlation IDs for analytics
4. Maintains task completion metadata
5. Returns success confirmation

**Manual alternative** (if wrapper unavailable):
```bash
# Update state file directly (not recommended)
./tasks set --task="" --branch="" --services=""
```

**Understanding how `./daic discussion` works:**

The mode command:
1. Updates DAIC mode in unified_session_state.json
2. Triggers statusline update
3. Resets tool blocking rules
4. Preserves all other state

**Note:** Wrappers ensure atomic state updates. Manual JSON editing can cause inconsistencies.