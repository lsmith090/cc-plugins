# PEP 723 Dependency Management

Complete guide to managing inline script dependencies for Claude Code hooks.

## Critical Rule: Complete Inline Dependencies

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

## Standard Dependency Versions

These versions are standardized across all brainworm hooks (from DEPENDENCIES.md):

**Core Dependencies:**
- `rich>=13.0.0` - UI formatting, console output
- `filelock>=3.13.0` - Atomic file operations
- `tomli-w>=1.0.0` - TOML writing (reading uses built-in `tomllib`)
- `typer>=0.9.0` - CLI framework
- `tiktoken>=0.7.0` - Token counting
- `pendulum>=3.0.0` - Advanced datetime handling

## Transitive Dependencies

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

## Common Dependency Patterns

### Hook using HookFramework (minimal)
```python
# dependencies = [
#     "rich>=13.0.0",
#     "filelock>=3.13.0",
# ]
```

### Hook with config access
```python
# dependencies = [
#     "rich>=13.0.0",
#     "tomli-w>=1.0.0",  # For utils.config
#     "filelock>=3.13.0",
# ]
```

### CLI script with Typer
```python
# dependencies = [
#     "rich>=13.0.0",
#     "typer>=0.9.0",
# ]
```

### Transcript processor
```python
# dependencies = [
#     "rich>=13.0.0",
#     "tiktoken>=0.7.0",
#     "tomli-w>=1.0.0",
#     "filelock>=3.13.0",
# ]
```

## Validation

Always validate dependencies after adding/changing them:

```bash
cd brainworm
python3 scripts/validate_dependencies.py --file hooks/your_hook.py
python3 scripts/validate_dependencies.py --verbose  # Check all files
```

## Common Utility Dependencies

Track which utilities require which dependencies:

| Utility Module | Required Dependencies |
|----------------|----------------------|
| `utils.config` | `tomli-w>=1.0.0` |
| `utils.hook_framework` | `rich>=13.0.0`, `filelock>=3.13.0` |
| `utils.file_manager` | `filelock>=3.13.0` |
| `utils.event_logger` | `rich>=13.0.0`, `filelock>=3.13.0` |
| `utils.daic_state_manager` | `filelock>=3.13.0` |

## Troubleshooting

**Import errors at runtime:**
- Check PEP 723 block is complete
- Verify all transitive dependencies included
- Run validation script
- Check version matches DEPENDENCIES.md

**Version conflicts:**
- Use exactly the versions from DEPENDENCIES.md
- Don't use `==` (exact), use `>=` (minimum)
- Consult DEPENDENCIES.md for rationale

**Missing dependencies:**
- Run validation script on your file
- Check stderr for import errors
- Add missing deps from standard versions list
