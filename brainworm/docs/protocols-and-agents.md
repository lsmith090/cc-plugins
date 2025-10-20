# Protocols & Agents

Brainworm provides structured workflows (protocols) and specialized subagents to handle complex development tasks.

## Table of Contents

- [Overview](#overview)
- [Protocols](#protocols)
  - [Task Creation](#task-creation-protocol)
  - [Task Startup](#task-startup-protocol)
  - [Task Completion](#task-completion-protocol)
  - [Context Compaction](#context-compaction-protocol)
- [Agents](#agents)
  - [Context-Gathering](#context-gathering-agent)
  - [Code Review](#code-review-agent)
  - [Logging](#logging-agent)
  - [Context Refinement](#context-refinement-agent)
  - [Service Documentation](#service-documentation-agent)
  - [Session Docs](#session-docs-agent)
- [Best Practices](#best-practices)

## Overview

**Protocols** are structured workflows for common development operations. They provide step-by-step guidance for tasks like creating new work items, completing tasks, and managing context limits.

**Agents** are specialized subagents with dedicated tool access and focused expertise. Each agent operates in its own context window and returns structured results.

## Protocols

Protocols guide you through complex workflows with clear steps and decision points.

### Task Creation Protocol

**Purpose:** Create structured, well-defined tasks with proper context and tracking.

**When to Use:**
- User explicitly requests task creation
- New feature or bug fix needs structured tracking
- Work scope is complex enough to warrant dedicated context
- Breaking work into smaller tasks improves focus

**Key Steps:**

1. **Understand the Request**
   - Clarify scope, success criteria, timeline
   - Identify dependencies and affected services

2. **Determine Task Type and Naming**
   ```bash
   # Task types determine branch prefix
   implement-[feature]    → feature/...
   fix-[issue]           → fix/...
   refactor-[component]  → refactor/...
   test-[scope]          → test/...
   docs-[area]           → docs/...
   ```

3. **Create Task with Wrapper**
   ```bash
   ./tasks create implement-user-auth
   ./tasks create fix-payment-bug --services=backend,database
   ```

   **The wrapper automatically:**
   - Creates task directory structure
   - Populates README.md from template
   - Creates appropriate git branch
   - Updates DAIC state
   - Initializes session correlation

4. **Customize Task Details**
   - Edit `.brainworm/tasks/[task-name]/README.md`
   - Expand description with requirements
   - Define detailed success criteria
   - Add technical notes and constraints

5. **Verify Task Creation**
   ```bash
   ./tasks status    # Check current task
   ./daic status     # Verify DAIC mode (should be discussion)
   ```

6. **Invoke Context-Gathering Agent**
   ```
   Use the context-gathering agent to analyze requirements for [task-name]
   and create a comprehensive context manifest. The task file is at
   .brainworm/tasks/[task-name]/README.md
   ```

**See Also:** [Task Management](task-management.md#creating-tasks)

### Task Startup Protocol

**Purpose:** Properly start or resume work on tasks with full context.

**When to Use:**
- Beginning work on a new task
- Resuming work after interruption
- Switching between different tasks
- After context compaction when continuing task work

**Key Steps:**

1. **Find and Switch to Task**
   ```bash
   ./tasks list                  # See all tasks
   ./tasks switch [task-name]    # Switch atomically
   ```

   **The wrapper automatically:**
   - Checks out task's git branch
   - Updates DAIC state
   - Warns if context manifest missing

2. **Review Task Context**
   - Read task file thoroughly
   - Understand goals and success criteria
   - Review Context Manifest section
   - Check Work Log for recent progress

3. **Context Validation**

   **If context missing or incomplete:**
   ```
   Use the context-gathering agent to create/update the context manifest
   for [task-name]. Task file: .brainworm/tasks/[task-name]/README.md
   ```

   **If context exists but outdated:**
   - Verify integration points are accurate
   - Check for configuration or API changes

4. **Verify DAIC Mode**
   ```bash
   ./daic status
   ```
   - Start in discussion mode for planning
   - Use trigger phrases when ready for implementation

5. **Plan the Work Session**
   - Define session goals
   - Identify discussion vs implementation priorities
   - Plan knowledge preservation for future sessions

6. **Environment Preparation**
   - Verify local development environment works
   - Check dependencies are available
   - Confirm test suite passes before changes

**Resumption Scenarios:**

**After Context Compaction:**
- Task file should have comprehensive context
- Work log should be clean and current
- Next steps clearly defined

**After Extended Break:**
- Review related codebase changes
- Check for team discussions or decisions
- Test current implementation state

**See Also:** [Task Management](task-management.md#switching-tasks)

### Task Completion Protocol

**Purpose:** Properly complete tasks while ensuring knowledge retention.

**When to Use:**
- All success criteria have been met
- User explicitly requests task completion
- Task has been blocked permanently and alternatives pursued

**Key Steps:**

1. **Verify Completion Readiness**
   - Review each success criterion in task file
   - Verify all checkboxes can be marked complete
   - Ensure testing requirements are met
   - Confirm documentation updates complete

2. **Code Quality Verification**
   ```
   Use the code-review agent to review all changes. Files modified:
   [list files and line ranges]. Task file: .brainworm/tasks/[task]/README.md
   ```

3. **Update Task File**
   - Mark all success criteria complete
   - Update task status to "completed"
   - Add completion date and outcome

4. **Run Logging Agent**
   ```
   Use the logging agent to consolidate and clean up the work log for this
   completed task. Remove redundant entries and provide clear summary.
   Task file: .brainworm/tasks/[task-name]/README.md
   ```

   **The logging agent will:**
   - Consolidate all work entries
   - Remove outdated "Next Steps"
   - Clean up redundant information
   - Provide clear summary of accomplishments

5. **Service Documentation Updates**
   ```
   Use the service-documentation agent to update relevant CLAUDE.md files
   with patterns and configurations discovered during this task.
   ```

   **Service updates should include:**
   - New configuration patterns learned
   - Integration patterns that worked well
   - Performance characteristics discovered
   - Common pitfalls and how to avoid them

6. **Branch and Git Management**
   ```bash
   git status                    # Ensure all changes committed
   git checkout main             # Switch back to main
   git branch -d feature/[task]  # Optional: delete branch if merged
   ```

7. **Task State Cleanup**
   ```bash
   ./tasks clear        # Clear current task from state
   ./daic discussion    # Reset to discussion mode
   ```

   **Verify clean state:**
   ```bash
   ./tasks status    # Should show "No active task"
   ./daic status     # Should show "Discussion mode"
   ```

**Completion Outcomes:**

- **Successful:** All criteria met, code merged, docs updated
- **Partial:** Core complete but some criteria deferred (create follow-ups)
- **Abandoned:** No longer relevant (document why for future reference)
- **Blocked:** External dependencies prevent completion (document blockers)

**See Also:** [Task Management](task-management.md#completing-tasks)

### Context Compaction Protocol

**Purpose:** Manage context window limits while preserving work continuity.

**When to Use:**
- Context window reaches 75% capacity (warning threshold)
- Context window reaches 90% capacity (urgent threshold)
- User explicitly requests context compaction
- At natural breakpoints in complex work sessions

**Key Steps:**

1. **Assess Current State**
   - Check context usage (token count and percentage)
   - Review current task status and accomplishments
   - Assess what information is still actively needed

2. **Preserve Critical Context**

   **Use logging agent to consolidate work:**
   ```
   Use the logging agent to consolidate and clean up the work log for the
   current task, removing redundant information while preserving important
   progress and decisions. Task file: .brainworm/tasks/[task]/README.md
   ```

   **Use context-refinement agent for ongoing tasks:**
   ```
   Use the context-refinement agent to update the task context with any
   new discoveries or insights from this work session before compaction.
   Task file: .brainworm/tasks/[task]/README.md
   ```

   **Document current implementation state:**
   - What's partially complete and in what state
   - Any temporary code or configurations
   - Decisions made not yet reflected in code
   - Next immediate steps to continue work

3. **Verify Current State**
   ```bash
   ./daic status     # Note current mode and task
   ./tasks status    # Verify task state
   ```

   **State is automatically preserved:**
   - Session correlation continues across compaction
   - Event data maintained automatically
   - Task association persists in unified state
   - No manual state updates needed

4. **Knowledge Extraction and Storage**

   **Extract key insights:**
   - Technical discoveries not yet documented
   - Successful approaches worth replicating
   - Problems encountered and solutions found

   **Update service documentation if significant discoveries:**
   ```
   Use the service-documentation agent to update relevant CLAUDE.md files
   with any significant patterns or insights discovered during this session.
   ```

   **Create continuation notes in task file:**
   - Work session summary
   - Current implementation state
   - Immediate next steps
   - Key decisions made

5. **Coordinate Transition**

   **If switching tasks after compaction:**
   ```bash
   ./tasks switch [new-task-name]
   ./daic discussion
   ```

   **If continuing same task:**
   - Ensure task file contains all necessary context
   - Verify implementation state clearly documented
   - Current task remains active automatically

   **Manage DAIC mode for resumption:**
   ```bash
   ./daic discussion      # If resuming needs planning
   ./daic implementation  # If continuing focused work
   ```

6. **Final Validation**
   - Task file contains complete current context
   - Work progress accurately documented
   - Implementation state clearly described
   - Next steps specific and actionable

**Compaction Quality Levels:**

- **Minimal (75%):** Remove redundant conversation, preserve core context
- **Standard (85%):** Run agents, preserve actively relevant context only
- **Deep (95%):** Complete cleanup, comprehensive resumption notes

**See Also:** [DAIC Workflow](daic-workflow.md#advanced-topics)

## Agents

Agents are specialized subagents with focused expertise. Each operates in its own context window.

### Context-Gathering Agent

**Purpose:** Create comprehensive context manifests for tasks.

**When to Use:**
- Creating a new task
- Starting/switching to a task that lacks context manifest
- Skip if task file already contains "Context Manifest" section

**Available Tools:** Read, Glob, Grep, LS, Bash, Edit, MultiEdit

**What It Does:**

1. **Understands the Task**
   - Reads entire task file
   - Identifies all components that will be involved
   - Includes anything tangentially relevant

2. **Researches Everything**
   - Every component/module that will be touched
   - Components that communicate with those components
   - Configuration files and environment variables
   - Database models and access patterns
   - Authentication and authorization flows
   - Error handling patterns
   - Existing similar implementations

3. **Writes Narrative Context Manifest**
   - Verbose, comprehensive paragraphs
   - Explains how things currently work
   - Details what needs to connect for new features
   - Provides technical reference section

**Output Format:**

The agent adds a "Context Manifest" section to the task file with:

```markdown
## Context Manifest

### How This Currently Works: [System Name]
[VERBOSE NARRATIVE explaining full flow step-by-step]

### For New Feature Implementation: [What Needs to Connect]
[How new feature integrates with existing system]

### Technical Reference Details
- Component interfaces & signatures
- Data structures
- Configuration requirements
- File locations
```

**Usage Example:**
```
Use the context-gathering agent to analyze requirements for implement-user-auth
and create a comprehensive context manifest. The task file is at
.brainworm/tasks/implement-user-auth/README.md
```

**Key Principle:** Better to over-include context than miss something critical.

**See Also:** [Task Management](task-management.md#task-file-structure)

### Code Review Agent

**Purpose:** Review code for security vulnerabilities, bugs, performance issues, and consistency.

**When to Use:**
- Explicitly requested by user
- Invoked by a protocol (e.g., task completion)
- DO NOT use proactively

**Available Tools:** Read, Grep, Glob, Bash (read-only)

**What It Does:**

1. **Gets Changes**
   ```bash
   git diff HEAD
   ```

2. **Understands Existing Patterns**
   - How existing code handles similar problems
   - What conventions are established
   - Project's current approach

3. **Review Focus**
   - Does it work correctly?
   - Is it secure?
   - Does it handle errors?
   - Is it consistent with existing code?

**Review Checklist:**

**🔴 Critical (Blocks Deployment):**
- **Security:** Exposed secrets, injection vulnerabilities, XSS, path traversal
- **Correctness:** Logic errors, missing error handling, race conditions, data corruption

**🟡 Warning (Should Address):**
- **Reliability:** Unhandled edge cases, resource leaks, missing timeouts
- **Performance:** N+1 queries, unbounded memory growth, blocking I/O
- **Inconsistency:** Deviates from established patterns

**🟢 Notes (Optional):**
- Alternative approaches used elsewhere
- Documentation that might help
- Test cases worth adding

**Output Format:**

```markdown
# Code Review: [Brief Description]

## Summary
[Does it work? Is it safe? Any major concerns?]

## 🔴 Critical Issues (0)
None found.

## 🟡 Warnings (2)
### 1. Unhandled Network Error
**File**: `path/to/file:45-52`
**Issue**: Network call can fail but error not handled
**Impact**: Application crashes when service unavailable
**Existing Pattern**: See similar handling in `other/file:30-40`

## 🟢 Notes (1)
### 1. Different Approach Than Existing Code
**Note**: Uses approach X while similar code uses Y
```

**Usage Example:**
```
Use the code-review agent to review all changes. Files modified:
- backend/auth.py:45-120
- backend/models/user.py:30-80
Task file: .brainworm/tasks/implement-user-auth/README.md
```

**Key Principles:**
- Focus on what matters (correctness, security, reliability)
- Respect existing choices (follow project patterns)
- Be specific (exact lines, concrete fixes)

### Logging Agent

**Purpose:** Consolidate and organize work logs into task's Work Log section.

**When to Use:**
- During context compaction
- At task completion
- Do NOT use proactively during normal work

**Available Tools:** Read, Edit, MultiEdit, Bash, Grep, Glob

**What It Does:**

1. **Reads the entire target file** before making changes
2. **Reads full conversation transcript** to understand what was accomplished
3. **Assesses what needs cleanup:**
   - Outdated information no longer applicable
   - Redundant entries across sections
   - Completed items still listed as pending
   - Obsolete context that's been superseded
4. **Removes irrelevant content:**
   - Outdated Next Steps
   - Obsolete Context Manifest entries
   - Redundant work log entries
5. **Updates existing content:**
   - Success Criteria checkboxes
   - Next Steps to reflect current reality
6. **Adds new content:**
   - New work completed in this session
   - Important decisions and discoveries

**Work Log Format:**

```markdown
## Work Log

### [Date]

#### Completed
- Implemented X feature
- Fixed Y bug

#### Decisions
- Chose approach A because B

#### Discovered
- Issue with E component

#### Next Steps
- Continue with G
```

**Rules for Clean Logs:**
1. **Cleanup First:** Remove completed Next Steps, delete obsolete context
2. **Chronological Integrity:** Never place entries out of order
3. **Consolidation:** Merge small updates, remove redundancy
4. **Clarity:** Use consistent terminology, reference specific files
5. **Scope:** Update ALL sections for relevance and accuracy

**Usage Example:**
```
Use the logging agent to consolidate and clean up the work log for the
completed task, removing redundant information while preserving important
progress and decisions. Task file: .brainworm/tasks/[task]/README.md
```

**Remember:** Leave the task file cleaner than you found it. Show what's been accomplished, what's currently true, and what needs to happen next.

### Context Refinement Agent

**Purpose:** Update task context with discoveries from current work session.

**When to Use:**
- At end of context window (if task continuing)
- Only updates if drift or new discoveries found

**Available Tools:** Read, Edit, MultiEdit, LS, Glob

**What It Does:**

1. **Reads transcript files** to understand work session
2. **Analyzes for drift or discoveries:**
   - Component behavior different than documented
   - Gotchas not originally documented
   - Hidden dependencies revealed
   - Wrong assumptions in original context
   - Unexpected error handling requirements
3. **Decision point:**
   - NO significant discoveries → Report "No updates needed"
   - Discoveries found → Append to Context Manifest

**Update Format:**

```markdown
### Discovered During Implementation
[Date: YYYY-MM-DD]

During implementation, we discovered that [what was found]. This wasn't
documented in the original context because [reason]. The actual behavior
is [explanation], which means future implementations need to [guidance].

#### Updated Technical Details
- [New signatures/endpoints/patterns discovered]
- [Updated understanding of data flows]
- [Corrected assumptions]
```

**What Qualifies as Worth Updating:**

**YES - Update for these:**
- Undocumented component interactions
- Incorrect assumptions about how something works
- Missing configuration requirements
- Hidden side effects or dependencies
- Complex error cases not documented
- Performance constraints discovered
- Security requirements found

**NO - Don't update for these:**
- Minor typos or clarifications
- Things that were implied but not explicit
- Standard debugging discoveries
- Temporary workarounds
- Implementation choices (unless they reveal constraints)

**Usage Example:**
```
Use the context-refinement agent to update the task context with any new
discoveries or insights from this work session before compaction.
Task file: .brainworm/tasks/[task]/README.md
```

**Self-Check:** Would the NEXT person implementing similar work benefit from this discovery?

### Service Documentation Agent

**Purpose:** Update CLAUDE.md files and module documentation to reflect current implementation.

**When to Use:**
- During context compaction
- At task completion
- If documentation has drifted from code significantly

**Available Tools:** Read, Grep, Glob, LS, Edit, MultiEdit, Bash

**What It Does:**

1. **Detects repository structure:**
   - Super-repo with services
   - Mono-repo with services
   - Mono-repo without services
   - Single-purpose repository

2. **Scans affected areas:**
   - Identifies changed files
   - Maps module/service boundaries
   - Finds existing documentation

3. **Updates documentation appropriately:**
   - Service directories → CLAUDE.md files
   - Python modules → Module docstrings
   - Package directories → README.md updates
   - Root level → Main CLAUDE.md

4. **Verifies cross-references:**
   - All file references exist
   - Line numbers are current
   - Documentation links work

**CLAUDE.md Structure (Service-based):**

```markdown
# [Service Name] CLAUDE.md

## Purpose
[1-2 sentences on what this service does]

## Narrative Summary
[1-2 paragraphs explaining implementation]

## Key Files
- `server.py` - Main application entry
- `models.py:45-89` - Core data models
- `auth.py` - Authentication logic

## API Endpoints (if applicable)
- `POST /auth/login` - User authentication
- `GET /users/:id` - Retrieve user details

## Integration Points
### Consumes
- ServiceA: `/api/endpoint`
- Redis: Sessions, caching

### Provides
- `/webhooks/events` - Event notifications

## Configuration
Required environment variables:
- `DATABASE_URL` - Database connection
```

**Documentation Philosophy:**
1. **Reference over Duplication** - Point to code, don't copy it
2. **Navigation over Explanation** - Help developers find what they need
3. **Current over Historical** - Document what is, not what was
4. **Practical over Theoretical** - Focus on development needs

**What to Include:**

✅ **DO Include:**
- File locations with line numbers
- Module/class/function references with line ranges
- Configuration requirements
- Integration dependencies
- Test file locations

❌ **DON'T Include:**
- Code snippets of ANY kind
- Code examples
- Implementation details
- Historical changes
- TODO lists

**Usage Example:**
```
Use the service-documentation agent to update relevant CLAUDE.md files
with patterns and configurations discovered during this task.
```

### Session Docs Agent

**Purpose:** Create ad-hoc session memories during active development.

**When to Use:**
- Proactively during development
- When significant development insights emerge
- Capture architectural decisions in real-time
- Document development patterns and workflow effectiveness

**Available Tools:** Read, Write, Bash, Grep, Glob

**What It Does:**

1. **Reads session transcript** to understand current session work
2. **Analyzes current git state:**
   ```bash
   git status
   git log --oneline -10
   git diff --name-only
   ```
3. **Reads session state** for analytics bridge
4. **Checks existing memory files** to avoid duplication
5. **Creates memory file** using specific naming convention
6. **Writes memory** using exact template format

**File Naming Format:**
```
.brainworm/memory/YYYY-MM-DD-HHMM-[focus-area].md
```

**Focus Area Examples:**
- `hook-system-fixes`
- `analytics-correlation`
- `daic-workflow-updates`
- `agent-system-enhancements`

**Memory File Template:**

```markdown
# brainworm [Focus Area] Development Session - [Date] [Time]

## Session Overview
- **Duration**: [estimated timeframe]
- **Branch**: [current branch]
- **Focus**: [primary development area]
- **Session ID**: [from unified_session_state.json]
- **Correlation ID**: [from unified_session_state.json]
- **Files Changed**: [count]

## Git Analysis
- **Commits**: [recent commits]
- **Files Modified**: [key files with purposes]

## Development Insights
- **Architectural Decisions**: [key design choices]
- **Technical Discoveries**: [important findings]
- **Pattern Recognition**: [emerging patterns]

## Code Areas Active
- **Hooks System**: [changes]
- **Event Storage**: [updates]
- **DAIC Workflow**: [modifications]

## Issues & Solutions
- **Challenges**: [obstacles encountered]
- **Solutions**: [approaches that worked]
- **Technical Debt**: [items for future attention]

## Next Development Directions
- [Immediate next steps]
- [Areas requiring investigation]
```

**Usage Pattern:**
- **FOR:** Ad-hoc session documentation during development
- **NOT FOR:** Task-specific logging (use logging agent for that)

**Analytics Bridge:** Session memories include structured metadata for automatic harvesting by analytics systems.

## Best Practices

### Using Protocols

**Follow the Steps:**
- Protocols provide structure - don't skip steps
- Each step builds on the previous
- Verification steps catch issues early

**Use Wrapper Commands:**
- `./tasks create` handles task creation complexity
- `./tasks switch` atomic task switching
- `./daic` commands manage workflow state

**Document as You Go:**
- Update task files continuously
- Don't wait until the end
- Small updates are easier to maintain

### Using Agents

**Be Specific in Prompts:**
```
✅ Good:
Use the context-gathering agent to analyze requirements for implement-user-auth
and create a comprehensive context manifest. The task file is at
.brainworm/tasks/implement-user-auth/README.md

❌ Vague:
Create context for the auth task
```

**Provide Necessary Information:**
- Agent name and purpose
- Task file path (always)
- Specific files/line ranges (for code-review)
- Clear instructions on what to do

**Trust Agent Output:**
- Agents operate with full tool access in their domain
- Review output but don't second-guess comprehensive work
- Agents are designed to be thorough

**Don't Overuse:**
- Code-review: Only when requested or at task completion
- Logging: Only during compaction or completion
- Context-refinement: Only when discoveries made
- Service-documentation: Only at major milestones

**Agent Scope Restrictions:**
- Agents CAN ONLY edit task files or memory files
- Agents CANNOT modify system state
- Agents CANNOT change DAIC mode
- Agents CANNOT edit codebase (except service-documentation for docs)

### Workflow Integration

**Start with Protocols:**
1. Task Creation → creates structure
2. Task Startup → loads context
3. Work Session → regular development
4. Context Compaction → preserves progress
5. Task Completion → captures knowledge

**Use Agents During Protocols:**
- Task Creation → context-gathering
- Context Compaction → logging + context-refinement
- Task Completion → code-review + logging + service-documentation

**DAIC Mode Awareness:**
- Protocols respect DAIC workflow
- Agents operate regardless of DAIC mode
- Mode switches happen at protocol boundaries

### Common Patterns

**Starting a New Feature:**
```bash
# 1. Create task
./tasks create implement-feature-x

# 2. Gather context (in discussion mode)
"Use the context-gathering agent to analyze requirements..."

# 3. Review context, plan approach

# 4. Switch to implementation
"Okay, make it so"

# 5. Implement feature

# 6. Return to discussion, review work
./daic discussion
```

**Completing Work:**
```bash
# 1. Verify success criteria met

# 2. Review code
"Use the code-review agent to review changes..."

# 3. Clean up logs
"Use the logging agent to consolidate work log..."

# 4. Update documentation
"Use the service-documentation agent to update CLAUDE.md..."

# 5. Clear task
./tasks clear
./daic discussion
```

**Managing Context Limits:**
```bash
# 1. Notice context warning (75%+)

# 2. Consolidate logs
"Use the logging agent to clean up work log..."

# 3. Refine context
"Use the context-refinement agent to update context..."

# 4. Document state clearly

# 5. Restart session, continue work
```

## Troubleshooting

### Protocol Issues

**Wrapper command fails:**
- Check you're in project root
- Verify wrapper files exist: `ls daic tasks`
- Make executable: `chmod +x daic tasks`
- Run via bash: `bash daic status`

**Task creation fails:**
- Check `.brainworm/` directory exists
- Verify git repository initialized
- Check for uncommitted changes preventing branch creation

**State gets out of sync:**
- Use `./tasks status` to verify current state
- Manually sync if needed: `./tasks set --task=X --branch=Y`
- Check `.brainworm/state/unified_session_state.json`

### Agent Issues

**Agent doesn't update task file:**
- Verify you provided correct task file path
- Check agent has Edit/MultiEdit tools
- Task file must exist before agent runs

**Context-gathering adds too much:**
- This is intentional - comprehensive context is goal
- You can edit down after if truly excessive
- Better to have too much than too little

**Code-review finds nothing:**
- Agent may report "No critical issues"
- This is good news!
- Agent respects existing project patterns

**Logging agent removes too much:**
- Agent consolidates redundant entries
- Completed items removed from Next Steps
- This is intentional cleanup behavior

**Context-refinement says "no updates needed":**
- Agent only updates if significant drift found
- No update means context is still accurate
- This is normal and expected

## See Also

- **[Getting Started](getting-started.md)** - First task walkthrough with protocols
- **[DAIC Workflow](daic-workflow.md)** - How protocols integrate with DAIC
- **[Task Management](task-management.md)** - Complete task lifecycle with protocols
- **[CLI Reference](cli-reference.md)** - Commands used in protocols
- **[Architecture](architecture.md)** - How protocols and agents are implemented

---

**[← Back to Documentation Home](README.md)** | **[Next: Troubleshooting →](troubleshooting.md)**
