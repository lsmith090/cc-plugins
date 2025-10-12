# Brainworm Architecture - Complete Claude Code Workflow & Intelligence System

## System Design

Brainworm is a comprehensive Claude Code enhancement system that transforms basic AI assistance into a structured workflow management system with analytics capabilities. The system provides two core capabilities in a unified architecture:

### Core Capabilities
1. **DAIC Workflow Enforcement** - Discussion → Alignment → Implementation → Check methodology with intelligent tool blocking
2. **Analytics Intelligence** - Analytics platform with session correlation, indexed database performance, and predictive insights

## Unified System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Claude Code Session                     │
├─────────────────────────────────────────────────────────────┤
│  DAIC Workflow Enforcement          Analytics Intelligence  │
│  ┌─ Enhanced Pre-Tool-Use Hook ─────────────────────────┐   │
│  │  1. Security check                                   │   │
│  │  2. DAIC enforcement (block tools in discussion)     │   │
│  │  3. Analytics capture (log all events)              │   │
│  │  4. Smart recommendations (ML-driven insights)       │   │
│  └─────────────────────────────────────────────────────┘   │
│                              ↓                             │
│  ┌─ Unified State Management ─┬─ Real-Time Intelligence ─┐   │
│  │  • DAIC mode tracking     │  • Live metrics           │   │
│  │  • Task state             │  • Session correlation    │   │
│  │  • Session correlation    │  • Predictive alerts      │   │
│  │  • Git branch enforcement │  • Pattern insights       │   │
│  └────────────────────────────┴────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. DAIC Workflow System (`src/hooks/templates/`)

**Enhanced Hook System**:
- **`daic_pre_tool_use.py`** - DAIC enforcement + analytics capture for implementation tools
- **`transcript_processor.py`** - **CRITICAL**: Intelligent transcript processing for Task tools
- **`user_messages.py`** - Trigger phrase detection and mode management
- **`post_tool_use.py`** - Tool execution tracking and success pattern analysis
- **`stop.py`** - Session lifecycle and state persistence
- **`daic_state_manager.py`** - Unified DAIC + analytics state coordination

**Critical Hook Dependencies**:
- **Task Hook**: transcript_processor.py MUST be configured for "Task" tools in PreToolUse
- **DAIC Hook**: daic_pre_tool_use.py MUST be configured for implementation tools
- **Missing either hook prevents core system functionality**

**Tool Blocking Engine**:
- Discussion mode blocks implementation tools (`Edit`, `Write`, `MultiEdit`, `NotebookEdit`)
- Read-only commands allowed (extensive allowlist for basic, git, docker, etc.)
- Trigger phrase detection (`"make it so"`, `"ship it"`, `"go ahead"`, etc.)
- Codebase pattern learning and discussion quality insights

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
- Reviews quality and security with brainworm analytics integration
- Applies learned success patterns
- Provides confidence-scored recommendations
- Integrates with success pattern recognition

**Logging Agent**:
- Maintains clean chronological logs
- Session correlation tracking
- Analytics integration
- Cross-session continuity

**Context-Refinement Agent**:
- Updates context with discoveries from work sessions
- Brainworm analytics insights integration
- Intelligent context optimization

**Service-Documentation Agent**:
- Updates service CLAUDE.md files
- Understands brainworm project structures
- Pattern-based documentation updates

### 3. Protocol System

**Task Creation Protocol** (`.brainworm/protocols/task-creation.md`):
- **Automated wrapper**: `./tasks create [task-name]`
- Structured task setup with DAIC integration
- Submodule-aware branch management for super-repo projects
- Analytics correlation from task inception
- Automatic branch creation and state initialization
- Context-gathering agent invocation

**Task Completion Protocol** (`.brainworm/protocols/task-completion.md`):
- Knowledge retention and pattern recording
- Success metric tracking
- Analytics integration for future predictions
- Clean task closure with learning capture

**Context Compaction Protocol** (`.brainworm/protocols/context-compaction.md`):
- Session continuity across context limits
- State preservation and correlation tracking
- Analytics-informed context optimization

**Task Startup Protocol** (`.brainworm/protocols/task-startup.md`):
- Proper context loading for existing tasks
- State synchronization and correlation restoration
- Analytics-driven approach recommendations

### 4. Analytics Intelligence System (`src/analytics/`)

**Background Intelligence Layer**:
- **Session Correlation**: Multi-strategy session mapping with 95% accuracy
- **Pattern Recognition**: Successful workflow sequence identification  
- **Performance Monitoring**: Real-time workflow health tracking
- **Cross-Project Learning**: Organizational knowledge aggregation (optional)

**Database**: Optimized SQLite with critical indexes (<100ms queries, 29MB typical size)

See [`docs/ANALYTICS.md`](ANALYTICS.md) for complete analytics capabilities and usage.

## Core Principles

- **Self-Contained** - Everything runs within the project's `.brainworm` directory
- **Zero Dependencies** - No external services or network requirements (except optional Metabase)
- **Privacy-First** - All data stays on your local filesystem
- **Performance-Optimized** - Sub-100ms hook execution with validated analytics performance (29MB local, 89MB central database)
- **Workflow-Aware** - DAIC methodology enforcement with intelligent adaptation
- **Self-Improving** - Continuous learning from patterns and success metrics

## Complete Data Flow

```
User Interaction
    ↓
DAIC Workflow Enforcement (pre_tool_use)
    ├─ Security Check
    ├─ Mode Enforcement (discussion/implementation)  
    ├─ Tool Blocking Logic
    └─ Analytics Capture
    ↓
Tool Execution (if allowed)
    ↓
Post-Tool Analytics Processing
    ├─ Event Storage (SQLite + JSONL)
    ├─ Session Correlation Tracking
    ├─ Success Pattern Analysis
    └─ Real-Time Intelligence Updates
    ↓
State Management Updates
    ├─ DAIC State Coordination
    ├─ Task State Synchronization
    └─ Session Correlation Maintenance
    ↓
Intelligence Processing
    ├─ Pattern Recognition
    ├─ Predictive Analysis
    ├─ Real-Time Alerts
    └─ Recommendation Generation
```

## File Structure (Complete System)

```
Project/.brainworm/
├── hooks/                          # Complete hook system
│   ├── pre_tool_use.py             # DAIC enforcement + analytics
│   ├── user_messages.py            # Trigger detection
│   ├── post_tool_use.py            # Tool execution tracking
│   ├── stop.py                     # Session lifecycle
│   ├── session_start.py            # Session initialization
│   ├── analytics_processor.py      # Core analytics engine
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
├── analytics/                      # Analytics intelligence
│   ├── hooks.db                    # SQLite event database
│   ├── logs/                       # Daily JSONL backups
│   └── correlations/               # Session correlation data
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

- **Hook Execution**: Sub-100ms per event validated (including DAIC enforcement + analytics)
- **Analytics Processing**: Optimized database with critical indexes for fast queries
- **Storage Efficiency**: 29MB local, 89MB central database with proper indexing
- **Session Correlation**: Validated across all active sessions
- **Mode Switching**: Near-instantaneous DAIC state transitions
- **Intelligence Processing**: Optimized foundation ready for real-time features

## Extension Points

### DAIC Customization
- Trigger phrase configuration in `brainworm-config.toml`
- Tool blocking customization per project
- Branch enforcement patterns and rules
- Intelligence feature toggles

### Analytics Customization
- Hook customization via `.claude/settings.json`
- Data source configuration for multi-project analytics
- Custom analytics via JSONL log analysis
- ML model parameter tuning

### Workflow Extensions
- Custom subagents in `src/hooks/templates/`
- New protocols for specialized workflows
- Extended slash commands for workflow control
- Advanced intelligence feature development

## Integration Architecture

### Git Workflow Integration
- Automatic branch management based on task types
- Branch enforcement with DAIC mode coordination
- Git activity tracking in statusline
- Commit analytics and pattern recognition

### Real-Time Intelligence Integration
- Live session monitoring with confidence scoring
- Predictive intervention recommendations
- Cross-session pattern application
- Success-based workflow adaptation

### Multi-Project Intelligence
- Central analytics database aggregation
- Cross-project pattern sharing
- Organizational knowledge accumulation
- Success pattern replication across teams

This architecture enables Brainworm to provide both structured workflow enforcement and intelligent adaptation, creating a self-improving development system that learns from every interaction while maintaining proven development methodologies.

## Critical Requirements

**Hook Configuration**: System requires proper hook configuration in `.claude/settings.json` for:
- **Task Hook**: Enables transcript processing and context delivery to subagents
- **DAIC Hook**: Enforces workflow discipline and tool blocking

**Installation**: Brainworm is installed via the Claude Code plugin marketplace. All hooks are configured automatically on first session.

**Validation**: Run `uv run src/hooks/verify_installation.py` to verify proper setup.

See [`docs/CONFIGURATION.md`](CONFIGURATION.md) for detailed configuration requirements.