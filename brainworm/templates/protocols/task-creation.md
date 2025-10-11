# Task Creation Protocol

## Overview
This protocol guides the creation of structured, well-defined tasks in the DAIC-enhanced brainworm workflow system. Tasks are the fundamental unit of work, ensuring focused development with proper context preservation and analytics integration.

## When to Use This Protocol
- User explicitly requests task creation
- A new feature or bug fix needs structured tracking
- Work scope is complex enough to warrant dedicated context
- Need to switch between different types of work
- Analytics suggest breaking work into smaller tasks for better success rates

## Task Creation Process

### Step 1: Understand the Request
**Clarify the scope:**
- What exactly needs to be built/fixed/improved?
- What are the success criteria?
- What's the expected timeline/priority?
- Are there dependencies on other work?
- What services or components are involved?

**Ask clarifying questions if needed:**
- "Should this include testing and documentation?"
- "Are there specific performance requirements?"
- "Should this integrate with existing analytics tracking?"
- "What's the priority level for this work?"

### Step 2: Determine Task Type and Naming
**Task Types:**
- `implement-[feature-name]` - New features or capabilities
- `fix-[issue-description]` - Bug fixes or error resolution
- `refactor-[component-name]` - Code improvement without feature changes
- `migrate-[system-change]` - Data or system migrations
- `test-[scope]` - Testing infrastructure or coverage improvements
- `docs-[area]` - Documentation updates or creation

**Naming Convention:**
- Use lowercase with hyphens
- Be descriptive but concise
- Include the main component/area affected
- Examples: `implement-user-authentication`, `fix-payment-webhook-failures`, `refactor-database-connections`

### Step 3: Create Task with Automated Wrapper

**Use the tasks wrapper for automated task creation:**
```bash
# Basic task creation
./tasks create [task-name]

# With explicit submodule
./tasks create [task-name] --submodule=your-submodule

# With affected services
./tasks create [task-name] --services=service1,service2
```

**The wrapper automatically:**
- Creates task directory structure (`.brainworm/tasks/[task-name]/`)
- Populates README.md from template with task name and metadata
- Creates appropriate git branch (`feature/`, `fix/`, `refactor/`, etc.)
- Handles submodule-aware branch creation for super-repo projects
- Updates DAIC state with task, branch, and service information
- Initializes analytics correlation tracking
- Runs in non-interactive mode for automation compatibility

**Manual fallback (if wrapper unavailable):**
```bash
# Create directory
mkdir -p .brainworm/tasks/[task-name]

# Copy and customize template
cp .brainworm/templates/TEMPLATE.md .brainworm/tasks/[task-name]/README.md

# Then manually update the template with:
# - Task name and description
# - Priority and status
# - Success criteria
# - Affected services/components
```

### Step 4: Customize Task Details

**Edit the generated task file** (`.brainworm/tasks/[task-name]/README.md`):
- Expand the task description with specific requirements
- Define detailed success criteria
- Add technical notes or constraints
- List integration points and dependencies
- Document any special considerations

### Step 5: Configure DAIC State

**If using manual method, update DAIC state:**
```json
{
  "current_task": "[task-name]",
  "current_branch": "[feature/fix/refactor]/[task-name]",
  "task_services": ["service1", "service2"],
  "updated": "[current-date]",
  "correlation_id": "[generated-correlation-id]",
  "session_id": "[current-session-id]"
}
```

**Note:** The automated wrapper handles this automatically.

**Verify DAIC mode:**
- Tasks start in discussion mode by default
- This ensures proper planning before implementation
- Use trigger phrases to switch to implementation mode when ready

### Step 6: Invoke Context-Gathering Agent
**Use the context-gathering agent to:**
- Research all relevant components and dependencies
- Create a comprehensive context manifest
- Document current system state and patterns
- Identify integration points and requirements

**Agent invocation:**
```
Use the context-gathering agent to analyze the requirements for [task-name] 
and create a comprehensive context manifest. The task file is at .brainworm/tasks/[task-name]/README.md
```

### Step 7: Verify Branch Setup

**Check branch creation:**
```bash
git branch --show-current  # Should show your new task branch
./daic status              # Verify task and branch are registered
```

**If using manual method:**
- Create branch: `git checkout -b [feature/fix/refactor]/[task-name]`
- Branch naming should match task naming convention
- Use prefixes: `feature/`, `fix/`, `refactor/`, etc.
- Ensure branch name matches what's in task state

**Note:** The automated wrapper handles branch creation automatically, including submodule-aware branching for super-repo projects.

### Step 8: Verify Analytics Integration

**The automated wrapper initializes:**
- Task creation event in brainworm analytics
- Association with current session and correlation ID
- Task type and complexity estimates
- Success pattern matching for similar tasks

**Manual verification:**
```bash
uv run .brainworm/hooks/view_analytics.py  # Check task is tracked
```

## Task Priority Guidelines

### High Priority (`h-[task-name]`)
- Critical bugs affecting users
- Security vulnerabilities
- Blocking other work
- Production issues

### Medium Priority (`m-[task-name]`)
- New features
- Performance improvements
- Non-critical bug fixes
- Developer experience improvements

### Low Priority (`l-[task-name]`)
- Nice-to-have features
- Code cleanup without functional changes
- Documentation improvements
- Future considerations

### Investigation Priority (`?-[task-name]`)
- Research tasks
- Proof of concepts
- Feasibility studies
- Technical spikes

## Integration with Brainworm Analytics

### Success Pattern Recognition
- Analyze similar completed tasks for success patterns
- Use analytics to estimate task complexity and duration
- Identify common pitfalls from historical data
- Suggest optimal team member assignments based on past performance

### Workflow Optimization
- Track DAIC transition effectiveness for task types
- Monitor discussion-to-implementation timing patterns
- Identify optimal task breakdown sizes
- Measure correlation between task structure and success rates

### Predictive Insights
- Predict task completion likelihood based on initial structure
- Suggest additional context gathering for complex tasks
- Recommend task splitting when complexity indicators are high
- Alert to potential blockers based on similar historical tasks

## Common Patterns

### Breaking Down Large Tasks
If a task feels too large:
- Split into multiple related tasks
- Create a parent task for coordination
- Use consistent naming: `parent-task`, `parent-task-part1`, `parent-task-part2`
- Link tasks in descriptions for context

### Handling Dependencies
When tasks have dependencies:
- Document dependencies clearly in task description
- Use analytics to identify common dependency patterns
- Consider creating prerequisite tasks explicitly
- Track dependency resolution in work logs

### Cross-Service Tasks
For tasks affecting multiple services:
- List all affected services in task metadata
- Use context-gathering agent to map service interactions
- Create service-specific implementation notes
- Update relevant service CLAUDE.md files when complete

## Success Metrics

Track these metrics for task creation effectiveness:
- Time from task creation to first implementation
- Success rate of tasks with comprehensive context vs. minimal context
- DAIC workflow effectiveness (discussion quality vs. implementation success)
- Task completion rate by priority level
- Correlation between task structure quality and outcome

## Remember

Good task creation:
- Provides clear scope and success criteria
- Enables focused work with proper context
- Integrates with analytics for continuous improvement
- Supports the DAIC workflow for better outcomes
- Creates institutional knowledge for future similar work

The effort invested in proper task creation pays dividends throughout the development process.