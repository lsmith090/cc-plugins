# Brainworm Documentation

Welcome to the brainworm plugin documentation. Brainworm enhances Claude Code with DAIC workflow enforcement, structured task management, and intelligent event storage.

## Quick Links

**New to brainworm?**
- [Getting Started](getting-started.md) - Installation, quick start, and your first task

**Using brainworm:**
- [DAIC Workflow](daic-workflow.md) - Understanding Discussion and Implementation modes
- [Task Management](task-management.md) - Creating, switching, and completing tasks
- [Protocols & Agents](protocols-and-agents.md) - Using workflow protocols and specialized agents
- [CLI Reference](cli-reference.md) - Complete command reference for `./daic`, `./tasks`, and slash commands
- [Configuration](configuration.md) - Customizing brainworm via `config.toml`

**Getting Help:**
- [Troubleshooting](troubleshooting.md) - Common issues and solutions

**Contributing:**
- [Contributing Guide](contributing.md) - How to contribute to brainworm
- [Architecture](architecture.md) - System design and implementation details

**Reference:**
- [Technical Reference](reference.md) - Hooks, events, schemas, and internals

## What is Brainworm?

Brainworm is a Claude Code plugin that implements structured development workflows through:

**DAIC Methodology:**
- **Discussion Mode**: Plan, explore, and understand before implementing
- **Implementation Mode**: Execute agreed-upon changes
- **Trigger Phrases**: Natural language mode switching ("make it so", "go ahead")

**Task Management:**
- Structured task files with context, success criteria, and work logs
- Git branch integration for isolation
- Session correlation for workflow continuity

**Event Storage:**
- SQLite database capturing all workflow events
- Session correlation for cross-session analysis
- Local-only storage for privacy

**Protocols & Agents:**
- 4 workflow protocols for common operations
- 6 specialized agents for context gathering, code review, logging, etc.

## Documentation Structure

### For New Users

Start with [Getting Started](getting-started.md) which covers installation through completing your first task.

### For Active Users

Core workflow documentation:
1. [DAIC Workflow](daic-workflow.md) - Master the discussion → implementation cycle
2. [Task Management](task-management.md) - Organize your work effectively
3. [Protocols & Agents](protocols-and-agents.md) - Use advanced workflow features
4. [CLI Reference](cli-reference.md) - Quick command lookup
5. [Configuration](configuration.md) - Customize to your preferences

### For Contributors

Development documentation:
1. [Contributing Guide](contributing.md) - Getting started with contributions
2. [Architecture](architecture.md) - Understanding the system design
3. [Technical Reference](reference.md) - Detailed implementation specs

### For Troubleshooting

Having issues? Check [Troubleshooting](troubleshooting.md) for solutions to common problems.

## Installation Quick Reference

```bash
# Add marketplace
/plugin marketplace add https://github.com/lsmith090/cc-plugins

# Install brainworm
/plugin install brainworm@medicus-it

# Verify installation (auto-setup runs on first session)
./daic status
./tasks status
```

## Key Concepts

**DAIC Modes:**
- **Discussion** (purple) - Tools blocked, focus on planning
- **Implementation** (green) - Tools enabled, execute changes

**Tasks:**
- Structured units of work with dedicated context
- Git branch integration
- Session correlation for continuity

**Protocols:**
- Standardized workflows for common operations
- Task creation, completion, context compaction, task startup

**Agents:**
- Specialized subagents with dedicated token budgets
- Context gathering, code review, logging, documentation

## Getting Help

**In this documentation:**
- Use the navigation above to find specific topics
- Each doc includes cross-references to related material

**For issues:**
- Check [Troubleshooting](troubleshooting.md) first
- See contributing guide for bug reports

## Version

This documentation is for brainworm v1.0.0 and later.

---

**Next:** Start with [Getting Started](getting-started.md) to install and use brainworm.
