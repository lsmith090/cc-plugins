---
allowed-tools: Write, Edit, Read, Glob, Bash(mkdir:*,chmod:*)
description: Scaffold complete plugin structure following repository conventions
argument-hint: "<plugin-name>"
---

# Create Plugin

Scaffolds a complete plugin structure following cc-plugins repository conventions.

**Usage:**
```bash
/create-plugin <plugin-name>
```

**What it creates:**

```
<plugin-name>/
  .claude-plugin/
    plugin.json           # Plugin metadata
  hooks/
    hooks.json            # Hook configuration (empty template)
  agents/                 # Subagent definitions directory
  commands/               # Slash commands directory
  scripts/                # Utility scripts directory
  utils/                  # Shared utilities directory
  docs/                   # Comprehensive documentation
    README.md             # Documentation hub
    getting-started.md    # Installation guide
    architecture.md       # Technical architecture
  CHANGELOG.md            # Version history
  DEPENDENCIES.md         # Dependency standards
  README.md               # Plugin overview
  CLAUDE.md               # Development guidance
  LICENSE                 # MIT license
tests/<plugin-name>/      # Test directory at repository root
  unit/                   # Unit tests
  integration/            # Integration tests
  e2e/                    # End-to-end tests
  conftest.py             # Pytest configuration
```

**Process:**

1. **Validate plugin name** - Must be lowercase with hyphens (kebab-case)
2. **Check for conflicts** - Ensure plugin doesn't already exist
3. **Create directory structure** - All directories and subdirectories
4. **Generate plugin.json** - With proper metadata fields
5. **Create template files** - README, CHANGELOG, CLAUDE.md, LICENSE, DEPENDENCIES.md
6. **Set up test structure** - At repository root with conftest.py
7. **Update root README.md** - Add plugin to "Available Plugins" section
8. **Create empty hooks.json** - Template for future hooks

**Plugin Metadata Fields:**

The plugin.json will include:
- name: Plugin name (kebab-case)
- version: Starting at 1.0.0
- description: Brief plugin description
- author: Developer info
- homepage: GitHub profile
- repository: cc-plugins repository URL
- license: MIT
- keywords: Relevant tags
- hooks: Path to hooks.json

**Template Contents:**

All template files follow repository standards:
- README.md: Installation, usage, features
- CHANGELOG.md: Version history with [1.0.0] header
- CLAUDE.md: Guidance for Claude Code (users and contributors)
- DEPENDENCIES.md: PEP 723 dependency standards
- LICENSE: MIT license with current year
- docs/: Complete documentation structure

**After Creation:**

You'll need to manually:
1. Implement hook scripts in hooks/
2. Update hooks.json with hook configurations
3. Add subagents in agents/
4. Create slash commands in commands/
5. Write tests in tests/<plugin-name>/
6. Document in docs/

**Example:**

```bash
/create-plugin my-awesome-plugin
```

This creates the complete structure and updates repository files. Then you can start implementing functionality.

**Implementation Guidelines:**

Follow these patterns from existing plugins (like brainworm):
- Hooks use PEP 723 inline dependencies
- Scripts use plugin-launcher wrapper
- State management via unified state files
- Documentation includes offline access
- Tests at repository level, not in plugin

**Next Steps After Scaffolding:**

1. Edit plugin.json with accurate description and keywords
2. Update README.md with plugin-specific details
3. Add hooks and register in hooks.json
4. Implement utility scripts
5. Write comprehensive tests
6. Document features in docs/
7. Update CHANGELOG.md as you add features
