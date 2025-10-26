# Changelog

All notable changes to the mcp-servers plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-10-26

### Added

**Playwright MCP Server Integration**
- Microsoft Playwright MCP server for browser automation
- Browser interaction capabilities (navigate, click, type, drag)
- Screenshot and PDF generation tools
- JavaScript execution in browser context
- Tab and session management
- Network request interception
- Console message retrieval
- Zero-configuration setup with headless mode by default
- Optional advanced configuration via config file

## [1.0.0] - 2025-01-15

### Added

**Context7 MCP Server Integration**
- Automatic Context7 MCP server startup on session start
- Fetches current, version-specific documentation from official sources
- Zero-configuration setup with sensible defaults
- Optional API key support for higher rate limits
- Seamless integration with Claude Code's MCP system

**SessionStart Hook**
- Automatic MCP server initialization on Claude Code startup
- Environment variable management for API keys
- Server health checking
- Graceful error handling and user feedback

**Configuration**
- Zero-configuration by default
- Optional API key configuration via environment variables
- Server settings customization support
- Expandable architecture for additional MCP servers

**Documentation**
- Installation and setup guide
- Configuration reference
- API key setup instructions
- Troubleshooting guide

### Features

- **Zero-Configuration**: Works out of the box with no manual setup required
- **Privacy-Conscious**: Optional API key usage, works without authentication
- **Extensible**: Architecture supports adding additional curated MCP servers
- **Reliable**: Health checking and graceful degradation on failures

[1.0.0]: https://github.com/lsmith090/cc-plugins/releases/tag/mcp-servers-v1.0.0
