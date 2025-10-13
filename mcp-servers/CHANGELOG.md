# Changelog

All notable changes to the mcp-servers plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-13

### Added
- Initial release of mcp-servers plugin
- Context7 MCP server integration for up-to-date documentation
- Automatic MCP server startup on session initialization
- Zero-configuration setup with sensible defaults
- Optional API key support for Context7 higher rate limits
- Comprehensive documentation (README.md, CLAUDE.md)
- Plugin manifest with MCP server configuration

### Features
- **Context7 Integration**: Fetch current, version-specific documentation from official sources
- **Automatic Loading**: MCP servers start automatically when plugin is enabled
- **Environment Variables**: Support for optional configuration via `CONTEXT7_API_KEY`
- **Extensible Architecture**: Ready for additional MCP servers to be added

### Documentation
- User-facing README with installation and usage instructions
- CLAUDE.md with development guidelines and architecture notes
- Troubleshooting section for common issues
- Contributing guidelines for adding new MCP servers

[1.0.0]: https://github.com/lsmith090/cc-plugins/releases/tag/mcp-servers-v1.0.0
