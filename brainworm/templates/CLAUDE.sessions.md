# CLAUDE.sessions.md

This file provides collaborative guidance and philosophy when using the Brainworm enhanced Claude Code system.

## Collaboration Philosophy

**Core Principles**:
- **Investigate patterns** - Look for existing examples, understand established conventions, don't reinvent what already exists
- **Confirm approach** - Explain your reasoning, show what you found in the codebase, get consensus before proceeding  
- **State your case if you disagree** - Present multiple viewpoints when architectural decisions have trade-offs
- When working on highly standardized tasks: Provide SOTA (State of the Art) best practices
- When working on novel approaches: Generate "opinion" through rigorous deductive reasoning from available evidence

## Task Management

### Best Practices
- One task at a time (check unified state with API)
- Update work logs as you progress  
- Mark todos as completed immediately after finishing

### Quick State Checks
```bash
./tasks status                    # Shows current task, branch, services
./tasks list                      # All tasks with status
./daic status                     # DAIC workflow mode
```

### Task Commands

**Creating tasks:**
```bash
./tasks create [task-name]                      # Create new task
./tasks create [task-name] --services=svc1,svc2 # With services
```

**Switching tasks:**
```bash
./tasks switch [task-name]        # Atomic task switching (git + state)
```

**Managing state:**
```bash
./tasks set --task=X --branch=Y   # Manual state update (rare)
./tasks clear                     # Clear current task
```

### State Management

**CRITICAL: Never edit state files directly**
- All state is managed through unified state API
- Use wrapper commands for all state operations
- State files are consolidated into `unified_session_state.json`

**DAIC Mode Commands:**
```bash
./daic discussion       # Switch to discussion mode
./daic implementation   # Switch to implementation mode
./daic status           # Check current mode
./daic toggle           # Toggle between modes
```

## Using Specialized Agents

You have specialized subagents for heavy lifting. Each operates in its own context window and returns structured results.

### Prompting Agents
Agent descriptions will contain instructions for invocation and prompting. In general, it is safer to issue lightweight prompts. You should only expand/explain in your Task call prompt insofar as your instructions for the agent are special/requested by the user, divergent from the normal agent use case, or mandated by the agent's description. Otherwise, assume that the agent will have all the context and instruction they need.

Specifically, avoid long prompts when invoking the logging or context-refinement agents. These agents receive the full history of the session and can infer all context from it.

### Available Agents

1. **context-gathering** - Creates comprehensive context manifests for tasks
   - Use when: Creating new task OR task lacks context manifest
   - ALWAYS provide the task file path so the agent can update it directly

2. **code-review** - Reviews code for quality and security with brainworm analytics
   - Use when: After writing significant code, before commits
   - Provide files and line ranges where code was implemented
   - Integrates with success pattern recognition

3. **context-refinement** - Updates context with discoveries from work session
   - Use when: End of context window (if task continuing)
   - Incorporates brainworm analytics insights

4. **logging** - Maintains clean chronological logs with analytics correlation
   - Use when: End of context window or task completion
   - Integrates with session correlation tracking

5. **service-documentation** - Updates service CLAUDE.md files
   - Use when: After service changes
   - Understands brainworm project structures

### Agent Principles
- **Delegate heavy work** - Let agents handle file-heavy operations
- **Be specific** - Give agents clear context and goals
- **One agent, one job** - Don't combine responsibilities

## DAIC Workflow Integration

### Understanding DAIC Modes
- **Discussion Mode**: Tools blocked, focus on planning and alignment (purple statusline)
- **Implementation Mode**: Tools enabled, execute agreed changes (green statusline)
- **Trigger Phrases**: "make it so", "ship it", "let's do it", "go ahead", "execute", "implement it"

### Working with DAIC
- Start sessions in discussion mode by default
- Use statusline to monitor current mode and context usage
- Respect the workflow - don't fight the tool blocking
- Use trigger phrases naturally when ready to implement

### DAIC Commands
```bash
./daic status          # Check current mode and task
./daic discussion      # Switch to discussion mode
./daic implementation  # Switch to implementation mode
./daic toggle          # Toggle between modes
```

## Code Philosophy

### Locality of Behavior
- Keep related code close together rather than over-abstracting
- Code that relates to a process should be near that process
- Functions that serve as interfaces to data structures should live with those structures

### Solve Today's Problems
- Deal with local problems that exist today
- Avoid excessive abstraction for hypothetical future problems

### Minimal Abstraction
- Prefer simple function calls over complex inheritance hierarchies
- Just calling a function is cleaner than complex inheritance scenarios

### Readability > Cleverness
- Code should be obvious and easy to follow
- Same structure in every file reduces cognitive load

## Protocol Management

### CRITICAL: Protocol Recognition Principle

**When the user mentions protocols:**

1. **EXPLICIT requests → Read protocol first, then execute**
   - Clear commands like "let's compact", "complete the task", "create a new task"
   - Read the relevant protocol file immediately and proceed

2. **VAGUE indications → Confirm first, read only if confirmed**
   - Ambiguous statements like "I think we're done", "context seems full"
   - Ask if they want to run the protocol BEFORE reading the file
   - Only read the protocol file after they confirm

**Never attempt to run protocols from memory. Always read the protocol file before executing.**

### Protocol Files and Recognition

These protocols guide specific workflows:

1. **.brainworm/protocols/task-creation.md** - Creating new tasks
   - **Wrapper command**: `./tasks create [task-name]`
   - EXPLICIT: "create a new task", "let's make a task for X"
   - VAGUE: "we should track this", "might need a task for that"
   - Wrapper handles: directory creation, template, branch, DAIC state, analytics

2. **.brainworm/protocols/task-startup.md** - Beginning work on existing tasks
   - **Wrapper command**: `./tasks switch [task-name]`
   - EXPLICIT: "switch to task X", "let's work on task Y", "start working on Z"
   - VAGUE: "maybe we should look at the other thing"
   - Wrapper handles: git checkout, state update, context verification

3. **.brainworm/protocols/task-completion.md** - Completing and closing tasks
   - **Wrapper commands**: `./tasks clear`, `./daic discussion`
   - EXPLICIT: "complete the task", "finish this task", "mark it done"
   - VAGUE: "I think we're done", "this might be finished"
   - Wrappers handle: state cleanup, mode reset

4. **.brainworm/protocols/context-compaction.md** - Managing context window limits
   - **Wrapper commands**: `./daic status`, `./tasks switch` (if switching)
   - EXPLICIT: "let's compact", "run context compaction", "compact and restart"
   - VAGUE: "context is getting full", "we're using a lot of tokens"
   - Wrappers preserve: state, analytics, session correlation

### Behavioral Examples

**Explicit → Read and execute:**
- User: "Let's complete this task"
- You: [Read task-completion.md first] → "I'll complete the task now. Running the logging agent..."

**Vague → Confirm before reading:**
- User: "I think we might be done here"
- You: "Would you like me to run the task completion protocol?"
- User: "Yes"
- You: [NOW read task-completion.md] → "I'll complete the task now..."

## Brainworm Analytics Integration

### Session Correlation
- All actions are correlated with session_id and correlation_id
- Success patterns are learned and applied automatically
- Performance data informs development effectiveness improvement

### Intelligent Recommendations  
- Use analytics insights to suggest optimal approaches
- Apply learned success patterns from similar tasks
- Leverage real-time performance data for decisions

### Statusline Awareness
- Monitor context usage with visual progress bar
- Track DAIC mode, current task, and git activity
- Use session analytics for workflow insights

### Success Pattern Application
```
Based on brainworm analytics, successful [task-type] tasks typically:
- Spend 30% of time in discussion mode for planning
- Use context-gathering agent early for comprehensive context
- Complete implementation in focused sessions
- Apply code-review agent before final completion
```

## Enhanced Task Lifecycle

### 1. Task Creation
**Use the wrapper:**
```bash
./tasks create [task-name]                      # Basic creation
./tasks create [task-name] --services=svc1,svc2 # With services
```

**Wrapper automatically handles:**
- Directory creation in `.brainworm/tasks/`
- Template population with metadata
- Git branch creation (feature/, fix/, etc.)
- DAIC state initialization
- Analytics correlation setup

**Then:**
- Edit task file for specific requirements
- Invoke context-gathering agent for comprehensive context

### 2. Task Startup
**Use the wrapper:**
```bash
./tasks list                  # Find available tasks
./tasks switch [task-name]    # Atomic task switching
```

**Wrapper automatically handles:**
- Git checkout to task branch
- DAIC state update
- Context verification warnings

**Then:**
- Read task file for context
- Verify DAIC mode with `./daic status`
- Begin work in discussion mode

### 3. Task Execution
- Follow DAIC workflow with intelligent timing
- Apply learned success patterns from analytics
- Use specialized agents for complex operations
- Update work logs as progress is made

### 4. Task Completion
**Follow protocol with wrappers:**
- Run logging agent for work log cleanup
- Run service-documentation agent for updates
- Clean up git branches manually
- Use wrappers for state cleanup:
  ```bash
  ./tasks clear         # Clear current task
  ./daic discussion     # Reset to discussion mode
  ```

### 5. Context Management
**Use wrappers for state operations:**
```bash
./daic status                     # Check mode before compaction
./tasks status                    # Verify task state
./tasks switch [task-name]        # Switch tasks if needed
./daic discussion                 # Set mode for resumption
```

**State persists automatically across compaction**

## Quality Integration Features

### Analytics-Driven Development
- Success pattern recognition guides approach selection
- Real-time performance monitoring informs decisions
- Historical data improves estimation accuracy

### Workflow Optimization  
- DAIC timing recommendations based on task complexity
- Intelligent agent selection for optimal outcomes  
- Context usage optimization through predictive modeling

### Continuous Learning
- Every session contributes to organizational knowledge
- Failed approaches are systematically avoided
- Successful patterns are automatically replicated

## Remember

Effective brainworm-enhanced development:
- Respects DAIC workflow for better code quality
- Leverages analytics for continuous improvement  
- Uses specialized agents for complex operations
- Follows protocols for consistent outcomes
- Builds organizational knowledge through every interaction

The brainworm system learns from every session to make future development more effective and successful.