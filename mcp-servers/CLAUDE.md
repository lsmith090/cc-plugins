# MCP Servers Plugin - Claude Code Guidance

Instructions for Claude Code when working with or on the mcp-servers plugin.

## For Users (Plugin Installed in Your Project)

This plugin provides MCP (Model Context Protocol) servers that extend Claude Code's capabilities.

### What This Plugin Does

**Automatic MCP Server Loading**:
- When enabled, MCP servers start automatically at session start
- Servers provide additional tools and context to Claude
- No manual configuration required (with sensible defaults)

**Current MCP Servers**:

1. **Context7** - Up-to-date documentation fetcher
   - Fetches current, version-specific documentation
   - Prevents outdated API usage
   - Supports multiple languages/frameworks

### How to Use

**Context7 Usage**:

When you need documentation or current API examples, simply ask naturally:

- "What's the latest way to create a React hook?"
- "Show me FastAPI router examples"
- "How do I use pandas DataFrame.merge()?"

Claude will automatically invoke Context7 tools to fetch current documentation.

**Configuration (Optional)**:

For higher rate limits with Context7:
1. Get API key from [context7.com](https://context7.com/)
2. Set environment variable: `export CONTEXT7_API_KEY="your-key"`
3. Restart Claude Code

### Troubleshooting

**MCP Server Not Working**:
- Ensure Node.js/npm installed: `node --version`
- Check plugin installed: `/plugin list`
- Restart Claude Code session

**Rate Limits**:
- Get free Context7 API key for higher limits
- Set `CONTEXT7_API_KEY` environment variable

## For Contributors (Developing MCP Servers Plugin)

### Plugin Architecture

**Directory Structure**:

```
mcp-servers/
├── .claude-plugin/
│   └── plugin.json       # Plugin metadata
├── .mcp.json             # MCP server configurations
├── docs/                 # Documentation
├── README.md             # User-facing overview
├── CLAUDE.md             # This file
├── CHANGELOG.md          # Version history
└── LICENSE               # MIT license
```

**Key Files**:

- **plugin.json**: Plugin manifest with `mcpServers` field pointing to `.mcp.json`
- **.mcp.json**: MCP server configurations (command, args, environment)
- **README.md**: Comprehensive user documentation

### MCP Server Configuration

**Structure of .mcp.json**:

```json
{
  "mcpServers": {
    "server-name": {
      "command": "executable",
      "args": ["arg1", "arg2"],
      "env": {
        "ENV_VAR": "${ENV_VAR}"
      }
    }
  }
}
```

**Environment Variable Substitution**:
- Use `${VAR_NAME}` syntax for environment variables
- Claude Code substitutes at runtime
- Allows optional configuration (graceful degradation)

### Adding a New MCP Server

1. **Research the Server**:
   - Find official MCP server package/repository
   - Verify it follows MCP specification
   - Check installation method (npm, python, etc.)
   - Test locally first

2. **Add to .mcp.json**:
   ```json
   {
     "mcpServers": {
       "existing-server": { ... },
       "new-server": {
         "command": "npx",
         "args": ["-y", "package-name"],
         "env": {
           "API_KEY": "${NEW_SERVER_API_KEY}"
         }
       }
     }
   }
   ```

3. **Document in README.md**:
   - Add to "Included MCP Servers" section
   - Describe purpose and capabilities
   - Include configuration instructions
   - Add usage examples

4. **Update CHANGELOG.md**:
   - Document the addition
   - Note any configuration requirements

5. **Test Thoroughly**:
   ```bash
   /plugin install mcp-servers@file:///path/to/cc-plugins/mcp-servers
   # Start new session
   # Verify server loads and functions correctly
   ```

### Development Guidelines

**Server Selection Criteria**:
- **Quality**: Well-maintained, active development
- **Usefulness**: Provides significant value to developers
- **Reliability**: Stable, tested, documented
- **Compatibility**: Works with npx/standard package managers
- **Configuration**: Minimal or zero-config preferred

**Testing MCP Servers**:

```bash
# Local installation
/plugin install mcp-servers@file:///Users/logansmith/repos/cc-plugins/mcp-servers

# In new session, verify:
# 1. Server starts without errors
# 2. Tools are available to Claude
# 3. Server responds to requests correctly
# 4. Error handling works gracefully
```

**Common Issues**:

- **Server Won't Start**: Check command availability (`npx`, `python`, etc.)
- **Environment Variables**: Ensure substitution syntax is correct
- **Permissions**: Verify package manager has install permissions
- **Conflicts**: Check for port conflicts or duplicate server names

### Version Management

**Updating Plugin Version**:

1. Edit `.claude-plugin/plugin.json`:
   ```json
   {
     "version": "1.1.0"
   }
   ```

2. Update `CHANGELOG.md`:
   ```markdown
   ## [1.1.0] - 2025-01-15
   ### Added
   - New MCP server: [server-name]
   ```

3. Follow semantic versioning:
   - **MAJOR**: Breaking changes (remove server, change configuration)
   - **MINOR**: New servers (backward-compatible)
   - **PATCH**: Bug fixes, documentation updates

### MCP Server Categories

**Current Focus Areas**:
- **Documentation**: Context7 (current)
- **CI/CD**: Pipeline monitoring (planned)
- **Observability**: Error tracking, monitoring (planned)
- **Issue Tracking**: Jira, Linear, GitHub (planned)
- **API Testing**: OpenAPI, Postman (planned)

### Best Practices

**Configuration**:
- Use environment variables for secrets/keys
- Provide sensible defaults (zero-config when possible)
- Document optional vs. required configuration
- Test with and without optional config

**Documentation**:
- Keep README.md comprehensive and current
- Include troubleshooting section
- Provide usage examples
- Link to official MCP server docs

**Testing**:
- Test each server independently
- Verify error handling
- Test with missing/invalid configuration
- Ensure graceful degradation

**Maintenance**:
- Monitor MCP server repositories for updates
- Update package versions periodically
- Test after updates
- Document breaking changes

### Integration with Repository

When developing within the cc-plugins repository:

**Repository Structure**:
- Plugin source: `mcp-servers/` (this directory)
- Tests: `../tests/mcp-servers/` (when created)
- Repository docs: `../CLAUDE.md`, `../README.md`

**Development Workflow**:
1. Make changes to plugin files
2. Update documentation
3. Test locally via file:// installation
4. Update version and changelog
5. Commit with conventional commit message

**Testing Installation**:
```bash
# In a test project
/plugin marketplace add file:///Users/logansmith/repos/cc-plugins
/plugin install mcp-servers@medicus-it
```

## Related Documentation

**Plugin Documentation**:
- [README.md](README.md) - User-facing overview
- [CHANGELOG.md](CHANGELOG.md) - Version history

**External Resources**:
- [Model Context Protocol Docs](https://modelcontextprotocol.io/)
- [Context7 GitHub](https://github.com/upstash/context7)
- [Awesome MCP Servers](https://github.com/wong2/awesome-mcp-servers)

**Repository Documentation**:
- [../CLAUDE.md](../CLAUDE.md) - Marketplace development guide
- [../README.md](../README.md) - Marketplace overview

## Support

**Issues**: https://github.com/lsmith090/cc-plugins/issues

**Suggestions**: Submit ideas for additional MCP servers via GitHub Issues

---

**Plugin Philosophy**: Curate high-quality MCP servers that provide immediate value with minimal configuration. Focus on developer productivity and seamless integration.
