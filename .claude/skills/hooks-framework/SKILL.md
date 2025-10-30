---
name: hooks-framework
description: Expert system for Claude Code hook development using the HooksFramework module. Provides deep knowledge of hook types, PEP 723 dependencies, typed schemas, testing patterns, event storage, and state management for brainworm-style plugin development.
triggers:
  - "implement a hook"
  - "add hook for"
  - "create hook"
  - "hook framework"
  - "how do hooks work"
  - "debug this hook"
  - "test the hook"
  - "hook dependencies"
  - "hook types"
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash]
---

# Hooks Framework Expert Skill

Develop Claude Code hooks using the HooksFramework pattern from the brainworm plugin. This skill covers hook implementation, PEP 723 dependencies, typed schemas, testing, event storage, and state management.

## When to Use This Skill

Use this skill when:
- Implementing new hook for Claude Code
- Debugging hook execution issues
- Understanding hook framework patterns
- Adding dependencies to existing hooks
- Writing tests for hook functionality
- Troubleshooting event logging
- Managing hook state and correlation

## Hook Framework Architecture

### Core Concepts

A hook is a Python script that Claude Code executes at specific lifecycle events. Brainworm uses a standardized framework (`utils/hook_framework.py`) that provides:
- Typed input/output schemas (`utils/hook_types.py`)
- Automatic event logging to SQLite + JSONL
- State management integration
- Debug logging infrastructure
- Graceful error handling

### Execution Flow

```
Claude Code → Hook stdin (JSON) → Hook Script (Python) → Hook stdout (JSON) → Claude Code
                                         ↓
                                   Side Effects:
                                   - Event storage (SQLite)
                                   - State updates (unified_session_state.json)
                                   - Debug logs (.brainworm/logs/)
```

## Hook Types (Summary)

**SessionStart** - Initialize state, setup infrastructure when session begins. See references/hook-types.md for schemas.

**PreToolUse** - Enforce policies, block/allow tools before execution. Returns `PreToolUseDecisionOutput` with approve/block decision. See references/hook-types.md for schemas.

**PostToolUse** - Track tool usage, analyze results after execution. See references/hook-types.md for schemas.

**UserPromptSubmit** - Detect trigger phrases, inject context before processing user input. See references/hook-types.md for schemas.

**SessionEnd** - Cleanup and finalization when session terminates.

**Stop** - Track interruptions when user stops Claude's response.

**Notification** - Log notification events.

For detailed schemas, use cases, and examples for each hook type, see **references/hook-types.md**.

## Quick Start

### 1. Use Hook Template

Start with template from **references/quick-patterns.md**:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
#     "filelock>=3.13.0",
# ]
# ///

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.hook_framework import HookFramework
from utils.hook_types import YourInputType, YourOutputType

def hook_logic(framework, typed_input):
    """Custom logic"""
    return None  # or YourOutputType

if __name__ == "__main__":
    HookFramework("hook_name", enable_event_logging=True) \
        .with_custom_logic(hook_logic) \
        .execute()
```

### 2. Add PEP 723 Dependencies

**CRITICAL:** Every hook MUST declare ALL dependencies, including transitive ones.

```python
# Minimal hook:
# dependencies = ["rich>=13.0.0", "filelock>=3.13.0"]

# Hook with config access:
# dependencies = ["rich>=13.0.0", "tomli-w>=1.0.0", "filelock>=3.13.0"]
```

If importing `utils.config`, must include `tomli-w>=1.0.0`. See **references/dependencies.md** for complete guide and standard versions.

### 3. Implement Logic Using Typed Schemas

```python
from utils.hook_types import PreToolUseInput, PreToolUseDecisionOutput
from utils.daic_state_manager import DAICStateManager

def pre_tool_use_logic(framework, typed_input):
    state_mgr = DAICStateManager(framework.project_root)
    daic_mode = state_mgr.get_daic_mode()

    if daic_mode == "discussion" and typed_input.tool_name == "Write":
        return PreToolUseDecisionOutput.block(
            reason="[DAIC: Tool Blocked] Write not allowed in discussion mode",
            validation_issues=["Write requires implementation mode"]
        )

    return PreToolUseDecisionOutput.approve()
```

### 4. Register in hooks.json

```json
{
  "PreToolUse": "Edit|Write|MultiEdit|NotebookEdit",
  "UserPromptSubmit": "*"
}
```

Pattern: Pipe-separated tool names for OR matching, `*` for all events.

### 5. Test with HookTestHarness

```python
from tests.brainworm.integration.hook_test_harness import HookTestHarness
import json

def test_hook(tmp_path, plugin_root):
    harness = HookTestHarness(tmp_path, plugin_root)
    harness.set_daic_mode("discussion")

    result = harness.execute_hook("pre_tool_use", "Write", {})
    output = json.loads(result.stdout)

    assert output["continue"] == False
```

See **references/testing.md** for comprehensive testing guide.

## State Management

Use `DAICStateManager` for all state operations:

```python
from utils.daic_state_manager import DAICStateManager

def hook_logic(framework, typed_input):
    state_mgr = DAICStateManager(framework.project_root)

    # Read state
    daic_mode = state_mgr.get_daic_mode()
    current_task = state_mgr.get_current_task()

    # Update state
    state_mgr.set_daic_mode("implementation", trigger="user_command")
    state_mgr.update_session_correlation(session_id, correlation_id)
```

Never edit state files directly - always use the state manager for atomic operations.

## Event Logging

HookFramework with `enable_event_logging=True` automatically logs events to:
- SQLite database: `.brainworm/events/hooks.db`
- JSONL logs: `.brainworm/logs/debug.jsonl` (if debug enabled)

Event logging captures hook execution, tool usage, timing, and correlation for workflow continuity.

## Debug Logging

Use framework's debug logger:

```python
def hook_logic(framework, typed_input):
    if framework.debug_logger:
        framework.debug_logger.info("Hook execution starting")
        framework.debug_logger.debug(f"Tool: {typed_input.tool_name}")
        framework.debug_logger.warning("Unexpected state")
        framework.debug_logger.error("Critical failure")
```

Enable in `.brainworm/config.toml`:
```toml
[debug]
enabled = true
level = "DEBUG"

[debug.outputs]
file = true
```

See **references/debugging.md** for troubleshooting guide.

## Implementation Checklist

Before deploying a hook:

- [ ] Hook script has PEP 723 inline dependencies
- [ ] All transitive dependencies included (check references/dependencies.md)
- [ ] `sys.path.insert(0, str(Path(__file__).parent.parent))` present
- [ ] Imports use typed schemas from hook_types
- [ ] HookFramework initialized with correct hook name
- [ ] Custom logic function defined
- [ ] Hook registered in hooks/hooks.json
- [ ] Unit tests written
- [ ] Integration tests with HookTestHarness
- [ ] Dependencies validated: `python3 scripts/validate_dependencies.py --file hooks/your_hook.py`
- [ ] Debug logging tested
- [ ] Event storage verified in database

## Common Patterns

### DAIC Workflow Enforcement

```python
def enforce_daic_workflow(framework, typed_input):
    state_mgr = DAICStateManager(framework.project_root)
    config = load_config(framework.project_root)

    daic_mode = state_mgr.get_daic_mode()
    blocked_tools = config["daic"]["blocked_tools"]

    if daic_mode == "discussion" and typed_input.tool_name in blocked_tools:
        return PreToolUseDecisionOutput.block(
            reason=f"[DAIC: Tool Blocked] {typed_input.tool_name} blocked in discussion mode",
            validation_issues=[f"Use trigger phrase to enable {typed_input.tool_name}"]
        )

    return PreToolUseDecisionOutput.approve()
```

### Trigger Phrase Detection

```python
def detect_trigger_phrases(framework, typed_input):
    config = load_config(framework.project_root)
    trigger_phrases = config["daic"]["trigger_phrases"]

    prompt_lower = typed_input.prompt.lower()

    for phrase in trigger_phrases:
        if phrase in prompt_lower:
            state_mgr = DAICStateManager(framework.project_root)
            state_mgr.set_daic_mode("implementation", trigger="trigger_phrase")

            return UserPromptContextResponse.create_context(
                context=f"[DAIC: Implementation Mode Activated] Trigger phrase '{phrase}' detected."
            )

    return None
```

See **references/quick-patterns.md** for more copy-paste ready code.

## Critical Gotchas

1. **Missing transitive dependencies** - If importing utils module that uses dependency, must include that dependency in PEP 723 block
2. **Direct state file edits** - Always use DAICStateManager, never edit JSON files directly
3. **Forgot sys.path insert** - Must add plugin root to sys.path or imports fail
4. **Wrong hook registration** - Tool names are case-sensitive in hooks.json, use pipe for OR
5. **Validation skipped** - Always run `validate_dependencies.py` before deploying

## Validation Commands

```bash
# Validate single hook dependencies
cd brainworm && python3 scripts/validate_dependencies.py --file hooks/your_hook.py

# Validate all hooks
python3 scripts/validate_dependencies.py --verbose

# Test hook directly
echo '{"session_id": "test", "cwd": "/tmp", "hook_event_name": "SessionStart"}' | \
    uv run hooks/your_hook.py

# Run hook tests
uv run pytest tests/brainworm/integration/test_your_hook.py -v

# View debug logs
tail -f .brainworm/logs/debug.jsonl | jq .
```

## Best Practices

**Performance:**
- Minimize I/O - only read/write files when necessary
- Fast execution - hooks should complete in < 100ms typically
- Lazy imports - import heavy dependencies only when needed
- Cache state - read state once, reuse throughout hook

**Reliability:**
- Fail-fast - use try/except with graceful degradation
- Atomic operations - use AtomicFileWriter for state updates
- Validation - validate input before processing
- Idempotency - hooks should be safe to re-run

**Maintainability:**
- Type hints - use typed schemas from hook_types.py
- Documentation - clear docstrings explaining purpose
- Testing - comprehensive unit + integration tests
- Logging - debug logs for troubleshooting

**Security:**
- Input sanitization - validate all tool inputs
- Path traversal - check file paths are within project
- Command injection - validate bash commands carefully
- Secrets - never log sensitive data

## Reference Documentation

For detailed information, see:
- **references/hook-types.md** - Complete schemas for all hook types with examples
- **references/dependencies.md** - PEP 723 dependency management and standard versions
- **references/testing.md** - Testing guide with HookTestHarness patterns
- **references/debugging.md** - Debugging techniques and troubleshooting
- **references/quick-patterns.md** - Copy-paste ready code for common scenarios

## File Locations

- **Hook scripts:** `brainworm/hooks/*.py`
- **Hook config:** `brainworm/hooks/hooks.json`
- **Hook types:** `brainworm/utils/hook_types.py`
- **Hook framework:** `brainworm/utils/hook_framework.py`
- **Test harness:** `tests/brainworm/integration/hook_test_harness.py`
- **Dependencies:** `brainworm/DEPENDENCIES.md`
- **Validation:** `brainworm/scripts/validate_dependencies.py`

## Example Implementation

See `brainworm/hooks/session_start.py` for comprehensive example showing:
- Auto-setup infrastructure
- State management
- Event logging
- Error handling
- Debug logging
- Session correlation
- Configuration management
