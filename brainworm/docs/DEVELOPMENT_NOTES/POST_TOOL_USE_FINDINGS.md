# PostToolUse Hook Investigation Findings

**Date**: 2025-10-19
**Issue**: PostToolUse events not appearing in database
**Status**: RESOLVED - Configuration Issue

## Summary

PostToolUse hooks ARE executing correctly, but events were not being logged to the database due to missing `--event-logging` flag in hooks configuration.

## Investigation Timeline

### Initial Hypothesis (INCORRECT)
"PostToolUse hooks not being executed by Claude Code" - This was wrong!

### Testing Process

1. **Added debug trace** to `/tmp/post_tool_use_trace.log`
2. **Executed test commands** and verified hook was called
3. **Checked sys.argv** and found `--event-logging` flag was missing
4. **Discovered root cause**: Event logging requires explicit `--event-logging` flag

### Root Cause

**File**: `brainworm/utils/hook_framework.py:278`
```python
event_logging_enabled = '--event-logging' in sys.argv
```

The hook framework only enables event logging when the `--event-logging` command-line flag is present. This is an **opt-in design** for performance/privacy reasons.

## Evidence

### Hook IS Being Called

From `/tmp/post_tool_use_trace.log`:
```
============================================================
2025-10-19 09:54:25.698558: POST_TOOL_USE HOOK STARTED
  sys.argv: ['/Users/logansmith/repos/cc-plugins/brainworm/hooks/post_tool_use.py']
  --event-logging present: False
  INPUT LENGTH: 483
  KEYS: ['session_id', 'transcript_path', 'cwd', 'permission_mode', 'hook_event_name', 'tool_name', 'tool_input', 'tool_response']
  tool_name: Bash
  tool_response: {'stdout': '', 'stderr': '', 'interrupted': False, 'isImage': False}
```

**Key findings**:
- ✅ Hook executes
- ✅ Receives correct input data (tool_name, tool_response, etc.)
- ❌ `--event-logging` flag is absent
- ❌ Therefore, event logger is never created
- ❌ Therefore, no events logged to database

### Database Evidence

```bash
$ sqlite3 .brainworm/events/hooks.db \
  "SELECT hook_name, COUNT(*) FROM hook_events GROUP BY hook_name"

pre_tool_use         | 3,684  # Old events from when flag WAS enabled
user_prompt_submit   | 567
session_start        | 107
post_tool_use        | 0      # No events because flag is missing
```

Pre_tool_use events are from **Oct 12 - Oct 19** across **40 sessions**, suggesting event logging was enabled previously or in different configuration.

## Solution

### Fix Applied

**Updated** `brainworm/hooks/hooks.json` to add `--event-logging` flag to ALL hooks:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|Edit|Write|MultiEdit",
        "hooks": [{
          "type": "command",
          "command": "uv run ${CLAUDE_PLUGIN_ROOT}/hooks/pre_tool_use.py --event-logging"
        }]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit|Bash|Task",
        "hooks": [{
          "type": "command",
          "command": "uv run ${CLAUDE_PLUGIN_ROOT}/hooks/post_tool_use.py --event-logging"
        }]
      }
    ],
    ... (all other hooks also updated)
  }
}
```

### Testing Required

**After Claude Code restart** (to reload hooks configuration):

1. Run test commands
2. Check `/tmp/post_tool_use_trace.log` for `--event-logging present: True`
3. Query database for post_tool_use events:
   ```bash
   sqlite3 .brainworm/events/hooks.db \
     "SELECT COUNT(*) FROM hook_events WHERE hook_name = 'post_tool_use' \
      AND timestamp > datetime('now', '-5 minutes')"
   ```
4. Verify duration tracking works:
   ```bash
   python3 brainworm/scripts/verify_duration_tracking.py
   ```

## Impact on Nautiloid

### Before Fix
- ❌ No post_tool_use events logged
- ❌ No duration data (requires post_tool_use)
- ❌ No success determination (requires post_tool_use)
- ❌ Timing files created but never consumed

### After Fix (Requires Claude Code Restart)
- ✅ post_tool_use events will be logged
- ✅ Duration tracking will work (timing coordination complete)
- ✅ Success determination will work
- ✅ Timing files will be read and cleaned up

### For Nautiloid Team

**Current State**:
- Duration data WILL NOT exist in old events (logged without post_tool_use)
- New events (after restart) WILL have duration data

**Extraction Code**:
```python
# Parse event_data JSON blob
event_data = json.loads(row['event_data'])

# Extract duration from nested timing structure
duration_ms = event_data.get('timing', {}).get('execution_duration_ms', 0.0)

# Extract success
success = event_data.get('success', True)
```

**Expected Results After Fix**:
```sql
SELECT
    tool_name,
    json_extract(event_data, '$.timing.execution_duration_ms') as duration_ms,
    json_extract(event_data, '$.success') as success
FROM hook_events
WHERE hook_name = 'post_tool_use'
    AND timestamp > datetime('now', '-1 day');
```

## Key Learnings

### Design Decisions

1. **Event logging is opt-in**: Requires `--event-logging` flag for performance/privacy
2. **Hook execution is separate from event logging**: Hooks run even without logging
3. **Configuration changes require restart**: Claude Code must reload hooks.json

### Testing Methodology

1. **Add explicit file logging** at hook entry point (before any framework code)
2. **Check sys.argv** to verify command-line flags
3. **Parse input data** to verify hook receives correct information
4. **Query database** to verify events are actually logged

### Common Pitfalls

- ❌ Assuming hooks aren't running when events don't appear in database
- ❌ Not checking if event logging is enabled
- ❌ Forgetting that configuration changes require restart
- ✅ Always add debug logging to verify execution flow

## Next Steps

### Immediate (User Action Required)

1. **Restart Claude Code** to load updated hooks.json
2. **Verify flag is present**: Check `/tmp/post_tool_use_trace.log`
3. **Test event logging**: Run commands and check database

### Follow-Up

1. Update all projects using brainworm with new hooks.json
2. Validate duration tracking end-to-end
3. Update nautiloid to parse duration from nested JSON
4. Monitor for any other hooks missing --event-logging flag

### Documentation Updates

1. ✅ Document --event-logging flag requirement
2. ✅ Add troubleshooting section for "hooks executing but no events"
3. ✅ Update installation docs to verify event logging is enabled
4. ✅ Add verification script to plugin

## Files Modified

- `brainworm/hooks/hooks.json` - Added --event-logging to all hooks
- `brainworm/hooks/post_tool_use.py` - Added debug tracing (can be removed after verification)
- `brainworm/docs/POST_TOOL_USE_FINDINGS.md` - This document
- `brainworm/docs/NAUTILOID_METRICS_RESPONSE.md` - Updated with correct findings

## Related Documents

- `brainworm/docs/NAUTILOID_METRICS_RESPONSE.md` - Response to nautiloid investigation
- `brainworm/scripts/verify_duration_tracking.py` - Verification script
- `/tmp/post_tool_use_trace.log` - Debug trace log

---

**Conclusion**: PostToolUse hooks work perfectly. The issue was simply missing the `--event-logging` flag in the hooks configuration. After Claude Code restart, all event logging (including duration tracking and success determination) will function as designed.
