# Hook Framework Quick Patterns

Quick copy-paste patterns for common hook scenarios. This file contains minimal boilerplate code ready for immediate use.

For detailed explanations and schemas, see:
- **hook-types.md** - Complete hook type documentation
- **dependencies.md** - Dependency management guide
- **testing.md** - Testing patterns and best practices
- **debugging.md** - Troubleshooting and debugging techniques

## Minimal Hook Template

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
#     "filelock>=3.13.0",
# ]
# ///

"""Hook Name - Purpose"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.hook_framework import HookFramework
from utils.hook_types import YourInputType, YourOutputType

def hook_logic(framework, typed_input):
    """Custom logic"""
    return None  # or YourOutputType

if __name__ == "__main__":
    HookFramework("hook_name", enable_event_logging=True) \\
        .with_custom_logic(hook_logic) \\
        .execute()
```

## PreToolUse: Block Tool in Discussion Mode

```python
from utils.hook_types import PreToolUseInput, PreToolUseDecisionOutput
from utils.daic_state_manager import DAICStateManager

def pre_tool_use_logic(framework, typed_input):
    state_mgr = DAICStateManager(framework.project_root)
    daic_mode = state_mgr.get_daic_mode()

    blocked_tools = ["Write", "Edit", "MultiEdit", "NotebookEdit"]

    if daic_mode == "discussion" and typed_input.tool_name in blocked_tools:
        return PreToolUseDecisionOutput.block(
            reason=f"[DAIC: Tool Blocked] {typed_input.tool_name} not allowed in discussion mode",
            validation_issues=[f"{typed_input.tool_name} requires implementation mode"],
            suppress_output=False
        )

    return PreToolUseDecisionOutput.approve()
```

## UserPromptSubmit: Trigger Phrase Detection

```python
from utils.hook_types import UserPromptSubmitInput, UserPromptContextResponse
from utils.daic_state_manager import DAICStateManager
from utils.config import load_config

def user_prompt_logic(framework, typed_input):
    config = load_config(framework.project_root)
    trigger_phrases = config["daic"]["trigger_phrases"]

    prompt_lower = typed_input.prompt.lower()

    for phrase in trigger_phrases:
        if phrase in prompt_lower:
            state_mgr = DAICStateManager(framework.project_root)
            state_mgr.set_daic_mode("implementation", trigger="trigger_phrase")

            return UserPromptContextResponse.create_context(
                context=f"[DAIC: Implementation Mode Activated] Trigger phrase '{phrase}' detected.",
                debug_info={"trigger": phrase, "mode": "implementation"}
            )

    return None
```

## SessionStart: Initialize Session

```python
from utils.hook_types import SessionStartInput
from utils.daic_state_manager import DAICStateManager

def session_start_logic(framework, typed_input):
    project_root = framework.project_root
    session_id = typed_input.session_id

    # Setup directories
    brainworm_dir = project_root / ".brainworm"
    (brainworm_dir / "state").mkdir(parents=True, exist_ok=True)
    (brainworm_dir / "events").mkdir(parents=True, exist_ok=True)

    # Initialize session correlation
    state_mgr = DAICStateManager(project_root)
    correlation_id = session_id[:16] if len(session_id) >= 16 else session_id
    state_mgr.update_session_correlation(session_id, correlation_id)

    if framework.debug_logger:
        session_short = session_id[:8]
        framework.debug_logger.info(f"Session started: {session_short}")
```

## PostToolUse: Track Tool Usage

```python
from utils.hook_types import PostToolUseInput
from utils.event_logger import get_event_logger

def post_tool_use_logic(framework, typed_input):
    logger = get_event_logger(framework.project_root)

    # Log tool usage analytics
    logger.log_event({
        "hook_name": "post_tool_use",
        "session_id": typed_input.session_id,
        "tool_name": typed_input.tool_name,
        "tool_succeeded": typed_input.tool_response is not None,
        "custom_analytics": {
            "file_path": getattr(typed_input.tool_input, "file_path", None)
        }
    })
```

## State Management: Read/Write DAIC Mode

```python
from utils.daic_state_manager import DAICStateManager

def manage_daic_mode(project_root):
    state_mgr = DAICStateManager(project_root)

    # Read current mode
    current_mode = state_mgr.get_daic_mode()  # "discussion" or "implementation"

    # Set new mode
    state_mgr.set_daic_mode("implementation", trigger="user_command")

    # Get full unified state
    state = state_mgr.get_unified_state()
    current_task = state.get("current_task")
    current_branch = state.get("current_branch")

    # Update session correlation
    state_mgr.update_session_correlation("session-id", "correlation-id")
```

## Testing: Basic Test with HookTestHarness

```python
import pytest
import json
from tests.brainworm.integration.hook_test_harness import HookTestHarness

def test_hook_blocks_write_in_discussion_mode(tmp_path, plugin_root):
    # Setup test environment
    harness = HookTestHarness(tmp_path, plugin_root)
    harness.set_daic_mode("discussion")

    # Execute hook
    result = harness.execute_hook(
        "pre_tool_use",
        "Write",
        {"file_path": "/test.py", "content": "test"}
    )

    # Parse and validate output
    output = json.loads(result.stdout)
    assert output["continue"] == False
    assert "DAIC: Tool Blocked" in output.get("stopReason", "")

    # Validate event storage
    events = harness.get_database_events()
    assert len(events) == 1
    assert events[0]["hook_name"] == "pre_tool_use"
    assert events[0]["tool_name"] == "Write"
```

## Testing: Hook Sequence

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

## Debug Logging: Structured Logging

```python
def hook_logic_with_logging(framework, typed_input):
    if framework.debug_logger:
        # INFO level - important events
        framework.debug_logger.info("Hook execution starting")

        # DEBUG level - detailed information
        framework.debug_logger.debug(f"Tool: {typed_input.tool_name}")
        framework.debug_logger.debug(f"Input: {typed_input.tool_input}")

        # WARNING level - unexpected but handled
        framework.debug_logger.warning("Unexpected state encountered")

        # ERROR level - failures
        framework.debug_logger.error("Critical failure occurred")
```

## Config Access: Load and Use Configuration

```python
from utils.config import load_config

def hook_with_config(framework, typed_input):
    config = load_config(framework.project_root)

    # Access DAIC config
    daic_enabled = config["daic"]["enabled"]
    trigger_phrases = config["daic"]["trigger_phrases"]
    blocked_tools = config["daic"]["blocked_tools"]

    # Access debug config
    debug_enabled = config["debug"]["enabled"]
    debug_level = config["debug"]["level"]

    # Use config values
    if daic_enabled and typed_input.tool_name in blocked_tools:
        # ... handle blocked tool
        pass
```

## PEP 723 Dependencies: Common Patterns

**Minimal hook:**
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
#     "tomli-w>=1.0.0",  # Required for utils.config
#     "filelock>=3.13.0",
# ]
```

**CLI script:**
```python
# dependencies = [
#     "rich>=13.0.0",
#     "typer>=0.9.0",
# ]
```

**Transcript processor:**
```python
# dependencies = [
#     "rich>=13.0.0",
#     "tiktoken>=0.7.0",
#     "tomli-w>=1.0.0",
#     "filelock>=3.13.0",
# ]
```

## Hooks Registration: hooks.json Patterns

```json
{
  "PreToolUse": "Edit|Write|MultiEdit|NotebookEdit",
  "PostToolUse": "Edit|Write|Read|Bash|Glob|Grep",
  "UserPromptSubmit": "*",
  "SessionStart": "*",
  "SessionEnd": "*",
  "Stop": "*",
  "Notification": "*"
}
```

**Pattern:**
- Pipe `|` separates multiple tool names (OR matching)
- `*` matches all events
- Tool names are case-sensitive
- Event names are PascalCase

## Error Handling: Graceful Degradation

```python
def hook_logic_with_error_handling(framework, typed_input):
    try:
        # Main logic
        result = perform_operation()
        return result
    except FileNotFoundError as e:
        # Handle specific errors
        if framework.debug_logger:
            framework.debug_logger.warning(f"File not found: {e}")
        return None  # Graceful degradation
    except Exception as e:
        # Catch-all for unexpected errors
        if framework.debug_logger:
            framework.debug_logger.error(f"Unexpected error: {type(e).__name__}: {e}")

        # Log to error file for debugging
        error_log = framework.project_root / ".brainworm" / "hook_errors.log"
        with open(error_log, "a") as f:
            import traceback
            f.write(f"\\n{'='*80}\\n")
            f.write(f"Hook: {framework.hook_name}\\n")
            f.write(f"Error: {str(e)}\\n")
            f.write(traceback.format_exc())
            f.write(f"{'='*80}\\n")

        return None  # Don't crash Claude Code
```

## Atomic File Operations

```python
from utils.file_manager import AtomicFileWriter
import json

def update_state_atomically(state_file, updates):
    # Read current state
    with open(state_file, "r") as f:
        state = json.load(f)

    # Update state
    state.update(updates)

    # Write atomically (prevents corruption)
    with AtomicFileWriter(state_file) as f:
        json.dump(state, f, indent=2)
```

## Event Storage Query Patterns

```python
import sqlite3

def query_hook_events(project_root, session_id):
    db_path = project_root / ".brainworm" / "events" / "hooks.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all events for session
    cursor.execute("""
        SELECT hook_name, tool_name, timestamp, event_data
        FROM hook_events
        WHERE session_id = ?
        ORDER BY timestamp
    """, (session_id,))

    events = cursor.fetchall()
    conn.close()

    return events
```

## Validation Commands

```bash
# Validate single hook
cd brainworm
python3 scripts/validate_dependencies.py --file hooks/your_hook.py

# Validate all hooks
python3 scripts/validate_dependencies.py --verbose

# Test hook execution
echo '{"session_id": "test", "cwd": "/tmp", "hook_event_name": "SessionStart"}' | \\
    uv run hooks/your_hook.py

# Run hook tests
uv run pytest tests/brainworm/integration/test_your_hook.py -v
```
