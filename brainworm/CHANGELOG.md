# Changelog

All notable changes to the brainworm plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-15

### Added

**DAIC Workflow Enforcement**
- Discussion mode with tool blocking for thoughtful planning
- Implementation mode with full tool access
- Trigger phrase detection for natural mode transitions
- Manual mode switching via slash commands
- Workflow guidance through structured development phases

**Event Storage System**
- Local SQLite event database (`.brainworm/events/hooks.db`)
- Session correlation for workflow continuity
- Hook execution tracking (PreToolUse, PostToolUse, SessionStart, SessionEnd, etc.)
- Tool usage analytics
- DAIC mode transition tracking
- Privacy-first design with all data stored locally

**Specialized Subagents**
- context-gathering: Comprehensive task analysis and context creation
- code-review: Quality and security review following established patterns
- logging: Maintains chronological work logs with session correlation
- context-refinement: Updates context with session discoveries
- service-documentation: Keeps CLAUDE.md files current

**Task Management**
- Task creation with automatic git branch management
- Task switching with state preservation
- Task completion protocol with knowledge retention
- Work log maintenance across sessions

**Hook System**
- SessionStart: Auto-setup and session initialization
- SessionEnd: Cleanup and final event writes
- UserPromptSubmit: Trigger phrase detection and DAIC transitions
- PreToolUse: DAIC enforcement and tool blocking
- PreToolUse (Transcript): Task tool transcript processing
- PostToolUse: Event capture and analytics
- Stop: Interrupt handling
- Notification: Notification event capture

**Configuration**
- Zero-configuration auto-setup on first session
- Customizable trigger phrases
- DAIC behavior configuration
- Event storage configuration

**Protocols**
- task-creation.md: Creating well-defined tasks
- task-completion.md: Proper task closure with knowledge retention
- context-compaction.md: Managing context limits while preserving continuity
- task-startup.md: Loading context for existing tasks

**Commands**
- `/brainworm:daic status` - Check current mode and task
- `/brainworm:daic discussion` - Switch to discussion mode
- `/brainworm:daic implementation` - Switch to implementation mode
- `/brainworm:daic toggle` - Toggle between modes
- `/brainworm:api-mode` - Toggle API mode (automated ultrathink)
- `/brainworm:add-trigger` - Add custom trigger phrase

**Documentation**
- Architecture documentation
- DAIC methodology guide
- Configuration reference
- End user guide
- Nautiloid integration guide (multi-project aggregation)

### Performance

- Hook execution: <100ms per event
- Database queries: <100ms with optimized indexes
- Zero impact on Claude Code responsiveness
- Efficient storage: ~29MB local database

### Security

- Input validation on all hooks
- Dangerous command detection
- Safe file operations only
- Sanitized error messages
- Privacy-first: all data stays local

[1.0.0]: https://github.com/lsmith090/cc-plugins/releases/tag/brainworm-v1.0.0
