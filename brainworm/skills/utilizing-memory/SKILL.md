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

### Quick Reference

**Recent work**: `ls -lt .brainworm/memory/*.md | head -10`

**Topic search**: `grep -l "topic" .brainworm/memory/*.md`

**Time range**: `ls .brainworm/memory/2025-10-*.md`

**Multiple keywords**: `grep -l -E "word1|word2" .brainworm/memory/*.md`

For complete search patterns including case-insensitive search, context display, multi-file patterns, and advanced grep techniques, see:

**@references/search-patterns.md**

## Memory File Structure

Each memory file follows a standard structure with frontmatter (session ID, task, branch) and sections for git analysis, insights, decisions, issues, and cross-references.

**Standard sections**: Session Overview, Git Analysis, Development Insights, Code Areas Active, Issues & Solutions, Next Development Directions, Memory Cross-References, Key Takeaways

For complete structure details, field descriptions, and examples, see:

**@references/memory-format-guide.md**

## Common Usage Patterns

**Pattern 1 - "What Did We Do About X?"**: Search topic → Read files → Summarize chronologically (when, decisions, implementation, issues) → Current state

**Pattern 2 - "How Did We Solve Y Before?"**: Search problem terms → Check "Issues & Solutions" → Extract solution → Verify relevance → Provide summary

**Pattern 3 - "Show Me Recent Work"**: List recent 5-10 files → Read overviews → Create timeline → Highlight themes → Note in-progress items

**Pattern 4 - "Find All Sessions About Z"**: Search all files → Read matches → Organize chronologically → Extract learnings → Show evolution

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

**Identify recurring themes**: Use grep with frequency counts to find most common topics, agents, or components

**Analyze evolution**: Compare oldest vs newest sessions on topic to show how understanding and practices evolved

For complete pattern analysis commands and techniques, see:

**@references/search-patterns.md**

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

For detailed information:
- **Memory structure**: @references/memory-format-guide.md
- **Search techniques**: @references/search-patterns.md
