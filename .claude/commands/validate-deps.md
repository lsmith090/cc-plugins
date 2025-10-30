---
allowed-tools: Bash(python3:*,cd:*)
description: Validate PEP 723 inline dependencies against standards
argument-hint: "[files...]"
---

# Validate Dependencies

Validates PEP 723 inline dependencies in hook scripts against DEPENDENCIES.md standards.

**Usage:**
```bash
/validate-deps                        # Validate all hooks
/validate-deps hooks/session_start.py # Validate specific file
/validate-deps hooks/*.py             # Validate multiple files
```

**What it validates:**
- Version consistency with DEPENDENCIES.md
- Import completeness (transitive dependencies)
- No deprecated dependencies
- Scripts can execute with declared dependencies

**Running validation:**

Use `cd` to navigate into plugin directory (brainworm), then run the validation script.

```bash
cd brainworm && python3 scripts/validate_dependencies.py $ARGUMENTS
```

**Examples:**

Check all dependencies:
```bash
/validate-deps
```

Check specific hook:
```bash
/validate-deps --file hooks/session_start.py
```

Verbose output:
```bash
/validate-deps --verbose
```
