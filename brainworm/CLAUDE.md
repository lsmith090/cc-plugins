# Brainworm Plugin - Development & Usage Guide

Instructions for Claude Code when working with or on the brainworm plugin.

## For Users (Plugin Installed in Your Project)

This plugin enforces the DAIC workflow methodology and captures development intelligence.

### Behavioral Guidance

For complete guidance on using brainworm, see CLAUDE.sessions.md:

@CLAUDE.sessions.md

This includes:
- **DAIC Workflow**: Discussion → Alignment → Implementation → Check methodology
- **Task Management**: Creating, working on, and completing tasks
- **Protocol Usage**: Task creation, completion, context compaction, startup
- **Subagent Coordination**: Using specialized agents effectively
- **Analytics Integration**: Understanding session correlation and pattern learning
- **Collaboration Philosophy**: Best practices for working with Claude Code

### Quick Reference

**Check Current Mode**:
```bash
./daic status
# or check: .brainworm/state/unified_session_state.json
```

**Mode Switching**:
- **Trigger Phrases**: "go ahead", "make it so", "ship it", "let's do it", "execute"
- **Manual Commands**:
  - `/brainworm:daic implementation` - Switch to implementation mode
  - `/brainworm:daic discussion` - Switch to discussion mode
  - `/brainworm:daic toggle` - Toggle between modes

**Task Management**:
```bash
./tasks create <task-name>          # Create new task
./tasks status                       # Show current task
./tasks session set --session-id=ID  # Set session correlation
```

**Slash Commands**:
- `/brainworm:daic [status|discussion|implementation|toggle]` - DAIC control
- `/brainworm:api-mode` - Toggle API mode (automated ultrathink)
- `/brainworm:add-trigger "phrase"` - Add custom trigger phrase

### Key Directories

When brainworm is installed in your project:

```
your-project/
  .brainworm/
    analytics/          # Local analytics database
    config.toml         # Configuration
    logs/               # Debug and timing logs
    protocols/          # Workflow protocols (copied from plugin)
    state/              # Session state
      unified_session_state.json
    tasks/              # Task tracking
  plugin-launcher       # Plugin script wrapper
  daic                  # DAIC mode control script
  tasks                 # Task management script
```

## For Contributors (Developing Brainworm)

### Plugin Architecture

**Directory Structure**:

```
brainworm/
  .claude-plugin/
    plugin.json         # Plugin metadata
  hooks/                # 10 hook implementations
    hooks.json          # Hook configuration
    session_start.py    # Session initialization
    user_prompt_submit.py # Prompt processing
    pre_tool_use.py     # DAIC enforcement
    ... (other hooks)
  agents/               # 6 subagent definitions
    code-review.md
    context-gathering.md
    context-refinement.md
    logging.md
    service-documentation.md
    session-docs.md
  commands/             # 3 slash commands
    daic.md
    api-mode.md
    add-trigger.md
  scripts/              # 14 utility scripts
    daic_command.py
    tasks_command.py
    create_task.py
    ... (other scripts)
  utils/                # 20 shared utilities
    daic_state_manager.py
    correlation_manager.py
    ... (other utilities)
  protocols/            # 4 workflow protocols
    task-creation.md
    task-completion.md
    context-compaction.md
    task-startup.md
  templates/            # Task and session templates
    TEMPLATE.md
    CLAUDE.sessions.md
    protocols/ (templates)
  docs/                 # Comprehensive documentation
    architecture.md
    daic-workflow.md
    configuration.md
    ... (other docs)
  CHANGELOG.md          # Version history
  README.md             # Plugin overview
  LICENSE               # MIT license
  CLAUDE.md             # This file
```

### Development Guidelines

**Important File Locations**:
- **Plugin code**: All files in `brainworm/` directory
- **Tests**: `../tests/brainworm/` (at repository root, NOT in plugin)
- **Documentation**: `docs/` (installed with plugin for offline access)

**Why Tests Are Outside Plugin**:

Tests live at repository level (`tests/brainworm/`) so they:
- Don't get installed to user projects
- Keep plugin distribution clean
- Allow proper test isolation and CI/CD

### Hook Development

**Adding a New Hook**:

1. Create hook file in `hooks/`:
   ```python
   #!/usr/bin/env python3
   import sys
   from pathlib import Path
   # Hook implementation
   ```

2. Update `hooks/hooks.json`:
   ```json
   {
     "PreToolUse": "Edit|Write|MultiEdit|NotebookEdit",
     "YourNewHook": "SomeEvent"
   }
   ```

3. Use proper paths:
   - Reference: `${CLAUDE_PLUGIN_ROOT}` in hook configurations
   - Hook receives expanded path at runtime
   - Scripts use plugin-launcher wrapper

4. Add tests in `../tests/brainworm/unit/` or `integration/`

5. Document in `docs/architecture.md`

**Hook Framework Integration**:
- Use `hook_types.py` for type safety
- Follow typed input/output schemas (aligned with official Claude Code spec)
- Handle errors gracefully with fail-fast architecture

**Hook Schema Compliance** (as of v1.4.0):

All hook schemas now align with official Claude Code hooks specification:

- **permission_mode field**: Added to all input types (BaseHookInput line 246, propagates to all derived schemas)
  - Values: "default", "plan", "acceptEdits", "bypassPermissions"
  - Enables hooks to understand permission context for smarter decisions

- **SubagentStop support**: Full typed schema implemented (hook_types.py:436-457)
  - SubagentStopInput with stop_hook_active field for recursion prevention
  - Registered in hooks.json, executes via hooks/subagent_stop.py
  - Logs subagent completion events to database

- **PreCompact support**: Full typed schema implemented (hook_types.py:459-480)
  - PreCompactInput with trigger ("manual"/"auto") and custom_instructions fields
  - Registered in hooks.json, executes via hooks/pre_compact.py
  - Enables state preservation before context compaction

- **Stop recursion prevention**: stop_hook_active field added to StopInput
  - Prevents infinite loops when Stop hook itself gets interrupted

- **Session source tracking**: source field added to SessionStartInput
  - Values: "startup", "resume", "clear", "compact"
  - Differentiates fresh sessions from resumed sessions for state initialization

- **PreToolUse parameter modification**: updated_input field added to PreToolUseDecisionOutput
  - Enables hooks to modify tool parameters before execution
  - Automatically serialized to hookSpecificOutput.updatedInput via to_dict()
  - No framework changes needed - data flow handles it automatically

See utils/hook_types.py for complete schema definitions. All changes maintain backward compatibility via Optional fields.

**Dependency Management** (CRITICAL):
- All hooks MUST declare complete inline dependencies in `# /// script` block
- Include ALL transitive dependencies (e.g., if importing hook_framework, add `tomli-w>=1.0.0`)
- Validate dependencies: `python3 scripts/validate_dependencies.py --file hooks/your_hook.py`
- See DEPENDENCIES.md and docs/reference.md for detailed dependency management
- CI automatically validates all dependencies before merging

**Standard Dependencies** (from DEPENDENCIES.md):
```python
# Common hook dependencies:
# dependencies = [
#     "rich>=13.0.0",
#     "tomli-w>=1.0.0",
#     "filelock>=3.13.0",
# ]
```

### Script Development

**Creating Utility Scripts**:

1. Add script to `scripts/`:
   ```python
   #!/usr/bin/env python3
   # Script implementation
   ```

2. Make executable:
   ```bash
   chmod +x scripts/your_script.py
   ```

3. Access plugin state:
   ```python
   from pathlib import Path
   import json

   # Read unified state
   state_file = Path(".brainworm/state/unified_session_state.json")
   state = json.loads(state_file.read_text())
   plugin_root = state.get("plugin_root")
   ```

4. Use plugin-launcher for cross-context execution:
   - Session start hook generates `.brainworm/plugin-launcher`
   - Scripts execute via: `.brainworm/plugin-launcher script_name.py args`
   - Provides stable path resolution without environment variables

### CLI Development with Typer

**CLI Commands** (like `./tasks` and `./daic`) use [Typer](https://typer.tiangolo.com/) for type-safe command-line interfaces.

**Why Typer**:
- Type-safe commands using Python type hints
- Automatic help generation from docstrings and type hints
- Decorator-based subcommand definition
- Built-in validation from types
- Auto-generated shell completion
- Rich integration for beautiful terminal output

**Example Pattern** (from `daic_command.py`):

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
#     "typer>=0.9.0",
# ]
# ///

import typer
from rich.console import Console

console = Console()
app = typer.Typer(
    name="daic",
    help="DAIC Mode Control - Switch between modes",
    no_args_is_help=True,  # Show help when no command provided
    add_completion=False,   # Disable shell completion for simplicity
)

@app.command(name="status", help="Show current mode")
def status() -> None:
    """Show current DAIC mode status"""
    # Implementation here
    console.print("Current mode: Discussion")

@app.command(name="toggle", help="Toggle between modes")
def toggle() -> None:
    """Toggle between discussion and implementation"""
    # Implementation here
    pass

def main() -> None:
    """Entry point"""
    try:
        app()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

if __name__ == '__main__':
    main()
```

**Command Arguments and Options**:

```python
@app.command(name="create")
def create(
    # Positional argument
    task_name: Optional[str] = typer.Argument(
        None,
        help="Name of the task to create"
    ),
    # Named option with flag
    services: Optional[str] = typer.Option(
        None,
        "--services",
        help="Comma-separated services"
    ),
    # Boolean flag
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Skip interactive prompts"
    ),
) -> None:
    """Create a new task"""
    # Type hints provide automatic validation
    # Help text is auto-generated
    pass
```

**Best Practices**:
1. Use `no_args_is_help=True` for commands that require subcommands
2. Add clear help text to all commands and options
3. Use type hints for automatic validation
4. Return proper exit codes with `raise typer.Exit(code=N)`
5. Keep Rich console integration for formatted output
6. Include typer in script inline dependencies

**Testing CLI Commands**:

```bash
# Test help generation
./tasks --help
./tasks create --help

# Test commands
./tasks status
./daic toggle
```

### Slash Command Development

**Adding a Command**:

1. Create command markdown in `commands/`:
   ```markdown
   # Command Name

   Description of what this command does.

   !.brainworm/plugin-launcher hooks/your_script.py $ARGUMENTS
   ```

2. Implement script in `scripts/`

3. Use allowed-tools whitelist:
   - `.brainworm/plugin-launcher` is whitelisted
   - Commands execute via wrapper, not direct paths

4. Test in real Claude Code session:
   ```bash
   /brainworm:your-command arg1 arg2
   ```

5. Document in `README.md` and relevant docs

### Documentation Updates

**When to Update Docs**:
- New features: Update README.md and relevant docs
- Behavior changes: Update daic-workflow.md or architecture.md
- Configuration: Update configuration.md
- Breaking changes: Update CHANGELOG.md with migration notes

**Documentation Standards**:
- Keep comprehensive (users may be offline)
- Include code examples
- Maintain table of contents
- Link between related docs

### Testing

**Run Tests** (from repository root):

```bash
# All brainworm tests
uv run pytest tests/brainworm/

# Specific suites
uv run pytest tests/brainworm/unit/        # Fast unit tests
uv run pytest tests/brainworm/integration/ # Integration tests
uv run pytest tests/brainworm/e2e/         # End-to-end tests (requires --runslow)

# E2E tests (marked as slow)
uv run pytest tests/brainworm/e2e/ --runslow

# With coverage
uv run pytest --cov=brainworm --cov-report=term-missing tests/brainworm/
```

**Test Organization**:
- `unit/` - Fast, isolated component tests (< 100ms per test)
- `integration/` - Component interaction tests with real databases/filesystem
- `e2e/` - Complete workflow validation simulating real usage
- `validation/` - Event validation utilities (db_validator, jsonl_validator, correlation_validator)
- `fixtures/events/` - Test fixtures with realistic session data
- `security/` - Security validation
- `performance/` - Performance regression checks
- `concurrency/` - Concurrency and race condition tests
- `edge_cases/` - Edge case and error condition tests

**Test Infrastructure**:

1. **Hook Test Harness** (`tests/brainworm/integration/hook_test_harness.py`)
   - Framework for executing hook sequences in realistic environments
   - Manages project structure, state files, and databases
   - Provides utilities for validating hook outputs
   - Example:
     ```python
     harness = HookTestHarness(project_root, plugin_root)
     result = harness.execute_hook("pre_tool_use", "Read", {"file_path": "/test.py"})
     events = harness.get_database_events()
     harness.validate_database_events()
     ```

2. **Event Validators** (`tests/brainworm/validation/`)
   - **DatabaseValidator**: Validates event storage in SQLite (`.brainworm/events/hooks.db`)
   - **JSONLValidator**: Validates JSONL event logs
   - **CorrelationValidator**: Validates correlation flows and PreToolUse/PostToolUse pairing
   - Used by integration and E2E tests for comprehensive validation

3. **Test Fixtures** (`tests/brainworm/fixtures/events/`)
   - Realistic session data in JSON format
   - Includes: basic_session, daic_blocking_workflow, multi_tool_workflow
   - All fixtures follow Event Schema v2.0
   - See `fixtures/events/README.md` for usage examples

4. **Shared Test Configuration** (`tests/brainworm/conftest.py`)
   - Pytest fixtures for all test categories
   - Auto-markers based on test directory
   - Database and project setup utilities
   - Performance baseline fixtures

**Testing Philosophy**:
- Focus on real value, not just coverage
- Test actual bug scenarios
- Integration tests over implementation details
- End-to-end validation of critical paths
- Use realistic test data and workflows

**Hook Testing Best Practices**:

1. **PEP 723 Inline Dependencies**
   - All hooks MUST declare complete dependencies in `# /// script` blocks
   - Include ALL transitive dependencies (e.g., hook_framework requires `tomli-w>=1.0.0`)
   - Test hooks via subprocess execution with `uv run` to validate dependencies
   - CI automatically validates all dependencies

2. **Subprocess Execution Pattern**
   - Execute hooks via `subprocess.run(["uv", "run", hook_path], input=json_data)`
   - Pass input via stdin as JSON
   - Capture stdout/stderr for validation
   - Use timeouts to prevent hanging tests
   - Example from hook_test_harness:
     ```python
     result = subprocess.run(
         ["uv", "run", str(hook_script)],
         input=json.dumps(hook_input).encode(),
         capture_output=True,
         timeout=10,
         cwd=project_root
     )
     ```

3. **Event Storage Validation**
   - Verify events written to both SQLite database and JSONL logs
   - Validate correlation IDs, session IDs, and timestamps
   - Check PreToolUse/PostToolUse pairing
   - Use DatabaseValidator and CorrelationValidator utilities

4. **DAIC Workflow Testing**
   - Test tool blocking in discussion mode
   - Verify trigger phrase detection
   - Validate mode transitions (discussion → implementation)
   - Check permission decisions in hook output

**Event Storage Architecture**:
- **Database Location**: `.brainworm/events/hooks.db` (SQLite)
- **Schema**: `hook_events` table with session_id, correlation_id, hook_name, timestamp, execution_id, event_data
- **Indexes**: Optimized for queries by session_id, timestamp, hook_name
- **Debug Logging**: Optional debug logs at `.brainworm/logs/debug.jsonl` (enable via config.toml)
- **Event Schema v2.0**: Required fields include session_id, correlation_id, hook_name, timestamp_ns, execution_id

**CI/CD Integration**:

GitHub Actions workflow (`.github/workflows/test-brainworm.yml`):
- Runs on Python 3.11 and 3.12
- Installs dependencies via `uv sync --group dev`
- Validates PEP 723 dependencies before tests
- Runs full test suite with coverage reporting
- Runs ruff linter for code quality

**Dependency Validation**:

```bash
# Validate all dependencies (static + dynamic)
cd brainworm && python3 scripts/validate_dependencies.py --verbose

# Validate specific file
cd brainworm && python3 scripts/validate_dependencies.py --file hooks/your_hook.py
```

This validates:
- Version consistency with DEPENDENCIES.md standards
- Import completeness (catches missing transitive dependencies)
- No deprecated dependencies
- Scripts can actually execute with declared dependencies

**Adding Tests for New Hooks**:
1. **Unit Tests**: Test hook logic in isolation with mocked I/O
2. **Integration Tests**: Test hook with real state files and databases
3. **E2E Tests**: Test hook as part of complete workflow sequences
4. **Use Hook Test Harness**: Leverage existing infrastructure for realistic testing
5. **Validate Events**: Use event validators to ensure proper storage
6. **Test DAIC Integration**: If hook enforces DAIC, test blocking/allowing behavior

See `tests/brainworm/README.md` for comprehensive testing documentation.

### State Management

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

**Critical Rules**:
- NEVER edit state files directly
- Use state update hooks/scripts:
  - `./tasks set --task=<name> --branch=<branch>`
  - `uv run .brainworm/scripts/update_daic_mode.py --mode=<mode>`
  - `./tasks session set --session-id=<id>`

### Configuration

**Plugin Configuration** (`.brainworm/config.toml`):

Key sections:
- `[daic]` - DAIC workflow settings
- `[daic.branch_enforcement]` - Git branch rules
- `[debug]` - Debug output settings

**Customization**:
- Users can edit `.brainworm/config.toml` in their projects
- Plugin provides defaults via templates
- Document all config options in `docs/configuration.md`

### Version Management

**Updating Version**:

1. Edit `.claude-plugin/plugin.json`:
   ```json
   {
     "version": "1.0.0"  // Semantic versioning
   }
   ```

2. Update `CHANGELOG.md`:
   - Add version header with date
   - List new features, fixes, breaking changes
   - Include migration notes if needed

3. Follow semantic versioning:
   - **MAJOR**: Breaking changes
   - **MINOR**: New features (backward-compatible)
   - **PATCH**: Bug fixes (backward-compatible)

### Common Development Tasks

**Add a Subagent**:
1. Create `.md` file in `agents/`
2. Define agent purpose, tools, and usage
3. Add to CLAUDE.sessions.md agent list
4. Document in `docs/architecture.md`
5. Test with Task tool invocation

**Update a Protocol**:
1. Edit protocol in `protocols/`
2. Update template in `templates/protocols/`
3. Update CLAUDE.sessions.md references
4. Test protocol execution end-to-end

**Add Configuration Option**:
1. Update config schema in plugin templates
2. Handle in relevant scripts/hooks
3. Document in `docs/configuration.md`
4. Add to example config.toml

### Debugging

**Hook Execution**:

```bash
# Check logs
cat .brainworm/debug_*.log
cat .brainworm/timing/*.jsonl

# Test hook directly
echo '{"test": true}' | python3 hooks/your_hook.py
```

**State Issues**:

```bash
# Check current state
cat .brainworm/state/unified_session_state.json | jq

# Verify plugin root
./daic status
```

**Plugin Installation**:

```bash
# Install from local path
/plugin install brainworm@file:///absolute/path/to/cc-plugins/brainworm
```

## Integration with Repository

When developing brainworm within the cc-plugins repository:

**Repository Structure**:
- Plugin source: `brainworm/` (this directory)
- Tests: `../tests/brainworm/`
- Repository docs: `../CLAUDE.md`, `../README.md`

**Using Brainworm While Developing**:
- This repo has brainworm installed
- DAIC workflow applies to development
- Use trigger phrases to switch modes
- Task management available via `./tasks`

See repository `CLAUDE.md` for marketplace development guidelines.

## Related Documentation

**Plugin Documentation** (in `docs/`):
- [README.md](docs/README.md) - Documentation hub
- [getting-started.md](docs/getting-started.md) - Installation and quick start
- [daic-workflow.md](docs/daic-workflow.md) - DAIC methodology guide
- [task-management.md](docs/task-management.md) - Task lifecycle and best practices
- [cli-reference.md](docs/cli-reference.md) - Complete CLI documentation
- [configuration.md](docs/configuration.md) - Configuration options
- [protocols-and-agents.md](docs/protocols-and-agents.md) - Protocols and subagents
- [troubleshooting.md](docs/troubleshooting.md) - Common issues and solutions
- [architecture.md](docs/architecture.md) - System design for contributors
- [contributing.md](docs/contributing.md) - Development setup and guidelines
- [reference.md](docs/reference.md) - Technical reference

**User Documentation**:
- [README.md](README.md) - Plugin overview and quick start
- [CHANGELOG.md](CHANGELOG.md) - Version history

**Repository Documentation**:
- [../CLAUDE.md](../CLAUDE.md) - Marketplace development guide
- [../README.md](../README.md) - Marketplace overview

## Support

**Issues**: https://github.com/lsmith090/cc-plugins/issues

**Related Projects**:
- **Nautiloid**: Multi-project analytics aggregation
  - Repository: https://github.com/lsmith090/nautiloid

**Plugin Philosophy**: Enforce thoughtful development through DAIC methodology while learning from every interaction to continuously improve the development experience.
