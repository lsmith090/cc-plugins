# Contributing to Brainworm

Guide for developers who want to contribute to brainworm.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Development Workflow](#development-workflow)
- [Adding Features](#adding-features)
- [Submitting Changes](#submitting-changes)
- [Release Process](#release-process)

## Getting Started

### Prerequisites

- Python 3.12 or higher
- Git
- Claude Code installed
- `uv` package manager (for dependency management)

### Repository Structure

```
cc-plugins/
├── brainworm/              # Plugin source (installed to user projects)
│   ├── .claude-plugin/
│   ├── hooks/
│   ├── agents/
│   ├── commands/
│   ├── scripts/
│   ├── utils/
│   ├── templates/
│   ├── docs/
│   ├── README.md
│   ├── CLAUDE.md
│   └── CHANGELOG.md
├── tests/brainworm/        # Test suites (NOT installed)
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── fixtures/
├── pyproject.toml          # Python project config
└── README.md               # Marketplace overview
```

**Key Separation:**
- Plugin files in `brainworm/` - Distributed to users
- Tests in `tests/brainworm/` - Development only

### Clone and Setup

1. **Clone repository:**
   ```bash
   git clone https://github.com/lsmith090/cc-plugins.git
   cd cc-plugins
   ```

2. **Install dependencies:**
   ```bash
   uv sync --group dev
   ```

3. **Install brainworm in test project:**
   ```bash
   cd /path/to/test-project
   /plugin install brainworm@file:///absolute/path/to/cc-plugins/brainworm
   ```

4. **Verify installation:**
   ```bash
   # In test project
   ./daic status
   ./tasks status
   ```

## Development Setup

### Development Environment

**Recommended Tools:**
- VS Code or PyCharm
- Python 3.12+ with type checking (mypy/pyright)
- Git with commit signing configured

**Editor Configuration:**

VS Code `.vscode/settings.json`:
```json
{
  "python.linting.enabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.testing.pytestEnabled": true
}
```

### Running Tests

**All tests:**
```bash
uv run pytest tests/brainworm/
```

**Specific test suites:**
```bash
uv run pytest tests/brainworm/unit/          # Fast unit tests
uv run pytest tests/brainworm/integration/   # Integration tests
uv run pytest tests/brainworm/e2e/           # E2E tests (slow)
```

**With coverage:**
```bash
uv run pytest --cov=brainworm --cov-report=term-missing tests/brainworm/
```

**E2E tests** (marked as slow):
```bash
uv run pytest tests/brainworm/e2e/ --runslow
```

### Linting and Formatting

**Run ruff:**
```bash
ruff check .
ruff format .
```

**Type checking:**
```bash
mypy brainworm/
```

### Dependency Validation

**Critical:** All hooks and scripts MUST declare complete inline dependencies.

**Validate dependencies:**
```bash
cd brainworm
python3 scripts/validate_dependencies.py --verbose
```

**Validate specific file:**
```bash
cd brainworm
python3 scripts/validate_dependencies.py --file hooks/your_hook.py
```

This validates:
- Version consistency with DEPENDENCIES.md
- Import completeness (catches missing transitive deps)
- No deprecated dependencies
- Scripts can execute with declared dependencies

## Code Standards

### Python Style

**Follow PEP 8:**
- Line length: 120 characters
- Use 4 spaces for indentation
- Use double quotes for strings

**Type Hints:**
```python
def update_task(
    task_name: str,
    branch: str,
    services: list[str] | None = None
) -> dict[str, Any]:
    """Update task state.

    Args:
        task_name: Name of the task
        branch: Git branch name
        services: Optional list of affected services

    Returns:
        Updated state dictionary
    """
    # Implementation
    pass
```

**Docstrings:**
- Use Google-style docstrings
- Document all public functions
- Include Args, Returns, Raises sections

### Hook Development

**PEP 723 Inline Dependencies** (CRITICAL):
```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
#     "tomli-w>=1.0.0",
#     "filelock>=3.13.0",
# ]
# ///

import sys
from pathlib import Path
```

**Include ALL dependencies:**
- Direct imports AND transitive dependencies
- Example: If importing `hook_framework`, add `tomli-w>=1.0.0`
- Validate with `validate_dependencies.py`

**Use Hook Framework:**
```python
from utils.hook_framework import execute_hook
from utils.hook_types import PreToolUseInput, PreToolUseOutput

def process_hook(input_data: PreToolUseInput) -> PreToolUseOutput:
    """Process the hook with type-safe I/O."""
    # Hook logic here
    return PreToolUseOutput(
        permission="allow",
        user_message="Tool allowed"
    )

if __name__ == "__main__":
    execute_hook(process_hook)
```

### Script Development

**Use Typer for CLI:**
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
    name="command-name",
    help="Command description",
    no_args_is_help=True
)

@app.command(name="subcommand")
def subcommand(
    arg: str = typer.Argument(..., help="Argument help"),
    option: bool = typer.Option(False, "--flag", help="Option help")
) -> None:
    """Subcommand description."""
    # Implementation
    pass

if __name__ == "__main__":
    app()
```

### Error Handling

**Fail-fast with clear messages:**
```python
# Good
if not task_file.exists():
    raise FileNotFoundError(
        f"Task file not found: {task_file}\n"
        f"Expected at: .brainworm/tasks/{task_name}/README.md"
    )

# Bad
if not task_file.exists():
    return None  # Silent failure
```

**Use structured errors:**
```python
from utils.hook_types import HookOutput

# Return structured error from hooks
return HookOutput(
    permission="deny",
    user_message="[DAIC: Tool Blocked] You're in discussion mode."
)
```

### State Management

**Always use DAICStateManager:**
```python
from utils.daic_state_manager import DAICStateManager

# Good
manager = DAICStateManager()
state = manager.get_state()
manager.update_daic_mode("discussion")

# Bad - don't edit state files directly
with open(".brainworm/state/unified_session_state.json", "w") as f:
    json.dump(state, f)  # Race conditions!
```

## Testing

### Test Organization

**Directory Structure:**
```
tests/brainworm/
├── unit/                   # Fast, isolated tests
│   ├── test_daic_state_manager.py
│   ├── test_bash_validator.py
│   └── ...
├── integration/            # Component interaction tests
│   ├── test_hook_execution.py
│   ├── test_event_storage.py
│   └── hook_test_harness.py
├── e2e/                    # End-to-end workflows
│   ├── test_task_creation_workflow.py
│   ├── test_daic_blocking_workflow.py
│   └── ...
├── fixtures/               # Test data
│   └── events/
├── validation/             # Validators
│   ├── db_validator.py
│   ├── jsonl_validator.py
│   └── correlation_validator.py
└── conftest.py            # Shared fixtures
```

### Writing Tests

**Unit Tests:**
```python
import pytest
from brainworm.utils.bash_validator import BashValidator

def test_read_only_command_allowed():
    """Test that read-only commands are allowed."""
    validator = BashValidator()
    assert validator.is_read_only("git status")
    assert validator.is_read_only("ls -la")

def test_write_command_blocked():
    """Test that write commands are blocked."""
    validator = BashValidator()
    assert not validator.is_read_only("git commit -m 'test'")
    assert not validator.is_read_only("rm -rf /")
```

**Integration Tests:**
```python
import pytest
from tests.brainworm.integration.hook_test_harness import HookTestHarness

def test_daic_blocking(tmp_path):
    """Test DAIC blocks tools in discussion mode."""
    harness = HookTestHarness(tmp_path, plugin_root)

    # Set discussion mode
    harness.set_daic_mode("discussion")

    # Try to use Edit tool
    result = harness.execute_hook(
        "pre_tool_use",
        "Edit",
        {"file_path": "/test.py"}
    )

    # Should be blocked
    assert result["permission"] == "deny"
    assert "discussion mode" in result["user_message"].lower()
```

**E2E Tests:**
```python
import pytest

@pytest.mark.slow
def test_complete_task_workflow(tmp_path):
    """Test complete task creation to completion workflow."""
    # Create task
    # Gather context
    # Switch to implementation
    # Make changes
    # Complete task
    # Verify all state correct
    pass
```

### Test Best Practices

**Focus on Real Value:**
- Test actual bug scenarios
- Test critical paths (DAIC enforcement, state management)
- Test error handling and edge cases

**Use Fixtures:**
```python
@pytest.fixture
def test_project(tmp_path):
    """Create a test project with brainworm initialized."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    # Initialize brainworm structure
    # Return project_root
    pass

def test_something(test_project):
    """Test uses the fixture."""
    assert (test_project / ".brainworm").exists()
```

**Validate Events:**
```python
from tests.brainworm.validation.db_validator import DatabaseValidator

def test_event_logged(test_project):
    """Test that events are properly logged."""
    # Trigger event
    # ...

    # Validate event in database
    validator = DatabaseValidator(test_project / ".brainworm/events/hooks.db")
    events = validator.get_events_by_hook("pre_tool_use")
    assert len(events) == 1
    assert events[0]["event_data"]["tool_name"] == "Edit"
```

## Development Workflow

### Using Brainworm While Developing Brainworm

This repository has brainworm installed, so:

**DAIC Workflow Applies:**
- Start in discussion mode
- Use trigger phrases: "go ahead", "make it so"
- Manual switch: `/brainworm:daic implementation`

**Task Management Available:**
- Create tasks: `./tasks create fix-bug-123`
- Track work: `./tasks status`
- Follow protocols for completion

### Branch Strategy

**Branch Types:**
- `feature/brainworm-<feature-name>` - New features
- `fix/brainworm-<issue>` - Bug fixes
- `refactor/brainworm-<component>` - Refactoring
- `docs/brainworm-<area>` - Documentation
- `test/brainworm-<scope>` - Test improvements

### Commit Messages

**Follow Conventional Commits:**
```
feat(brainworm): Add custom trigger phrase support

- Add /brainworm:add-trigger slash command
- Update config.toml schema
- Add trigger phrase validation

Closes #123
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `refactor` - Code refactoring
- `docs` - Documentation
- `test` - Test additions/changes
- `chore` - Maintenance

**Scope:** Always include `brainworm` to distinguish from other plugins.

### Code Review Checklist

Before submitting:

**Code Quality:**
- [ ] Follows code standards
- [ ] Type hints on all functions
- [ ] Docstrings on public functions
- [ ] No linting errors (`ruff check .`)
- [ ] Formatted (`ruff format .`)

**Testing:**
- [ ] Tests added for new functionality
- [ ] All tests pass (`pytest tests/brainworm/`)
- [ ] Coverage maintained or improved

**Dependencies:**
- [ ] PEP 723 dependencies complete
- [ ] Validated (`validate_dependencies.py`)
- [ ] Versions match DEPENDENCIES.md standards

**Documentation:**
- [ ] Updated relevant docs in `brainworm/docs/`
- [ ] CHANGELOG.md updated
- [ ] README.md updated if needed

## Adding Features

### Adding a Hook

1. **Create hook file:**
   ```bash
   touch brainworm/hooks/my_new_hook.py
   chmod +x brainworm/hooks/my_new_hook.py
   ```

2. **Implement with framework:**
   ```python
   #!/usr/bin/env python3
   # /// script
   # requires-python = ">=3.12"
   # dependencies = [
   #     "rich>=13.0.0",
   #     "tomli-w>=1.0.0",
   # ]
   # ///

   from utils.hook_framework import execute_hook
   from utils.hook_types import MyHookInput, MyHookOutput

   def process_hook(input_data: MyHookInput) -> MyHookOutput:
       # Implementation
       return MyHookOutput(...)

   if __name__ == "__main__":
       execute_hook(process_hook)
   ```

3. **Register in hooks.json:**
   ```json
   {
     "MyNewHook": "*"
   }
   ```

4. **Add tests:**
   - Unit test in `tests/brainworm/unit/test_my_new_hook.py`
   - Integration test if needed

5. **Validate dependencies:**
   ```bash
   cd brainworm
   python3 scripts/validate_dependencies.py --file hooks/my_new_hook.py
   ```

6. **Update documentation:**
   - Add to `docs/reference.md` hook list
   - Update `docs/architecture.md` if architectural change

### Adding a Script

1. **Create script:**
   ```bash
   touch brainworm/scripts/my_script.py
   chmod +x brainworm/scripts/my_script.py
   ```

2. **Implement with Typer:**
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
   # Implementation
   ```

3. **Add tests:**
   - Test in `tests/brainworm/unit/test_my_script.py`

4. **Update CLI reference:**
   - Add to `docs/cli-reference.md` if user-facing

### Adding an Agent

1. **Create agent definition:**
   ```bash
   touch brainworm/agents/my-agent.md
   ```

2. **Define agent:**
   ```markdown
   ---
   name: my-agent
   description: What this agent does and when to use it
   tools: Read, Grep, Glob, Edit
   ---

   # My Agent

   Instructions for the agent...
   ```

3. **Document usage:**
   - Add to `docs/protocols-and-agents.md`

4. **Test agent invocation:**
   - E2E test in `tests/brainworm/e2e/`

### Adding a Configuration Option

1. **Update config template:**
   ```python
   # In session_start hook
   config = {
       "my_section": {
           "my_option": "default_value"
       }
   }
   ```

2. **Document in configuration.md:**
   - Add to appropriate section
   - Explain purpose and values

3. **Add tests:**
   - Test config loading
   - Test option usage

## Submitting Changes

### Pull Request Process

1. **Create feature branch:**
   ```bash
   git checkout -b feature/brainworm-my-feature
   ```

2. **Make changes and commit:**
   ```bash
   git add .
   git commit -m "feat(brainworm): Add my feature"
   ```

3. **Run tests:**
   ```bash
   uv run pytest tests/brainworm/
   ruff check .
   ```

4. **Validate dependencies:**
   ```bash
   cd brainworm
   python3 scripts/validate_dependencies.py --verbose
   ```

5. **Push and create PR:**
   ```bash
   git push origin feature/brainworm-my-feature
   # Create PR on GitHub
   ```

6. **PR Description Template:**
   ```markdown
   ## Summary
   Brief description of changes

   ## Changes
   - Change 1
   - Change 2

   ## Testing
   - [ ] Unit tests added
   - [ ] Integration tests added
   - [ ] All tests pass
   - [ ] Dependencies validated

   ## Documentation
   - [ ] CHANGELOG.md updated
   - [ ] Relevant docs updated

   ## Closes
   Closes #123
   ```

### Code Review

**What reviewers check:**
- Code quality and style
- Test coverage
- Documentation completeness
- Dependency validation
- No breaking changes (or properly documented)

**Addressing feedback:**
- Make requested changes
- Push to same branch
- PR updates automatically

## Release Process

### Version Numbering

Use semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR:** Breaking changes
- **MINOR:** New features (backward-compatible)
- **PATCH:** Bug fixes (backward-compatible)

### Release Steps

1. **Update version:**
   ```json
   // brainworm/.claude-plugin/plugin.json
   {
     "version": "1.2.0"
   }
   ```

2. **Update CHANGELOG.md:**
   ```markdown
   ## [1.2.0] - 2025-10-20

   ### Added
   - New feature X

   ### Changed
   - Improved Y

   ### Fixed
   - Bug Z
   ```

3. **Test installation:**
   ```bash
   /plugin install brainworm@file:///path/to/cc-plugins/brainworm
   ```

4. **Create release commit:**
   ```bash
   git add brainworm/
   git commit -m "release(brainworm): v1.2.0"
   git tag brainworm-v1.2.0
   ```

5. **Push:**
   ```bash
   git push origin main --tags
   ```

### Breaking Changes

If release includes breaking changes:

1. **Document migration:**
   - Add migration guide to CHANGELOG.md
   - Update documentation

2. **Bump MAJOR version:**
   - `1.5.0` → `2.0.0`

3. **Communicate to users:**
   - GitHub release notes
   - Clear upgrade instructions

## Community Guidelines

### Code of Conduct

- Be respectful and professional
- Focus on constructive feedback
- Help newcomers learn
- Assume good faith

### Getting Help

**Questions:**
- GitHub Discussions for general questions
- Issues for bug reports
- Pull requests for contributions

**Documentation:**
- Read existing docs first
- Check issues for known problems
- Ask before starting major work

## See Also

- **[Architecture](architecture.md)** - System design and patterns
- **[Reference](reference.md)** - Technical schemas and APIs
- **[Testing Documentation](../tests/brainworm/README.md)** - Detailed testing guide
- **[Repository CLAUDE.md](../CLAUDE.md)** - Repository development guide

---

**[← Back to Documentation Home](README.md)** | **[Next: Reference →](reference.md)**
