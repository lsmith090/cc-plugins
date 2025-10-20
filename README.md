# Claude Code Plugins Marketplace

Private marketplace for distributing Claude Code plugins. Install plugins to enhance your Claude Code development workflow with structured discipline, enhanced capabilities, and workflow continuity.

## Quick Start

Add this marketplace to Claude Code:

```bash
/plugin marketplace add https://github.com/lsmith090/cc-plugins
```

List available plugins:

```bash
/plugin list
```

Install a plugin:

```bash
/plugin install <plugin-name>@medicus-it
```

## Available Plugins

### brainworm

DAIC workflow enforcement and event storage system for Claude Code.

**Install**: `/plugin install brainworm@medicus-it`

**Documentation**: [brainworm/](./brainworm/)

**Version**: 1.0.0

### mcp-servers

Curated collection of Model Context Protocol (MCP) servers for enhanced Claude Code capabilities.

**Install**: `/plugin install mcp-servers@medicus-it`

**Documentation**: [mcp-servers/](./mcp-servers/)

**Version**: 1.0.0

## Repository Structure

```
cc-plugins/
├── brainworm/              # DAIC workflow plugin
├── mcp-servers/            # MCP server collection
├── tests/                  # Test infrastructure (not distributed)
├── CLAUDE.md               # Development guidelines
└── README.md               # This file
```

Each plugin directory contains:
- `.claude-plugin/` - Plugin metadata
- `hooks/` - Hook implementations
- `commands/` - Slash commands
- `README.md` - Plugin documentation
- `CHANGELOG.md` - Version history

## Contributing

See [CLAUDE.md](./CLAUDE.md) for complete contribution guidelines including:
- Adding new plugins
- Testing requirements
- Documentation standards
- Release process

## Support

**Issues**: https://github.com/lsmith090/cc-plugins/issues

**Development**: See [CLAUDE.md](./CLAUDE.md)

**Plugin Documentation**: See individual plugin directories
