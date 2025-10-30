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

You are an expert in developing Claude Code hooks using the HooksFramework pattern from the brainworm plugin. This skill provides comprehensive knowledge for implementing, testing, and debugging hooks.

## Hook Framework Architecture

### Core Concepts

**What is a Hook?**
A hook is a Python script that Claude Code executes at specific lifecycle events:
- `SessionStart` - When a new session begins
- `SessionEnd` - When a session terminates
- `UserPromptSubmit` - Before processing user input
- `PreToolUse` - Before executing a tool (can block/allow)
- `PostToolUse` - After tool execution completes
- `Stop` - When user stops Claude's response
- `Notification` - When Claude sends a notification

**Hook Framework Pattern:**
Brainworm uses a standardized framework (`utils/hook_framework.py`) that provides:
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

## Hook Types and Input Schemas

### SessionStart Hook

**When:** New Claude Code session begins
**Purpose:** Initialize state, setup infrastructure, auto-configure
**Input Schema:** `SessionStartInput`
```python
from utils.hook_types import SessionStartInput

# Fields available:
- session_id: str         # Unique session identifier
- transcript_path: str    # Path to session transcript
- cwd: str               # Current working directory
- hook_event_name: str   # Always "SessionStart"
```

**Common Use Cases:**
- Auto-setup `.brainworm/` directory structure
- Initialize databases and state files
- Populate session_id in unified state
- Generate wrapper scripts
- Configure Claude Code settings

**Example Pattern:**
```python
def session_start_logic(framework, typed_input):
    project_root = framework.project_root
    session_id = typed_input.session_id

    # Auto-setup infrastructure
    setup_directories(project_root)

    # Populate session correlation
    state_mgr = DAICStateManager(project_root)
    state_mgr.update_session_correlation(session_id, correlation_id)
```

### PreToolUse Hook

**When:** Before Claude Code executes a tool (Read, Write, Edit, Bash, etc.)
**Purpose:** Enforce policies, validate inputs, block/allow tools
**Input Schema:** `PreToolUseInput`
```python
from utils.hook_types import PreToolUseInput, parse_tool_input

# Fields available:
- session_id: str
- tool_name: str              # "Read", "Write", "Edit", "Bash", etc.
- tool_input: ToolInputVariant # Typed tool parameters
- cwd: str
- hook_event_name: str        # Always "PreToolUse"
```

**Output Schema:** `PreToolUseDecisionOutput`
```python
from utils.hook_types import PreToolUseDecisionOutput

# To allow tool:
return PreToolUseDecisionOutput.approve(reason="Tool allowed")

# To block tool:
return PreToolUseDecisionOutput.block(
    reason="[DAIC: Tool Blocked] You're in discussion mode",
    validation_issues=["Write tool blocked in discussion mode"],
    suppress_output=False
)
```

**Common Use Cases:**
- DAIC workflow enforcement (block Write/Edit in discussion mode)
- Security validation (prevent dangerous operations)
- Branch enforcement (ensure correct git branch)
- Command validation (block destructive bash commands)

**Example Pattern:**
```python
def pre_tool_use_logic(framework, typed_input):
    tool_name = typed_input.tool_name

    # Check DAIC mode
    state_mgr = DAICStateManager(framework.project_root)
    daic_mode = state_mgr.get_daic_mode()

    # Block blocked tools in discussion mode
    if daic_mode == "discussion" and tool_name in ["Write", "Edit"]:
        return PreToolUseDecisionOutput.block(
            reason=f"[DAIC: Tool Blocked] {tool_name} not allowed in discussion mode",
            validation_issues=[f"{tool_name} requires implementation mode"]
        )

    return PreToolUseDecisionOutput.approve()
```

### PostToolUse Hook

**When:** After Claude Code completes a tool execution
**Purpose:** Track tool usage, analyze results, update analytics
**Input Schema:** `PostToolUseInput`
```python
from utils.hook_types import PostToolUseInput

# Fields available:
- session_id: str
- tool_name: str
- tool_input: ToolInputVariant
- tool_response: ToolResponse  # Tool execution results
- cwd: str
```

**Common Use Cases:**
- Analytics collection (track which tools are used)
- Error detection (identify failed operations)
- Pattern learning (understand development flows)
- Performance tracking (measure execution times)

### UserPromptSubmit Hook

**When:** User submits a prompt to Claude
**Purpose:** Context injection, intent analysis, trigger detection
**Input Schema:** `UserPromptSubmitInput`
```python
from utils.hook_types import UserPromptSubmitInput

# Fields available:
- session_id: str
- prompt: str           # User's input text
- cwd: str
```

**Output Schema:** `UserPromptContextResponse`
```python
from utils.hook_types import UserPromptContextResponse

# Inject context into prompt:
return UserPromptContextResponse.create_context(
    context="[[ ultrathink ]]",
    debug_info={"api_mode": True}
)
```

**Common Use Cases:**
- Trigger phrase detection ("go ahead" → switch to implementation mode)
- API mode management (auto-enable ultrathink)
- Context injection (add system reminders)
- Intent analysis (understand user goals)

## PEP 723 Dependency Management

### Critical Rule: Complete Inline Dependencies

**Every hook MUST declare ALL dependencies in inline script metadata.**

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
#     "filelock>=3.13.0",
# ]
# ///
```

### Standard Dependency Versions (from DEPENDENCIES.md)

**Core Dependencies:**
- `rich>=13.0.0` - UI formatting, console output
- `filelock>=3.13.0` - Atomic file operations
- `tomli-w>=1.0.0` - TOML writing (reading uses built-in `tomllib`)
- `typer>=0.9.0` - CLI framework
- `tiktoken>=0.7.0` - Token counting
- `pendulum>=3.0.0` - Advanced datetime handling

### Transitive Dependencies

**CRITICAL:** If you import a utility that uses a dependency, you MUST include that dependency.

**Example:**
```python
# If you import utils.config:
from utils.config import load_config

# utils.config uses tomli-w, so you MUST include it:
# dependencies = [
#     "rich>=13.0.0",
#     "tomli-w>=1.0.0",  # Required by utils.config
#     "filelock>=3.13.0",
# ]
```

### Common Patterns

**Hook using HookFramework (minimal):**
```python
# dependencies = [
#     "rich>=13.0.0",
#     "filelock>=3.13.0",
# ]
```

**Hook with config access:**
```python
# dependencies = [
#     "rich>=13.0.0",
#     "tomli-w>=1.0.0",  # For utils.config
#     "filelock>=3.13.0",
# ]
```

**CLI script with Typer:**
```python
# dependencies = [
#     "rich>=13.0.0",
#     "typer>=0.9.0",
# ]
```

### Validation

Always validate dependencies after adding/changing them:

```bash
cd brainworm
python3 scripts/validate_dependencies.py --file hooks/your_hook.py
python3 scripts/validate_dependencies.py --verbose  # Check all files
```

## Hook Implementation Patterns

### Basic Hook Structure

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
#     "filelock>=3.13.0",
# ]
# ///

"""
Hook Name - Purpose Description

Brief description of what this hook does.
"""

# Add plugin root to sys.path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.hook_framework import HookFramework
from utils.hook_types import PreToolUseInput, PreToolUseDecisionOutput

def hook_logic(framework, typed_input):
    """Custom hook logic"""
    project_root = framework.project_root

    # Your logic here

    # Return decision (PreToolUse) or None (other hooks)
    return PreToolUseDecisionOutput.approve()

if __name__ == "__main__":
    HookFramework("pre_tool_use", enable_event_logging=True) \\
        .with_custom_logic(hook_logic) \\
        .execute()
```

### State Management Pattern

```python
from utils.daic_state_manager import DAICStateManager

def hook_logic(framework, typed_input):
    project_root = framework.project_root
    state_mgr = DAICStateManager(project_root)

    # Read state
    unified_state = state_mgr.get_unified_state()
    daic_mode = state_mgr.get_daic_mode()
    current_task = state_mgr.get_current_task()

    # Update state
    state_mgr.set_daic_mode("implementation", trigger="user_command")
    state_mgr.update_session_correlation(session_id, correlation_id)
```

### Event Logging Pattern

**Automatic:** HookFramework with `enable_event_logging=True` automatically logs events to:
- SQLite database: `.brainworm/events/hooks.db`
- JSONL logs: `.brainworm/logs/debug.jsonl` (if debug enabled)

**Manual Event Logging:**
```python
from utils.event_logger import get_event_logger

def hook_logic(framework, typed_input):
    logger = get_event_logger(framework.project_root)

    # Log custom event
    logger.log_event({
        "hook_name": "custom_hook",
        "session_id": typed_input.session_id,
        "correlation_id": framework.correlation_id,
        "custom_data": {"key": "value"}
    })
```

### Debug Logging Pattern

```python
def hook_logic(framework, typed_input):
    # Use framework's debug logger
    if framework.debug_logger:
        framework.debug_logger.info("Hook starting")
        framework.debug_logger.debug(f"Tool: {typed_input.tool_name}")
        framework.debug_logger.warning("Unexpected state")
        framework.debug_logger.error("Critical failure")
```

## Testing Hooks

### Using HookTestHarness

```python
from tests.brainworm.integration.hook_test_harness import HookTestHarness

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

### Test Organization

**Unit Tests:**
- Test hook logic in isolation
- Mock file I/O and subprocess calls
- Fast (< 100ms per test)

**Integration Tests:**
- Test hooks with real state files and databases
- Use HookTestHarness for realistic execution
- Validate event storage and correlation

**E2E Tests:**
- Test complete workflow sequences
- Multiple hooks in realistic order
- Verify state transitions and event chains

### Subprocess Execution Pattern

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

## Common Hook Patterns

### DAIC Workflow Enforcement

```python
def enforce_daic_workflow(framework, typed_input):
    """Block tools in discussion mode"""
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
    """Check for DAIC trigger phrases"""
    config = load_config(framework.project_root)
    trigger_phrases = config["daic"]["trigger_phrases"]

    prompt_lower = typed_input.prompt.lower()

    for phrase in trigger_phrases:
        if phrase in prompt_lower:
            # Switch to implementation mode
            state_mgr = DAICStateManager(framework.project_root)
            state_mgr.set_daic_mode("implementation", trigger="trigger_phrase")

            return UserPromptContextResponse.create_context(
                context="[DAIC: Implementation Mode Activated] " +
                        f"Trigger phrase '{phrase}' detected."
            )

    return None
```

### Session Correlation

```python
def initialize_session_correlation(framework, typed_input):
    """Set up session and correlation IDs"""
    project_root = framework.project_root
    session_id = typed_input.session_id

    state_mgr = DAICStateManager(project_root)

    # Generate correlation ID from session
    correlation_id = session_id[:16] if len(session_id) >= 16 else session_id

    # Update unified state
    state_mgr.update_session_correlation(session_id, correlation_id)

    if framework.debug_logger:
        framework.debug_logger.info(f"Session: {session_id[:8]}, Correlation: {correlation_id}")
```

## Debugging Hooks

### Enable Debug Logging

In `.brainworm/config.toml`:
```toml
[debug]
enabled = true
level = "DEBUG"
format = "json"

[debug.outputs]
stderr = false
file = true
framework = true
```

### Reading Debug Logs

```bash
# View JSON logs
tail -f .brainworm/logs/debug.jsonl

# Parse with jq
cat .brainworm/logs/debug.jsonl | jq '.message'

# Filter by hook
cat .brainworm/logs/debug.jsonl | jq 'select(.hook_name == "pre_tool_use")'
```

### Common Issues

**Hook fails silently:**
- Check stderr output: Hook might be failing before logging
- Verify PEP 723 dependencies are complete
- Run hook directly: `uv run hooks/your_hook.py < test_input.json`

**Import errors:**
- Ensure `sys.path.insert(0, str(Path(__file__).parent.parent))` is present
- Check that utils/ directory is accessible from hook location
- Verify plugin_root is correctly set in unified state

**State not updating:**
- Use DAICStateManager, not direct file writes
- Check file permissions on .brainworm/state/
- Verify AtomicFileWriter is used for concurrent access

**Events not logging:**
- Confirm `enable_event_logging=True` in HookFramework
- Check database exists: `.brainworm/events/hooks.db`
- Verify event_logger has write permissions

## Hook Registration

### Update hooks.json

After creating a hook, register it in `hooks/hooks.json`:

```json
{
  "PreToolUse": "Edit|Write|MultiEdit|NotebookEdit",
  "PostToolUse": "Edit|Write|Read|Bash",
  "UserPromptSubmit": "*",
  "SessionStart": "*",
  "YourNewHook": "ToolName1|ToolName2"
}
```

**Pattern:** `"HookEvent": "matcher"`
- Use pipe `|` for OR matching
- Use `*` for all events
- Tool names are case-sensitive

## Best Practices

### Performance

1. **Minimize I/O:** Only read/write files when necessary
2. **Fast execution:** Hooks should complete in < 100ms typically
3. **Lazy imports:** Import heavy dependencies only when needed
4. **Cache state:** Read state once, reuse throughout hook

### Reliability

1. **Fail-fast:** Use try/except with graceful degradation
2. **Atomic operations:** Use AtomicFileWriter for state updates
3. **Validation:** Validate input before processing
4. **Idempotency:** Hooks should be safe to re-run

### Maintainability

1. **Type hints:** Use typed schemas from hook_types.py
2. **Documentation:** Clear docstrings explaining purpose
3. **Testing:** Comprehensive unit + integration tests
4. **Logging:** Debug logs for troubleshooting

### Security

1. **Input sanitization:** Validate all tool inputs
2. **Path traversal:** Check file paths are within project
3. **Command injection:** Validate bash commands carefully
4. **Secrets:** Never log sensitive data

## Quick Reference

### Hook Execution Checklist

- [ ] Hook script has PEP 723 inline dependencies
- [ ] All transitive dependencies included
- [ ] sys.path includes plugin root
- [ ] Imports use typed schemas from hook_types
- [ ] HookFramework initialized with correct hook name
- [ ] Custom logic function defined
- [ ] Hook registered in hooks/hooks.json
- [ ] Unit tests written
- [ ] Integration tests with HookTestHarness
- [ ] Dependencies validated with validation script
- [ ] Debug logging tested
- [ ] Event storage verified in database

### File Locations

- **Hook scripts:** `brainworm/hooks/*.py`
- **Hook config:** `brainworm/hooks/hooks.json`
- **Hook types:** `brainworm/utils/hook_types.py`
- **Hook framework:** `brainworm/utils/hook_framework.py`
- **Test harness:** `tests/brainworm/integration/hook_test_harness.py`
- **Dependencies:** `brainworm/DEPENDENCIES.md`
- **Validation:** `brainworm/scripts/validate_dependencies.py`

### Common Commands

```bash
# Validate dependencies
cd brainworm && python3 scripts/validate_dependencies.py --file hooks/your_hook.py

# Test hook directly
echo '{"session_id": "test", "cwd": "/tmp", "hook_event_name": "SessionStart"}' | \\
    uv run hooks/your_hook.py

# Run tests
uv run pytest tests/brainworm/integration/test_your_hook.py

# Enable debug logging
# Edit .brainworm/config.toml: debug.enabled = true

# View debug logs
tail -f .brainworm/logs/debug.jsonl | jq .
```

## Example: Complete Hook Implementation

See `brainworm/hooks/session_start.py` for a comprehensive example showing:
- Auto-setup infrastructure
- State management
- Event logging
- Error handling
- Debug logging
- Session correlation
- Configuration management

## When to Use This Skill

Use this skill when you need to:
- Implement a new hook for Claude Code
- Debug hook execution issues
- Understand hook framework patterns
- Add dependencies to existing hooks
- Write tests for hook functionality
- Troubleshoot event logging
- Manage hook state and correlation

This skill provides expert-level knowledge of the brainworm hook framework and should guide all hook development in the repository.
