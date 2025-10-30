# Changelog

All notable changes to the brainworm plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.1] - 2025-10-30

### Added

**Intelligent Skills System**
- Five user-facing skills with progressive disclosure pattern
- **managing-tasks** (263 lines): Orchestrates task lifecycle operations (create/switch/complete)
- **understanding-daic** (322 lines): Explains DAIC methodology and guides mode transitions
- **executing-protocols** (398 lines): Guides protocol execution with step-by-step instructions
- **coordinating-agents** (479 lines): Helps select and invoke specialized agents
- **utilizing-memory** (432 lines): Search and access session history for context continuity
- Natural language trigger phrases for intuitive skill invocation
- Comprehensive reference documentation (10 files, 5,200+ lines total)
- Skills reduce cognitive load and make brainworm workflows discoverable
- SKILL.md files under 500 lines with detailed references/ subdirectories

**Skills Architecture**
- YAML frontmatter with name, description, allowed-tools
- Minimal tool allowlists maintain security boundaries (Bash, Read, Task)
- Progressive disclosure: concise guidance with deep-dive docs available
- Cross-references between skills and reference documentation
- Seamless integration with existing wrapper commands and agents

### Changed
- Updated brainworm README.md with Intelligent Skills section
- Enhanced .claude/settings.json to register four new skills

## [1.1.0] - 2025-10-29

### Added

**GitHub Integration**
- Automatic issue linking via pattern matching in task names (`fix-bug-#123`)
- Explicit issue linking via `--link-issue=N` CLI flag
- Issue creation via `--create-issue` flag
- Manual session summary posting via `./tasks summarize` command
- Rich summaries generated from session-docs agent memory files
- Issue context fetching at session start
- Smart repository detection (supports SSH and HTTPS remotes)
- Configurable via `[github]` section in config.toml
- Graceful degradation when `gh` CLI unavailable

**Smart Branch Management**
- Detects current branch before creating tasks
- Uses existing branch when on feature branches (agent-friendly)
- Creates new branch only when on stable branches (main/master/develop)
- Deterministic behavior for automated workflows
- No prompts in non-interactive mode

**Configuration**
- New `[github]` configuration section with granular controls
- `enabled`: Master switch for GitHub integration
- `auto_link_issues`: Pattern matching for issue numbers in task names
- `create_issue_on_task`: Auto-create issues for new tasks

**CLI Enhancements**
- `./tasks summarize`: Generate and post session summaries to GitHub
- `--session-id`: Specify session to summarize
- `--link-issue=N`: Link task to existing issue
- `--create-issue`: Create new GitHub issue
- `--no-github`: Skip GitHub integration for specific task
- Enhanced help text with GitHub examples

**Testing**
- Comprehensive unit tests for GitHub integration utilities
- Pattern matching tests (14 test cases, 100% pass rate)
- Frontmatter update tests (atomic, safe operations)
- Repository detection tests (SSH, HTTPS, non-GitHub handling)

### Changed
- Task creation now checks current branch first before deciding to create new branch
- Task frontmatter extended with `github_issue` and `github_repo` fields
- Session start hook enhanced with GitHub issue context fetching
- Session end hook simplified (automatic summary posting removed in favor of manual `./tasks summarize`)

### Fixed
- Branch creation logic now respects existing feature branches
- Non-interactive mode works seamlessly for agent-driven workflows
- Task creation now properly replaces status field template placeholder with "pending" (fixes malformed `status: pending|in-progress|completed|blocked` in new tasks)

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
- Comprehensive documentation in `docs/` directory
- Getting started guide with installation and first task walkthrough
- DAIC methodology guide with detailed workflow explanations
- Task management guide with full lifecycle documentation
- Complete CLI reference for all commands
- Configuration reference with all options
- Protocols and agents guide for workflow automation
- Troubleshooting guide with common issues and solutions
- Architecture documentation for contributors
- Contributing guide with development setup
- Technical reference with schemas and APIs

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
