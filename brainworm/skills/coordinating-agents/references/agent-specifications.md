# Agent Specifications Technical Reference

Complete technical documentation for all brainworm specialized agents, their capabilities, invocation patterns, and integration requirements.

## Agent System Architecture

### Overview

Brainworm provides six specialized agents that operate in isolated contexts with full conversation history. Each agent has specific expertise, limited tool access, and defined input/output protocols.

### Agent Execution Model

**Isolation**: Each agent runs in a separate Claude Code agent context

**Context**: Agents receive full conversation transcript leading to invocation

**Tools**: Limited to specific tool allowlist per agent

**Output**: Agents return structured results to main conversation

**State**: Agents can read and write specific files (context-gathering, logging, etc.)

### Agent Definition Format

Location: `brainworm/agents/<agent-name>.md`

Structure:
```markdown
---
name: agent-name
description: When to use this agent and what it does
tools: Read, Write, Edit, ...
---

# Agent Name

[Detailed instructions for the agent]
[What to focus on]
[How to structure output]
[Specific requirements]
```

## Detailed Agent Specifications

### 1. context-gathering Agent

**File**: `brainworm/agents/context-gathering.md`

**Purpose**: Create comprehensive context manifests for tasks by analyzing codebase and documenting current implementation.

**When to Invoke**:
- ALWAYS after creating new task
- When starting task that lacks Context Manifest
- When existing context is outdated or incomplete

**Input Requirements**:
- Task file path (absolute, from project root)
- Description of what task involves
- What systems/components are relevant

**Tool Allowlist**:
- Read: Read any file in codebase
- Glob: Find files by pattern
- Grep: Search code for patterns
- LS: List directory contents
- Bash: Run git commands, check project structure
- Edit: Update task file only
- MultiEdit: Bulk edits to task file

**Critical Restrictions**:
- MAY ONLY edit the task file provided
- FORBIDDEN from editing any other codebase files
- Sole responsibility is updating task file with context

**Output Format**:

Adds "Context Manifest" section to task README:

```markdown
## Context Manifest

### How This Currently Works: [System Name]

[VERBOSE NARRATIVE - Multiple paragraphs explaining:]

When a user initiates [action], the request first hits [entry point]...
[Continue tracing through full flow]

### For New Feature Implementation: What Needs to Connect

Since we're implementing [feature], it will integrate at these points...
[Explain integration points and dependencies]

### Technical Reference Details

#### Component Interfaces
[Function signatures, API shapes]

#### Data Structures
[Database schemas, cache patterns]

#### Configuration Requirements
[Environment variables, config files]

#### File Locations
[Where to implement, related files]
```

**Service Context Awareness**:
- Detects multi-service vs single-service projects
- Reads service_context.json delivered automatically
- Focuses on current service in multi-service projects
- Documents cross-service dependencies

**Performance**:
- Can read many files (no token limit constraint within agent context)
- May take 30-90 seconds for complex tasks
- Produces comprehensive documentation (500-2000 lines typical)

**Validation**:
- Context Manifest section exists in task file
- Narrative explains current implementation
- Technical details are accurate and complete
- File paths are correct

### 2. code-review Agent

**File**: `brainworm/agents/code-review.md`

**Purpose**: Review code for security vulnerabilities, bugs, performance issues, and consistency with project patterns.

**When to Invoke**:
- After writing significant code
- Before committing changes
- When explicit review requested

**Input Requirements**:
- Files and line ranges to review
- Task file path for context
- Focus areas (security, performance, consistency, etc.)

**Tool Allowlist**:
- Read: Read any file
- Grep: Search for patterns
- Glob: Find related files
- Bash: Run git commands for context

**Critical Restrictions**:
- Read-only access (no Edit/Write tools)
- Cannot modify code
- Can only provide feedback

**Output Format**:

Returns structured review findings:

```markdown
# Code Review: [Task Name]

## Summary
[Overall assessment of code quality]

## Security Issues
- [Issue]: [Description] - [Severity: High/Medium/Low]
  Location: file.py:123-145
  Recommendation: [How to fix]

## Bugs and Code Smells
- [Issue]: [Description]
  Location: file.py:200
  Recommendation: [Fix]

## Performance Concerns
- [Issue]: [Description]
  Impact: [Performance impact]
  Recommendation: [Optimization]

## Consistency with Project Patterns
- [Deviation]: [How code differs from patterns]
  Pattern location: reference_file.py:50
  Recommendation: [How to align]

## Positive Observations
- [What was done well]

## Overall Recommendation
[Approve / Request changes / Major revision needed]
```

**Pattern Detection**:
- Reads existing codebase to understand patterns
- Compares new code against established conventions
- Identifies deviations and suggests alignment

**Security Focus**:
- SQL injection vulnerabilities
- XSS vulnerabilities
- Authentication/authorization issues
- Sensitive data exposure
- Input validation gaps

**Performance Analysis**:
- N+1 query problems
- Memory leaks
- Inefficient algorithms
- Missing indexes
- Caching opportunities

**Validation**:
- Review covers all specified files and line ranges
- Issues are categorized correctly
- Recommendations are actionable
- Severity levels are appropriate

### 3. logging Agent

**File**: `brainworm/agents/logging.md`

**Purpose**: Consolidate and organize work logs, removing redundancy and maintaining chronological integrity.

**When to Invoke**:
- During context compaction
- During task completion
- When work logs are messy

**Input Requirements**:
- Task file path (absolute)
- Current timestamp
- Context (compaction, completion, mid-session)

**Tool Allowlist**:
- Read: Read task file and transcripts
- Edit: Update task file
- MultiEdit: Bulk edits to task file
- Bash: Check project structure
- Grep: Search for information
- Glob: Find related files

**Critical Restrictions**:
- MAY ONLY edit task file provided
- MUST NOT modify state files
- MUST NOT change DAIC mode
- Stay in lane: task file editor only

**Transcript Access**:

Agent reads conversation transcripts from:
`.brainworm/state/logging/current_transcript_*.json`

Files are prepared by system before agent invocation.

**Cleanup Operations**:

1. **Remove completed Next Steps**
2. **Consolidate duplicate work log entries**
3. **Update Success Criteria checkboxes**
4. **Remove obsolete context information**
5. **Simplify verbose completed items**
6. **Ensure no redundancy across sections**

**Output Format**:

Updates Work Log section:

```markdown
## Work Log

### YYYY-MM-DD

#### Completed
- [Consolidated entry summarizing work done]
- [Another consolidated entry]

#### Decisions
- [Key decisions made, with reasoning]

#### Discovered
- [Issues or insights discovered]

#### Next Steps
- [Current, actionable next steps only]
```

**Service Context Awareness**:
- Understands multi-service vs single-service projects
- Uses service-relative paths for clarity
- Documents cross-service activities

**Validation**:
- Work Log is chronologically ordered
- Redundant entries removed
- Success Criteria updated correctly
- Next Steps are current and actionable
- No obsolete information remains

### 4. context-refinement Agent

**File**: `brainworm/agents/context-refinement.md`

**Purpose**: Update task context with discoveries and learnings from current work session.

**When to Invoke**:
- End of long session before context compaction
- When significant discoveries were made
- When understanding evolved during work

**Input Requirements**:
- Task file path (absolute)
- Summary of key discoveries
- What changed in understanding

**Tool Allowlist**:
- Read: Read task file and transcripts
- Edit: Update task file
- MultiEdit: Bulk edits to task file
- LS: Check directory structure
- Glob: Find related files

**Critical Restrictions**:
- MAY ONLY edit task file provided
- Updates Context Manifest section only
- Does not modify Work Log (that's logging agent's job)

**Transcript Access**:

Reads from: `.brainworm/state/context-refinement/current_transcript_*.json`

**Refinement Operations**:

1. **Identify drift** - What changed from original understanding
2. **Document discoveries** - New patterns or approaches found
3. **Update architectural details** - Corrections to technical reference
4. **Add new integration points** - Previously unknown dependencies
5. **Refine implementation guidance** - Better understanding of what to build

**Output Format**:

Updates Context Manifest section with new information:

```markdown
## Context Manifest

[Existing narrative updated with discoveries]

### Session Discoveries (YYYY-MM-DD)

During implementation, we discovered:
- [Discovery 1]: [What we learned and implications]
- [Discovery 2]: [New understanding]

These discoveries require:
- [Updated approach or consideration]

[Technical Reference section updated with corrections]
```

**Validation**:
- Context Manifest contains new discoveries
- Existing information updated where drift occurred
- Technical details corrected if wrong
- No duplicate information with Work Log

### 5. service-documentation Agent

**File**: `brainworm/agents/service-documentation.md`

**Purpose**: Update CLAUDE.md files to reflect current implementation, keeping documentation synchronized with code.

**When to Invoke**:
- During context compaction if services modified
- During task completion if services changed
- When documentation has drifted from code

**Input Requirements**:
- List of services modified
- Summary of changes made
- What new patterns were introduced

**Tool Allowlist**:
- Read: Read any file
- Grep: Search for patterns
- Glob: Find files
- LS: Check structure
- Edit: Update CLAUDE.md files
- MultiEdit: Bulk edits to docs
- Bash: Run git commands

**Critical Restrictions**:
- MAY ONLY edit CLAUDE.md and related documentation
- MUST NOT modify code files
- MUST NOT modify state files

**Project Structure Awareness**:

Adapts to three project types:

1. **Super-repo**: Multiple independent repositories
2. **Monorepo**: Single repo with multiple services/submodules
3. **Single-repo**: Single service project

Detects structure and locates CLAUDE.md files accordingly.

**Documentation Updates**:

1. **Read current implementation** - Understand what code does now
2. **Read existing CLAUDE.md** - Understand current documentation
3. **Identify drift** - What documentation doesn't match reality
4. **Update sections** - Correct inaccurate information
5. **Add new patterns** - Document new approaches introduced
6. **Maintain consistency** - Keep style and structure consistent

**Output Format**:

Updates CLAUDE.md files with:

```markdown
# Service Name

[Updated description reflecting current implementation]

## Architecture

[Updated architecture details]

## Key Components

[Updated component descriptions]

### New Pattern: [Pattern Name]

[Document newly introduced patterns]

## Configuration

[Updated configuration options]

## Integration Points

[Updated integration details]
```

**Validation**:
- CLAUDE.md files reflect current code
- New patterns documented
- Inaccurate information corrected
- Consistent style maintained

### 6. session-docs Agent

**File**: `brainworm/agents/session-docs.md`

**Purpose**: Create ad-hoc session memory files capturing insights, decisions, and progress.

**When to Invoke**:
- During development to capture insights
- After significant work sessions
- When valuable learning should be preserved

**Input Requirements**:
- Topic or focus for the session memory
- Key topics to document
- What should be captured

**Tool Allowlist**:
- Read: Read any file
- Write: Create new memory files
- Bash: Run git commands for analysis
- Grep: Search for information
- Glob: Find related files

**Output Location**:
`.brainworm/memory/YYYY-MM-DD-HHMM-topic.md`

**Memory File Format**:

```markdown
# Session Memory: [Topic]

**Date**: YYYY-MM-DD HH:MM
**Session ID**: [UUID]
**Correlation ID**: [ID]
**Focus Area**: [Topic]

## Summary

[High-level summary of session work]

## Key Insights

### [Insight Category]
- [Insight 1]: [Description and implications]
- [Insight 2]: [Description]

## Technical Discoveries

### [Discovery]
[Detailed explanation]

## Decisions Made

- [Decision]: [Rationale]

## Implementation Details

[Relevant technical details]

## Git Analysis

[Analysis of commits, branches, changes]

## Next Steps

[Recommendations for future work]

## Cross-References

- Related to: [other-memory-file.md]
- Builds on: [previous-session.md]
```

**Git Analysis**:
- Examines recent commits
- Analyzes branch changes
- Identifies modified files
- Extracts commit messages

**Session Correlation**:
- Includes session_id for harvester compatibility
- Includes correlation_id
- Links to related memory files
- Enables continuity tracking

**Validation**:
- Memory file created in correct location
- Contains structured information
- Includes session correlation IDs
- References other relevant files

## Agent Invocation Standards

### Standard Invocation Pattern

All agent invocations must use this pattern:

```
Use Task tool with:
- subagent_type: "brainworm:<agent-name>"
- description: "<brief-description>"
- prompt: "<detailed-instructions>

          File/Context: <required-paths>

          Focus: <specific-focus>

          Deliverable: <what-agent-should-produce>"
```

### Path Requirements

**Always use absolute paths**:
```
# Good
Task file: /Users/user/project/.brainworm/tasks/my-task/README.md

# Bad
Task file: .brainworm/tasks/my-task/README.md
Task file: ../tasks/my-task/README.md
```

**Project root determination**:
```bash
pwd  # Current directory is project root
```

### Context Provision

Provide sufficient context for agent to work effectively:

**Minimal context**:
- File paths
- What to focus on
- What to deliver

**Better context**:
- File paths with descriptions
- What changed and why
- Related systems and components
- Specific requirements or constraints
- Examples of what you want

### Agent Response Handling

After agent completes:

1. **Read the output** - Agent returns structured results
2. **Verify completion** - Check agent accomplished task
3. **Validate results** - Confirm output is correct
4. **Inform user** - Summarize what agent did
5. **Take next steps** - Continue workflow

## Agent Coordination Patterns

### Sequential Invocation

When multiple agents are needed in order:

```
Step 1: Invoke agent A
Step 2: Wait for agent A completion
Step 3: Process agent A output
Step 4: Invoke agent B
Step 5: Wait for agent B completion
Step 6: Process agent B output
```

Example: Context compaction
1. Invoke logging agent (consolidate logs)
2. Invoke context-refinement agent (update context)
3. Verify both completed successfully

### Conditional Invocation

Some agents are optional based on conditions:

```
if (condition):
    Invoke agent X
else:
    Skip agent X
```

Example: Context refinement
- If discoveries were made: Invoke context-refinement
- If no discoveries: Skip context-refinement

### Parallel Invocation (Future)

Not currently supported, but planned:

```
Invoke agents A, B, C simultaneously
Wait for all completions
Process all outputs
```

## Performance Characteristics

### Execution Time

**Fast agents** (< 30 seconds):
- session-docs (simple memory creation)

**Medium agents** (30-60 seconds):
- logging (depends on transcript size)
- context-refinement (depends on changes)
- code-review (depends on code amount)

**Slow agents** (60-120 seconds):
- context-gathering (comprehensive analysis)
- service-documentation (multiple services)

### Token Usage

Agents receive full conversation transcript:
- Large transcripts = higher token usage
- Long sessions = expensive agent invocations
- Context compaction helps manage this

### Resource Limits

- Agents have same model limits as main conversation
- No special token allocation
- Must work within standard constraints

## Agent Development

### Creating New Agents

To add a new specialized agent:

1. **Create agent file**: `brainworm/agents/new-agent.md`

2. **Define frontmatter**:
```yaml
---
name: new-agent
description: When to use and what it does
tools: Read, Write, ...
---
```

3. **Write detailed instructions** for the agent

4. **Document in CLAUDE.md** and relevant docs

5. **Add to coordinating-agents skill** agent list

6. **Test thoroughly** with various scenarios

### Agent Design Principles

1. **Single responsibility** - One clear purpose
2. **Limited scope** - Focused tool allowlist
3. **Clear instructions** - Detailed guidance in agent file
4. **Structured output** - Consistent format
5. **Error handling** - Graceful failure modes
6. **Documentation** - Explain when and how to use

## Troubleshooting

### Agent Invocation Fails

**Symptoms**: Task tool returns error

**Diagnosis**:
- Check subagent_type spelling
- Verify agent file exists
- Check prompt format

**Solution**:
- Correct spelling/format
- Ensure agent is installed
- Follow standard invocation pattern

### Agent Produces Wrong Output

**Symptoms**: Agent output doesn't match expectations

**Diagnosis**:
- Was enough context provided?
- Were file paths correct?
- Was focus clear?

**Solution**:
- Provide more detailed prompt
- Verify paths are absolute
- Clarify what you want

### Agent Takes Too Long

**Symptoms**: Agent execution exceeds 2 minutes

**Diagnosis**:
- Is task too complex?
- Is transcript too large?
- Is scope too broad?

**Solution**:
- Break into smaller operations
- Consider context compaction first
- Narrow agent focus

### Agent Can't Access Files

**Symptoms**: Agent reports file not found

**Diagnosis**:
- Are paths absolute?
- Do files exist?
- Does agent have access?

**Solution**:
- Use absolute paths from project root
- Verify files exist before invocation
- Check agent tool allowlist

## Future Enhancements

Planned agent system improvements:

- **Parallel agent invocation**: Run multiple agents simultaneously
- **Agent composition**: Agents that invoke other agents
- **Agent streaming**: Real-time progress updates
- **Agent caching**: Cache agent results for reuse
- **Custom agents**: User-defined agents for project-specific needs
- **Agent metrics**: Track agent performance and usage
