# Task Lifecycle Technical Reference

Complete technical documentation of brainworm's task management system architecture and lifecycle.

## System Architecture

### Three-Layer Design

1. **CLI Wrapper Layer** (`scripts/tasks_command.py`)
   - Typer-based command-line interface
   - Type-safe argument parsing
   - Delegates to core scripts via plugin-launcher

2. **Orchestration Layer** (`scripts/create_task.py`, `scripts/switch_task.py`)
   - Business logic for task operations
   - Git operations and state management
   - GitHub integration and validation

3. **State Management Layer** (`utils/daic_state_manager.py`)
   - Atomic state updates with file locking
   - Pre-validation and consistency checks
   - Unified session state maintenance

## Task Creation Workflow

### 11-Step Process

When `./tasks create my-feature` executes:

1. **Project Structure Detection**
   - `SubmoduleManager` reads `.gitmodules`
   - Executes `git submodule status` for paths
   - Builds mapping: `{submodule_name: absolute_path}`

2. **Submodule Selection** (interactive if TTY)
   - Prompts user to select target submodule
   - Skipped in non-interactive contexts (Claude Code)
   - Can be specified via `--submodule=name` flag

3. **Branch Naming Convention**
   - Inspects task name prefix
   - Mappings: `fix-*` → `fix/`, `refactor-*` → `refactor/`, etc.
   - Default: `feature/`

4. **Task Directory Creation**
   - Creates `.brainworm/tasks/<task-name>/`
   - Directory is gitignored (in `.brainworm/.gitignore`)

5. **Template Population**
   - Reads `brainworm/templates/TEMPLATE.md`
   - String replacements:
     - `[prefix]-[descriptive-name]` → task name
     - `feature/[name]|...` → determined branch
     - `[submodule-path]|none` → submodule or "none"
     - `YYYY-MM-DD` → current date
     - `[current-session-id]` → "pending"
     - `[brainworm-correlation-id]` → `{task}_correlation`

6. **GitHub Integration** (if enabled)
   - Repository detection (gh CLI or git remote parsing)
   - Issue number extraction from task name
   - Issue linking or creation
   - Frontmatter updates

7. **Smart Branch Detection**
   - Checks if branch already exists locally
   - Checks if branch exists on remote
   - Avoids conflicts with existing branches

8. **Git Branch Creation**
   - Main repo: `git checkout -b <branch-name>`
   - Submodule: `git checkout -b <branch-name>` in submodule dir

9. **Multi-Service Branch Creation** (monorepo)
   - For each service listed in `--services`
   - Creates matching branch in each submodule
   - Records in `active_submodule_branches` state

10. **DAIC State Update**
    - Updates `unified_session_state.json`
    - Sets current task, branch, services
    - Atomic write with file locking

11. **Confirmation Output**
    - Pretty-printed success message
    - Task file location
    - Branch information
    - Next steps guidance

## Task Switching Workflow

### Atomic State Transition

When `./tasks switch other-task` executes:

1. **Task Validation**
   - Verifies task directory exists
   - Reads task README frontmatter
   - Validates branch field exists

2. **Submodule Task Detection**
   - Checks `submodule` field in frontmatter
   - Determines if switch requires submodule operations

3. **Git Checkout Strategy**

   **For main repo tasks**:
   ```bash
   git checkout <branch-name>
   ```

   **For submodule tasks**:
   ```bash
   cd <submodule-path>
   git checkout <branch-name>
   cd ../..
   ```

   **For multi-service tasks**:
   - Reads `active_submodule_branches` from state
   - Checks out correct branch in each service submodule
   - Handles missing branches gracefully

4. **State Update**
   - Atomically updates unified_session_state.json
   - Sets new current task and branch
   - Preserves multi-service branch mappings

5. **Verification**
   - Confirms git checkout succeeded
   - Validates state file was updated
   - Returns success/failure status

## Task Completion Workflow

### Two-Phase Process

**Phase 1: State Cleanup** (`./tasks clear`)
- Removes current task from unified state
- Preserves task directory and history
- Quick operation (no protocol)

**Phase 2: Protocol Execution** (optional, manual)
- Logging agent consolidates work logs
- Service-documentation agent updates docs
- Git cleanup (merge, delete branches)
- Archive task directory if desired

## State Management

### Unified Session State

Location: `.brainworm/state/unified_session_state.json`

**Structure**:
```typescript
interface UnifiedSessionState {
  daic_mode: "discussion" | "implementation";
  current_task: string | null;
  current_branch: string | null;
  task_services: string[];
  session_id: string;
  correlation_id: string;
  plugin_root: string;
  developer: {
    name: string;
    email: string;
  };
  active_submodule_branches?: {
    [submodule: string]: string;
  };
}
```

### State Update Guarantees

The `DAICStateManager` provides:

1. **Atomicity**: File locking ensures single writer
2. **Validation**: Pre-update structural validation
3. **Consistency**: Semantic validation (valid modes, formats)
4. **Durability**: Atomic write-and-rename pattern

**Update pattern**:
```python
manager = DAICStateManager(project_root)
manager.update(
    current_task="my-feature",
    current_branch="feature/my-feature"
)
```

## Task Directory Structure

```
.brainworm/tasks/my-feature/
├── README.md              # Task definition and work log
└── [session-artifacts]    # Optional: screenshots, data files
```

### Task README Frontmatter

```yaml
---
task: my-feature
branch: feature/my-feature
submodule: none
status: pending|in-progress|completed
created: 2025-10-29
modules: [service-name, ...]
session_id: uuid-format
correlation_id: task_correlation
github_issue: 42
github_repo: owner/repo
---
```

### Task README Sections

1. **Problem/Goal**: What we're solving/building
2. **Success Criteria**: Measurable outcomes (checklist)
3. **Context Manifest**: Added by context-gathering agent
4. **Context Files**: File references for agent
5. **User Notes**: Developer-added notes
6. **Work Log**: Chronological progress tracking

## CLI Commands Reference

### create

```bash
./tasks create <task-name> [options]

Options:
  --submodule TEXT       Target submodule name
  --services TEXT        Comma-separated service list
  --link-issue INTEGER   Link to existing GitHub issue
  --create-issue         Create new GitHub issue
  --no-interactive       Skip interactive prompts
```

### switch

```bash
./tasks switch <task-name>

Atomically switches to existing task:
- Checks out git branch
- Updates DAIC state
- Handles multi-service coordination
```

### status

```bash
./tasks status

Displays:
- Current task name
- Git branch
- Services involved
- Session/correlation IDs
```

### list

```bash
./tasks list

Shows all tasks with:
- Status (pending/in-progress/completed)
- Task name
- Branch
- Created date
```

### clear

```bash
./tasks clear

Clears current task from state.
Does NOT run task completion protocol.
```

### set

```bash
./tasks set --task TEXT --branch TEXT

Manual state update (debugging only).
Bypasses validation and git operations.
```

### session

```bash
./tasks session set --session-id TEXT

Updates session correlation ID.
Used for session continuity tracking.
```

### summarize

```bash
./tasks summarize

Generates GitHub issue comment from:
- Session memory files
- Task work log
- Key discoveries and decisions

Posts to linked GitHub issue.
```

## Multi-Service Projects

### Detection

Projects with git submodules are treated as multi-service:

```bash
# .gitmodules
[submodule "frontend"]
    path = services/frontend
    url = git@github.com:org/frontend.git
```

### Task Scoping

Tasks can be scoped to:
- **Main repository**: `submodule: none`
- **Specific service**: `submodule: frontend`
- **Multiple services**: `modules: [frontend, backend]`

### Branch Coordination

When switching multi-service tasks:
- Each service checks out its designated branch
- Branch mapping stored in `active_submodule_branches`
- Missing branches handled gracefully (warning, not error)

## Integration with DAIC Workflow

### Mode Awareness

Task operations respect DAIC modes:

**Discussion Mode**:
- Can create tasks (planning activity)
- Can query status and list tasks
- Can switch tasks (organizational activity)
- Cannot run implementation tools

**Implementation Mode**:
- All task operations available
- Can invoke agents (context-gathering, etc.)
- Can execute full workflows

### Mode Checking

```bash
./daic status
```

Returns current mode, task, and context usage.

## Context-Gathering Integration

After task creation, invoke the context-gathering agent:

```bash
# Via Claude Code Task tool
subagent_type: brainworm:context-gathering
prompt: "Create context manifest for task X.
         Task file: /absolute/path/.brainworm/tasks/X/README.md

         Focus on understanding: [relevant systems]"
```

**What the agent does**:
1. Reads entire task README
2. Analyzes codebase for relevant context
3. Traces through architectural layers
4. Documents how current systems work
5. Adds comprehensive Context Manifest section
6. Provides integration points for implementation

## Error Handling

### Common Errors

**"Task already exists"**:
- Task directory already present
- Solution: Use different name or remove old task

**"Branch already exists"**:
- Git branch conflict
- Solution: Delete old branch or use different name

**"GitHub CLI not found"**:
- `gh` command not available
- Solution: Install gh CLI or disable GitHub integration

**"Issue not found"**:
- Invalid issue number
- Solution: Verify issue exists, check repo access

**"Cannot checkout branch"**:
- Uncommitted changes blocking checkout
- Solution: Commit or stash changes first

### Debug Logging

All task operations are logged to:
- `.brainworm/logs/debug.jsonl` (if enabled in config)
- Includes timestamps, operation details, errors

## Performance Considerations

### Optimization Strategies

1. **Lazy Loading**: Submodule detection only when needed
2. **Caching**: Git operations cached during single command
3. **Atomic Operations**: State updates minimize lock time
4. **Parallel Operations**: Multi-service branches created concurrently (future)

### Typical Timings

- Task creation: 100-500ms
- Task switching: 50-200ms (depends on git checkout)
- Status query: 10-50ms (reads JSON)
- List tasks: 50-100ms (scans directory)

## File Locations

**Scripts**:
- `brainworm/scripts/tasks_command.py` - CLI entry point
- `brainworm/scripts/create_task.py` - Task creation logic
- `brainworm/scripts/switch_task.py` - Task switching logic
- `brainworm/scripts/list_tasks.py` - List and summarize

**Utilities**:
- `brainworm/utils/daic_state_manager.py` - State management
- `brainworm/utils/github_manager.py` - GitHub integration
- `brainworm/utils/submodule_manager.py` - Submodule detection
- `brainworm/utils/correlation_manager.py` - Session correlation

**Templates**:
- `brainworm/templates/TEMPLATE.md` - Task README template

**State**:
- `.brainworm/state/unified_session_state.json` - Current state
- `.brainworm/tasks/<task-name>/README.md` - Task definitions

## Testing

Task management is tested at multiple levels:

**Unit tests**: `tests/brainworm/unit/`
- State manager operations
- Template processing
- Frontmatter parsing

**Integration tests**: `tests/brainworm/integration/`
- Task creation with git operations
- GitHub integration
- Multi-service coordination

**E2E tests**: `tests/brainworm/e2e/`
- Complete task lifecycle
- Real git repository operations
- Agent invocations

Run tests:
```bash
uv run pytest tests/brainworm/ -v
```

## Best Practices for Skill Implementation

1. **Always check current state first** - Read unified_session_state.json
2. **Use wrapper commands** - Don't bypass ./tasks CLI
3. **Handle errors gracefully** - Expect git and GitHub failures
4. **Invoke context-gathering** - Essential for new tasks
5. **Respect DAIC modes** - Check mode before operations
6. **Use absolute paths** - When invoking agents
7. **Confirm success** - Verify operations completed
8. **Explain next steps** - Guide user after operations
