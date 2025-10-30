# Hook Debugging Guide

Complete guide to debugging Claude Code hooks.

## Enable Debug Logging

Configure debug logging in `.brainworm/config.toml`:

```toml
[debug]
enabled = true
level = "DEBUG"  # Options: DEBUG, INFO, WARNING, ERROR
format = "json"

[debug.outputs]
stderr = false      # Don't output to stderr (interferes with Claude)
file = true         # Write to debug.jsonl
framework = true    # Log framework events
```

## Debug Logging in Hooks

Use the framework's debug logger:

```python
def hook_logic(framework, typed_input):
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

## Reading Debug Logs

```bash
# View JSON logs
tail -f .brainworm/logs/debug.jsonl

# Parse with jq
cat .brainworm/logs/debug.jsonl | jq '.message'

# Filter by hook
cat .brainworm/logs/debug.jsonl | jq 'select(.hook_name == "pre_tool_use")'

# Filter by level
cat .brainworm/logs/debug.jsonl | jq 'select(.level == "ERROR")'

# Show timestamps
cat .brainworm/logs/debug.jsonl | jq '{timestamp, hook_name, message}'
```

## Common Issues

### Hook fails silently

**Symptoms:** Hook doesn't execute, no output

**Diagnosis:**
1. Check stderr output: Hook might be failing before logging
2. Verify PEP 723 dependencies are complete
3. Run hook directly to see errors

**Solutions:**
```bash
# Run hook directly with test input
echo '{"session_id": "test", "cwd": "/tmp", "hook_event_name": "SessionStart"}' | \
    uv run hooks/your_hook.py

# Check stderr for errors
uv run hooks/your_hook.py < test_input.json 2>&1

# Validate dependencies
python3 scripts/validate_dependencies.py --file hooks/your_hook.py
```

### Import errors

**Symptoms:** `ModuleNotFoundError`, `ImportError`

**Diagnosis:**
1. Check `sys.path.insert(0, str(Path(__file__).parent.parent))` is present
2. Verify utils/ directory is accessible
3. Check plugin_root in unified state

**Solutions:**
```python
# Add at top of hook script:
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### State not updating

**Symptoms:** State changes don't persist, old values returned

**Diagnosis:**
1. Check using DAICStateManager, not direct file writes
2. Verify file permissions on .brainworm/state/
3. Check AtomicFileWriter is used

**Solutions:**
```python
# Always use DAICStateManager:
from utils.daic_state_manager import DAICStateManager
state_mgr = DAICStateManager(framework.project_root)
state_mgr.set_daic_mode("implementation", trigger="user_command")

# For custom state files, use AtomicFileWriter:
from utils.file_manager import AtomicFileWriter
with AtomicFileWriter(state_file) as f:
    json.dump(state, f, indent=2)
```

### Events not logging

**Symptoms:** Database has no events, JSONL logs empty

**Diagnosis:**
1. Confirm `enable_event_logging=True` in HookFramework
2. Check database exists: `.brainworm/events/hooks.db`
3. Verify event_logger has write permissions

**Solutions:**
```python
# Enable event logging:
HookFramework("hook_name", enable_event_logging=True) \
    .with_custom_logic(hook_logic) \
    .execute()

# Check database manually:
sqlite3 .brainworm/events/hooks.db "SELECT * FROM hook_events LIMIT 5;"
```

### Transitive dependency errors

**Symptoms:** Import works but runtime error on nested import

**Diagnosis:**
1. Utility module uses dependency not in PEP 723 block
2. Check DEPENDENCIES.md for required transitive deps

**Solutions:**
```python
# If using utils.config, must include tomli-w:
# dependencies = [
#     "rich>=13.0.0",
#     "tomli-w>=1.0.0",  # Required by utils.config
#     "filelock>=3.13.0",
# ]

# Run validation to catch these:
python3 scripts/validate_dependencies.py --file hooks/your_hook.py
```

## Error Handling Pattern

Implement graceful degradation:

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
            f.write(f"\n{'='*80}\n")
            f.write(f"Hook: {framework.hook_name}\n")
            f.write(f"Error: {str(e)}\n")
            f.write(traceback.format_exc())
            f.write(f"{'='*80}\n")

        return None  # Don't crash Claude Code
```

## Testing Debug Output

Validate debug logging works:

```python
def test_hook_debug_logging(tmp_path, plugin_root):
    # Enable debug logging
    config_path = tmp_path / ".brainworm" / "config.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("""
[debug]
enabled = true
level = "DEBUG"
format = "json"

[debug.outputs]
file = true
    """)

    # Execute hook
    harness = HookTestHarness(tmp_path, plugin_root)
    result = harness.execute_hook("pre_tool_use", "Write", {})

    # Check debug logs were created
    debug_log = tmp_path / ".brainworm" / "logs" / "debug.jsonl"
    assert debug_log.exists()

    # Parse and validate log entries
    logs = [json.loads(line) for line in debug_log.read_text().splitlines()]
    assert len(logs) > 0
    assert any(log["hook_name"] == "pre_tool_use" for log in logs)
```

## Performance Profiling

Identify slow operations:

```python
import time

def hook_logic(framework, typed_input):
    start_time = time.time()

    # Operation 1
    op1_start = time.time()
    perform_operation_1()
    op1_duration = time.time() - op1_start

    # Operation 2
    op2_start = time.time()
    perform_operation_2()
    op2_duration = time.time() - op2_start

    total_duration = time.time() - start_time

    if framework.debug_logger:
        framework.debug_logger.info(f"Hook completed in {total_duration:.3f}s")
        framework.debug_logger.debug(f"Op1: {op1_duration:.3f}s, Op2: {op2_duration:.3f}s")
```
