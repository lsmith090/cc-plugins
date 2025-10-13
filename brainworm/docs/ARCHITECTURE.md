# Brainworm Architecture - Complete Claude Code Workflow & Intelligence System

## System Design

Brainworm is a comprehensive Claude Code enhancement system that transforms basic AI assistance into a structured workflow management system with event tracking capabilities. The system provides two core capabilities in a unified architecture:

### Core Capabilities
1. **DAIC Workflow Enforcement** - Discussion → Alignment → Implementation → Check methodology with intelligent tool blocking
2. **Event Storage System** - Workflow event capture with session correlation, indexed database storage, and continuity tracking

## Unified System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Claude Code Session                     │
├─────────────────────────────────────────────────────────────┤
│  DAIC Workflow Enforcement          Event Storage System    │
│  ┌─ Enhanced Pre-Tool-Use Hook ─────────────────────────┐   │
│  │  1. Security check                                   │   │
│  │  2. DAIC enforcement (block tools in discussion)     │   │
│  │  3. Event capture (log all hook executions)         │   │
│  │  4. Session correlation tracking                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                              ↓                             │
│  ┌─ Unified State Management ─┬─ Event Storage          ─┐   │
│  │  • DAIC mode tracking     │  • Hook event logging     │   │
│  │  • Task state             │  • Session correlation    │   │
│  │  • Session correlation    │  • Workflow continuity    │   │
│  │  • Git branch enforcement │  • Timing metrics         │   │
│  └────────────────────────────┴────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. DAIC Workflow System (`src/hooks/templates/`)

**Enhanced Hook System**:
- **`daic_pre_tool_use.py`** - DAIC enforcement + event capture for implementation tools
- **`transcript_processor.py`** - **CRITICAL**: Intelligent transcript processing for Task tools
- **`user_messages.py`** - Trigger phrase detection and mode management
- **`post_tool_use.py`** - Tool execution tracking and event logging
- **`stop.py`** - Session lifecycle and state persistence
- **`daic_state_manager.py`** - Unified DAIC + event storage state coordination

**Critical Hook Dependencies**:
- **Task Hook**: transcript_processor.py MUST be configured for "Task" tools in PreToolUse
- **DAIC Hook**: daic_pre_tool_use.py MUST be configured for implementation tools
- **Missing either hook prevents core system functionality**

**Tool Blocking Engine**:
- Discussion mode blocks implementation tools (`Edit`, `Write`, `MultiEdit`, `NotebookEdit`)
- Read-only commands allowed (extensive allowlist for basic, git, docker, etc.)
- Trigger phrase detection (`"make it so"`, `"ship it"`, `"go ahead"`, etc.)
- Event logging for workflow tracking and session correlation

**State Management**:
```json
{
  "daic_mode": "discussion|implementation",
  "current_task": "task-name",
  "current_branch": "feature/branch",
  "task_services": ["service1", "service2"],
  "session_id": "uuid",
  "correlation_id": "correlation-id",
  "workflow_confidence": null
}
```

### 2. Specialized Subagent System

**Context-Gathering Agent**:
- Analyzes requirements for complex tasks
- Creates comprehensive context manifests
- Integrates with task creation workflow
- Provides architectural understanding

**Code-Review Agent**:
- Reviews quality and security
- Follows established code patterns
- Provides detailed code analysis
- Identifies potential issues

**Logging Agent**:
- Maintains clean chronological logs
- Session correlation tracking
- Event data integration
- Cross-session continuity

**Context-Refinement Agent**:
- Updates context with discoveries from work sessions
- Incorporates session insights
- Intelligent context optimization

**Service-Documentation Agent**:
- Updates service CLAUDE.md files
- Understands brainworm project structures
- Pattern-based documentation updates

**Transcript Delivery System**:
- **`wait_for_transcripts.py`** - Synchronization script for transcript file availability
- Solves race condition between hook execution and file system writes
- Implements exponential backoff polling (50ms → 1600ms, 5s timeout)
- Verifies file stability before returning to subagent
- Required step in all subagent transcript reading workflows

**Subagent Transcript Access Pattern**:
```bash
# Step 1: Wait for files to be ready
.brainworm/plugin-launcher scripts/wait_for_transcripts.py <subagent-type>

# Step 2: Read transcript chunks
cat "$(pwd)/.brainworm/state/<subagent-type>/current_transcript_"*.json
```

### 3. Protocol System

**Task Creation Protocol** (`.brainworm/protocols/task-creation.md`):
- **Automated wrapper**: `./tasks create [task-name]`
- Structured task setup with DAIC integration
- Submodule-aware branch management for super-repo projects
- Event correlation from task inception
- Automatic branch creation and state initialization
- Context-gathering agent invocation

**Task Completion Protocol** (`.brainworm/protocols/task-completion.md`):
- Knowledge retention and documentation
- Task completion tracking
- Event data integration for session continuity
- Clean task closure with context preservation

**Context Compaction Protocol** (`.brainworm/protocols/context-compaction.md`):
- Session continuity across context limits
- State preservation and correlation tracking
- Context optimization with session preservation

**Task Startup Protocol** (`.brainworm/protocols/task-startup.md`):
- Proper context loading for existing tasks
- State synchronization and correlation restoration
- Session continuity and context restoration

### 4. Event Storage System

**Local Event Capture**:
Brainworm captures hook execution events locally in `.brainworm/events/hooks.db` for session tracking and correlation. This is infrastructure that runs transparently - events are automatically captured with session IDs and correlation IDs to maintain workflow continuity.

**Storage Details**:
- SQLite database with minimal schema (5 columns + JSON blob)
- Session correlation tracking for workflow continuity
- All data stays local on your filesystem
- No configuration needed - always enabled

## Core Principles

- **Self-Contained** - Everything runs within the project's `.brainworm` directory
- **Zero Dependencies** - No external services or network requirements
- **Privacy-First** - All data stays on your local filesystem
- **Performance-Optimized** - Sub-100ms hook execution with validated event storage performance (29MB local database)
- **Workflow-Aware** - DAIC methodology enforcement with session tracking
- **Continuity-Focused** - Session correlation for seamless workflow continuation

## Complete Data Flow

```
User Interaction
    ↓
DAIC Workflow Enforcement (pre_tool_use)
    ├─ Security Check
    ├─ Mode Enforcement (discussion/implementation)
    ├─ Tool Blocking Logic
    └─ Event Capture
    ↓
Tool Execution (if allowed)
    ↓
Post-Tool Event Processing
    ├─ Event Storage (SQLite + JSONL)
    ├─ Session Correlation Tracking
    ├─ Workflow Timing Metrics
    └─ State Updates
    ↓
State Management Updates
    ├─ DAIC State Coordination
    ├─ Task State Synchronization
    └─ Session Correlation Maintenance
```

## File Structure (Complete System)

```
Project/.brainworm/
├── hooks/                          # Complete hook system
│   ├── pre_tool_use.py             # DAIC enforcement + event capture
│   ├── user_messages.py            # Trigger detection
│   ├── post_tool_use.py            # Tool execution tracking
│   ├── stop.py                     # Session lifecycle
│   ├── session_start.py            # Session initialization
│   ├── event_store.py              # Core event storage engine
│   ├── daic_state_manager.py       # Unified state management
│   └── subagent_stop.py            # Subagent coordination
├── protocols/                      # Workflow protocols
│   ├── task-creation.md            # Task setup workflow
│   ├── task-completion.md          # Task closure workflow
│   ├── context-compaction.md       # Context management
│   └── task-startup.md             # Task initialization
├── state/                          # State management
│   ├── daic-mode.json              # DAIC workflow mode
│   └── unified_session_state.json  # Complete session state (includes task tracking)
├── events/                         # Event storage
│   └── hooks.db                    # SQLite event database
├── templates/                      # System templates
│   ├── TEMPLATE.md                 # Task template
│   ├── CLAUDE.sessions.md          # Behavioral guidance
│   └── subagents.md                # Subagent documentation
└── settings.json                   # Complete system configuration
```

## Installation & Configuration

See [`CLAUDE.md`](../CLAUDE.md) for installation commands and [`docs/CONFIGURATION.md`](CONFIGURATION.md) for detailed configuration options.

## Performance Characteristics

**Validated Performance Characteristics** (Current System Status):

- **Hook Execution**: Sub-100ms per event validated (including DAIC enforcement + event capture)
- **Event Storage**: Optimized database with critical indexes for fast queries
- **Storage Efficiency**: 29MB local database with proper indexing
- **Session Correlation**: Validated across all active sessions
- **Mode Switching**: Near-instantaneous DAIC state transitions
- **Event Processing**: Optimized storage with minimal overhead

## Extension Points

### DAIC Customization
- Trigger phrase configuration in `config.toml`
- Tool blocking customization per project
- Branch enforcement patterns and rules
- Workflow behavior configuration

### Event Storage Customization
- Hook customization via `.claude/settings.json`
- Event capture is automatic and always enabled
- Optional external aggregation via Nautiloid

### Workflow Extensions
- Custom subagents for specialized tasks
- New protocols for specialized workflows
- Extended slash commands for workflow control
- Additional event tracking capabilities

## Integration Architecture

### Git Workflow Integration
- Automatic branch management based on task types
- Branch enforcement with DAIC mode coordination
- Git activity tracking in statusline
- Commit event tracking

### Multi-Project Event Aggregation (via Nautiloid)
- Central event database aggregation
- Cross-project workflow tracking
- Organizational event analysis
- Dashboard and visualization support

This architecture enables Brainworm to provide both structured workflow enforcement and comprehensive event tracking, creating a disciplined development system that maintains workflow continuity through session correlation.

## Critical Requirements

**Hook Configuration**: System requires proper hook configuration in `.claude/settings.json` for:
- **Task Hook**: Enables transcript processing and context delivery to subagents
- **DAIC Hook**: Enforces workflow discipline and tool blocking

**Installation**: Brainworm is installed via the Claude Code plugin marketplace. All hooks are configured automatically on first session.

**Validation**: Run `uv run src/hooks/verify_installation.py` to verify proper setup.

See [`docs/CONFIGURATION.md`](CONFIGURATION.md) for detailed configuration requirements.