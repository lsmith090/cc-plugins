# Architecture

Technical architecture and design patterns for brainworm contributors.

## Table of Contents

- [System Overview](#system-overview)
- [Core Components](#core-components)
- [Architectural Patterns](#architectural-patterns)
- [Data Flow](#data-flow)
- [State Management](#state-management)
- [Event Storage](#event-storage)
- [Hook System](#hook-system)
- [Integration Points](#integration-points)
- [Design Decisions](#design-decisions)

## System Overview

Brainworm is a ~14,000 LOC Claude Code plugin that enforces DAIC workflow methodology while capturing development intelligence for continuous improvement.

**Core Capabilities:**
- DAIC workflow enforcement (Discussion → Alignment → Implementation → Check)
- Task management with git integration
- Session correlation and event storage
- Specialized subagents for complex operations
- Zero-configuration auto-setup

**Technology Stack:**
- Python 3.12+ with PEP 723 inline dependencies
- SQLite for event storage
- TOML for configuration
- Git for version control and branch management
- Claude Code hook system for integration

**Key Statistics:**
- 10 hooks for Claude Code integration (7 active in hooks.json)
- 20 utility modules
- 14 CLI scripts
- 6 specialized subagents
- 4 workflow protocols
- 3 slash commands

## Core Components

### 1. Hooks System

Hooks integrate brainworm with Claude Code's lifecycle events.

**Hook Types:**

**Session Lifecycle:**
- `session_start.py` - Initialize environment, create wrappers, setup state
- `session_end.py` - Cleanup, finalize session

**Workflow Control:**
- `user_prompt_submit.py` - Detect trigger phrases, inject ultrathink
- `pre_tool_use.py` - Enforce DAIC blocking, validate tool usage (Edit, Write, MultiEdit, Bash)
- `transcript_processor.py` - Process Task tool usage for agent transcript delivery
- `post_tool_use.py` - Capture tool results, event logging
- `pre_compact.py` - Handle context compaction preparation

**Interrupts & Notifications:**
- `stop.py` - Handle user interrupts
- `subagent_stop.py` - Handle subagent completion
- `notification.py` - Capture notification events

**Architecture:**
All hooks use unified hook framework (`utils/hook_framework.py`) for:
- Consistent error handling
- State management
- Event logging
- Type safety via `utils/hook_types.py`

### 2. Utility Modules

20 shared utilities provide infrastructure:

**State Management:**
- `daic_state_manager.py` - Unified session state operations
- `file_manager.py` - File I/O with atomic locking
- `correlation_manager.py` - Session and correlation ID management

**DAIC Workflow:**
- `bash_validator.py` - Parse and validate bash commands for read-only operations
- `business_controllers.py` - Business logic controllers

**Event Storage:**
- `event_store.py` - SQLite event storage with correlation
- `event_logger.py` - Event logging abstraction
- `sqlite_manager.py` - SQLite database management

**Infrastructure:**
- `config.py` - TOML configuration loading and writing
- `project.py` - Project root and context detection
- `git.py` - Git operations and utilities
- `git_submodule_manager.py` - Git submodule management

**Hook Framework:**
- `hook_framework.py` - Unified hook execution framework
- `hook_types.py` - Type-safe hook I/O schemas
- `hook_logging.py` - Hook-specific logging utilities

**Specialized:**
- `transcript_parser.py` - Parse agent transcripts
- `input_handling.py` - Input validation and handling
- `security_validators.py` - Security validation utilities
- `debug_logger.py` - Debug logging infrastructure

### 3. CLI Scripts

14 CLI scripts provide user interface:

**DAIC Commands:**
- `daic_command.py` - Main DAIC CLI (status, discussion, implementation, toggle)
- `update_daic_mode.py` - Low-level mode updates

**Task Commands:**
- `tasks_command.py` - Main tasks CLI (status, create, list, switch, session)
- `create_task.py` - Create new task with branch
- `switch_task.py` - Atomic task switching
- `list_tasks.py` - List all tasks with status
- `update_task_state.py` - Manual task state updates
- `update_session_correlation.py` - Update session correlation IDs

**Configuration:**
- `add_trigger.py` - Add custom trigger phrase
- `api_mode.py` - Toggle API mode (automated ultrathink)

**Development:**
- `statusline-script.py` - Generate statusline data
- `validate_dependencies.py` - Validate PEP 723 dependencies
- `verify_duration_tracking.py` - Verify event duration tracking
- `wait_for_transcripts.py` - Wait for agent transcript files

**CLI Framework:**
All commands use Typer for type-safe CLI interfaces with automatic help generation.

### 4. Specialized Agents

6 agents handle complex operations:

**Agent** | **Purpose** | **Tools** | **When Used**
---|---|---|---
context-gathering | Create comprehensive context manifests | Read, Glob, Grep, LS, Bash, Edit, MultiEdit | New task or missing context
code-review | Security, bugs, performance review | Read, Grep, Glob, Bash | On request or task completion
logging | Consolidate and organize work logs | Read, Edit, MultiEdit, Bash, Grep, Glob | Context compaction or completion
context-refinement | Update context with discoveries | Read, Edit, MultiEdit, LS, Glob | End of session if drift found
service-documentation | Update CLAUDE.md files | Read, Grep, Glob, LS, Edit, MultiEdit, Bash | Context compaction or completion
session-docs | Create ad-hoc session memories | Read, Write, Bash, Grep, Glob | Proactively during development

**Agent Architecture:**
- Each operates in separate context window
- Defined in `.md` files with frontmatter
- Access to specific tool subsets
- Return structured results to main session

### 5. Workflow Protocols

4 protocols guide common operations:

**Protocol** | **Purpose** | **Key Steps**
---|---|---
task-creation | Create structured tasks | Understand request → Name task → Create with wrapper → Customize → Gather context
task-startup | Resume work with context | Find task → Review context → Validate → Verify mode → Plan session
task-completion | Complete with knowledge retention | Verify readiness → Review code → Update logs → Update docs → Cleanup
context-compaction | Manage context limits | Assess state → Preserve context → Verify state → Extract knowledge → Coordinate transition

**Protocol Storage:**
- Templates in `templates/protocols/`
- Copied to `.brainworm/protocols/` on initialization
- Referenced by CLAUDE.sessions.md

### 6. State Files

**Unified Session State** (`.brainworm/state/unified_session_state.json`):
```json
{
  "daic_mode": "discussion|implementation",
  "current_task": "task-name",
  "current_branch": "feature/task-name",
  "task_services": ["service1", "service2"],
  "session_id": "uuid",
  "correlation_id": "correlation-id",
  "plugin_root": "/path/to/plugin",
  "developer": {
    "name": "Developer Name",
    "email": "email@example.com"
  }
}
```

**Coordination Flags** (`.brainworm/state/`):
- `trigger_phrase_detected.flag` - Trigger phrase found
- `in_subagent_context.flag` - Subagent executing

**Purpose:**
- Single source of truth for session state
- Atomic updates via file locking
- Persistent across context compaction

## Architectural Patterns

### 1. Unified Hook Framework

**Pattern:** All hooks use common framework for consistency.

**Implementation:**
```python
# hooks/example_hook.py
from hook_framework import execute_hook, HookInput, HookOutput

def process_hook(input_data: HookInput) -> HookOutput:
    # Hook logic here
    return HookOutput(...)

if __name__ == "__main__":
    execute_hook(process_hook)
```

**Benefits:**
- Consistent error handling across all hooks
- Automatic state management
- Standardized event logging
- Type safety via schemas

### 2. Single Source of Truth

**Pattern:** Unified session state eliminates state fragmentation.

**Before (Anti-pattern):**
- Separate files for DAIC mode, task, branch, services
- Race conditions between updates
- State drift and inconsistencies

**After (Current):**
- Single `unified_session_state.json` file
- Atomic updates with file locking
- Managed via `DAICStateManager` class

**Benefits:**
- No state drift
- Atomic multi-field updates
- Clear ownership of state

### 3. Event-Driven Architecture

**Pattern:** Capture all workflow events for learning and continuity.

**Flow:**
1. Hook executes (e.g., `pre_tool_use`)
2. Hook calls `event_store.log_event()`
3. Event written to SQLite with correlation
4. Event available for analytics and resumption

**Schema:**
```sql
CREATE TABLE hook_events (
    id INTEGER PRIMARY KEY,
    session_id TEXT NOT NULL,
    correlation_id TEXT,
    hook_name TEXT NOT NULL,
    timestamp_ns INTEGER NOT NULL,
    execution_id TEXT,
    event_data TEXT,  -- JSON
    duration_ms INTEGER
);
```

**Benefits:**
- Complete workflow history
- Session correlation for continuity
- Analytics for pattern learning
- Debugging and audit trail

### 4. Zero-Configuration Auto-Setup

**Pattern:** Plugin initializes automatically on first use.

**Session Start Flow:**
1. Check if `.brainworm/` exists
2. If not, create directory structure
3. Copy templates (config, protocols)
4. Initialize state files
5. Create wrapper scripts
6. Ready to use

**Benefits:**
- No manual setup required
- Consistent initialization
- Idempotent (safe to re-run)

### 5. Fail-Fast Architecture

**Pattern:** Hooks fail fast with clear errors rather than silent failures.

**Implementation:**
- Validate inputs before processing
- Check preconditions explicitly
- Return structured errors
- Log failures for debugging

**Benefits:**
- Easier debugging
- Clear error messages
- No silent state corruption

### 6. Type Safety

**Pattern:** Use type hints throughout for correctness.

**Implementation:**
```python
from hook_types import PreToolUseInput, PreToolUseOutput

def pre_tool_use(input_data: PreToolUseInput) -> PreToolUseOutput:
    # Type-checked by mypy/pyright
    return PreToolUseOutput(
        permission="allow",
        user_message="Tool allowed"
    )
```

**Benefits:**
- Catch errors at development time
- Self-documenting code
- Editor autocomplete

## Data Flow

### DAIC Workflow Enforcement

```
User Message
    ↓
user_prompt_submit hook
    ↓
Detect trigger phrases
    ↓
[If found] Update DAIC mode → implementation
    ↓
Claude prepares tool use
    ↓
pre_tool_use hook
    ↓
Check DAIC mode + tool name
    ↓
[discussion mode + blocked tool] → Return permission: denied
[implementation mode] → Return permission: allow
    ↓
Claude executes or skips tool
    ↓
post_tool_use hook
    ↓
Log event, cleanup flags
```

### Task Creation Flow

```
User: ./tasks create my-task
    ↓
create_task.py
    ↓
1. Parse task name
2. Determine branch type (feature/, fix/, etc.)
3. Create .brainworm/tasks/my-task/
4. Copy TEMPLATE.md → README.md
5. Create git branch
6. Update unified_session_state.json
7. Initialize correlation tracking
    ↓
Task ready for context gathering
```

### Event Capture Flow

```
Tool Execution
    ↓
pre_tool_use hook → Log tool start, validate DAIC
    ↓
Tool executes
    ↓
post_tool_use hook → Log tool result and timing
    ↓
Event stored in SQLite (via event_store.py)
    ↓
Tagged with session_id and correlation_id
    ↓
Available for analytics and resumption
```

## State Management

### Unified Session State

**Manager:** `utils/daic_state_manager.py`

**Key Methods:**
- `get_unified_state()` - Read current unified state
- `set_daic_mode(mode)` - Update DAIC mode
- `toggle_daic_mode()` - Toggle between modes
- `get_task_state()` - Get current task information
- `set_task_state(task, branch, services, ...)` - Update task info
- `update_session_correlation(session_id, correlation_id)` - Update IDs
- `should_block_tool(tool_name, tool_input)` - Check if tool should be blocked

**Concurrency:**
- File locking via `filelock` library
- Atomic read-modify-write
- Safe for concurrent access

**State Lifecycle:**
1. Initialized on session start
2. Updated by hooks and CLI commands
3. Read by hooks for decisions
4. Persists across context compaction
5. Survives session restarts

### Coordination Flags

**Purpose:** Inter-hook communication for single session.

**Examples:**
- `trigger_phrase_detected.flag` - User said trigger phrase
- `in_subagent_context.flag` - Subagent is executing

**Lifecycle:**
1. Created by one hook
2. Read by another hook
3. Deleted after use
4. Ephemeral (not persisted)

**Location:** `.brainworm/state/`

## Event Storage

### Database Schema

**File:** `.brainworm/events/hooks.db`

**Table:** `hook_events`

```sql
CREATE TABLE hook_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    correlation_id TEXT,
    hook_name TEXT NOT NULL,
    timestamp_ns INTEGER NOT NULL,
    execution_id TEXT,
    event_data TEXT,
    duration_ms INTEGER,
    INDEX idx_session (session_id),
    INDEX idx_correlation (correlation_id),
    INDEX idx_timestamp (timestamp_ns),
    INDEX idx_hook (hook_name)
);
```

**Fields:**
- `session_id` - Claude Code session identifier
- `correlation_id` - Task correlation identifier
- `hook_name` - Which hook logged event
- `timestamp_ns` - Nanosecond timestamp
- `execution_id` - Tool execution identifier
- `event_data` - JSON blob with event details
- `duration_ms` - Tool execution duration (if applicable)

### Event Types

**DAIC Events:**
- Mode transitions (discussion ↔ implementation)
- Trigger phrase detections
- Tool blocking decisions

**Task Events:**
- Task creation
- Task switching
- Task completion

**Tool Events:**
- Tool execution start
- Tool completion with duration
- Tool results

**Session Events:**
- Session start
- Session end
- Context compaction

### Analytics Integration

Events enable:
- Workflow pattern analysis
- Time-in-mode metrics
- Tool usage statistics
- Session correlation for continuity
- Multi-project aggregation (via Nautiloid)

## Hook System

### Hook Registration

**File:** `hooks/hooks.json`

```json
{
  "SessionStart": "*",
  "SessionEnd": "*",
  "UserPromptSubmit": "*",
  "PreToolUse": "Edit|Write|MultiEdit|NotebookEdit",
  "PostToolUse": "Edit|Write|MultiEdit|NotebookEdit",
  "ToolStart": "*",
  "ToolEnd": "*",
  "TranscriptProcessor": "*",
  "ClaudeMdRequest": "*",
  "StatusLine": "*"
}
```

**Pattern Matching:**
- `*` - Match all events
- `Edit|Write|...` - Match specific tools (pipe-separated)

### Hook Execution

**Flow:**
1. Claude Code detects event (e.g., tool use)
2. Checks `hooks.json` for matching hooks
3. Executes hook via `uv run` with PEP 723 dependencies
4. Passes input via stdin as JSON
5. Reads output from stdout as JSON
6. Applies hook result (e.g., block tool, inject message)

**PEP 723 Inline Dependencies:**
```python
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
#     "tomli-w>=1.0.0",
#     "filelock>=3.13.0",
# ]
# ///
```

Benefits:
- Self-contained hook dependencies
- No global package installation
- `uv run` handles dependency management

### Hook Types

**Session Hooks:**
- `SessionStart` - Setup environment
- `SessionEnd` - Cleanup and finalize

**Prompt Hooks:**
- `UserPromptSubmit` - Process user input, inject context

**Tool Hooks:**
- `PreToolUse` - Validate before execution
- `PostToolUse` - Process after execution
- `ToolStart` - Log execution start
- `ToolEnd` - Log completion and timing

**Content Hooks:**
- `TranscriptProcessor` - Prepare conversation for agents
- `ClaudeMdRequest` - Inject behavioral guidance
- `StatusLine` - Provide visual indicators

## Integration Points

### Claude Code Integration

**Via Hooks:**
- Session lifecycle (start, end)
- User prompts (inject context, detect triggers)
- Tool execution (block/allow, log events)
- Content delivery (inject guidance, status)

**Plugin Directory:**
```
your-project/
├── .claude/
│   └── plugins/
│       └── brainworm@medicus-it/
│           ├── hooks/
│           ├── agents/
│           ├── commands/
│           ├── scripts/
│           └── utils/
└── .brainworm/
    ├── config.toml
    ├── state/
    ├── tasks/
    ├── events/
    └── protocols/
```

### Git Integration

**Branch Management:**
- Automatic branch creation on task creation
- Branch naming based on task type
- Branch switching on task switch
- Submodule support for monorepos

**Operations:**
- `git checkout -b feature/task-name`
- `git checkout feature/task-name`
- `git branch`
- `git status`

### File System Integration

**Directory Structure:**
```
.brainworm/
├── config.toml              # User configuration
├── state/
│   ├── unified_session_state.json
│   └── *.flag               # Coordination flags
├── tasks/
│   └── task-name/
│       └── README.md        # Task file
├── events/
│   └── hooks.db            # SQLite event storage
├── protocols/              # Protocol templates
├── logs/                   # Debug logs (optional)
└── memory/                 # Session memories (optional)
```

**Wrapper Scripts** (project root):
- `daic` - DAIC CLI wrapper
- `tasks` - Tasks CLI wrapper
- Generated by `session_start` hook
- Use `.brainworm/plugin-launcher` internally

## Design Decisions

### Why Unified Session State?

**Problem:** Previous architecture had separate state files that could drift.

**Solution:** Single `unified_session_state.json` with atomic updates.

**Trade-offs:**
- ✅ No state drift
- ✅ Atomic multi-field updates
- ✅ Simpler to reason about
- ❌ Larger file (minimal impact)
- ❌ Must lock entire file (acceptable)

### Why SQLite for Events?

**Alternatives Considered:**
- JSONL files - Simple but poor query performance
- In-memory - Lost on restart
- External database - Requires setup

**Why SQLite:**
- ✅ Zero-config embedded database
- ✅ ACID transactions
- ✅ Efficient querying and indexing
- ✅ Portable (single file)
- ✅ No external dependencies

### Why PEP 723 Inline Dependencies?

**Problem:** Hooks need dependencies but global installation is problematic.

**Solution:** PEP 723 inline script dependencies with `uv run`.

**Benefits:**
- ✅ Self-contained hooks
- ✅ No global package pollution
- ✅ Version pinning per hook
- ✅ `uv` handles dependency resolution
- ✅ Fast execution (cached environments)

### Why TOML for Configuration?

**Alternatives:**
- JSON - No comments, strict syntax
- YAML - Complex, security issues
- INI - Limited nested structures

**Why TOML:**
- ✅ Human-friendly syntax
- ✅ Comments supported
- ✅ Strong typing
- ✅ Nested structures
- ✅ Python standard library support

### Why Separate Agents?

**Problem:** Complex operations (context gathering, logging) consume main context.

**Solution:** Specialized subagents with separate context windows.

**Benefits:**
- ✅ Main context preserved
- ✅ Agents can be thorough without limits
- ✅ Parallel execution possible
- ✅ Focused tool access
- ✅ Clear separation of concerns

### Why Fail-Fast?

**Problem:** Silent failures led to state corruption and hard debugging.

**Solution:** Validate early, fail with clear errors.

**Benefits:**
- ✅ Bugs caught immediately
- ✅ Clear error messages
- ✅ Easier debugging
- ✅ No silent state corruption

## Performance Considerations

### Event Storage

**Optimization:**
- Indexed queries on session_id, correlation_id, timestamp
- Batch inserts where possible
- Periodic vacuum for database maintenance

**Trade-offs:**
- Storage grows over time (acceptable)
- Query performance degrades with millions of events (unlikely)

### State Updates

**Optimization:**
- File locking minimizes contention
- JSON is fast to parse
- State file is small (< 1KB)

**Trade-offs:**
- File I/O on every update (acceptable)
- Lock contention with many processes (rare)

### Hook Execution

**Optimization:**
- `uv` caches dependency environments
- Hooks execute quickly (< 100ms typical)
- Parallel hook execution where possible

**Trade-offs:**
- First run slower (dependency install)
- Hook count affects total latency

## Testing Strategy

**Test Levels:**
1. **Unit Tests** - Individual components in isolation
2. **Integration Tests** - Component interactions with real files/databases
3. **E2E Tests** - Complete workflows end-to-end

**Test Infrastructure:**
- Hook test harness for realistic hook execution
- Event validators for database and JSONL validation
- Correlation validators for event flow verification
- Fixtures with realistic session data

**Coverage Focus:**
- Critical paths (DAIC enforcement, state management)
- Error handling and edge cases
- Performance regression prevention

## Security Considerations

**Bash Command Validation:**
- `bash_validator.py` parses commands for safety
- Whitelist of read-only commands
- Blocks destructive operations in discussion mode
- Quote-aware parsing prevents injection

**State File Access:**
- File locking prevents race conditions
- Atomic updates prevent corruption
- Validation on read prevents malformed state

**Event Storage:**
- SQL injection prevention via parameterized queries
- Event data validated before storage
- No user input directly into SQL

## Scalability

**Current Limits:**
- Tasks: Unlimited (file-based)
- Events: Millions (SQLite scales well)
- State: Single file (acceptable)
- Hooks: 10 (Claude Code limit)

**Future Considerations:**
- Event database partitioning (if needed)
- State sharding (unlikely needed)
- Hook optimization (if latency becomes issue)

## See Also

- **[Contributing](contributing.md)** - Development workflow and standards
- **[Reference](reference.md)** - Technical schemas and APIs
- **[DAIC Workflow](daic-workflow.md)** - User-facing workflow documentation
- **[Task Management](task-management.md)** - Task system documentation

---

**[← Back to Documentation Home](README.md)** | **[Next: Contributing →](contributing.md)**
