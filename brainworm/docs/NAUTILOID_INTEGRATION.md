# Nautiloid Integration Guide

## Overview

Brainworm and Nautiloid work together as complementary systems with clear separation of responsibilities:

- **Brainworm** - DAIC workflow enforcement and local session analytics
- **Nautiloid** - Multi-project analytics aggregation and intelligence

## Architecture

```
┌─────────────────────────────────┐
│   Brainworm (Plugin)            │
│   - DAIC workflow enforcement   │
│   - Tool blocking               │
│   - Local session analytics     │
│   - Task management             │
│                                 │
│   Stores:                       │
│   .claude/analytics/hooks.db    │ ← Nautiloid reads (read-only)
│   .serena/memories/*.md         │ ← Nautiloid reads (read-only)
│   .claude/logs/*.jsonl          │ ← Nautiloid reads (read-only)
└─────────────────────────────────┘
                ↓ (pull-based harvesting)
┌─────────────────────────────────┐
│   Nautiloid (Container)         │
│   - Multi-project aggregation   │
│   - Cross-project correlation   │
│   - Pattern recognition         │
│   - Grafana dashboards          │
│                                 │
│   Stores:                       │
│   /var/lib/nautiloid/analytics.db
└─────────────────────────────────┘
```

## What Brainworm Provides

Brainworm captures local development intelligence:

### 1. Hook Events Database
**Location:** `.claude/analytics/hooks.db`

Contains:
- Tool usage events
- DAIC mode transitions
- Session and correlation IDs
- Success/failure patterns
- Timing data

### 2. Session Notes
**Location:** `.serena/memories/*.md`

Contains:
- Session summaries
- Technical decisions
- Git statistics
- Performance metrics
- Architectural insights

### 3. Event Logs
**Location:** `.claude/logs/*.jsonl`

Contains:
- Real-time event stream
- Hook execution data
- Additional context

## What Nautiloid Does

Nautiloid operates independently to aggregate intelligence:

### Pull-Based Harvesting
- Reads brainworm databases (read-only)
- Scheduled every 15 minutes (configurable)
- No modifications to brainworm data
- No brainworm configuration changes needed

### Multi-Project Correlation
- Bridges session IDs with correlation IDs
- 95%+ accuracy for session tracking
- Cross-project pattern recognition
- Success pattern identification

### Intelligence Dashboards
- Live Grafana visualization
- Session activity monitoring
- Workflow pattern analysis
- Project health metrics

## Integration Setup

### Prerequisites

1. **Brainworm installed and working**
   ```bash
   /plugin install brainworm@brainworm-marketplace
   ```

2. **Nautiloid repository cloned**
   ```bash
   git clone https://github.com/lsmith090/nautiloid.git ~/repos/nautiloid
   ```

### Configuration

**Step 1: Configure Nautiloid Sources**

Edit `~/.config/nautiloid/config.toml`:

```toml
[[sources]]
name = "my-project"
type = "brainworm"
path = "/path/to/your/project"  # Absolute path
enabled = true

[sources.patterns]
jsonl = ".claude/logs/**/*.jsonl"
sessions = ".serena/memories/**/*.md"

[sources.filters]
exclude_patterns = ["**/test/**", "**/node_modules/**"]
min_file_age_minutes = 5
```

**Step 2: Update Docker Compose**

Edit `nautiloid/docker/docker-compose.yml`:

```yaml
services:
  nautiloid:
    volumes:
      # Mount your brainworm project (read-only)
      - /path/to/your/project:/mnt/projects/my-project:ro
```

**Step 3: Start Nautiloid**

```bash
cd ~/repos/nautiloid/docker
docker-compose up -d
```

### Verification

**Check brainworm is capturing data:**
```bash
sqlite3 .claude/analytics/hooks.db "SELECT COUNT(*) FROM hook_events"
```

**Check nautiloid is harvesting:**
```bash
docker exec nautiloid nautiloid harvest --verbose
```

**View analytics:**
```bash
docker exec nautiloid nautiloid analytics --summary
```

**Access Grafana:**
- Open http://localhost:3000
- Login: admin / admin
- View dashboards

## Data Flow

### What Brainworm Captures

**Automatically on every Claude Code interaction:**
- Tool invocations (Edit, Write, Bash, etc.)
- Hook executions (pre_tool_use, post_tool_use, etc.)
- DAIC mode changes
- Session start/end
- Correlation tracking

**Stored locally in:**
- `.claude/analytics/hooks.db` - SQLite database
- `.claude/logs/*.jsonl` - JSONL event logs
- `.serena/memories/*.md` - Session notes (via session-docs agent)

### What Nautiloid Harvests

**Every 15 minutes (default):**
- New events from `hooks.db`
- New JSONL logs
- Updated session notes

**Aggregates into:**
- Central database (`/var/lib/nautiloid/analytics.db`)
- Correlation mappings (session ↔ correlation IDs)
- Pattern libraries

### What You See

**In Grafana dashboards:**
- Live session activity
- Success rate trends
- Workflow patterns
- Cross-project insights
- Performance metrics

## Privacy & Security

**All data stays local:**
- Brainworm: On your machine in `.claude/`
- Nautiloid: In Docker volumes on your machine
- No cloud services
- No external network calls

**Read-only access:**
- Nautiloid mounts projects as read-only (`:ro`)
- Cannot modify your code or brainworm data
- Safe to run continuously

**Data control:**
- You control what projects are harvested
- Easy to disable sources in config
- Complete data ownership

## Troubleshooting

### No Data in Nautiloid

**Check brainworm is capturing:**
```bash
ls -la .claude/analytics/hooks.db
sqlite3 .claude/analytics/hooks.db "SELECT COUNT(*) FROM hook_events"
```

**Check nautiloid can access:**
```bash
docker exec nautiloid ls -la /mnt/projects/my-project/.claude/analytics/hooks.db
```

**Run manual harvest:**
```bash
docker exec nautiloid nautiloid harvest --source my-project --verbose
```

### Grafana Not Showing Data

**Check database exists:**
```bash
docker exec nautiloid ls -la /var/lib/nautiloid/analytics.db
```

**Query database directly:**
```bash
docker exec nautiloid sqlite3 /var/lib/nautiloid/analytics.db \
  "SELECT COUNT(*) FROM central_hook_events"
```

**Restart Grafana:**
```bash
docker-compose restart grafana
```

### Correlation Issues

**Check session notes exist:**
```bash
ls -la .serena/memories/
```

**View correlation mappings:**
```bash
docker exec nautiloid sqlite3 /var/lib/nautiloid/analytics.db \
  "SELECT * FROM session_id_bridge LIMIT 10"
```

## Best Practices

### For Optimal Analytics

1. **Use session-docs agent regularly**
   - Creates rich session notes
   - Improves correlation accuracy
   - Captures architectural decisions

2. **Let brainworm run naturally**
   - Don't disable analytics
   - Let hooks capture naturally
   - Trust the background process

3. **Check nautiloid periodically**
   - Review Grafana dashboards
   - Identify workflow patterns
   - Learn from successful sessions

### For Performance

1. **Exclude large directories**
   ```toml
   exclude_patterns = [
       "**/node_modules/**",
       "**/dist/**",
       "**/.git/**"
   ]
   ```

2. **Adjust harvest frequency if needed**
   ```toml
   [harvesting]
   schedule = "*/30 * * * *"  # Every 30 minutes
   ```

3. **Monitor database size**
   ```bash
   docker exec nautiloid du -h /var/lib/nautiloid/analytics.db
   ```

## Advanced Usage

### Custom Queries

Access nautiloid database directly:

```bash
docker exec -it nautiloid sqlite3 /var/lib/nautiloid/analytics.db
```

Example queries:

```sql
-- Recent sessions by project
SELECT project_source, COUNT(DISTINCT session_id)
FROM central_hook_events
WHERE timestamp > datetime('now', '-7 days')
GROUP BY project_source;

-- Success rates by hook
SELECT hook_name,
       AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) * 100 as success_rate
FROM central_hook_events
GROUP BY hook_name;

-- Tool usage patterns
SELECT event_type, COUNT(*) as usage_count
FROM central_hook_events
GROUP BY event_type
ORDER BY usage_count DESC;
```

### Custom Grafana Dashboards

1. Login to Grafana (http://localhost:3000)
2. Create new dashboard
3. Add panel
4. Select "Nautiloid Analytics" datasource
5. Write SQL queries
6. Save dashboard

## Further Reading

- [Nautiloid README](https://github.com/lsmith090/nautiloid/blob/main/README.md)
- [Nautiloid Setup Guide](https://github.com/lsmith090/nautiloid/blob/main/docs/SETUP.md)
- [Nautiloid Architecture](https://github.com/lsmith090/nautiloid/blob/main/docs/ARCHITECTURE.md)
- [Grafana Dashboard Guide](https://github.com/lsmith090/nautiloid/blob/main/visualization/grafana/README.md)

---

**Summary:** Brainworm and Nautiloid work together seamlessly with zero configuration changes to brainworm. Install brainworm for workflow enforcement, add nautiloid for multi-project intelligence. Both systems remain completely independent.
