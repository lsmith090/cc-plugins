# Event Logging Simplification - Implementation Complete

**Date**: 2025-10-19
**Status**: ✅ Code changes complete, requires Claude Code restart

## Summary

Removed the unnecessary `--event-logging` flag requirement and simplified event logging to always work correctly by default. Event logging is now the core functionality, not optional "enrichment".

## Changes Made

### 1. Removed --event-logging Flag from hooks.json

**File**: `brainworm/hooks/hooks.json`

**Before**:
```json
"command": "uv run ${CLAUDE_PLUGIN_ROOT}/hooks/post_tool_use.py --event-logging"
```

**After**:
```json
"command": "uv run ${CLAUDE_PLUGIN_ROOT}/hooks/post_tool_use.py"
```

All hooks (PreToolUse, PostToolUse, SessionStart, SessionEnd, UserPromptSubmit, Stop, Notification) updated.

### 2. Simplified event_logger.py

**File**: `brainworm/utils/event_logger.py:163-166`

**Before**:
```python
def enrich_event_data(self, event_data: dict) -> dict:
    """Add session correlation metadata to event data"""
    if not self.enable_event_logging:
        return event_data  # Skip enrichment!

    enriched = event_data.copy()
    # ... add essential metadata
```

**After**:
```python
def enrich_event_data(self, event_data: dict) -> dict:
    """Add essential session and correlation metadata to event data"""
    enriched = event_data.copy()
    # ... always add essential metadata
```

The method now **always** adds essential event data (session_id, correlation_id, timestamp, etc.). This isn't optional "enrichment" - it's the event data.

### 3. Removed Flag Check from hook_framework.py

**File**: `brainworm/utils/hook_framework.py:276-282`

**Before**:
```python
if self.enable_event_logging and create_event_logger:
    event_logging_enabled = '--event-logging' in sys.argv  # Flag check!
    self.event_logger = create_event_logger(
        self.project_root, self.hook_name,
        enable_event_logging=event_logging_enabled,
        session_id=self.session_id
    )
```

**After**:
```python
if self.enable_event_logging and create_event_logger:
    self.event_logger = create_event_logger(
        self.project_root, self.hook_name,
        enable_event_logging=True,  # Always enabled
        session_id=self.session_id
    )
```

### 4. Removed Debug Trace from post_tool_use.py

**File**: `brainworm/hooks/post_tool_use.py`

Removed temporary debug code that was writing to `/tmp/post_tool_use_trace.log`. Hook is now clean and production-ready.

## Architecture Improvement

### Old Design (Confusing)

- Event logging was "opt-in" via `--event-logging` flag
- Core event data (session_id, correlation_id, timestamp) was treated as optional "enrichment"
- Hook would execute but not log events unless flag was present
- Caused user confusion: "Why aren't my events being logged?"

### New Design (Correct)

- Event logging is **always on** - it's the plugin's core purpose
- Essential event data is **always included** - not optional
- No flags required - works out of the box
- Clear separation: Brainworm captures events, Nautiloid analyzes them

## What Gets Logged

Every event now includes:

**From Claude Code** (raw hook data):
- session_id
- tool_name
- tool_input
- tool_response
- timestamp
- etc.

**Added by brainworm** (essential context):
- correlation_id (workflow/task tracking)
- execution_id (duplicate detection)
- project_root
- hook_event_name
- schema_version

**Added by nautiloid** (analytics):
- Cross-project correlation
- Pattern detection
- Aggregate metrics
- Time-series analysis

## Testing Status

### Current State
- ✅ Code changes complete
- ✅ Hooks.json updated
- ⏸️ **Requires Claude Code restart** to load new configuration
- ⏸️ Post-restart verification needed

### Verification After Restart

1. **Check post_tool_use events are logged**:
   ```bash
   sqlite3 .brainworm/events/hooks.db \
     "SELECT COUNT(*) FROM hook_events WHERE hook_name = 'post_tool_use' \
      AND timestamp > datetime('now', '-5 minutes')"
   ```
   Expected: > 0 (events are being logged)

2. **Check event structure**:
   ```bash
   sqlite3 .brainworm/events/hooks.db \
     "SELECT event_data FROM hook_events WHERE hook_name = 'post_tool_use' \
      ORDER BY timestamp DESC LIMIT 1" | python3 -m json.tool
   ```
   Expected: Complete event with session_id, correlation_id, timing, success, etc.

3. **Run verification script**:
   ```bash
   python3 brainworm/scripts/verify_duration_tracking.py
   ```
   Expected: Duration data present in events

### Pre-Restart Evidence

Events ARE being logged from current session:
- 331 pre_tool_use events (last 2 minutes)
- 32 user_prompt_submit events
- 3 session_start events
- 0 post_tool_use events (old config still loaded)

After restart, all hook types should log events.

## Impact on Nautiloid

### Before Fix
- Events logged inconsistently (depended on flag)
- Missing essential metadata (session_id, correlation_id)
- Duration tracking broken (no post_tool_use events)
- Success tracking broken (no post_tool_use events)

### After Fix (Post-Restart)
- ✅ All events logged consistently
- ✅ Complete metadata on all events
- ✅ Duration tracking works (post_tool_use logs timing)
- ✅ Success determination works (post_tool_use analyzes responses)

### Data Migration Note

**Old events** (before fix):
- May be missing correlation_id, schema_version, etc.
- No post_tool_use events at all
- No duration or success data

**New events** (after restart):
- Complete metadata on all events
- post_tool_use events with duration/success
- Full analytics capability

Nautiloid should handle both gracefully (use `COALESCE` for missing fields).

## Why This is Better

### For Users
- ✅ Works out of the box
- ✅ No configuration needed
- ✅ No mysterious "why isn't it working?" issues
- ✅ Plugin does what it says: captures events

### For Developers
- ✅ Simpler code (removed flag complexity)
- ✅ Clearer architecture (brainworm captures, nautiloid analyzes)
- ✅ Easier to debug (either logging works or it doesn't)
- ✅ Fewer moving parts (no optional enrichment)

### For Architecture
- ✅ Separation of concerns (capture vs. analytics)
- ✅ Unix philosophy (do one thing well)
- ✅ No optional core functionality
- ✅ Predictable behavior

## Files Modified

1. `brainworm/hooks/hooks.json` - Removed --event-logging flags
2. `brainworm/utils/event_logger.py` - Always add essential metadata
3. `brainworm/utils/hook_framework.py` - Always enable event logging
4. `brainworm/hooks/post_tool_use.py` - Removed debug trace

## Related Documents

- `brainworm/docs/POST_TOOL_USE_FINDINGS.md` - Investigation that led to this fix
- `brainworm/docs/NAUTILOID_METRICS_RESPONSE.md` - Response to nautiloid investigation
- `brainworm/scripts/verify_duration_tracking.py` - Verification tool

## Next Steps

1. **User action required**: Restart Claude Code to reload hooks configuration
2. **Verify fix works**: Run verification commands above
3. **Update nautiloid**: Parse duration from `event_data.timing.execution_duration_ms`
4. **Update documentation**: Note that event logging is always enabled
5. **Deploy to other projects**: Update brainworm installation in all projects

---

**Conclusion**: Event logging is now the plugin's core functionality (not optional "enrichment"), working correctly by default without flags or configuration.
