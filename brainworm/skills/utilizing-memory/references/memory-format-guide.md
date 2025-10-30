# Memory Format Guide

Complete technical reference for brainworm session memory file structure, contents, and conventions.

## Overview

Session memory files capture work sessions in structured markdown format. These files are created by the session-docs agent and stored in `.brainworm/memory/`.

**Purpose**: Preserve session context across context window boundaries, enabling continuity and learning.

## File Naming Convention

**Pattern**: `YYYY-MM-DD-HHMM-topic.md`

**Components**:
- `YYYY-MM-DD`: Date (e.g., 2025-10-29)
- `HHMM`: Time in 24-hour format (e.g., 1822 for 6:22 PM)
- `topic`: Brief description using kebab-case (e.g., skills-investigation-and-planning)

**Examples**:
```
2025-10-29-1630-github-integration-completion.md
2025-10-29-1822-skills-investigation-and-planning.md
2025-10-29-1834-managing-tasks-skill-implementation.md
2025-10-29-2011-skills-system-implementation.md
```

**Sorting**: Files sort chronologically by name, making it easy to find recent or historical sessions.

## File Structure

### Standard Template

Every memory file follows this structure:

```markdown
# [Topic] Session - YYYY-MM-DD HH:MM

## Session Overview
- **Duration**: Approximate time span
- **Branch**: Git branch active during session
- **Focus**: What work was being done
- **Status**: Completion state (completed, in-progress, blocked, etc.)
- **Session ID**: UUID for event correlation
- **Correlation ID**: Task/feature correlation identifier
- **Files Changed**: Count of modified files
- **Lines Added**: Lines added during session
- **Lines Deleted**: Lines removed during session

## Git Analysis
- **Repository**: Project name
- **Commits**: Recent commits and their significance
- **Files Modified**: Key files changed
- **Branch Activity**: Branch operations (creation, merging, etc.)
- **[Additional git context as relevant]**

## Development Insights

### Architectural Decisions
[Key technical decisions made during session]

### Technical Discoveries
[New technical learnings or revelations]

### Pattern Recognition
[Patterns identified or established]

### Performance Notes
[Performance observations or benchmarks]

## Code Areas Active

**[Area/Component Name]**: Description of what was modified
- Specific files or directories
- Nature of changes
- Integration points

[Repeat for each active area]

## Issues & Solutions

### Challenges
[Problems encountered during session]

### Solutions
[How challenges were resolved]

### Technical Debt
[Any debt incurred or identified]

### Workarounds
[Temporary solutions implemented]

## Next Development Directions

### Immediate Next Steps
[What to do next in the current work stream]

### Phase N: [Category]
[Organized future work by phase or priority]

### Integration Points
[How this work connects to other systems]

### Research Areas
[Topics requiring further investigation]

## Memory Cross-References
- Previous session: [link to prior related session]
- Related development: [link to related work]
- Task reference: [path to task file if applicable]
- Builds on: [foundational work reference]

## Strategic Context (optional)

### Why This Matters
[Broader significance of the work]

### Success Metrics
[How to measure success]

### Implementation Philosophy
[Guiding principles for the work]

## Key Takeaways

[Summary of most important learnings from session]
```

## Section Details

### Session Overview

**Required fields**:
- Duration
- Focus
- Status

**Optional but common fields**:
- Session ID (UUID)
- Correlation ID
- Branch name
- File/line counts
- Services or modules involved

**Example**:
```markdown
## Session Overview
- **Duration**: Approximately 2 hours
- **Branch**: feature/implement-managing-tasks-skill
- **Focus**: Implementing brainworm user skills system
- **Status**: Core implementation complete (4 of 6 skills implemented)
- **Session ID**: bc0cd5e7-638d-46d8-a82f-1c629115d099
- **Correlation ID**: f1e8cfc1
- **Files Changed**: 2 modified, 9 new
- **Lines Added**: 4157
```

### Git Analysis

Captures git context for the session:

**Common elements**:
- Repository name
- Recent commits with messages
- Files modified with significance
- Branch operations (creation, switching, merging)
- Pull request activity

**Example**:
```markdown
## Git Analysis
- **Repository**: cc-plugins (brainworm plugin)
- **Commits**: Work not yet committed (implementation mode active)
- **Files Modified**:
  - `.claude/settings.json` - Added skills configuration
  - `brainworm/README.md` - Updated with skills documentation
- **Files Created**:
  - `brainworm/skills/managing-tasks/` - Task management skill
  - `brainworm/skills/understanding-daic/` - DAIC methodology skill
- **Branch Activity**: Working on feature branch for skills implementation
```

### Development Insights

Technical learnings and decisions:

**Subsections** (use as appropriate):
- Architectural Decisions
- Technical Discoveries
- Pattern Recognition
- Performance Notes

**Example**:
```markdown
## Development Insights

### Architectural Decisions

**Progressive Disclosure Pattern Established**
- Created two-tier documentation structure:
  1. **SKILL.md** - Concise actionable guidance (<500 lines)
  2. **references/** - Comprehensive technical documentation
- Pattern ensures users get quick guidance while detailed reference
  remains available

**Tool Allowlist Strategy**
- Skills granted minimal tools needed for their function:
  - `managing-tasks`: Bash, Read, Task
  - `understanding-daic`: Bash, Read
- Design prevents skill scope creep and maintains security boundaries
```

### Code Areas Active

What parts of the codebase were modified:

**Format**: Component name with description and specifics

**Example**:
```markdown
## Code Areas Active

**Skills System**: New directory structure created
- `brainworm/skills/` - Root skills directory
- Four skill subdirectories with SKILL.md + references/
- Each skill is self-contained with complete documentation

**Configuration**: Claude Code settings updated
- `.claude/settings.json` - Added skills configuration
- Registered four new skills with brainworm namespace

**Documentation**: Main README updated
- `brainworm/README.md` - Added Skills System section
- Documents progressive disclosure approach
```

### Issues & Solutions

Problems encountered and their resolutions:

**Subsections**:
- Challenges
- Solutions
- Technical Debt
- Workarounds

**Example**:
```markdown
## Issues & Solutions

**Challenge**: How to structure skill documentation without
overwhelming users

**Solution**: Progressive disclosure pattern - concise SKILL.md
(<500 lines) with comprehensive references/ directory

**Challenge**: Defining appropriate tool allowlists for each skill

**Solution**: Minimal tool grants - only what's needed for skill's
specific function

**Technical Debt**: None introduced in this session
```

### Next Development Directions

What comes after this session:

**Common categories**:
- Immediate Next Steps
- Phased implementation plans
- Integration requirements
- Research areas
- Testing needs

**Example**:
```markdown
## Next Development Directions

**Immediate Next Steps**:
- Test skill invocation in real Claude Code session
- Verify skill trigger phrase matching works as expected
- Validate tool allowlists are appropriate

**Phase 2: Additional Skills**:
- Implement remaining 2 brainworm user skills
- Consider meta-skills for repository development

**Testing & Validation**:
- Test each skill with real user scenarios
- Verify skills reduce main context usage
- Confirm tool allowlists are secure and sufficient
```

### Memory Cross-References

Links to related sessions and resources:

**Common references**:
- Previous session (temporal link)
- Related development (topical link)
- Task reference (work item link)
- Builds on (foundational link)

**Example**:
```markdown
## Memory Cross-References
- Previous session: 2025-10-29-1834-managing-tasks-skill-implementation.md
- Related development: Skills system builds on existing agent infrastructure
- Task reference: .brainworm/tasks/implement-managing-tasks-skill/
- Builds on: Agent and protocol infrastructure from v1.0.0
```

### Strategic Context

Optional section for broader context:

**When to include**:
- Major architectural changes
- Strategic decisions
- Philosophy or methodology changes
- Significant milestones

**Example**:
```markdown
## Strategic Context

### Why Skills Matter for Brainworm
1. **Reduced Cognitive Load**: Users don't need to remember specific
   wrapper commands
2. **Discoverability**: Natural language triggers make workflows accessible
3. **Determinism**: Skills enforce proper execution patterns
4. **Integration Complexity**: Skills absorb complexity from features like
   GitHub integration

### Implementation Philosophy
- **Pattern-First**: First skill establishes patterns for all subsequent skills
- **Integration Over Reimplementation**: Skills leverage existing infrastructure
- **Progressive Disclosure**: Keep focused guidance with deep-dive docs available
```

### Key Takeaways

Summary of most important learnings:

**Format**: Bold statement with explanation

**Example**:
```markdown
## Key Takeaways

**Skills System Success**:
The progressive disclosure pattern works extremely well. Users get
concise actionable guidance in SKILL.md while comprehensive technical
reference remains accessible.

**Natural Language Interface**:
Trigger phrases enable skills to feel invisible - users express intent
naturally and appropriate skill is invoked.

**Tool Security**:
Minimal tool allowlists per skill maintain security while enabling
functionality.
```

## Optional Sections

Memory files may include additional sections based on session content:

### Performance Metrics

When performance testing or benchmarking occurs:

```markdown
## Performance Metrics

**Skill Loading Time**: <50ms for metadata pre-load
**File Read Operations**: ~100ms average
**Search Performance**: grep across all files <500ms
```

### Security Findings

When security analysis is performed:

```markdown
## Security Findings

**Input Validation**: All user inputs validated before processing
**File Access**: Restricted to skill directory, no path traversal
**Tool Restrictions**: Enforced via allowed-tools allowlist
```

### Testing Results

When tests are run:

```markdown
## Testing Results

**Unit Tests**: 45/45 passed
**Integration Tests**: 12/12 passed
**Coverage**: 87% overall

**Key Test Additions**:
- Skill metadata validation
- Trigger phrase detection
- Tool allowlist enforcement
```

## Metadata Extraction

For search and organization, these fields are particularly important:

**Date/Time**: From filename (YYYY-MM-DD-HHMM)
**Topic**: From filename (kebab-case description)
**Session ID**: From Session Overview section
**Correlation ID**: From Session Overview section
**Branch**: From Session Overview or Git Analysis
**Status**: From Session Overview (completed, in-progress, blocked)

**Extracting metadata with grep**:

```bash
# Find session IDs
grep "Session ID:" .brainworm/memory/*.md

# Find correlation IDs
grep "Correlation ID:" .brainworm/memory/*.md

# Find branches
grep "Branch:" .brainworm/memory/*.md

# Find status
grep "Status:" .brainworm/memory/*.md
```

## Session Correlation

Session IDs enable correlation across:

**Event Storage**: Events in `.brainworm/events/hooks.db` with same session_id
**Task Files**: Tasks with matching session_id in frontmatter
**Memory Files**: Multiple memory files from same session
**Analytics**: Session-based analytics and pattern analysis

**Finding correlated content**:

```bash
# Find all memory files for a session
SESSION_ID="bc0cd5e7"
grep -l "$SESSION_ID" .brainworm/memory/*.md

# Find task associated with session
grep -r "$SESSION_ID" .brainworm/tasks/*/README.md
```

## Common Patterns

### Multi-Session Work

Some work spans multiple sessions:

```markdown
## Session Overview
- **Duration**: 45 minutes (continued from previous session)
- **Previous Session**: 2025-10-29-1822-skills-investigation-and-planning.md
- **Continuation**: Implementing skills identified in planning session

## Memory Cross-References
- Previous session: 2025-10-29-1822-skills-investigation-and-planning.md
- This is session 2 of 3 for skills implementation
```

### Context Compaction

When context window is compacted:

```markdown
## Session Overview
- **Duration**: Extended session with context compaction at hour 3
- **Context Management**: Ran logging agent and context-refinement agent
  at 18:45
- **Continuation**: Session continued after compaction

## Development Insights

### Context Compaction Process
- Logging agent consolidated work logs
- Context-refinement agent updated task context
- Session state preserved across compaction
- Resumed work with refreshed context window
```

### Task Completion

When task is completed:

```markdown
## Session Overview
- **Status**: Task completed
- **Task**: implement-managing-tasks-skill
- **Outcome**: All 4 skills implemented and tested

## Next Development Directions

**Task Completion Protocol**:
- Run logging agent for final consolidation
- Update version and CHANGELOG
- Commit changes
- Clear task state

**Follow-up Work**:
- Consider implementing remaining 2 skills
- Test skills in production usage
```

## File Size Guidelines

**Typical size**: 200-400 lines
**Maximum recommended**: 1000 lines

Longer sessions produce longer files, but excessively long files indicate:
- Session should have been split
- Too much verbosity in sections
- Unnecessary detail included

## Version History

Memory file format has evolved:

**Current version** (implicit):
- Structured sections with consistent headings
- Session ID and Correlation ID included
- Memory Cross-References section
- Git Analysis section
- Strategic Context (optional)

**Legacy patterns** (older files may use):
- Less structured section organization
- Missing session IDs
- Simpler git information
- No cross-references

When reading older memory files, adapt to their structure rather than expecting the current standard template.

## Best Practices for Readers

When utilizing memory files:

1. **Start with filename**: Date and topic give initial context
2. **Read Session Overview**: Get high-level understanding quickly
3. **Check Cross-References**: Find related sessions
4. **Scan section headings**: Locate relevant information
5. **Extract specific content**: Quote or summarize as needed
6. **Provide context**: Always mention source file and date
7. **Follow threads**: Use cross-references to build complete picture

## Example: Complete Memory File

See existing files in `.brainworm/memory/` for real examples:

```bash
# View a recent complete example
cat $(ls -t .brainworm/memory/*.md | head -1)

# View an older example for comparison
cat $(ls -t .brainworm/memory/*.md | tail -1)
```

Real examples show how the template adapts to different types of work: planning sessions, implementation sessions, debugging sessions, refactoring sessions, etc.
