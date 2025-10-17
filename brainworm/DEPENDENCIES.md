# Brainworm Plugin Dependencies

This document defines the standard dependency versions for the brainworm plugin. When adding or updating inline script metadata (`# /// script`), use these exact versions to ensure consistency.

## Standard Dependency Versions

### Core Dependencies

- **`rich>=13.0.0`** - UI formatting and console output
  - Used by: hooks, scripts, utilities
  - Purpose: Beautiful terminal output, progress bars, tables

- **`filelock>=3.13.0`** - Atomic file operations
  - Used by: hooks, hook framework
  - Purpose: Prevent race conditions in concurrent hook execution

- **`tomli-w>=1.0.0`** - TOML writing (Python 3.12+)
  - Used by: config management, scripts that modify .toml files
  - Purpose: Write TOML configuration files
  - Note: Reading TOML uses built-in `tomllib` (Python 3.12+)

- **`tiktoken>=0.7.0`** - Token counting
  - Used by: transcript processor
  - Purpose: Accurate token counting for context management

- **`typer>=0.9.0`** - CLI framework
  - Used by: CLI command scripts (tasks, daic)
  - Purpose: Type-safe command-line interfaces

- **`pendulum>=3.0.0`** - Advanced datetime handling
  - Used by: event logger
  - Purpose: Timezone-aware datetime operations

## Common Dependency Patterns

### For Hooks (using HookFramework)

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

**When hooks need config access** (add tomli-w):
```python
# dependencies = [
#     "rich>=13.0.0",
#     "tomli-w>=1.0.0",  # For utils.config which may write TOML
#     "filelock>=3.13.0",
# ]
```

### For CLI Scripts (Typer-based)

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
#     "typer>=0.9.0",
# ]
# ///
```

### For Config Management Scripts

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "tomli-w>=1.0.0",  # For reading (tomllib) and writing TOML
# ]
# ///
```

### For Utilities (Minimal Dependencies)

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
```

## TOML Handling (Python 3.12+)

**Important:** Python 3.12+ has built-in `tomllib` for reading TOML files. We only need `tomli-w` for writing.

### Reading TOML Files

```python
import tomllib  # Built-in, no dependency needed

with open('config.toml', 'rb') as f:  # Note: 'rb' mode required
    config = tomllib.load(f)
```

### Writing TOML Files

```python
import tomli_w  # Requires tomli-w>=1.0.0

with open('config.toml', 'wb') as f:  # Note: 'wb' mode required
    tomli_w.dump(config, f)
```

### Files Using TOML Operations

**Read-only** (use `tomllib`, no inline dependency):
- Most hooks (via `utils.config`)
- Most scripts (via `utils.config`)
- `utils/daic_state_manager.py` (fallback only)

**Read + Write** (requires `tomli-w>=1.0.0`):
- `utils/config.py` - Writes default config, updates values
- `scripts/add_trigger.py` - Adds trigger phrases to config
- `scripts/api_mode.py` - Toggles API mode in config
- All other scripts that import `utils.config` (which uses `tomli-w`)

## Dependency Update Procedures

### When Updating Dependency Versions

1. **Update this document first** with new version
2. **Find all occurrences** of the old version:
   ```bash
   grep -r "old-package>=X.Y.Z" brainworm/
   ```
3. **Update all inline script metadata** to use new version
4. **Run validation script** to ensure consistency:
   ```bash
   python3 scripts/validate_dependencies.py
   ```
5. **Update `pyproject.toml` dev dependencies** if needed
6. **Test with `uv run`** on several files to verify

### Adding a New Dependency

1. **Add to this document** with version and purpose
2. **Add to relevant inline script metadata**
3. **Add to `pyproject.toml` dev dependencies**:
   ```toml
   [dependency-groups]
   dev = [
       ...
       "new-package>=X.Y.Z",
   ]
   ```
4. **Run `uv sync`** to install
5. **Update validation script** to recognize new dependency
6. **Document usage patterns** in this file

### Removing a Dependency

1. **Search for all uses**:
   ```bash
   grep -r "package-name" brainworm/
   ```
2. **Remove from all inline script metadata**
3. **Remove from `pyproject.toml`**
4. **Update this documentation**
5. **Run validation** to ensure no orphaned references

## Validation

The plugin includes a validation script to check for dependency inconsistencies:

```bash
# Validate all dependencies match documentation
python3 scripts/validate_dependencies.py

# Validate with detailed output
python3 scripts/validate_dependencies.py --verbose

# Check specific file
python3 scripts/validate_dependencies.py --file brainworm/hooks/pre_tool_use.py
```

The validator checks:
- All inline dependencies match documented versions
- No deprecated packages (e.g., `toml>=0.10.0`)
- Version string consistency
- Missing dependencies in files that import them

## Development Dependencies

The repository's `pyproject.toml` includes all plugin dependencies for development:

```toml
[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.3.0",
    "rich>=13.0.0",
    "tomli-w>=1.0.0",
    "psutil>=5.9.0",
    "typer>=0.9.0",
    "filelock>=3.13.0",
    "tiktoken>=0.7.0",
    "pendulum>=3.0.0",
]
```

These are installed via `uv sync` for development and testing.

## Why PEP 723 Inline Dependencies?

Brainworm uses [PEP 723](https://peps.python.org/pep-0723/) inline script metadata because:

1. **Self-contained execution**: Hooks/scripts run via `uv run --script` without installation
2. **Isolated environments**: Each script gets correct dependencies automatically
3. **No installation required**: Works in user projects without installing plugin as package
4. **Claude Code compatibility**: Matches how Claude Code executes hooks

This means dependencies **must** be declared inline in each file that needs them, even though it causes some duplication.

## Dependency Philosophy

**Minimal viable dependencies**:
- Only include what's strictly necessary
- Prefer standard library when possible (e.g., `tomllib` over `toml`)
- Keep hook dependencies lightweight for fast execution
- Share utilities to avoid duplicating logic

**Version constraints**:
- Use `>=` for minimum version (allows updates)
- Pin major version when breaking changes are a concern
- Test compatibility with stated versions

**Centralization strategy**:
- Document standard versions here (single source of truth)
- Validate consistency via automation
- Accept duplication as necessary for inline script pattern
- Keep maintenance burden low via validation

## Migration History

### v1.0.0 - TOML Dependency Migration

**Deprecated**: `toml>=0.10.0` (third-party package)
**Replaced with**: `tomli-w>=1.0.0` (write-only) + `tomllib` (built-in read-only)

**Reason**: Python 3.12+ has built-in `tomllib` for reading TOML. The `toml` package is deprecated and unnecessary.

**Changes**:
- Updated 14 files from `toml>=0.10.0` → `tomli-w>=1.0.0`
- Updated imports: `import toml` → `import tomllib` + `import tomli_w`
- Updated file modes: `'r'/'w'` → `'rb'/'wb'` for TOML operations
- Updated pyproject.toml: Removed `toml`, added `tomli-w`

**Files affected**:
- Hooks: `pre_tool_use.py`, `session_start.py`, `transcript_processor.py`, `user_prompt_submit.py`
- Scripts: `add_trigger.py`, `api_mode.py`, `create_task.py`, `daic_command.py`, `statusline-script.py`, `switch_task.py`, `update_daic_mode.py`, `update_session_correlation.py`, `update_task_state.py`
- Utils: `config.py`, `daic_state_manager.py`

## Quick Reference

| Dependency | Version | Usage | Files |
|------------|---------|-------|-------|
| `rich` | `>=13.0.0` | UI/console output | 18 files |
| `filelock` | `>=3.13.0` | Atomic operations | 10 files |
| `tomli-w` | `>=1.0.0` | TOML writing | 14 files |
| `typer` | `>=0.9.0` | CLI framework | 2 files |
| `tiktoken` | `>=0.7.0` | Token counting | 1 file |
| `pendulum` | `>=3.0.0` | Datetime handling | 1 file |

---

**Last Updated**: 2025-10-17
**Maintainer**: See repository CLAUDE.md for contribution guidelines
