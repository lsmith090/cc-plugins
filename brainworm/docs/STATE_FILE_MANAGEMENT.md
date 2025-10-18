# State File Management

Comprehensive guide to state file ownership, concurrent access patterns, and thread safety in the brainworm plugin.

## Table of Contents

- [State File Overview](#state-file-overview)
- [File Ownership Rules](#file-ownership-rules)
- [Concurrent Access Patterns](#concurrent-access-patterns)
- [FileLock Usage](#filelock-usage)
- [State File Types](#state-file-types)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## State File Overview

Brainworm manages state through various JSON files in `.brainworm/state/`. These files coordinate workflow state, session correlation, and task tracking across multiple processes and contexts.

**State Directory Structure**:
```
.brainworm/
└── state/
    ├── unified_session_state.json      # Primary workflow state
    ├── .correlation_state              # Session correlation mapping
    ├── .context_warning_shown          # UI state flag
    ├── <subagent-name>/                # Subagent batch outputs
    │   ├── current_transcript_*.json
    │   └── service_context.json
    └── .*.json.lock                    # Lock files for atomic operations
```

## File Ownership Rules

### Single Owner Files

Files with a **single designated owner** that has exclusive write access:

| File | Owner | Write Access | Read Access |
|------|-------|--------------|-------------|
| `unified_session_state.json` | DAICStateManager | Exclusive via update methods | All hooks/scripts |
| `.correlation_state` | CorrelationManager | Exclusive via FileLock | All hooks/scripts |
| Subagent transcripts | transcript_processor hook | Exclusive during write | Subagent scripts |

**Rule**: Only the designated owner may write to these files. All other code must read through the owner's API.

### Shared Access Files

Files with **multiple writers** that require coordination:

| File | Writers | Coordination Method |
|------|---------|---------------------|
| `config.toml` | User edits, add_trigger.py, api_mode.py | FileLock recommended |
| `.context_warning_shown` | user_prompt_submit.py | Atomic check-and-create |

**Rule**: All writers must use FileLock or atomic operations to prevent race conditions.

## Concurrent Access Patterns

### Pattern 1: Read-Modify-Write with FileLock

**Use when**: Multiple processes may simultaneously read, modify, and write the same file.

**Implementation**:
```python
from filelock import FileLock
from pathlib import Path
import json

def update_config_safely(config_file: Path, updates: dict):
    """Safely update configuration with concurrent access protection"""
    lock_file = config_file.parent / f".{config_file.name}.lock"
    lock = FileLock(lock_file, timeout=10)

    with lock:
        # Read current state
        if config_file.exists():
            data = json.loads(config_file.read_text())
        else:
            data = {}

        # Modify
        data.update(updates)

        # Write atomically
        config_file.write_text(json.dumps(data, indent=2))
```

**Used in**:
- `correlation_manager.py` - Session correlation clearing
- `add_trigger.py` - Adding trigger phrases
- `api_mode.py` - Toggling API mode
- `user_prompt_submit.py` - Context warning flags
- `event_logger.py` - Timing file coordination

### Pattern 2: Atomic API Methods

**Use when**: A manager class owns a file and provides atomic operations.

**Implementation**:
```python
class DAICStateManager:
    def _update_unified_state(self, updates: dict):
        """Atomic state update with internal locking"""
        # No external lock needed - method is atomic
        current = self.get_unified_state()
        current.update(updates)
        self._save_unified_state(current)
```

**Used in**:
- `DAICStateManager` - All state modifications
- `CorrelationManager` - Correlation storage

**Rule**: Callers must use the API methods, never direct file access.

### Pattern 3: Check-and-Create (Flag Files)

**Use when**: Simple boolean flags that are set once and never modified.

**Implementation**:
```python
def set_warning_shown_flag():
    """Atomically create flag file if it doesn't exist"""
    flag_file = Path(".brainworm/state/.context_warning_shown")

    # Atomic on POSIX systems (single syscall)
    try:
        flag_file.touch(exist_ok=False)
        return True  # We created it
    except FileExistsError:
        return False  # Already existed
```

**Used in**:
- `user_prompt_submit.py` - Context warning display

### Pattern 4: Write-Once Read-Many (Subagent Outputs)

**Use when**: Files are written once by a single process, then read by others.

**Implementation**:
```python
def write_subagent_output(batch_dir: Path, transcripts: list):
    """Write subagent outputs (single writer, no locking needed)"""
    # Only transcript_processor writes these files
    # No concurrent writes possible

    for i, transcript in enumerate(transcripts):
        output_file = batch_dir / f"current_transcript_{i+1}.json"
        output_file.write_text(json.dumps(transcript, indent=2))
```

**Used in**:
- `transcript_processor.py` - Subagent batch outputs

**Note**: Readers must use file stability detection (see `wait_for_transcripts.py`).

## FileLock Usage

### When to Use FileLock

**Use FileLock when**:
- Multiple processes/threads may write to the same file
- Read-modify-write operations need atomicity
- Preventing lost updates is critical

**Don't use FileLock when**:
- Single writer, multiple readers (write-once pattern)
- Using atomic API methods (locking already internal)
- Operating on separate, independent files

### FileLock Configuration

**Standard timeout values** (from CONFIGURATION.md):

```python
from filelock import FileLock

# Standard configuration
lock = FileLock(lock_file, timeout=10)

# Context manager (automatic cleanup)
with lock:
    # Protected operations
    pass
```

**Timeout Guidelines**:
- **Local operations**: 10 seconds (standard)
- **Network operations**: 30 seconds
- **User scripts**: 60 seconds

**Lock file naming**: `.{original_filename}.lock`
- Example: `config.json` → `.config.json.lock`

### Error Handling

```python
from filelock import FileLock, Timeout

try:
    lock = FileLock(lock_file, timeout=10)
    with lock:
        # Protected operations
        pass
except Timeout:
    # Lock acquisition failed
    logger.error(f"Could not acquire lock after 10s: {lock_file}")
    raise RuntimeError(
        "State file is locked by another process. "
        "Verify no other brainworm operations are running."
    )
```

## State File Types

### 1. Unified Session State

**File**: `unified_session_state.json`

**Owner**: `DAICStateManager`

**Schema**:
```json
{
  "daic_mode": "discussion|implementation",
  "current_task": "task-name",
  "current_branch": "feature/task-name",
  "task_services": ["service1", "service2"],
  "session_id": "session-uuid",
  "correlation_id": "correlation-id",
  "plugin_root": "/path/to/plugin",
  "developer": {
    "name": "Developer Name",
    "email": "email@example.com"
  }
}
```

**Access Pattern**: Atomic API methods

**Writers**: Only `DAICStateManager._update_unified_state()`

**Readers**: All hooks and scripts via `DAICStateManager.get_unified_state()`

### 2. Correlation State

**File**: `.correlation_state`

**Owner**: `CorrelationManager`

**Schema**:
```json
{
  "session_id": "correlation-id"
}
```

**Access Pattern**: FileLock for clearing

**Writers**:
- `CorrelationManager._store_session_correlation()` (atomic)
- `CorrelationManager.clear_session_correlation()` (with FileLock)

**Readers**: `CorrelationManager._get_session_correlation()`

### 3. Configuration

**File**: `config.toml`

**Owners**: Multiple (user, scripts)

**Access Pattern**: FileLock recommended for programmatic updates

**Writers**:
- User (manual edits)
- `add_trigger.py` (should use FileLock)
- `api_mode.py` (should use FileLock)

**Readers**: All via `config.py` utilities

### 4. Context Warning Flag

**File**: `.context_warning_shown`

**Owner**: `user_prompt_submit.py`

**Access Pattern**: Check-and-create (atomic)

**Schema**: Empty file (existence = flag set)

**Writers**: `user_prompt_submit.py` (touch with exist_ok=False)

**Readers**: `user_prompt_submit.py` (exists check)

### 5. Timing Files

**File**: `.brainworm/logs/timing/*.jsonl`

**Owner**: `event_logger.py`

**Access Pattern**: FileLock for coordination

**Writers**: `event_logger.py._write_timing_with_lock()`

**Readers**: Timing analysis tools

## Best Practices

### 1. Never Edit State Files Directly

**❌ Wrong**:
```python
# DON'T: Direct file manipulation
state_file = Path(".brainworm/state/unified_session_state.json")
data = json.loads(state_file.read_text())
data["current_task"] = "new-task"
state_file.write_text(json.dumps(data))
```

**✅ Correct**:
```python
# DO: Use manager API
from brainworm.utils.daic_state_manager import DAICStateManager

manager = DAICStateManager(project_root)
manager.set_task_state(
    task="new-task",
    branch="feature/new-task",
    services=["service1"]
)
```

### 2. Use FileLock for Read-Modify-Write

**❌ Wrong**:
```python
# DON'T: Unprotected read-modify-write (race condition)
data = json.loads(config_file.read_text())
data["trigger_phrases"].append("new phrase")
config_file.write_text(json.dumps(data))
```

**✅ Correct**:
```python
# DO: Protected with FileLock
from filelock import FileLock

lock_file = config_file.parent / f".{config_file.name}.lock"
lock = FileLock(lock_file, timeout=10)

with lock:
    data = json.loads(config_file.read_text())
    data["trigger_phrases"].append("new phrase")
    config_file.write_text(json.dumps(data))
```

### 3. Lock File Cleanup

**Lock files are automatically cleaned up** by FileLock when the lock is released.

**Manual cleanup** (if needed):
```python
# Lock files can be safely deleted when no locks are held
lock_file = Path(".config.json.lock")
if lock_file.exists() and not_currently_locked(lock_file):
    lock_file.unlink()
```

### 4. Timeout Configuration

**Use appropriate timeouts** based on operation type:

```python
# Quick local operations
lock = FileLock(lock_file, timeout=10)

# Operations that may involve network/disk
lock = FileLock(lock_file, timeout=30)

# User-facing operations (be patient)
lock = FileLock(lock_file, timeout=60)
```

### 5. Error Context

**Provide actionable error messages** when lock acquisition fails:

```python
try:
    with FileLock(lock_file, timeout=10):
        # Operations
        pass
except Timeout:
    raise RuntimeError(
        f"Could not acquire lock on {lock_file.name}. "
        "Possible causes:\n"
        "  - Another brainworm operation is running\n"
        "  - A previous operation crashed holding the lock\n"
        "  - Slow disk I/O\n"
        f"Try: rm {lock_file}"
    )
```

### 6. State Validation

**Validate state after updates**:

```python
def update_state_safely(manager, updates):
    """Update state with validation"""
    # Update
    manager._update_unified_state(updates)

    # Verify
    new_state = manager.get_unified_state()
    assert new_state["current_task"] == updates.get("current_task")
```

## Troubleshooting

### Problem: "Could not acquire lock" error

**Symptoms**: Lock timeout after 10 seconds

**Causes**:
1. Another process holds the lock
2. Previous process crashed without releasing
3. Slow disk I/O

**Solutions**:
```bash
# Check for running brainworm processes
ps aux | grep brainworm

# Remove stale lock files (if no processes running)
find .brainworm/state -name ".*.lock" -delete

# Check disk I/O performance
time ls -la .brainworm/state/
```

### Problem: Lost updates / race conditions

**Symptoms**: Configuration changes disappear, state inconsistencies

**Cause**: Missing FileLock on read-modify-write

**Solution**: Add FileLock protection:
```python
# Before (unsafe)
data = json.loads(file.read_text())
data["value"] = new_value
file.write_text(json.dumps(data))

# After (safe)
with FileLock(lock_file, timeout=10):
    data = json.loads(file.read_text())
    data["value"] = new_value
    file.write_text(json.dumps(data))
```

### Problem: State file corruption

**Symptoms**: Invalid JSON, parse errors

**Causes**:
1. Incomplete write (process crash)
2. Concurrent writes without locking
3. Disk full

**Prevention**:
- Use FileLock for all writes
- Implement atomic write patterns
- Monitor disk space

**Recovery**:
```bash
# Check state file validity
python3 -m json.tool .brainworm/state/unified_session_state.json

# Restore from backup (if available)
cp .brainworm/state/unified_session_state.json.backup \
   .brainworm/state/unified_session_state.json

# Reinitialize state
./tasks clear  # Clear current task
./daic discussion  # Reset to discussion mode
```

### Problem: Subagent timeout waiting for transcripts

**Symptoms**: "Timeout waiting for transcripts" error

**Cause**: Files not stabilizing (still being written)

**Debug**:
```bash
# Check if files exist
ls -lh .brainworm/state/<subagent-name>/

# Monitor file changes
watch -n 0.5 'ls -lh .brainworm/state/<subagent-name>/'

# Check timing logs
cat .brainworm/logs/timing/*.jsonl | grep transcript_processor
```

**Solution**: Increase timeout or check hook performance

## Implementation Checklist

When implementing new state management features:

- [ ] Identify file ownership (single vs. multiple writers)
- [ ] Choose appropriate access pattern
- [ ] Use FileLock for read-modify-write operations
- [ ] Configure appropriate timeout (10-60s)
- [ ] Implement error handling with actionable messages
- [ ] Add state validation after updates
- [ ] Document ownership in this file
- [ ] Add tests for concurrent access
- [ ] Consider lock file cleanup strategy

## References

- [CONFIGURATION.md](./CONFIGURATION.md) - Timeout policy
- [ARCHITECTURE.md](./ARCHITECTURE.md) - State management architecture
- [filelock documentation](https://py-filelock.readthedocs.io/)
- [Test suite](../../tests/brainworm/concurrency/) - Concurrent access tests

---

**Last Updated**: 2025-10-18 (Phase 3 code review remediation)
