# Claude Code Plugins Marketplace

Private marketplace for Claude Code plugins.

## Available Plugins

### brainworm
DAIC workflow enforcement and event storage system for Claude Code.

**Installation:**
```
/plugin marketplace add https://github.com/lsmith090/cc-plugins
/plugin install brainworm@brainworm-marketplace
```

**Features:**
- DAIC workflow enforcement (Discussion → Alignment → Implementation → Check)
- Event storage system with session correlation
- Intelligent trigger phrase detection
- Comprehensive hook system (PreToolUse, PostToolUse, SessionStart, SessionEnd, etc.)
- Task management and workflow continuity
- Specialized subagents for code review, logging, documentation

**Repository:** https://github.com/lsmith090/cc-plugins

### mcp-servers
Curated collection of Model Context Protocol (MCP) servers for enhanced Claude Code capabilities.

**Installation:**
```
/plugin marketplace add https://github.com/lsmith090/cc-plugins
/plugin install mcp-servers@brainworm-marketplace
```

**Features:**
- Context7 MCP server for up-to-date documentation
- Automatic server startup on session start
- Zero-configuration with sensible defaults
- Optional API key support for higher rate limits
- Expandable with additional curated MCP servers

**Included MCP Servers:**
- **Context7**: Fetches current, version-specific documentation from official sources

**Repository:** https://github.com/lsmith090/cc-plugins
