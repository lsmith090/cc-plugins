# Repository Governance System

## Overview

Brainworm implements a comprehensive governance system to ensure that changes are made in source templates (`src/hooks/templates/`) rather than generated files (`.claude/hooks/`). This prevents accidental edits to generated files and ensures proper workflow for system modifications.

## Core Principles

1. **Source of Truth**: All changes must be made in `src/hooks/templates/` 
2. **Generated Files**: Files in `.claude/hooks/` are auto-generated and should never be edited directly
3. **Governance Headers**: Generated files contain clear warnings and metadata
4. **Automatic Tracking**: Installation system tracks all generated files with checksums
5. **Validation Tools**: Commands to check and fix governance violations

## File Structure

### Templates (Source Files)
```
src/hooks/templates/
├── daic_state_manager.py      # Template for DAIC workflow management
├── transcript_processor.py    # Template for transcript processing
├── analytics_processor.py     # Template for analytics capture
└── ... (other template files)
```

### Generated Files (Install Targets)
```
.claude/hooks/
├── daic_state_manager.py      # Generated from template (DO NOT EDIT)
├── transcript_processor.py    # Generated from template (DO NOT EDIT) 
├── analytics_processor.py     # Generated from template (DO NOT EDIT)
└── ... (other generated files)
```

### Governance Metadata
```
.claude/governance-manifest.json   # Tracks all generated files with checksums
```

## Governance Headers

Generated files include headers that clearly identify them as auto-generated:

```python
# THIS FILE IS AUTO-GENERATED - DO NOT EDIT DIRECTLY
# Generated from: src/hooks/templates/daic_state_manager.py
# Generation time: 2025-09-02T15:30:00Z
# Template checksum: abc123...
# 
# To modify this file, edit the source template and run: ./install
# For questions about this file, see: docs/GOVERNANCE.md
#
```

## Governance Commands

### Check Governance Status
```bash
./check-governance              # Show status of all generated files
./check-governance --status     # Same as above
```

### Fix Governance Issues
```bash
./check-governance --fix        # Reinstall modified files
```

### File Utilities
```bash
./check-governance --which-template <file>     # Show template for generated file
./check-governance --help-file <file>          # Show help for modified file
```

## Workflow for Making Changes

### ✅ Correct Workflow
1. **Identify the template**: Use `./check-governance --which-template <generated-file>` 
2. **Edit the template**: Make changes in `src/hooks/templates/`
3. **Test locally**: Run tests to validate changes
4. **Reinstall system**: Run `./install` to apply changes
5. **Verify**: Run `./check-governance` to confirm proper installation

### ❌ Incorrect Workflow (Blocked by Governance)
1. ~~Edit files in `.claude/hooks/` directly~~ (Will be detected and blocked)
2. ~~Commit changes to generated files~~ (Pre-commit hook will prevent)
3. ~~Ignore governance warnings~~ (System will detect modifications)

## Governance Manifest

The system maintains a governance manifest at `.claude/governance-manifest.json`:

```json
{
  "version": "1.0",
  "generated": "2025-09-02T15:30:00Z",
  "installer_version": "1.1.0",
  "files": {
    ".claude/hooks/daic_state_manager.py": {
      "source": "src/hooks/templates/daic_state_manager.py",
      "source_checksum": "abc123...",
      "generated_checksum": "def456...",
      "generated_time": "2025-09-02T15:30:00Z",
      "status": "up-to-date"
    }
  }
}
```

## Status Indicators

- **up-to-date**: ✅ File matches expected state
- **modified**: ❌ File has been changed since generation  
- **missing**: ⚠️ Generated file is missing

## Error Messages and Guidance

### Direct Edit Detection
When a generated file is modified, the governance system provides clear guidance:

```
ERROR: Direct edit detected in generated file
File: .claude/hooks/daic_state_manager.py
Source: src/hooks/templates/daic_state_manager.py

This file is auto-generated from a template. Direct edits will be lost.

To modify this file:
1. Edit the source template: src/hooks/templates/daic_state_manager.py
2. Reinstall: ./install  
3. Test your changes: uv run -m pytest tests/ -v

To restore the original file: ./check-governance --fix
```

## Integration with Development Workflow

### Installation Process
- `./install` automatically enables governance for all generated files
- Checksums are computed and stored during installation
- Governance manifest is updated with each installation

### Git Integration (Future)
- Pre-commit hooks prevent committing modified generated files
- Git ignore patterns exclude governance metadata from commits
- Branch protection ensures proper review of template changes

### IDE Integration (Future)
- File headers provide visual warnings in editors
- Extension could highlight generated files differently
- Quick actions to jump from generated file to source template

## Best Practices

### For Developers
1. **Always check template source** before making changes
2. **Use governance commands** to understand file relationships
3. **Test changes thoroughly** before committing templates
4. **Run governance checks** as part of development workflow

### For System Modifications
1. **Edit templates only** - never generated files
2. **Test installation** after template changes
3. **Update documentation** when adding new templates
4. **Validate governance** before submitting changes

### For Troubleshooting
1. **Check governance status** first: `./check-governance`
2. **Use file utilities** to understand relationships
3. **Fix issues promptly** with `./check-governance --fix`
4. **Reinstall if needed** with `./install`

## Implementation Details

### Governance Utilities (`src/hooks/governance_utils.py`)
- File checksum computation
- Governance header generation
- Manifest management
- Validation and status checking

### Installation Integration
- Modified installer adds governance headers during file copying
- Checksums computed for both templates and generated files
- Manifest updated automatically during installation

### Validation System
- Real-time status checking against expected checksums
- Detection of missing, modified, or corrupted files
- Automated fixing through reinstallation

## Future Enhancements

### Phase 2
- Pre-commit Git hooks for governance enforcement
- IDE plugins for better developer experience
- Automated template change detection

### Phase 3  
- Central governance dashboard
- Integration with CI/CD pipelines
- Advanced diff utilities for template changes

## Troubleshooting

### Governance Check Fails
1. Verify you're in the brainworm project root
2. Check that `src/hooks/governance_utils.py` exists
3. Run `./install` to ensure governance is properly set up

### Generated File Missing
1. Run `./install` to regenerate all files
2. Check that template source exists
3. Verify file permissions and directory structure

### Modified File Detected
1. Use `./check-governance --help-file <file>` for guidance
2. Edit the source template instead of generated file
3. Run `./install` to apply changes properly

The governance system ensures that the brainworm system maintains its integrity while providing clear guidance for developers making legitimate changes.