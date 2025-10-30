# Search Patterns Reference

Advanced search techniques and grep patterns for effectively searching brainworm session memory files.

## Overview

This guide provides grep patterns, bash commands, and search strategies for efficiently finding information in `.brainworm/memory/` files.

**Philosophy**: Use progressive filtering - start broad, narrow down, then read specific files.

## Basic Search Operations

### List Files by Date

**Most recent files**:
```bash
ls -lt .brainworm/memory/*.md | head -10
```

**Oldest files**:
```bash
ls -lt .brainworm/memory/*.md | tail -10
```

**Files from specific date**:
```bash
ls .brainworm/memory/2025-10-29-*.md
```

**Files from date range**:
```bash
ls .brainworm/memory/2025-10-{25..31}-*.md
```

**Count total files**:
```bash
ls .brainworm/memory/*.md | wc -l
```

### Simple Text Search

**Find files containing keyword**:
```bash
grep -l "GitHub" .brainworm/memory/*.md
```

The `-l` flag shows only filenames, not content.

**Case-insensitive search**:
```bash
grep -il "github" .brainworm/memory/*.md
```

**Show matching lines with filenames**:
```bash
grep -n "GitHub" .brainworm/memory/*.md
```

The `-n` flag includes line numbers.

**Show matching lines with context**:
```bash
grep -n -C 3 "GitHub" .brainworm/memory/*.md
```

The `-C 3` shows 3 lines before and after each match.

## Advanced Grep Patterns

### Multiple Keywords (OR)

**Files containing any of several terms**:
```bash
grep -l -E "task|protocol|agent" .brainworm/memory/*.md
```

The `-E` flag enables extended regex. `|` means OR.

**Case-insensitive multi-keyword**:
```bash
grep -il -E "github|issue|pr" .brainworm/memory/*.md
```

### Multiple Keywords (AND)

**Files containing all of several terms**:
```bash
grep -l "GitHub" .brainworm/memory/*.md | xargs grep -l "integration"
```

This finds files with "GitHub" AND "integration".

**Three-way AND**:
```bash
grep -l "task" .brainworm/memory/*.md | \
  xargs grep -l "GitHub" | \
  xargs grep -l "issue"
```

### Phrase Search

**Exact phrase**:
```bash
grep -n "session correlation" .brainworm/memory/*.md
```

**Multi-word phrase with quotes**:
```bash
grep -n "progressive disclosure pattern" .brainworm/memory/*.md
```

### Exclude Results

**Files NOT containing term**:
```bash
grep -L "testing" .brainworm/memory/*.md
```

The `-L` flag shows files that DON'T match.

**Find files with X but not Y**:
```bash
grep -l "skill" .brainworm/memory/*.md | xargs grep -L "agent"
```

## Section-Specific Searches

### Search Specific Sections

**Find in Development Insights sections**:
```bash
grep -A 50 "## Development Insights" .brainworm/memory/*.md | \
  grep "pattern"
```

The `-A 50` shows 50 lines after the match (the section content).

**Find in Issues & Solutions**:
```bash
grep -A 30 "## Issues & Solutions" .brainworm/memory/*.md | \
  grep -n "Challenge"
```

**Find in Next Development Directions**:
```bash
grep -A 40 "## Next Development Directions" .brainworm/memory/*.md | \
  grep -n "Phase"
```

### Extract Section Content

**Extract entire section**:
```bash
# Get Development Insights section from specific file
sed -n '/## Development Insights/,/## Code Areas Active/p' \
  .brainworm/memory/2025-10-29-*.md
```

This uses sed to extract from one heading to the next.

**Extract multiple sections**:
```bash
# Get both Insights and Issues sections
grep -A 100 "## Development Insights" \
  .brainworm/memory/2025-10-29-1822-*.md | head -150
```

## Metadata Extraction

### Session IDs

**Find all session IDs**:
```bash
grep "Session ID:" .brainworm/memory/*.md
```

**Extract just the ID values**:
```bash
grep "Session ID:" .brainworm/memory/*.md | \
  sed 's/.*Session ID: *//' | \
  sort -u
```

**Find files with specific session ID**:
```bash
grep -l "bc0cd5e7" .brainworm/memory/*.md
```

### Correlation IDs

**Find correlation IDs**:
```bash
grep "Correlation ID:" .brainworm/memory/*.md
```

**Group files by correlation ID**:
```bash
for id in $(grep "Correlation ID:" .brainworm/memory/*.md | \
            sed 's/.*Correlation ID: *//' | sort -u); do
  echo "Correlation: $id"
  grep -l "Correlation ID: $id" .brainworm/memory/*.md
  echo
done
```

### Branches

**Find all branches mentioned**:
```bash
grep "Branch:" .brainworm/memory/*.md | sed 's/.*Branch: *//' | sort -u
```

**Files from specific branch**:
```bash
grep -l "Branch: feature/implement-managing-tasks-skill" \
  .brainworm/memory/*.md
```

### Status Values

**Find all status values used**:
```bash
grep "Status:" .brainworm/memory/*.md | sed 's/.*Status: *//' | sort -u
```

**Find completed sessions**:
```bash
grep -l "Status.*completed" .brainworm/memory/*.md
```

**Find in-progress sessions**:
```bash
grep -l "Status.*in-progress" .brainworm/memory/*.md
```

## Pattern Analysis

### Frequency Analysis

**Count occurrences of term per file**:
```bash
grep -c "agent" .brainworm/memory/*.md
```

**Sort by frequency**:
```bash
grep -c "agent" .brainworm/memory/*.md | sort -t: -k2 -rn
```

The `-t:` sets delimiter, `-k2` sorts by second field, `-rn` reverses numerically.

**Most common terms**:
```bash
cat .brainworm/memory/*.md | \
  tr '[:upper:]' '[:lower:]' | \
  tr -s '[:space:]' '\n' | \
  grep -v '^$' | \
  sort | uniq -c | sort -rn | head -20
```

### Temporal Analysis

**Files by month**:
```bash
ls .brainworm/memory/*.md | cut -d/ -f3 | cut -d- -f1-2 | uniq -c
```

**Sessions per day**:
```bash
ls .brainworm/memory/*.md | cut -d/ -f3 | cut -d- -f1-3 | uniq -c
```

**Recent activity trend**:
```bash
# Count files per date for last 7 days
for date in $(seq -7 0 | xargs -I {} date -v-{}d +%Y-%m-%d); do
  count=$(ls .brainworm/memory/${date}-*.md 2>/dev/null | wc -l)
  echo "$date: $count sessions"
done
```

## Cross-Reference Following

### Memory Cross-References

**Find files that reference other files**:
```bash
grep -n "Previous session:" .brainworm/memory/*.md
```

**Extract referenced filenames**:
```bash
grep "Previous session:" .brainworm/memory/*.md | \
  sed 's/.*Previous session: *//' | \
  sed 's/ .*//'
```

**Build reference chain**:
```bash
# Follow chain of previous sessions
current="2025-10-29-2011-skills-system-implementation.md"
while [ -n "$current" ]; do
  echo "Session: $current"
  current=$(grep "Previous session:" \
            .brainworm/memory/$current | \
            sed 's/.*Previous session: *//' | \
            sed 's/ .*//')
done
```

### Task References

**Find files mentioning tasks**:
```bash
grep -l "Task reference:" .brainworm/memory/*.md
```

**Extract task paths**:
```bash
grep "Task reference:" .brainworm/memory/*.md | \
  sed 's/.*Task reference: *//'
```

**Find sessions for specific task**:
```bash
grep -l ".brainworm/tasks/implement-managing-tasks-skill" \
  .brainworm/memory/*.md
```

## Topic-Based Searches

### Technology Topics

**Find by technology**:
```bash
# Python-related sessions
grep -il "python" .brainworm/memory/*.md

# Git-related sessions
grep -il -E "git|branch|commit|merge" .brainworm/memory/*.md

# Testing-related sessions
grep -il -E "test|pytest|coverage" .brainworm/memory/*.md
```

### Activity Types

**Implementation sessions**:
```bash
grep -il -E "implement|build|create|develop" .brainworm/memory/*.md
```

**Debugging sessions**:
```bash
grep -il -E "fix|bug|debug|error|issue" .brainworm/memory/*.md
```

**Planning sessions**:
```bash
grep -il -E "plan|design|architect|strategy" .brainworm/memory/*.md
```

**Refactoring sessions**:
```bash
grep -il -E "refactor|cleanup|reorganize" .brainworm/memory/*.md
```

### Component-Based

**Find sessions touching specific components**:
```bash
# Skills-related
grep -il "skill" .brainworm/memory/*.md

# Agent-related
grep -il "agent" .brainworm/memory/*.md

# Hook-related
grep -il "hook" .brainworm/memory/*.md

# Protocol-related
grep -il "protocol" .brainworm/memory/*.md
```

## Complex Queries

### Decision Tracking

**Find all decisions**:
```bash
grep -n -E "decided|decision|chose|selected" .brainworm/memory/*.md
```

**Find decisions with reasoning**:
```bash
grep -B 3 -A 3 "decided" .brainworm/memory/*.md | grep -A 6 "rationale"
```

### Problem-Solution Pairs

**Find challenges and their solutions**:
```bash
grep -A 10 "Challenge:" .brainworm/memory/*.md | grep -A 2 "Solution:"
```

**Extract all problems encountered**:
```bash
grep -A 2 "Challenge:" .brainworm/memory/*.md
```

### Architecture Changes

**Find architectural decisions**:
```bash
grep -n -E "Architectural|Architecture" .brainworm/memory/*.md
```

**Find pattern discussions**:
```bash
grep -n -i "pattern" .brainworm/memory/*.md
```

### Performance Information

**Find performance notes**:
```bash
grep -A 5 "Performance" .brainworm/memory/*.md
```

**Find benchmarks**:
```bash
grep -n -E "[0-9]+ms|[0-9]+s|benchmark" .brainworm/memory/*.md
```

## Combining with Task System

### Task-Memory Cross-Reference

**Find memory files for current task**:
```bash
# Get current task from state
current_task=$(jq -r '.current_task' \
               .brainworm/state/unified_session_state.json)

# Find related memory files
grep -l "$current_task" .brainworm/memory/*.md
```

**List all tasks mentioned in memory**:
```bash
grep "Task:" .brainworm/memory/*.md | \
  sed 's/.*Task: *//' | \
  sort -u
```

## Output Formatting

### Clean Output

**Remove line numbers and filenames**:
```bash
grep -h "pattern" .brainworm/memory/*.md
```

The `-h` flag suppresses filenames.

**Format as list**:
```bash
grep -l "pattern" .brainworm/memory/*.md | while read f; do
  echo "- $(basename $f)"
done
```

### JSON Output

**Convert matches to JSON**:
```bash
echo '{'
grep -l "GitHub" .brainworm/memory/*.md | while read f; do
  basename=$(basename $f .md)
  echo "  \"$basename\": {"
  echo "    \"file\": \"$f\","
  session=$(grep "Session ID:" $f | sed 's/.*Session ID: *//')
  echo "    \"session_id\": \"$session\""
  echo "  },"
done
echo '}'
```

## Performance Optimization

### Fast Pre-Filtering

**Use filename patterns first**:
```bash
# Instead of searching all files
grep "October" .brainworm/memory/*.md

# Use date pattern to limit search
grep "October" .brainworm/memory/2025-10-*.md
```

**Index search results**:
```bash
# Create temporary index
grep -l "skill" .brainworm/memory/*.md > /tmp/skill-files.txt

# Use index for subsequent searches
cat /tmp/skill-files.txt | xargs grep -l "agent"
```

### Parallel Search

**Search multiple patterns in parallel**:
```bash
# Search for multiple unrelated patterns
grep -l "skill" .brainworm/memory/*.md &
grep -l "agent" .brainworm/memory/*.md &
grep -l "task" .brainworm/memory/*.md &
wait
```

## Specialized Searches

### Code Block Extraction

**Find code examples**:
```bash
# Find Python code blocks
grep -A 10 '```python' .brainworm/memory/*.md

# Find bash code blocks
grep -A 5 '```bash' .brainworm/memory/*.md
```

### URL Extraction

**Find URLs mentioned**:
```bash
grep -o 'https\?://[^[:space:]]*' .brainworm/memory/*.md | sort -u
```

### File Path Extraction

**Find file paths mentioned**:
```bash
grep -o '[a-zA-Z0-9_/.-]*\.[a-z]*' .brainworm/memory/*.md | \
  grep '/' | sort -u
```

## Practical Workflows

### Workflow 1: "What did we do about X?"

```bash
# Step 1: Find relevant files
FILES=$(grep -il "github integration" .brainworm/memory/*.md)

# Step 2: Show dates and topics
echo "$FILES" | while read f; do
  basename "$f" | sed 's/.md$//'
done | sort

# Step 3: Read most recent
RECENT=$(echo "$FILES" | xargs ls -t | head -1)
cat "$RECENT"

# Step 4: Find related sessions
grep "Previous session:" "$RECENT" | sed 's/.*Previous session: *//'
```

### Workflow 2: "Timeline of feature X"

```bash
# Find all sessions about feature
FEATURE="skills"
FILES=$(grep -il "$FEATURE" .brainworm/memory/*.md | sort)

# Extract timeline
echo "Timeline for: $FEATURE"
echo
echo "$FILES" | while read f; do
  date=$(basename "$f" | cut -d- -f1-3)
  time=$(basename "$f" | cut -d- -f4 | cut -c1-4)
  topic=$(basename "$f" | sed 's/.*-[0-9]\{4\}-//' | sed 's/.md$//')
  status=$(grep "Status:" "$f" | sed 's/.*Status: *//' | head -1)
  echo "$date $time - $topic [$status]"
done
```

### Workflow 3: "Find decisions about Y"

```bash
# Find files discussing topic
TOPIC="GitHub"
FILES=$(grep -il "$TOPIC" .brainworm/memory/*.md)

# Extract decisions
echo "Decisions about: $TOPIC"
echo
echo "$FILES" | while read f; do
  echo "File: $(basename $f)"
  grep -A 5 -i "decision" "$f" | head -20
  echo
done
```

## Tips and Tricks

**Combine searches progressively**:
```bash
# Start broad
grep -l "feature" .brainworm/memory/*.md | \

# Narrow down
xargs grep -l "implementation" | \

# Further narrow
xargs grep -l "complete"
```

**Use aliases for common searches**:
```bash
alias mem-recent="ls -lt .brainworm/memory/*.md | head -10"
alias mem-search="grep -il"
alias mem-context="grep -n -C 3"
```

**Create search functions**:
```bash
mem_find() {
  grep -il "$1" .brainworm/memory/*.md
}

mem_read_recent() {
  cat $(ls -t .brainworm/memory/*.md | head -1)
}

mem_timeline() {
  grep -il "$1" .brainworm/memory/*.md | sort | while read f; do
    basename "$f" | cut -d- -f1-3
  done | uniq
}
```

## Common Mistakes to Avoid

**Don't**: Search without filters
```bash
# This is slow and overwhelming
grep "the" .brainworm/memory/*.md
```

**Do**: Use specific terms and filters
```bash
# This is fast and useful
grep -l "GitHub integration" .brainworm/memory/2025-10-*.md
```

**Don't**: Read all files sequentially
```bash
# Inefficient
for f in .brainworm/memory/*.md; do cat "$f"; done
```

**Do**: Pre-filter with grep
```bash
# Efficient
grep -l "topic" .brainworm/memory/*.md | head -3 | xargs cat
```

**Don't**: Ignore file modification times
```bash
# May miss most relevant files
ls .brainworm/memory/*.md
```

**Do**: Sort by time for recency
```bash
# Shows most recent work first
ls -lt .brainworm/memory/*.md
```
