# Claude Code Plugins Marketplace

Repository for distributing Claude Code plugins via plugin marketplace.

## Repository Purpose

This repository hosts plugins for installation via:
```bash
/plugin marketplace add https://github.com/lsmith090/cc-plugins
/plugin install <plugin-name>@brainworm-marketplace
```

## Repository Structure

```
cc-plugins/
├── <plugin-name>/          # Each plugin in its own directory
│   ├── .claude-plugin/     # Plugin metadata
│   ├── hooks/              # Plugin hooks
│   ├── agents/             # Plugin agents
│   ├── commands/           # Plugin slash commands
│   ├── scripts/            # Plugin scripts
│   ├── utils/              # Plugin utilities
│   ├── docs/               # Plugin documentation
│   ├── CLAUDE.md           # Plugin-specific guidance
│   └── README.md           # Plugin overview
├── tests/                  # Repository-level tests (not installed)
│   └── <plugin-name>/      # Plugin test suites
├── pyproject.toml          # Python project config
├── README.md               # Marketplace overview
└── CLAUDE.md               # This file
```

## Key Separation: Plugin vs Repository

**Plugin Files** (installed to user projects):
- Everything inside `<plugin-name>/` directory
- Gets distributed when users install the plugin
- Includes documentation for offline access

**Repository Files** (never installed):
- `tests/` - Test suites stay at repo level
- Root config files (pyproject.toml, etc.)
- CI/CD workflows (.github/)
- Repository README and CLAUDE.md

This separation ensures users only get the plugin files they need, not development infrastructure.

## Current Plugins

### brainworm
DAIC workflow enforcement and event storage system for Claude Code.

**Location**: `brainworm/`
**Tests**: `tests/brainworm/`
**Documentation**: `brainworm/docs/`
**Plugin Guidance**: `brainworm/CLAUDE.md`

## Adding a New Plugin

### 1. Create Plugin Directory

```bash
mkdir <plugin-name>
cd <plugin-name>
```

### 2. Create Plugin Metadata

Create `.claude-plugin/plugin.json`:

```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "Plugin description",
  "author": {
    "name": "Your Name",
    "email": "your.email@example.com"
  },
  "homepage": "https://github.com/yourusername",
  "repository": "https://github.com/lsmith090/cc-plugins",
  "license": "MIT",
  "keywords": ["workflow", "productivity"],
  "hooks": "./hooks/hooks.json"
}
```

### 3. Implement Plugin Functionality

Create necessary directories and files:
- `hooks/` - Hook implementations
- `hooks/hooks.json` - Hook configuration
- `commands/` - Slash commands
- `scripts/` - Utility scripts
- `docs/` - Documentation
- `README.md` - Plugin overview
- `CLAUDE.md` - Plugin-specific guidance for Claude
- `CHANGELOG.md` - Version history
- `LICENSE` - License file

### 4. Add Tests

Create test directory at repository root:

```bash
mkdir -p tests/<plugin-name>
```

Add test files following pytest conventions:
- `tests/<plugin-name>/unit/` - Unit tests
- `tests/<plugin-name>/integration/` - Integration tests
- `tests/<plugin-name>/e2e/` - End-to-end tests

### 5. Update Repository Files

**Update root README.md**:
Add plugin to "Available Plugins" section with installation instructions.

**Update pyproject.toml** (if needed):
Add any Python dependencies the plugin requires.

### 6. Documentation

Create `<plugin-name>/CLAUDE.md` with:
- Usage guidance for Claude Code
- Development guidelines for contributors
- Reference to plugin-specific behavioral docs

## Testing Plugins

### Run All Tests

```bash
uv run pytest tests/
```

### Test Specific Plugin

```bash
uv run pytest tests/<plugin-name>/
```

### With Coverage

```bash
uv run pytest --cov=<plugin-name> --cov-report=term-missing tests/<plugin-name>/
```

**Note**: Always use `uv run` to ensure tests run with the correct dependencies and plugin package is built.

### Test Organization

Each plugin should have:
- **Unit tests**: Fast, isolated component tests
- **Integration tests**: Component interaction tests
- **E2E tests**: Complete workflow validation
- **Security tests**: Security validation
- **Performance tests**: Performance regression checks

## Development Workflow

### Working on a Plugin

1. **Make changes** in `<plugin-name>/` directory
2. **Update documentation** in `<plugin-name>/docs/`
3. **Add/update tests** in `tests/<plugin-name>/`
4. **Update CHANGELOG.md** in plugin directory
5. **Run tests** to validate changes
6. **Update version** in `.claude-plugin/plugin.json`

### Branch Strategy

- `main` - Production-ready releases
- `feature/<plugin>-<feature-name>` - New features
- `fix/<plugin>-<issue>` - Bug fixes
- `refactor/<plugin>-<component>` - Refactoring

### Commit Messages

Follow conventional commit format with plugin scope:

```
feat(brainworm): Add custom trigger phrase support
fix(plugin-name): Resolve hook execution issue
docs(brainworm): Update DAIC workflow documentation
test(plugin-name): Add comprehensive parsing tests
```

## Release Process

### For a Plugin Release

1. **Update Version**:
   - Edit `<plugin-name>/.claude-plugin/plugin.json`
   - Update `version` field (use semantic versioning)

2. **Update Changelog**:
   - Edit `<plugin-name>/CHANGELOG.md`
   - Document changes, fixes, breaking changes

3. **Run Tests**:
   ```bash
   uv run pytest tests/<plugin-name>/
   ```

4. **Test Installation**:
   ```bash
   # Install from local path in test project
   /plugin install <plugin-name>@file:///path/to/cc-plugins/<plugin-name>
   ```

5. **Commit and Tag**:
   ```bash
   git add <plugin-name>/
   git commit -m "release(<plugin-name>): v1.0.0"
   git tag <plugin-name>-v1.0.0
   ```

6. **Push**:
   ```bash
   git push origin main --tags
   ```

### Versioning Guidelines

Use semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes, incompatible API changes
- **MINOR**: New features, backward-compatible
- **PATCH**: Bug fixes, backward-compatible

## Code Quality Standards

### Python Standards

- **Style**: Follow PEP 8
- **Line Length**: 120 characters
- **Type Hints**: Use throughout
- **Docstrings**: All public functions
- **Linting**: Use ruff (configured in pyproject.toml)

### Testing Standards

- **Coverage**: Aim for meaningful coverage, not just metrics
- **Real Value**: Test actual bug scenarios
- **Integration**: Test component interactions
- **Performance**: Include regression tests

### Documentation Standards

- **README.md**: Clear installation and usage
- **CLAUDE.md**: Guidance for Claude Code
- **docs/**: Comprehensive technical documentation
- **Inline**: Docstrings and comments for complex logic

## Plugin Development Best Practices

### Hook Development

**Use Proper Paths**:
- Reference `${CLAUDE_PLUGIN_ROOT}` in hook configs
- Use plugin-launcher wrapper for scripts
- Access state via unified_session_state.json

**Follow Schema**:
- Use hook_types for type safety
- Follow Claude Code hook specifications
- Handle errors gracefully

### Slash Commands

**Command Files** (`commands/*.md`):
- Clear description
- Usage examples
- Argument documentation

**Execution**:
- Use plugin-launcher wrapper for cross-context execution
- Handle arguments properly
- Provide helpful error messages

### Documentation

**For Users**:
- Installation instructions
- Quick start guide
- Configuration examples
- Troubleshooting

**For Developers**:
- Architecture overview
- Development setup
- Testing guidelines
- Contribution process

## Testing Installation

### Local Testing

```bash
# In a test project
/plugin marketplace add file:///path/to/cc-plugins
/plugin install <plugin-name>@brainworm-marketplace
```

### Verify Installation

1. Check plugin files copied correctly
2. Test slash commands work
3. Verify hooks execute
4. Confirm auto-setup functionality
5. Validate zero-configuration experience

## Troubleshooting

### Tests Failing

**Check Dependencies**:
```bash
uv sync
```

**Run Verbose**:
```bash
uv run pytest -v tests/<plugin-name>/
```

**Check Isolation**:
```bash
uv run pytest tests/<plugin-name>/unit/test_specific.py
```

### Plugin Installation Issues

**Verify plugin.json**:
- Valid JSON syntax
- Correct version format
- All required fields present

**Check hooks.json**:
- Pipe-separated matchers: `"Edit|Write|MultiEdit"`
- Correct paths to hook scripts
- Valid hook event names

**Test Locally**:
```bash
/plugin install <plugin-name>@file:///absolute/path
```

## Development with Brainworm

This repository has brainworm installed, so you'll experience:

**DAIC Workflow Enforcement**:
- Discussion mode blocks implementation tools
- Use trigger phrases: "go ahead", "make it so", "ship it"
- Manual switch: `/brainworm:daic implementation`

**Task Management**:
- Create tasks: `./tasks create <task-name>`
- Check status: `./tasks status`
- Follow protocols for completion

**Behavioral Guidance**:
See `CLAUDE.sessions.md` for complete brainworm workflow practices.

## Repository Maintenance

### Regular Tasks

1. **Keep tests passing**: Run `pytest tests/` regularly
2. **Update dependencies**: Keep pyproject.toml current
3. **Review issues**: Address plugin-specific issues
4. **Update documentation**: Keep READMEs accurate
5. **Monitor performance**: Watch for regression

### Adding Dependencies

Edit `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.3.0",
]
```

Then sync:
```bash
uv sync
```

## Support and Issues

**GitHub Issues**: https://github.com/lsmith090/cc-plugins/issues

**Documentation**:
- Marketplace: This file
- Plugin-specific: Each plugin's CLAUDE.md
- Technical: Plugin docs/ directories

## Quick Reference

### Repository Structure

- `<plugin-name>/` - Plugin source (installed)
- `tests/<plugin-name>/` - Plugin tests (not installed)
- `README.md` - Marketplace overview
- `CLAUDE.md` - This file

### Common Commands

```bash
# Testing
uv run pytest tests/<plugin-name>/
uv run pytest --cov=<plugin-name> tests/<plugin-name>/

# Linting
ruff check .

# Development (with brainworm)
./daic status
./tasks create <task-name>
```

---

**Marketplace Philosophy**: Provide high-quality, well-documented Claude Code plugins that enhance development workflows. Focus on user experience, reliability, and continuous improvement.

## Brainworm System Behaviors

@CLAUDE.sessions.md
