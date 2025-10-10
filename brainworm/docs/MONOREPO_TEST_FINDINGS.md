# Monorepo Test Findings

**Test Date**: 2025-10-08
**Test Project**: ~/repos/super-cool-project
**Test Task**: implement-custom-message-button

## Issue #1: Submodule Branch Management

### Observed Behavior

When a task is created that spans multiple submodules, the branch is only created in the main repository, not in the affected submodules.

**Task Configuration:**
```yaml
task: implement-custom-message-button
branch: feature/custom-message-button
submodule: none  # ← Should be "frontend" or "backend" or indicate multi-submodule
status: pending
modules: [frontend, backend]
```

**Actual Git State:**
```
Main repo:
  ✓ Branch: feature/implement-custom-message-button (created)

Frontend submodule:
  ✗ Branch: master (stayed on default)
  ✗ Changes: Modified src/pages/Home.tsx (uncommitted on master)

Backend submodule:
  ✗ Branch: master (stayed on default)
  ✗ Changes: New files + modifications (uncommitted on master)
```

**Expected Git State:**
```
Main repo:
  ✓ Branch: feature/implement-custom-message-button

Frontend submodule:
  ✓ Branch: feature/implement-custom-message-button
  ✓ Changes: Committed to feature branch

Backend submodule:
  ✓ Branch: feature/implement-custom-message-button
  ✓ Changes: Committed to feature branch
```

### Root Cause Analysis

**Location**: Task creation in `.brainworm/scripts/create_task.py` or task wrapper

**Problem**: The task creation system:
1. ✓ Recognizes multiple services: `task_services: ["frontend", "backend"]` in unified_session_state.json
2. ✓ Creates branch in main repo
3. ✗ Does NOT create corresponding branches in submodules
4. ✗ Does NOT switch submodules to feature branches before work begins

**State Tracking**:
```json
{
  "current_task": "implement-custom-message-button",
  "current_branch": "feature/implement-custom-message-button",
  "task_submodule": null,  // ← Should track which submodules are active
  "task_submodule_path": null,
  "task_services": ["frontend", "backend"]  // ← Knows about services
}
```

### Impact

1. **Developer Experience**: Changes made directly to submodules' default branches
2. **Code Review**: Can't PR submodule changes independently
3. **Branch Isolation**: Feature work not isolated in submodules
4. **Git History**: Confusing history with feature work on master
5. **Workflow Consistency**: Main repo has feature branch, submodules don't

### Evidence Files

**Submodule Status Files:**
- Frontend: `/Users/logansmith/repos/super-cool-project/frontend/` - on master with uncommitted changes
- Backend: `/Users/logansmith/repos/super-cool-project/backend/` - on master with uncommitted changes

**State Files:**
- `/Users/logansmith/repos/super-cool-project/.brainworm/state/unified_session_state.json`
- `/Users/logansmith/repos/super-cool-project/.brainworm/tasks/implement-custom-message-button/README.md`

**Git Evidence:**
```bash
# Main repo
$ cd /Users/logansmith/repos/super-cool-project && git branch
* feature/implement-custom-message-button
  master

# Frontend submodule
$ cd frontend && git branch
* master  # ← Should be on feature branch

# Backend submodule
$ cd backend && git branch
* master  # ← Should be on feature branch
```

### Recommended Solution

**Phase 1: Task Creation Enhancement**

Modify `create_task.py` to:
1. Detect when `modules` array contains submodule names
2. For each submodule in `modules`:
   ```bash
   cd <submodule_path>
   git checkout -b <branch_name>
   cd ../..
   ```
3. Update state tracking to include `active_submodule_branches: {frontend: "branch", backend: "branch"}`

**Phase 2: Git Submodule Manager Enhancement**

Enhance `src/hooks/templates/utils/git_submodule_manager.py`:
- Add `create_submodule_branch(submodule_path, branch_name)` method
- Add `get_submodule_current_branch(submodule_path)` method
- Add `ensure_submodule_on_branch(submodule_path, branch_name)` method

**Phase 3: Hook Integration**

Update hooks to be submodule-aware:
- `pre_tool_use.py`: Before write/edit operations, verify correct branch in submodule context
- `post_tool_use.py`: Track which submodules have been modified
- `session_end.py`: Ensure all submodule changes are committed to correct branches

**Phase 4: Task Completion Enhancement**

Modify task completion to:
1. Commit changes in each submodule's feature branch
2. Update main repo to point to new submodule commits
3. Commit main repo's submodule pointer updates

### Test Validation Needed

After implementing fixes:
1. Create new task with `modules: [frontend, backend]`
2. Verify branches created in both submodules
3. Make changes in both submodules
4. Verify changes committed to correct feature branches
5. Complete task and verify proper commit structure

### Related Test Scenarios

This finding validates **Test Scenario #9** from TEST_MONOREPO_PLAN.md:
- ✓ Issue identified: Branch only created in main repo
- ✓ Impact documented: Submodules stay on master
- ✗ Solution not yet implemented
- ✗ Not yet retested

### Additional Observations

**Task README Quality**: The context-gathering agent created an excellent, comprehensive README with:
- Complete understanding of the architecture
- Detailed integration patterns
- Specific implementation guidance
- This shows context gathering works well across submodules

**Agent Implementation**: The agent successfully:
- Created backend service and controller
- Modified frontend Home component
- Followed existing patterns correctly
- BUT committed to wrong branches

**State Tracking**: The unified state knows about:
- Multiple services: `task_services: ["frontend", "backend"]`
- But doesn't track submodule branches: `task_submodule: null`

## Issue #2: Task Submodule Field Ambiguity

### Problem

The task file shows `submodule: none` but `modules: [frontend, backend]`. This creates ambiguity:
- Is `submodule` meant for single-submodule tasks?
- Are `modules` just tags or do they drive behavior?
- Should multi-submodule tasks have special handling?

### Recommendation

Clarify the data model:
```yaml
task: task-name
branch: feature/task-name
primary_submodule: frontend  # Main focus
affected_services: [frontend, backend]  # All touched services
create_branches_in: [frontend, backend]  # Where to create feature branches
```

## Next Steps

1. **Immediate**: Document this finding (✓ Done)
2. **Short-term**: Implement git submodule manager enhancements
3. **Medium-term**: Update task creation workflow
4. **Long-term**: Add automated tests for monorepo git operations

## Session Data References

- **Analytics DB**: `/Users/logansmith/repos/super-cool-project/.brainworm/analytics/hooks.db`
- **Session Snapshots**: `/Users/logansmith/repos/super-cool-project/.brainworm/snapshots/`
- **State Files**: `/Users/logansmith/repos/super-cool-project/.brainworm/state/`

## Testing Context

This issue was discovered during systematic testing of brainworm's monorepo capabilities using the test project at `~/repos/super-cool-project`. The test environment successfully demonstrated:
- ✓ Brainworm installation in monorepo context
- ✓ Context gathering across submodules
- ✓ DAIC workflow enforcement
- ✓ Multi-service task creation
- ✗ Submodule branch management (this issue)

The test infrastructure is working as designed - it successfully identified a real gap in the workflow.
