# Hook Testing Guide

Complete guide to testing Claude Code hooks with the HookTestHarness.

## Test Organization

Each plugin should have:
- **Unit tests**: Fast, isolated component tests
- **Integration tests**: Component interaction tests using HookTestHarness
- **E2E tests**: Complete workflow validation

## Using HookTestHarness

The HookTestHarness provides realistic hook execution for integration tests.

### Basic Test Pattern

```python
from tests.brainworm.integration.hook_test_harness import HookTestHarness
import json

def test_pre_tool_use_blocking(tmp_path, plugin_root):
    # Setup harness
    harness = HookTestHarness(tmp_path, plugin_root)
    harness.set_daic_mode("discussion")

    # Execute hook
    result = harness.execute_hook(
        "pre_tool_use",
        "Write",
        {"file_path": "/test.py", "content": "test"}
    )

    # Parse output
    output = json.loads(result.stdout)
    assert output["continue"] == False
    assert "DAIC: Tool Blocked" in output.get("stopReason", "")

    # Validate events
    db_events = harness.get_database_events()
    assert len(db_events) == 1
    assert db_events[0]["hook_name"] == "pre_tool_use"
    assert db_events[0]["tool_name"] == "Write"
```

## Testing Hook Sequences

Test multiple hooks in realistic order:

```python
def test_daic_workflow_sequence(tmp_path, plugin_root):
    harness = HookTestHarness(tmp_path, plugin_root)

    # Start in discussion mode
    harness.set_daic_mode("discussion")

    # User submits trigger phrase
    result1 = harness.execute_hook(
        "user_prompt_submit",
        None,
        {"prompt": "go ahead and implement this"}
    )

    # Verify mode switched
    state = harness._read_state()
    assert state["daic_mode"] == "implementation"

    # Now Write tool should be allowed
    result2 = harness.execute_hook(
        "pre_tool_use",
        "Write",
        {"file_path": "/test.py", "content": "test"}
    )

    output = json.loads(result2.stdout)
    assert output["continue"] == True
```

## Subprocess Execution Pattern

Hooks are executed via `uv run` in subprocesses:

```python
import subprocess
import json

def execute_hook_subprocess(hook_path, hook_input):
    result = subprocess.run(
        ["uv", "run", str(hook_path)],
        input=json.dumps(hook_input).encode(),
        capture_output=True,
        timeout=10,
        cwd=project_root
    )

    if result.returncode != 0:
        print(f"Hook failed: {result.stderr.decode()}")
        return None

    return json.loads(result.stdout.decode())
```

## Test Fixtures

Common pytest fixtures for hook testing:

```python
import pytest
from pathlib import Path

@pytest.fixture
def plugin_root():
    """Return path to brainworm plugin root"""
    return Path(__file__).parent.parent.parent / "brainworm"

@pytest.fixture
def tmp_project(tmp_path):
    """Create temporary project structure"""
    brainworm_dir = tmp_path / ".brainworm"
    (brainworm_dir / "state").mkdir(parents=True)
    (brainworm_dir / "events").mkdir(parents=True)
    (brainworm_dir / "logs").mkdir(parents=True)
    return tmp_path
```

## Running Tests

```bash
# Run all hook tests
uv run pytest tests/brainworm/integration/

# Run specific test file
uv run pytest tests/brainworm/integration/test_your_hook.py

# Run with verbose output
uv run pytest tests/brainworm/integration/ -v

# Run with coverage
uv run pytest --cov=brainworm tests/brainworm/integration/
```

## Common Assertions

**Check hook output:**
```python
output = json.loads(result.stdout)
assert output["continue"] == True  # or False
assert "expected message" in output.get("stopReason", "")
```

**Check state changes:**
```python
state = harness._read_state()
assert state["daic_mode"] == "implementation"
assert state["current_task"] == "task-name"
```

**Check event logging:**
```python
events = harness.get_database_events()
assert len(events) == 1
assert events[0]["hook_name"] == "pre_tool_use"
assert events[0]["tool_name"] == "Write"
```

**Check debug logs:**
```python
logs = harness.get_debug_logs()
assert any("expected log message" in log for log in logs)
```

## Best Practices

### Performance
- Unit tests should run in < 100ms
- Integration tests should run in < 1s
- Use fixtures to avoid repeated setup

### Reliability
- Test both success and failure paths
- Validate event storage and correlation
- Check error handling and graceful degradation
- Test with realistic input data

### Maintainability
- Clear test names describing what's tested
- Arrange-Act-Assert pattern
- Comments explaining complex setups
- Reusable fixtures for common scenarios
