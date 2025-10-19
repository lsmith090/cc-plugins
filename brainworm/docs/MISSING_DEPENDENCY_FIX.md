# Post Tool Use Hook - Missing Dependency Fix

**Date**: 2025-10-19
**Status**: ✅ RESOLVED

## Problem Summary

After removing the `--event-logging` flag requirement (see EVENT_LOGGING_SIMPLIFICATION.md), post_tool_use hooks were executing but **not logging any events** to the database.

### Observed Symptoms

1. Database showed 0 post_tool_use events despite hooks executing
2. Timing files being created by pre_tool_use but never consumed
3. Duration tracking completely broken (no post_tool_use events to calculate durations)
4. Success field determination not working (requires post_tool_use analysis)

### Investigation Evidence

```bash
# Database before fix
sqlite3 .brainworm/events/hooks.db "SELECT hook_name, COUNT(*) FROM hook_events GROUP BY hook_name"
pre_tool_use|3779
session_start|111
user_prompt_submit|587
# NO post_tool_use events!
```

## Root Cause Analysis

### Discovery Process

1. **Confirmed hooks were executing**: Claude Code showed "Running PostToolUse hooks..." messages
2. **Added debug tracing**: Discovered `event_logger` was **None** in post_tool_use
3. **Traced initialization**: Found `create_event_logger` function was None
4. **Checked imports**: Import of event_logger failing silently in post_tool_use.py
5. **Found import error**: `ModuleNotFoundError: No module named 'tomli_w'`

### The Missing Dependency

**File**: `brainworm/hooks/post_tool_use.py` (lines 1-7)

**Before** (broken):
```python
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
#     "filelock>=3.13.0",
# ]
# ///
```

**Missing**: `tomli-w>=1.0.0`

**Why it matters**:
- When `uv run` executes the script, it only installs declared dependencies
- `hook_framework.py` imports `config.py`
- `config.py` requires `tomli_w` for TOML file operations
- Without `tomli_w`, entire import chain fails silently
- Fallback sets `create_event_logger = None`
- Result: No event logger, no events logged

### Why Pre-Tool Use Worked

**File**: `brainworm/hooks/pre_tool_use.py` (lines 1-8)

```python
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
#     "tomli-w>=1.0.0",     # ← Had this!
#     "filelock>=3.13.0",
# ]
# ///
```

Pre-tool use hook had `tomli-w` declared, so:
- ✅ Import chain succeeded
- ✅ `create_event_logger` function available
- ✅ Event logger created
- ✅ Events logged to database

## The Fix

**File**: `brainworm/hooks/post_tool_use.py` (line 5)

**After** (fixed):
```python
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
#     "tomli-w>=1.0.0",      # ← Added this line
#     "filelock>=3.13.0",
# ]
# ///
```

**Just one line added**: `"tomli-w>=1.0.0",`

## Verification

### Test Results After Fix

```bash
# Database after fix
sqlite3 .brainworm/events/hooks.db \
  "SELECT hook_name, COUNT(*) FROM hook_events \
   WHERE timestamp > datetime('now', '-2 minutes') \
   GROUP BY hook_name"

post_tool_use|3        # ← Events appearing!
pre_tool_use|431
session_start|7
user_prompt_submit|38
```

### Duration Tracking Verification

```bash
sqlite3 .brainworm/events/hooks.db \
  "SELECT
     json_extract(event_data, '$.tool_name') as tool,
     json_extract(event_data, '$.timing.execution_duration_ms') as duration_ms
   FROM hook_events
   WHERE hook_name = 'post_tool_use'
   ORDER BY timestamp DESC LIMIT 5"

Bash|202.875    # ← Duration tracking works!
Bash|181.272
Bash|196.575
Edit|308.758
```

## Lessons Learned

### 1. Inline Script Dependencies Must Be Complete

**Problem**: Easy to forget transitive dependencies when using `uv run` inline scripts.

**Solution**: Each hook script must declare ALL dependencies it needs, including those used by imported modules.

**Check**: If a hook imports from `utils/`, ensure all dependencies used by those utils are declared.

### 2. Silent Import Failures

**Problem**: The try/except around imports made failures invisible:

```python
try:
    from .event_logger import SessionEventLogger, create_event_logger
except ImportError:
    create_event_logger = None  # Silent failure!
```

**Trade-off**: Fallback provides graceful degradation but hides dependency issues.

**Mitigation**: Added debug tracing (removed after fix) to diagnose import failures.

### 3. Hook Dependency Parity

**Problem**: Different hooks (pre_tool_use vs post_tool_use) had different dependencies despite using same infrastructure.

**Solution**: Standardize hook dependencies. If hooks use `hook_framework.py`, they should have the same core dependencies.

**Future**: Consider creating a shared dependency list:
```python
# hook_dependencies.py
HOOK_CORE_DEPS = [
    "rich>=13.0.0",
    "tomli-w>=1.0.0",
    "filelock>=3.13.0",
]
```

### 4. Testing Hook Scripts in Isolation

**Problem**: Hooks were tested as a system, not individually with `uv run`.

**Better Testing**:
```bash
# Test each hook script can import its dependencies
echo '{}' | uv run /path/to/hook.py
# Should not fail with ModuleNotFoundError
```

## Impact

### Before Fix
- ❌ No post_tool_use events logged
- ❌ Duration tracking broken (0 ms for all events)
- ❌ Success field not determined
- ❌ Timing coordination broken
- ❌ Nautiloid analytics missing critical data

### After Fix
- ✅ post_tool_use events logging correctly
- ✅ Duration tracking working (202ms, 181ms, etc.)
- ✅ Success determination functional
- ✅ Timing files properly consumed
- ✅ Complete event data for nautiloid analytics

## Files Modified

1. **brainworm/hooks/post_tool_use.py** (line 5)
   - Added: `"tomli-w>=1.0.0",` to dependencies

That's it! One line fix.

## Related Documentation

- **EVENT_LOGGING_SIMPLIFICATION.md** - The flag removal that preceded this issue
- **NAUTILOID_METRICS_RESPONSE.md** - Original investigation from nautiloid project
- **POST_TOOL_USE_FINDINGS.md** - Initial debugging investigation

## Recommendations

1. **Audit all hook scripts**: Ensure dependency completeness
2. **Create dependency standard**: Document required dependencies for hook framework
3. **Add CI test**: Verify each hook script can run independently with `uv run`
4. **Consider dependency injection**: Pass config_loader as parameter instead of importing

## Summary

**Root Cause**: Missing `tomli-w` dependency in post_tool_use.py inline script metadata
**Fix**: Added one line declaring the dependency
**Impact**: Restored 100% of post_tool_use event logging and duration tracking
**Lesson**: Inline script dependencies must be exhaustive, not minimal
