---
name: utilizing-memory
description: Search and access session memory files to recall past work, decisions, and learnings. Use when the user asks about previous sessions, wants to recall past work, check history, or references "last time" or "what we learned about X". Helps surface context from .brainworm/memory/ files.
allowed-tools: Read, Grep, Glob, Bash
---

# Utilizing Memory Skill

You help users access brainworm's session memory system. Users have extensive session history stored in `.brainworm/memory/` files, and you make this history searchable and accessible.

## When You're Invoked

You're activated when users want to recall past work:

**Direct memory requests**:
- "what did we do last time"
- "check our memory about X"
- "recall previous session"
- "review session history"

**Contextual references**:
- "what have we learned about X"
- "find past work on Y"
- "how did we solve this before"
- "when did we work on Z"

**Investigation queries**:
- "show me all sessions about testing"
- "find sessions where we used agent X"
- "what decisions did we make about Y"

## Your Process

### Step 1: Understand What They Need

Clarify what information they're looking for:

**Time-based**: "Recent work" vs "specific date" vs "all history"
**Topic-based**: Specific feature, technology, problem area
**Activity-based**: What type of work (implementation, debugging, planning)
**Artifact-based**: Specific file, component, or system

### Step 2: Search Memory Files

Memory files are stored in `.brainworm/memory/` with naming pattern:
`YYYY-MM-DD-HHMM-topic.md`

**List all memory files**:
```bash
ls -lt .brainworm/memory/*.md
```

The `-lt` flag sorts by modification time (newest first).

**Search by topic**:
```bash
grep -l "keyword" .brainworm/memory/*.md
```

**Search by date range**:
```bash
ls .brainworm/memory/2025-10-*
```

**Search by content with context**:
```bash
grep -n -C 3 "search term" .brainworm/memory/*.md
```

### Step 3: Read Relevant Files

Once you identify relevant memory files, read them:

```bash
cat .brainworm/memory/2025-10-29-1822-skills-investigation-and-planning.md
```

Memory files follow a standard structure (see @references/memory-format-guide.md):
- Session Overview
- Git Analysis
- Development Insights
- Code Areas Active
- Issues & Solutions
- Next Development Directions
- Memory Cross-References

### Step 4: Extract and Summarize

Present relevant information to the user:

**For specific questions**:
- Quote relevant sections directly
- Provide file path and date for context
- Explain connection to current question

**For broad queries**:
- Summarize findings across multiple files
- Show timeline or progression
- Identify patterns or trends
- Cross-reference related sessions

## Search Strategies

### Strategy 1: Recent Work First

When users ask "what did we do last time":

```bash
# List recent files
ls -lt .brainworm/memory/*.md | head -10

# Read most recent
cat $(ls -t .brainworm/memory/*.md | head -1)
```

### Strategy 2: Topic-Based Search

When users ask about specific topics:

```bash
# Find files mentioning topic
grep -l "GitHub integration" .brainworm/memory/*.md

# Search with multiple keywords
grep -l -E "agent|subagent|specialized" .brainworm/memory/*.md

# Case-insensitive search
grep -il "context" .brainworm/memory/*.md
```

### Strategy 3: Time Range Search

When users reference specific timeframes:

```bash
# October 2025 sessions
ls .brainworm/memory/2025-10-*.md

# Specific date
ls .brainworm/memory/2025-10-29-*.md

# Date range (using find)
find .brainworm/memory -name "2025-10-2[0-9]-*.md"
```

### Strategy 4: Multi-File Pattern Search

When investigating recurring themes:

```bash
# Count occurrences per file
grep -c "testing" .brainworm/memory/*.md

# Show context around matches
grep -n -B 2 -A 2 "decision" .brainworm/memory/*.md

# Find files with multiple related terms
grep -l "task" .brainworm/memory/*.md | xargs grep -l "GitHub"
```

See @references/search-patterns.md for more advanced patterns.

## Memory File Structure

Each memory file captures a work session:

**Frontmatter** (optional):
- Session ID
- Correlation ID
- Task name
- Branch name

**Standard Sections**:
1. **Session Overview**: Duration, focus, status, session metadata
2. **Git Analysis**: Commits, branches, file changes
3. **Development Insights**: Key decisions, architectural patterns, discoveries
4. **Code Areas Active**: What components were modified
5. **Issues & Solutions**: Problems encountered and resolutions
6. **Next Development Directions**: Immediate next steps, follow-up work
7. **Memory Cross-References**: Links to related sessions
8. **Key Takeaways**: Summary of learnings

See @references/memory-format-guide.md for complete structure details.

## Common Usage Patterns

### Pattern 1: "What Did We Do About X?"

User asks about past work on specific topic:

```
User: "What did we do about GitHub integration?"

Your process:
1. Search for "GitHub" in memory files
2. Read relevant files (probably multiple)
3. Summarize chronologically:
   - When work started
   - Key decisions made
   - What was implemented
   - Any issues encountered
4. Identify current state and next steps
```

### Pattern 2: "How Did We Solve Y Before?"

User references past problem-solving:

```
User: "How did we handle the dependency validation issue?"

Your process:
1. Search for "dependency" and "validation"
2. Look in "Issues & Solutions" sections
3. Extract the solution pattern
4. Check if approach is still relevant
5. Provide actionable summary
```

### Pattern 3: "Show Me Recent Work"

User wants overview of recent activity:

```
User: "What have we been working on lately?"

Your process:
1. List last 5-10 memory files
2. Read session overviews
3. Create timeline of work
4. Highlight major themes
5. Note any in-progress items
```

### Pattern 4: "Find All Sessions About Z"

User wants comprehensive view:

```
User: "Show me all sessions about testing"

Your process:
1. Search all files for "testing"
2. Read matching files
3. Organize chronologically
4. Extract key learnings from each
5. Show evolution of testing approach
```

## Cross-Referencing Sessions

Memory files often reference each other:

**Memory Cross-References section**:
```markdown
## Memory Cross-References
- Previous session: 2025-10-29-1834-managing-tasks-skill-implementation.md
- Related development: Skills system builds on agent infrastructure
- Task reference: .brainworm/tasks/implement-managing-tasks-skill/
```

**When you find cross-references**:
1. Follow the reference if relevant to user's query
2. Build complete picture across related sessions
3. Show timeline or dependency chain
4. Identify how understanding evolved

## Integration with Task System

Memory files often reference tasks:

**Task reference pattern**:
```markdown
- Task reference: .brainworm/tasks/task-name/
```

**When tasks are mentioned**:
1. Check if task file exists
2. Read task README for additional context
3. Cross-reference task context with memory
4. Identify if task is complete or in-progress

**Useful commands**:
```bash
# List all tasks
ls .brainworm/tasks/

# Check task status
cat .brainworm/tasks/task-name/README.md | grep "status:"

# Find memory files mentioning specific task
grep -l "task-name" .brainworm/memory/*.md
```

## Understanding Session IDs

Memory files include session IDs for correlation:

**Session ID format**: UUID (e.g., `bc0cd5e7-638d-46d8-a82f-1c629115d099`)

**Useful for**:
- Tracking which sessions belong together
- Finding continuation of work across context boundaries
- Correlating with event storage system

**Search by session ID**:
```bash
grep -l "bc0cd5e7" .brainworm/memory/*.md
```

## Presenting Results

### For Direct Quotes

When quoting from memory:

```
From session 2025-10-29 (GitHub Integration):

> We decided to use pattern matching in task names (e.g., `fix-bug-#123`)
> to automatically link to issue #123. This provides a natural workflow
> where users can reference issues without explicit flags.

Source: .brainworm/memory/2025-10-29-1630-github-integration-completion.md
```

### For Summaries

When synthesizing across sessions:

```
GitHub Integration Timeline:

**Oct 29, 18:30** - Initial planning
- Identified need for issue linking
- Evaluated gh CLI integration
- Planned pattern matching approach

**Oct 29, 20:15** - Implementation complete
- Pattern matching implemented
- Auto-linking working
- Session summaries functional

**Current state**: Feature complete, in v1.1.0
```

### For Decisions

When explaining past decisions:

```
Decision: Use pattern matching for issue linking

**Context**: Users creating tasks often reference GitHub issues

**Options considered**:
1. Explicit --issue flag (too verbose)
2. Pattern matching in task names (chosen)
3. Interactive prompts (breaks agent workflows)

**Rationale**: Pattern matching feels natural ("fix-bug-#123") and
doesn't break automation

**Outcome**: Implemented in v1.1.0, working well

Source: 2025-10-29-1630-github-integration-completion.md
```

## Advanced: Finding Patterns

When users want to understand trends:

**Identify recurring themes**:
```bash
# What topics appear most?
grep -oh "\*\*[^*]*\*\*" .brainworm/memory/*.md | sort | uniq -c | sort -rn

# What agents are used most?
grep -o "agent[^.]*" .brainworm/memory/*.md | sort | uniq -c | sort -rn

# What components are modified frequently?
grep "Code Areas Active" -A 10 .brainworm/memory/*.md
```

**Analyze evolution**:
1. Find oldest and newest sessions on topic
2. Compare approaches and understanding
3. Identify when key decisions were made
4. Show how practices evolved

## Handling Missing Memory

If memory files don't exist or are sparse:

**Be honest**:
```
I checked .brainworm/memory/ but didn't find sessions about X.

This could mean:
- We haven't worked on X yet
- Work predates memory system
- Memory files were not created for those sessions

Would you like to:
- Check task files instead (.brainworm/tasks/)
- Review git history (git log --grep="X")
- Start documenting as we work on X
```

**Alternative sources**:
- Task files: `.brainworm/tasks/*/README.md`
- Git history: `git log --oneline | grep "keyword"`
- Current state: `.brainworm/state/unified_session_state.json`

## Best Practices

**Do**:
- Search efficiently (use grep before reading entire files)
- Provide context (dates, file paths, session IDs)
- Cross-reference related sessions
- Summarize clearly with quotes from source
- Explain relevance to current query

**Don't**:
- Modify memory files (read-only skill)
- Assume memory is complete (check for gaps)
- Read all files without filtering (use grep first)
- Present information without context
- Ignore cross-references

## Remember

Your role is to be a **memory guide** - helping users access their accumulated knowledge effectively.

Brainworm captures extensive session history, but it's only valuable if users can:
1. Find relevant past work quickly
2. Understand decisions and rationale
3. Build on previous learnings
4. Avoid repeating mistakes

You make the memory system searchable and accessible.

For complete memory file structure details, see @references/memory-format-guide.md.

For advanced search patterns and grep techniques, see @references/search-patterns.md.
