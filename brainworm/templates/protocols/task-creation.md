# Task Creation Protocol

## Overview
This protocol guides the creation of structured, well-defined tasks in the DAIC-enhanced brainworm workflow system. Tasks are the fundamental unit of work, ensuring focused development with proper context preservation and event correlation.

## When to Use This Protocol
- User explicitly requests task creation
- A new feature or bug fix needs structured tracking
- Work scope is complex enough to warrant dedicated context
- Need to switch between different types of work
- Breaking work into smaller tasks improves focus and success rates

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
- "Are there any specific workflow tracking needs?"
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
- Initializes session correlation tracking for workflow continuity
- Runs in non-interactive mode for automation compatibility

**Verify creation:**
```bash
./tasks status    # Shows the newly created task as current
```

### Step 4: Customize Task Details

**Edit the generated task file** (`.brainworm/tasks/[task-name]/README.md`):
- Expand the task description with specific requirements
- Define detailed success criteria
- Add technical notes or constraints
- List integration points and dependencies
- Document any special considerations

**The wrapper already populated:**
- Basic metadata (task name, branch, date)
- Template structure
- Status tracking fields
- DAIC state in unified_session_state.json
- Event correlation tracking

### Step 5: Verify Task Creation

**Check task state:**
```bash
./tasks status     # Shows current task, branch, services
./daic status      # Verify DAIC mode (should be discussion)
```

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

**The agent will:**
- Read the task description and goals
- Research related code and systems
- Create detailed context manifest
- Update task file directly with findings

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

## Integration with Brainworm Event Storage

### Session Correlation
- Events are captured with task correlation from creation
- Session IDs link all work within this task
- Workflow continuity maintained across context boundaries

### Workflow Tracking
- DAIC mode transitions tracked for the task
- Tool usage and timing captured
- State changes preserved for session continuity

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
- Review similar past tasks for common dependency patterns
- Consider creating prerequisite tasks explicitly
- Track dependency resolution in work logs

### Cross-Service Tasks
For tasks affecting multiple services:
- List all affected services in task metadata
- Use context-gathering agent to map service interactions
- Create service-specific implementation notes
- Update relevant service CLAUDE.md files when complete

## Task Quality Indicators

Consider these factors for effective task creation:
- Clear scope definition and success criteria
- Comprehensive context from context-gathering agent
- Proper DAIC workflow adherence
- Well-defined service boundaries
- Appropriate task size and complexity

## Remember

Good task creation:
- Provides clear scope and success criteria
- Enables focused work with proper context
- Integrates with event storage for continuity
- Supports the DAIC workflow for better outcomes
- Creates institutional knowledge through task documentation

The effort invested in proper task creation pays dividends throughout the development process.

---

## Reference: Manual Task Creation

**Understanding how `./tasks create` works internally:**

The create command performs these operations:
1. Detects project structure (monorepo vs single-service)
2. Creates `.brainworm/tasks/[task-name]/` directory
3. Copies and customizes TEMPLATE.md with task metadata
4. Creates git branch with appropriate prefix (feature/, fix/, etc.)
5. Handles submodule-aware branching for monorepos
6. Updates unified_session_state.json via DAICStateManager
7. Initializes session correlation tracking for workflow continuity
8. Provides next steps guidance

**If wrapper is unavailable, manual process:**
1. Create directory: `mkdir -p .brainworm/tasks/[task-name]`
2. Copy template: `cp .brainworm/templates/TEMPLATE.md .brainworm/tasks/[task-name]/README.md`
3. Edit template with task details
4. Create branch: `git checkout -b feature/[task-name]`
5. Update state: `./tasks set --task=[task-name] --branch=feature/[task-name]`
6. Verify: `./tasks status`

**Note:** Manual process is time-consuming and error-prone. Use `./tasks create` whenever possible.
