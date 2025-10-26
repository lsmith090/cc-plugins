# MCP Servers Plugin

Curated collection of Model Context Protocol (MCP) servers for enhanced Claude Code capabilities.

## Overview

This plugin provides a carefully selected set of MCP servers that extend Claude Code with powerful integrations and capabilities. MCP servers automatically start when the plugin is enabled and provide additional tools and context to Claude.

## Included MCP Servers

### Context7

**Purpose**: Up-to-date code documentation for LLMs and AI code editors

**What it does**:
- Fetches version-specific documentation and code examples directly from official sources
- Eliminates outdated or hallucinated API usage
- Provides accurate, current code generation based on real documentation
- Supports multiple programming languages and frameworks

**Provider**: [Upstash Context7](https://context7.com/)
**GitHub**: [upstash/context7](https://github.com/upstash/context7)
**Package**: `@upstash/context7-mcp`

**Configuration**:
- Optional: Set `CONTEXT7_API_KEY` environment variable for higher rate limits and private repository access
- Without API key: Works with default rate limits for public documentation

### Playwright

**Purpose**: Browser automation and testing capabilities for Claude Code

**What it does**:
- Automate browser interactions (navigate, click, type, drag)
- Capture screenshots and generate PDFs
- Execute JavaScript in browser context
- Manage tabs and browser sessions
- Intercept network requests
- Retrieve console messages and debugging info

**Provider**: [Microsoft Playwright](https://playwright.dev/)
**GitHub**: [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp)
**Package**: `@playwright/mcp`

**Configuration**:
- Zero-config: Works out of the box in headless mode
- Optional: Advanced configuration available via config file (see [Playwright MCP docs](https://github.com/microsoft/playwright-mcp))

## Installation

### From Marketplace

```bash
/plugin marketplace add https://github.com/lsmith090/cc-plugins
/plugin install mcp-servers@medicus-it
```

### From Local Path (Development)

```bash
/plugin install mcp-servers@file:///absolute/path/to/cc-plugins/mcp-servers
```

## Configuration

### Optional: Context7 API Key

To get higher rate limits and access to private repositories:

1. Visit [context7.com](https://context7.com/) and sign up
2. Get your API key from the dashboard
3. Set environment variable:

```bash
# Add to your shell profile (~/.zshrc, ~/.bashrc, etc.)
export CONTEXT7_API_KEY="your-api-key-here"
```

4. Restart Claude Code or reload your shell

### Verify Installation

After installing the plugin, MCP servers will start automatically. You can verify by:

```bash
# Check that Claude Code recognizes the MCP servers
# (MCP servers are loaded on session start)
```

## Usage

Once installed, the MCP servers are available automatically in all Claude Code sessions.

### Using Context7

Context7 provides tools to Claude for fetching up-to-date documentation. Claude will automatically use these tools when needed, for example:

- "Show me the latest FastAPI examples"
- "What are the current React hooks best practices?"
- "Get me documentation for the pandas DataFrame API"

No manual invocation required - Claude knows when to use Context7 for documentation lookups.

### Using Playwright

Playwright provides browser automation tools to Claude. Claude will automatically use these tools when needed, for example:

- "Navigate to example.com and take a screenshot"
- "Click the login button and fill out the form"
- "Test this website's accessibility and user flow"
- "Extract data from this webpage"

Playwright runs in headless mode by default, making it ideal for automated testing, web scraping, and browser-based workflows.

## Benefits

### For Individual Developers

- **Accurate Code**: Always use current APIs and best practices
- **Less Context Switching**: Documentation appears in your conversation
- **Faster Development**: No tab-switching to documentation sites
- **Version-Specific**: Get docs for the exact version you're using

### For Teams

- **Consistency**: Everyone uses current, official documentation
- **Onboarding**: New developers get accurate examples immediately
- **Quality**: Reduces bugs from outdated or incorrect API usage

## Troubleshooting

### MCP Server Not Starting

1. Check that Node.js and npm are installed:
   ```bash
   node --version
   npm --version
   ```

2. Verify plugin installation:
   ```bash
   /plugin list
   ```

3. Check for errors in Claude Code output during session start

### Context7 Rate Limits

If you hit rate limits:
- Get a free API key from [context7.com](https://context7.com/)
- Set `CONTEXT7_API_KEY` environment variable
- Restart Claude Code

### Permission Issues

Ensure `npx` has permission to install packages:
```bash
npm config get prefix
# Should show a directory you have write access to
```

## Future MCP Servers

This plugin will be expanded with additional curated MCP servers:

- **Observability** (Sentry, Datadog integration)
- **CI/CD** (GitHub Actions, GitLab CI monitoring)
- **Issue Tracking** (Jira, Linear, GitHub Issues)
- **API Testing** (OpenAPI, Postman collections)

Suggestions welcome via [GitHub Issues](https://github.com/lsmith090/cc-plugins/issues)!

## Contributing

### Adding a New MCP Server

1. Edit `.mcp.json` to add server configuration
2. Update this README with server details
3. Test thoroughly in a real project
4. Submit PR with changelog entry

### Testing Changes

```bash
# Install locally
/plugin install mcp-servers@file:///path/to/cc-plugins/mcp-servers

# Start new session to load MCP servers
# Verify server functionality
```

## Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [Context7 GitHub](https://github.com/upstash/context7)
- [MCP Community Servers](https://github.com/wong2/awesome-mcp-servers)

## License

MIT License - see [LICENSE](LICENSE) file

## Support

- Issues: [GitHub Issues](https://github.com/lsmith090/cc-plugins/issues)
- Discussions: [GitHub Discussions](https://github.com/lsmith090/cc-plugins/discussions)

---

**Plugin Philosophy**: Provide carefully curated, high-quality MCP servers that enhance Claude Code with minimal configuration and maximum value.
