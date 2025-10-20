# Brainworm - DAIC Workflow Enhancement for Claude Code

Transform your Claude Code development workflow with structured discipline and workflow continuity.

## What is Brainworm?

Brainworm is a comprehensive Claude Code plugin that enforces the **DAIC methodology** (Discussion → Alignment → Implementation → Check) while capturing workflow events for session tracking and continuity.

### Core Features

**🎯 DAIC Workflow Enforcement**
- **Discussion Mode**: Tool blocking encourages thorough planning before implementation
- **Trigger Phrases**: Natural transitions with "make it so", "ship it", "go ahead", etc.
- **Workflow Guidance**: Enforces thoughtful development practices through structured phases

**🤖 Specialized Subagents**
- **context-gathering**: Comprehensive task analysis and context creation
- **code-review**: Quality and security review following established patterns
- **logging**: Maintains chronological work logs with session correlation
- **context-refinement**: Updates context with session discoveries
- **service-documentation**: Keeps CLAUDE.md files current

**📊 Event Storage System**
- **Seamless session continuity**: Resume any task with full context, powered by intelligent correlation
- **Complete workflow capture**: Every decision, transition, and pattern tracked for learning
- **Privacy-first by design**: All analytics data stays local on your machine

**⚡ Zero Configuration**
- Auto-setup on first session
- No manual installation steps
- Automatic state management
- Seamless git workflow integration

## Installation

### Via Plugin Marketplace

```bash
# Add the marketplace
/plugin marketplace add https://github.com/lsmith090/cc-plugins

# Install brainworm
/plugin install brainworm@medicus-it
```

That's it! Brainworm will automatically set up on your first Claude Code session.

## Quick Start

### 1. Start a Session in Discussion Mode

By default, you begin in **Discussion Mode** where implementation tools are blocked:

```
Claude: I'll help with that. Let me first understand the requirements...
[Reads code, explores patterns, asks clarifying questions]
```

### 2. Transition to Implementation

When ready, use a trigger phrase:

```
You: "Okay, go ahead and implement it"
```

Brainworm automatically switches to **Implementation Mode** and all tools become available.

### 3. Use Slash Commands

```bash
/brainworm:daic status           # Check current mode and task
/brainworm:daic discussion       # Switch to discussion mode
/brainworm:daic implementation   # Switch to implementation mode

/brainworm:api-mode              # Toggle API mode (automated ultrathink)
/brainworm:add-trigger "phrase"  # Add custom trigger phrase
```

### 4. Leverage Specialized Agents

```
Use the context-gathering agent to analyze requirements for [task-name]
and create a comprehensive context manifest.
```

Agents operate autonomously with full conversation context.

## The DAIC Methodology

### Discussion Phase 🎯
**Purpose**: Understand requirements and explore approaches

**What You Can Do**:
- Read files and explore code
- Run git commands (`git status`, `git log`, `git diff`)
- Search and analyze patterns
- Use specialized subagents
- Ask questions and consider alternatives

**Tools Blocked**: Edit, Write, MultiEdit, NotebookEdit

### Alignment Phase 🤝
**Purpose**: Achieve consensus on the approach

**Key Activities**:
- Present findings and recommendations
- Identify risks and dependencies
- Get explicit user confirmation
- Document the agreed plan

### Implementation Phase ⚡
**Purpose**: Execute efficiently

**Activation**: Trigger phrases or `/brainworm:daic implementation`

**Tools Available**: All implementation tools unlocked

**Best Practices**:
- Follow the agreed plan
- Implement incrementally
- Test as you go
- Document decisions

### Check Phase ✅
**Purpose**: Validate quality and completeness

**Activities**:
- Run tests
- Perform code review (use code-review agent)
- Validate success criteria
- Update documentation

## Task Management

### Create a Task

```bash
./tasks create implement-user-authentication
```

Automatically:
- Creates task directory in `.brainworm/tasks/`
- Creates git branch (`feature/implement-user-authentication`)
- Updates DAIC state
- Initializes event correlation tracking

### Work on a Task

```bash
./tasks status                    # Show current task
git branch --show-current         # Verify branch
./daic status                     # Check DAIC mode
```

### Complete a Task

Follow the task-completion protocol to:
- Consolidate work logs
- Update documentation
- Capture learnings
- Close the task properly

## Protocols

Brainworm includes structured protocols for common workflows:

- **task-creation.md**: Creating well-defined tasks
- **task-completion.md**: Proper task closure with knowledge retention
- **context-compaction.md**: Managing context limits while preserving continuity
- **task-startup.md**: Loading context for existing tasks

Access protocols in `.brainworm/protocols/` or via specialized agents.

## Event Storage & Tracking

### Local Event Capture

Brainworm automatically captures workflow events:
- Tool usage tracking
- DAIC mode transitions
- Session correlation data
- Hook execution events
- Workflow timing metrics

**Storage**: `.brainworm/events/hooks.db` (SQLite)

### View Event Data

```bash
# Check event database
sqlite3 .brainworm/events/hooks.db "SELECT COUNT(*) FROM hook_events"

# View recent events
sqlite3 .brainworm/events/hooks.db "SELECT * FROM hook_events ORDER BY timestamp DESC LIMIT 10"
```

### Multi-Project Aggregation (Optional)

For cross-project event aggregation and dashboards, see:
- [Nautiloid Integration Guide](docs/NAUTILOID_INTEGRATION.md)
- [Nautiloid Repository](https://github.com/lsmith090/nautiloid)

Nautiloid aggregates event data from multiple brainworm projects for analysis.

## Configuration

### Customize Trigger Phrases

```bash
# Add custom trigger
/brainworm:add-trigger "let's build this"

# Edit config directly
vim .brainworm/config.toml
```

### Adjust DAIC Behavior

Edit `.brainworm/config.toml`:

```toml
[daic]
enabled = true
default_mode = "discussion"
trigger_phrases = [
    "make it so",
    "go ahead",
    "ship it",
    "let's do it",
    "execute",
    "implement it"
]
```

### Configure Event Storage

Event storage is always enabled and configured automatically. Events are captured to `.brainworm/events/hooks.db` with session correlation for workflow continuity.

## Documentation

**Comprehensive guides in `docs/`:**

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design and components
- [DAIC_WORKFLOW.md](docs/DAIC_WORKFLOW.md) - Detailed DAIC methodology
- [CONFIGURATION.md](docs/CONFIGURATION.md) - Complete configuration reference
- [NAUTILOID_INTEGRATION.md](docs/NAUTILOID_INTEGRATION.md) - Multi-project event aggregation
- [END_USER_GUIDE.md](docs/END_USER_GUIDE.md) - Detailed user guide

## Troubleshooting

### Tools Being Blocked?

You're in discussion mode. Either:
1. Complete your analysis and use a trigger phrase
2. Switch manually: `/brainworm:daic implementation`

### Check Current State

```bash
./daic status                    # DAIC mode and task info
./tasks status                   # Current task
git branch --show-current        # Active branch
```

### Mode Not Switching?

Only human users can switch modes (Claude cannot self-transition). Use:
- Trigger phrases: "make it so", "go ahead", "ship it"
- Manual command: `/brainworm:daic implementation`
- Restart Claude Code if hooks were recently updated

### Events Not Being Captured?

```bash
# Check hooks are configured
cat .claude/settings.json | grep brainworm

# Verify database exists
ls -la .brainworm/events/hooks.db

# Test hook execution
echo '{"test": true}' | uv run .brainworm/hooks/stop.py
```

## Privacy & Security

**Privacy-First Design**:
- All data stays local (`.brainworm/` directory)
- No external services or network calls
- Complete data ownership and control
- Read-only access for external systems

**Security Measures**:
- Input validation on all hooks
- Dangerous command detection
- Safe file operations only
- Sanitized error messages

## Contributing

Brainworm is part of the cc-plugins marketplace. Contributions welcome!

**Repository**: https://github.com/lsmith090/cc-plugins

For development guidelines, see the repository README.

## License

MIT License - See [LICENSE](LICENSE) for details.

## Support

**Issues & Questions**:
- GitHub Issues: https://github.com/lsmith090/cc-plugins/issues
- Repository: https://github.com/lsmith090/cc-plugins

## Related Projects

**Nautiloid**: Multi-project event aggregation and dashboards
- Repository: https://github.com/lsmith090/nautiloid
- Integration: [NAUTILOID_INTEGRATION.md](docs/NAUTILOID_INTEGRATION.md)

---

**Built with discipline. Powered by structure. Enhanced by workflow tracking.**

Transform your development workflow with Brainworm.
