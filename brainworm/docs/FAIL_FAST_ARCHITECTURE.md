# Fail-Fast Architecture Implementation

**Date**: 2025-10-19
**Status**: ✅ Implemented
**Related**: MISSING_DEPENDENCY_FIX.md, EVENT_LOGGING_SIMPLIFICATION.md

## Problem: Silent Failures Were Hiding Bugs

### What Was Wrong

**Before** (`hook_framework.py` lines 39-66):
```python
try:
    from .event_logger import SessionEventLogger, create_event_logger
    from .config import load_config  # Requires tomli_w
except ImportError:
    # SILENT FAILURE - no error, no warning, no indication
    create_event_logger = None
    load_config = None
```

**Result**:
- Hook executes "successfully" (exit code 0)
- No events logged (create_event_logger is None)
- No error message
- No warning
- User has NO IDEA anything is wrong

### Real-World Impact

This silent failure pattern is **exactly why** we spent hours debugging the missing `tomli-w` dependency:

1. **Oct 18**: Removed `--event-logging` flag, restarted Claude Code
2. **Oct 19**: User noticed 0 post_tool_use events in database
3. **Hours of debugging**: Database queries, code review, architecture analysis
4. **Finally found**: Missing `tomli-w` in post_tool_use.py dependencies
5. **Root cause**: try/except hid the ImportError, hook ran without logging

If the hook had **failed fast** with a clear error, we would have found it in 2 minutes.

## Solution: Fail Fast with Clear Errors

### New Behavior

**After** (`hook_framework.py` lines 39-85):
```python
try:
    from .event_logger import SessionEventLogger, create_event_logger
    from .config import load_config
except ImportError as import_error:
    # FAIL FAST - Print clear error and re-raise
    error_msg = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     CRITICAL: HOOK INFRASTRUCTURE FAILURE                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Hook framework failed to import required infrastructure modules.             ║
║                                                                               ║
║ Import Error: {str(import_error)}                                            ║
║                                                                               ║
║ This usually means:                                                           ║
║  • Missing dependency in inline script metadata (# /// script)               ║
║  • Common missing: tomli-w>=1.0.0, rich>=13.0.0, filelock>=3.13.0           ║
║                                                                               ║
║ 🔧 How to fix:                                                                ║
║  1. Check the hook script's inline dependencies                              ║
║  2. Run: python3 scripts/validate_dependencies.py --file path/to/hook.py    ║
║  3. Add missing dependencies to the script's dependency list                 ║
║                                                                               ║
║ 📚 See: brainworm/docs/MISSING_DEPENDENCY_FIX.md                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    print(error_msg, file=sys.stderr)
    traceback.print_exc(file=sys.stderr)

    # Re-raise to fail the hook execution
    raise RuntimeError(
        f"Hook infrastructure import failed: {import_error}. "
        "Fix dependency issues before running hooks."
    ) from import_error
```

**Result**:
- ✅ Hook **FAILS** immediately (exit code 1)
- ✅ Clear, boxed error message
- ✅ Identifies the exact problem
- ✅ Provides fix instructions
- ✅ Points to documentation
- ✅ Full traceback for debugging
- ✅ **User knows immediately something is wrong**

## Test Results

### Testing with Broken Hook

```bash
# Create hook missing tomli-w dependency
echo '{"session_id":"test"}' | uv run --no-project hooks/broken.py
```

**Output**:
```
╔══════════════════════════════════════════════════════╗
║  CRITICAL: HOOK INFRASTRUCTURE FAILURE               ║
║  Import Error: No module named 'tomli_w'             ║
║  [Clear fix instructions]                            ║
╚══════════════════════════════════════════════════════╝

RuntimeError: Hook infrastructure import failed: No module named 'tomli_w'
```

Perfect! Immediate, actionable feedback.

## Benefits

### 1. Immediate Problem Detection
**Before**: Hours of debugging to find silent failures
**After**: Instant error message when hook runs

### 2. Clear Remediation Path
**Before**: "Why aren't events logging?" → investigate database, code, architecture
**After**: "Missing tomli-w" → add to dependencies → done

### 3. No Silent Data Loss
**Before**: Hooks run but don't log events, data silently lost
**After**: Hook fails, user knows immediately to fix it

### 4. Better Developer Experience
**Before**: Confusion, time waste, complex debugging
**After**: Clear error, clear fix, quick resolution

### 5. Validates Inline Dependencies
**Before**: Missing dependencies go unnoticed until runtime failure
**After**: Missing dependencies cause immediate, visible failures

## Philosophy: Fail Loudly > Fail Silently

### Why This Is Better

**Silent Failure** (old approach):
```
✗ Hook runs
✗ No events logged
✗ No error
✗ User confused
✗ Hours of debugging
✗ Data loss
```

**Loud Failure** (new approach):
```
✓ Hook fails
✓ Clear error
✓ User informed
✓ Fix in minutes
✓ No data loss
```

### The Zen of Python

> "Errors should never pass silently.
> Unless explicitly silenced."

Our old try/except **explicitly silenced** critical errors. This violates Python best practices and caused real problems.

## Integration with Validation

The validator (`validate_dependencies.py`) now detects these failures:

```python
# Run script with uv --no-project to test dependencies
result = subprocess.run(["uv", "run", "--no-project", script_path])

# Check for our fail-fast error
if "HOOK INFRASTRUCTURE FAILURE" in result.stderr:
    # Extract missing module and report
    errors.append(f"Missing dependency: {module_name}")
```

This creates **defense in depth**:
1. **Static validation**: Check dependency versions match standards
2. **Dynamic validation**: Actually run scripts to test imports
3. **Runtime validation**: Fail-fast error if imports fail in production

## Lessons Learned

### 1. Don't Hide Errors

**Bad**:
```python
try:
    critical_import()
except ImportError:
    pass  # Hope it works out!
```

**Good**:
```python
try:
    critical_import()
except ImportError as e:
    print(f"CRITICAL ERROR: {e}", file=sys.stderr)
    raise
```

### 2. Make Errors Actionable

Don't just say "Import failed." Say:
- What failed
- Why it probably failed
- How to fix it
- Where to find more info

### 3. Test Failure Modes

We tested happy paths but never tested:
- What happens if dependency is missing?
- What error message does user see?
- Can they fix it from the error alone?

### 4. Silent Fallbacks Are Dangerous

"Graceful degradation" sounds nice, but:
- If core functionality fails, FAIL THE OPERATION
- Don't pretend everything is fine when it's not
- Users need to know when things are broken

## Migration Impact

### Existing Installations

**Q**: Will this break existing installations?
**A**: Only if they have missing dependencies (which is already broken, just silently)

**Q**: What if someone relies on fallback behavior?
**A**: The fallback was masking bugs. Better to fix the bugs than hide them.

### Rollout Strategy

1. ✅ Update hook_framework.py with fail-fast error
2. ✅ Update validator to detect failures
3. ⏭️ Deploy to test environment
4. ⏭️ Verify all hooks work correctly
5. ⏭️ Deploy to production
6. ⏭️ Monitor for any import errors

## Files Modified

1. **brainworm/utils/hook_framework.py** (lines 38-85)
   - Removed silent fallback
   - Added fail-fast error with clear message
   - Re-raises ImportError as RuntimeError

2. **brainworm/scripts/validate_dependencies.py** (line 219)
   - Detects fail-fast error in stderr
   - Reports missing dependencies clearly

3. **brainworm/hooks/post_tool_use.py** (line 5)
   - Added missing `tomli-w>=1.0.0` dependency
   - Would have been caught immediately with fail-fast

## Related Issues

- **Missing tomli-w**: MISSING_DEPENDENCY_FIX.md
- **Flag removal**: EVENT_LOGGING_SIMPLIFICATION.md
- **Validation**: validate_dependencies.py enhancement

## Conclusion

**Silent failures are the enemy of maintainable software.**

By failing fast with clear errors, we:
- Save debugging time
- Prevent data loss
- Improve developer experience
- Catch problems immediately

This architectural change would have prevented the entire debugging session that led to discovering the `tomli-w` issue. That alone justifies the change.

**Fail fast. Fail clearly. Fail helpfully.**
