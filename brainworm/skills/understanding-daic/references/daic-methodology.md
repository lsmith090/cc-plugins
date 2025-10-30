# DAIC Methodology Technical Reference

Complete reference for the DAIC (Discussion → Alignment → Implementation → Check) workflow methodology implemented by brainworm.

## Overview

DAIC is a structured development methodology that enforces thoughtful, deliberate software development by separating planning from execution. It prevents "code first, think later" patterns that lead to bugs, technical debt, and refactoring cycles.

## The Four Phases

### Discussion Phase (D) 🎯

**Purpose**: Achieve thorough understanding before any implementation

**Philosophy**:
The discussion phase recognizes that most software problems arise from **insufficient understanding**, not insufficient execution speed. By blocking implementation tools, brainworm forces developers and AI assistants to fully comprehend:
- What needs to be built
- Why it needs to be built
- What constraints exist
- What patterns already exist in the codebase
- What edge cases need handling

**Available Actions**:
- **Read operations**: Read files, grep for patterns, glob for file matches
- **Git exploration**: git status, git log, git diff, git blame
- **Agent invocations**: All specialized agents available for deep analysis
- **Task management**: Create tasks, switch tasks (planning activities)
- **Questions**: Ask clarifying questions, explore alternatives

**Blocked Actions**:
- Edit, Write, MultiEdit, NotebookEdit tools
- Any file modification operations

**Typical Activities**:
1. Read existing code to understand current implementation
2. Search for similar patterns or related functionality
3. Trace through data flows and component interactions
4. Identify integration points and dependencies
5. Use context-gathering agent for comprehensive analysis
6. Ask questions about requirements and constraints
7. Explore edge cases and error conditions
8. Review documentation and tests

**Duration**: Variable - from minutes to hours depending on complexity

**Completion Signal**: When you can answer:
- What exactly needs to be built?
- How will it integrate with existing code?
- What patterns should be followed?
- What are the edge cases?
- What could go wrong?

### Alignment Phase (A) 🤝

**Purpose**: Achieve explicit consensus on the implementation approach

**Philosophy**:
Alignment is the bridge between understanding and execution. It ensures both the developer and AI assistant agree on the plan before writing code. This prevents misaligned implementations and reduces iteration cycles.

**Key Activities**:
1. **Present findings** from discussion phase
2. **Propose specific approach** with technical details
3. **Identify risks** and mitigation strategies
4. **Define success criteria** for the implementation
5. **Get explicit confirmation** from user

**Communication Pattern**:
```
Assistant: Based on my analysis, here's what I found:

[Current state explanation]

I propose the following approach:
1. [Specific step with technical details]
2. [Another specific step]
3. [Final step]

This approach:
- Follows the existing pattern in [file.py]
- Handles edge case X by [method]
- Integrates with [system] via [interface]

Risks:
- [Risk 1]: Mitigated by [strategy]
- [Risk 2]: Acceptable because [reason]

Does this approach work for you?
```

**User Confirmation**:
The user confirms readiness with trigger phrases:
- "go ahead"
- "make it so"
- "ship it"
- "let's do it"
- "execute"
- "implement it"

Or manual command: `./daic implementation`

**Duration**: Usually brief (1-2 exchanges)

**Completion Signal**: Explicit user approval to proceed

### Implementation Phase (I) 🛠️

**Purpose**: Execute the agreed-upon implementation efficiently

**Philosophy**:
With clarity achieved in discussion and consensus reached in alignment, implementation becomes straightforward execution. The methodology prevents scope creep and maintains focus on the agreed plan.

**Available Actions**:
- **All discussion-phase tools**, PLUS:
- Edit, Write, MultiEdit, NotebookEdit
- Full file modification capabilities
- Code writing and refactoring

**Implementation Discipline**:
1. **Stay focused** on the agreed scope
2. **Follow the plan** established in discussion/alignment
3. **Make concrete changes** without second-guessing
4. **Handle discovered issues** appropriately:
   - Minor issues: Fix inline
   - Major issues: Return to discussion mode

**Typical Activities**:
1. Write code according to agreed approach
2. Create new files as planned
3. Modify existing files as discussed
4. Follow patterns identified in discussion
5. Implement error handling as designed
6. Add tests as agreed upon

**Duration**: Variable based on scope

**Return to Discussion When**:
- Discovered a major issue not considered in discussion
- Requirements change mid-implementation
- Original approach proves unworkable
- New complexity emerges

**Completion Signal**: All agreed-upon changes are implemented

### Check Phase (C) ✅

**Purpose**: Verify implementation quality and completeness

**Philosophy**:
The check phase ensures what was built matches what was planned and works correctly. It closes the loop and validates the entire DAIC cycle.

**Key Activities**:
1. **Run tests**: Verify functionality works
2. **Code review**: Use code-review agent for quality check
3. **Compare to plan**: Verify all success criteria met
4. **Check for regressions**: Ensure nothing broke
5. **Validate edge cases**: Test the edge cases discussed earlier

**Tools and Processes**:
- `pytest` or relevant test framework
- `code-review` specialized agent
- Manual testing of key scenarios
- Linting and type checking

**Outcomes**:
- **Success**: Implementation complete, meets criteria, tests pass
- **Issues found**: Return to appropriate phase:
  - Minor fixes: Quick iteration in implementation
  - Design issues: Return to discussion
  - Scope questions: Return to alignment

**Duration**: Usually quick (minutes), unless issues found

**Completion Signal**: All checks pass, user satisfied

## State Management

### Mode Storage

Current DAIC mode is stored in `.brainworm/state/unified_session_state.json`:

```json
{
  "daic_mode": "discussion",
  "daic_timestamp": "2025-10-29T22:45:44.304760+00:00",
  "previous_daic_mode": "implementation",
  ...
}
```

### Mode Transitions

**Discussion → Implementation**:
- Triggered by: User trigger phrases or `./daic implementation`
- Hook: `user_prompt_submit.py` detects trigger phrases
- State update: Atomic write to unified state
- Tool availability: All tools enabled

**Implementation → Discussion**:
- Triggered by: `./daic discussion` command
- State update: Atomic write to unified state
- Tool availability: Edit tools blocked

**Mode checking**:
- `pre_tool_use.py` hook checks mode before each tool invocation
- Blocks Edit/Write/MultiEdit/NotebookEdit in discussion mode
- Returns permission denied with explanation

## Trigger Phrase Detection

### Standard Trigger Phrases

Built-in phrases (case-insensitive, normalized):
- "go ahead"
- "make it so"
- "ship it"
- "let's do it"
- "let's implement"
- "execute"
- "implement it"
- "do it"

### Custom Trigger Phrases

Users can add custom triggers:

```bash
/brainworm:add-trigger "your custom phrase"
```

Stored in: `.brainworm/config.toml`

```toml
[daic]
trigger_phrases = ["go ahead", "make it so", "your custom phrase"]
```

### Trigger Detection Algorithm

From `user_prompt_submit.py`:

1. Normalize prompt text (lowercase, strip)
2. Check for exact phrase matches
3. Check for phrases at start/end of sentences
4. Ignore trigger words in quoted code or commands
5. Return implementation mode activation on match

## Tool Blocking Mechanism

### How Tools Are Blocked

**Pre-tool-use Hook** (`pre_tool_use.py`):

```python
# Pseudocode
if daic_mode == "discussion":
    if tool_name in ["Edit", "Write", "MultiEdit", "NotebookEdit"]:
        return {
            "permission": "denied",
            "message": "[DAIC: Discussion Mode] Tools blocked. Use trigger phrase to switch."
        }
return {"permission": "approved"}
```

**Tool Allowlist** (discussion mode):
- Read, Grep, Glob, LS
- Bash (with restrictions on destructive operations)
- Task (agent invocations)
- All other tools as needed EXCEPT file modification

**Full Access** (implementation mode):
- All tools available
- No restrictions (except configured safety rules)

### User Experience

**When tool blocked**:
```
User: Edit the file...
Claude: [Attempts Edit tool]
Hook: Permission denied - discussion mode
Claude: "I'm currently in discussion mode where editing tools are blocked.
        Based on our discussion, are you ready to implement? Say 'go ahead' to switch."
```

**After trigger phrase**:
```
User: "go ahead"
Hook: Detects trigger, switches to implementation mode
Claude: "Switching to implementation mode. Making the changes now..."
[Edit tool now succeeds]
```

## Configuration

### DAIC Settings

Location: `.brainworm/config.toml`

```toml
[daic]
# Enable/disable DAIC enforcement
enabled = true

# Default mode on session start
default_mode = "discussion"

# Custom trigger phrases
trigger_phrases = [
    "go ahead",
    "make it so",
    "ship it"
]

# Branch enforcement (optional)
[daic.branch_enforcement]
discussion_branches = ["main", "master"]
implementation_branches = ["feature/*", "fix/*", "refactor/*"]
```

### Branch Enforcement (Optional)

**Concept**: Restrict implementation mode to feature branches

**Configuration**:
```toml
[daic.branch_enforcement]
discussion_branches = ["main", "master"]
```

**Behavior**:
- On `main`/`master`: Force discussion mode, block implementation
- On feature branch: Allow mode switching
- Prevents accidental changes to protected branches

**Use case**: Teams that want extra safety on main branch

## Integration with Other Brainworm Systems

### Task Management

DAIC modes respect task operations:
- **Task creation**: Allowed in both modes (planning activity)
- **Task switching**: Allowed in both modes (organizational activity)
- **Task completion**: Usually done in discussion mode (review activity)

### Specialized Agents

All agents work in both modes:
- **context-gathering**: Analysis, not modification
- **code-review**: Read-only review
- **logging**: Updates work logs (special permission)
- **context-refinement**: Updates context (special permission)
- **service-documentation**: Updates docs (special permission)

Agents that write (logging, documentation) have special permissions to bypass mode restrictions because they update metadata, not code.

### Event Storage

Mode transitions are captured as events:
- Stored in `.brainworm/events/hooks.db`
- Includes: timestamp, previous mode, new mode, trigger source
- Used for analytics and session reconstruction

## Benefits of DAIC

### For AI Assistants

1. **Clarity**: Clear signal about what phase of work you're in
2. **Focus**: Discussion phase lets you fully understand before acting
3. **Quality**: Prevents premature implementation
4. **Efficiency**: Less rework from misunderstanding

### For Developers

1. **Thoughtful development**: Enforced planning reduces bugs
2. **Better communication**: Alignment phase ensures consensus
3. **Reduced refactoring**: Better upfront design
4. **Learning**: Discussion phase encourages exploration

### For Teams

1. **Consistent workflow**: Everyone follows same methodology
2. **Knowledge capture**: Discussion phase creates documentation trail
3. **Quality gates**: Explicit alignment checkpoints
4. **Reduced technical debt**: Better design decisions

## Common Patterns

### Pattern 1: Simple Feature

```
Discussion (5 min):
- Read existing code
- Identify where to add feature
- Check for similar patterns

Alignment (1 min):
- Present approach
- Get confirmation

Implementation (10 min):
- Write the feature code
- Follow identified pattern

Check (2 min):
- Run tests
- Quick review
```

### Pattern 2: Complex Refactoring

```
Discussion (30 min):
- Analyze current architecture
- Identify all affected components
- Use context-gathering agent
- Explore migration strategies
- Consider edge cases

Alignment (5 min):
- Present comprehensive plan
- Identify risks
- Get approval for phased approach

Implementation (2 hours):
- Execute refactoring in phases
- Follow plan step-by-step

Check (15 min):
- Run full test suite
- Code review agent
- Verify all edge cases
```

### Pattern 3: Bug Investigation and Fix

```
Discussion (15 min):
- Reproduce bug
- Read related code
- Trace execution flow
- Identify root cause
- Check for similar issues

Alignment (2 min):
- Explain root cause
- Propose fix approach
- Confirm understanding

Implementation (5 min):
- Apply the fix
- Add test case

Check (5 min):
- Verify fix works
- Ensure no regressions
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Rushing Discussion

**Bad**:
```
User: "Add auth to the app"
Claude: [Reads one file quickly]
Claude: "I'll add auth"
User: "go ahead"
[Incomplete, doesn't integrate properly]
```

**Good**:
```
User: "Add auth to the app"
Claude: [Thorough exploration]
- Current auth patterns?
- User model structure?
- Session management approach?
- Integration with existing middleware?
- Edge cases for auth failures?
[Comprehensive understanding before proposal]
```

### Anti-Pattern 2: Staying in Discussion Too Long

**Bad**:
```
[Clear requirements, simple change]
Claude: [Explores every file remotely related]
Claude: [Analyzes alternatives endlessly]
Claude: [Asks excessive questions]
[User frustrated, simple task delayed]
```

**Good**:
```
[Clear requirements, simple change]
Claude: [Quick focused analysis]
Claude: "This is straightforward. I'll follow the pattern in X. Ready?"
User: "go ahead"
[Efficient implementation]
```

### Anti-Pattern 3: Ignoring Mode Transitions

**Bad**:
```
[In implementation mode]
User: "Actually, we need to support OAuth too"
Claude: [Immediately starts adding OAuth]
[Scope creep, poor design]
```

**Good**:
```
[In implementation mode]
User: "Actually, we need to support OAuth too"
Claude: "This significantly changes our approach. Let me switch to discussion mode to explore OAuth requirements."
./daic discussion
[Proper analysis of new requirement]
```

## Troubleshooting

### Issue: Tools Unexpectedly Blocked

**Symptoms**: Edit tools blocked when trying to implement

**Diagnosis**:
```bash
./daic status  # Check current mode
```

**Solution**:
- Verify you're in implementation mode
- If in discussion mode, use trigger phrase or `./daic implementation`
- Check for branch enforcement restrictions

### Issue: Can't Switch to Implementation

**Symptoms**: Trigger phrases not working

**Diagnosis**:
1. Check if brainworm is properly installed
2. Verify hooks are running: `.brainworm/logs/debug.jsonl`
3. Check state file exists: `.brainworm/state/unified_session_state.json`

**Solution**:
- Manual switch: `./daic implementation`
- Check hook logs for errors
- Verify config.toml has trigger phrases

### Issue: Mode Switching Too Frequently

**Symptoms**: Constant mode switching disrupts flow

**Solution**:
- Stay in discussion longer for complex tasks
- Use context-gathering agent upfront for thorough analysis
- Make sure alignment is explicit before implementation
- Consider if rapid switching indicates unclear requirements

## Best Practices

1. **Start in discussion** - Default to discussion for new work
2. **Be thorough in discussion** - Time spent understanding pays dividends
3. **Make alignment explicit** - Don't assume, confirm the approach
4. **Stay focused in implementation** - Execute the plan without deviation
5. **Return to discussion when needed** - Don't force implementation on new questions
6. **Use agents in discussion** - Leverage specialized agents for deep analysis
7. **Check your work** - Don't skip the check phase
8. **Respect the methodology** - Trust the process, don't fight the tool blocking

## Implementation Details

**Source Files**:
- `brainworm/hooks/user_prompt_submit.py` - Trigger phrase detection
- `brainworm/hooks/pre_tool_use.py` - Tool blocking enforcement
- `brainworm/scripts/daic_command.py` - Mode switching CLI
- `brainworm/utils/daic_state_manager.py` - State management
- `.brainworm/config.toml` - Configuration

**State Schema**:
```typescript
interface DAICState {
  daic_mode: "discussion" | "implementation";
  daic_timestamp: string;  // ISO 8601
  previous_daic_mode: "discussion" | "implementation";
}
```

**Hook Flow**:
```
User submits prompt
  → user_prompt_submit hook
    → Check for trigger phrases
    → If found: Switch to implementation mode
  → Claude processes prompt
  → Claude attempts tool use
    → pre_tool_use hook
      → Check daic_mode
      → If discussion + edit tool: Deny
      → Otherwise: Approve
```

## Philosophy

DAIC recognizes that software development is fundamentally about **understanding problems**, not just writing code. By enforcing separation between thinking and doing, it produces:

- **Better designs** - More thought before implementation
- **Fewer bugs** - Edge cases considered upfront
- **Less rework** - Clearer requirements reduce iteration
- **Better code quality** - Following patterns, not rushing
- **Improved learning** - Exploration and analysis embedded in workflow

The methodology is not about slowing down—it's about **going fast by going right the first time**.
