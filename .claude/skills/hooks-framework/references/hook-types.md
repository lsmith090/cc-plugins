# Hook Types and Input Schemas

Complete reference for all Claude Code hook types, their input schemas, output schemas, and common use cases.

## SessionStart Hook

**When:** New Claude Code session begins
**Purpose:** Initialize state, setup infrastructure, auto-configure
**Input Schema:** `SessionStartInput`

```python
from utils.hook_types import SessionStartInput

# Fields available:
- session_id: str         # Unique session identifier
- transcript_path: str    # Path to session transcript
- cwd: str               # Current working directory
- hook_event_name: str   # Always "SessionStart"
```

**Common Use Cases:**
- Auto-setup `.brainworm/` directory structure
- Initialize databases and state files
- Populate session_id in unified state
- Generate wrapper scripts
- Configure Claude Code settings

**Example Pattern:**
```python
def session_start_logic(framework, typed_input):
    project_root = framework.project_root
    session_id = typed_input.session_id

    # Auto-setup infrastructure
    setup_directories(project_root)

    # Populate session correlation
    state_mgr = DAICStateManager(project_root)
    state_mgr.update_session_correlation(session_id, correlation_id)
```

## PreToolUse Hook

**When:** Before Claude Code executes a tool (Read, Write, Edit, Bash, etc.)
**Purpose:** Enforce policies, validate inputs, block/allow tools
**Input Schema:** `PreToolUseInput`

```python
from utils.hook_types import PreToolUseInput, parse_tool_input

# Fields available:
- session_id: str
- tool_name: str              # "Read", "Write", "Edit", "Bash", etc.
- tool_input: ToolInputVariant # Typed tool parameters
- cwd: str
- hook_event_name: str        # Always "PreToolUse"
```

**Output Schema:** `PreToolUseDecisionOutput`

```python
from utils.hook_types import PreToolUseDecisionOutput

# To allow tool:
return PreToolUseDecisionOutput.approve(reason="Tool allowed")

# To block tool:
return PreToolUseDecisionOutput.block(
    reason="[DAIC: Tool Blocked] You're in discussion mode",
    validation_issues=["Write tool blocked in discussion mode"],
    suppress_output=False
)
```

**Common Use Cases:**
- DAIC workflow enforcement (block Write/Edit in discussion mode)
- Security validation (prevent dangerous operations)
- Branch enforcement (ensure correct git branch)
- Command validation (block destructive bash commands)

**Example Pattern:**
```python
def pre_tool_use_logic(framework, typed_input):
    tool_name = typed_input.tool_name

    # Check DAIC mode
    state_mgr = DAICStateManager(framework.project_root)
    daic_mode = state_mgr.get_daic_mode()

    # Block blocked tools in discussion mode
    if daic_mode == "discussion" and tool_name in ["Write", "Edit"]:
        return PreToolUseDecisionOutput.block(
            reason=f"[DAIC: Tool Blocked] {tool_name} not allowed in discussion mode",
            validation_issues=[f"{tool_name} requires implementation mode"]
        )

    return PreToolUseDecisionOutput.approve()
```

## PostToolUse Hook

**When:** After Claude Code completes a tool execution
**Purpose:** Track tool usage, analyze results, update analytics
**Input Schema:** `PostToolUseInput`

```python
from utils.hook_types import PostToolUseInput

# Fields available:
- session_id: str
- tool_name: str
- tool_input: ToolInputVariant
- tool_response: ToolResponse  # Tool execution results
- cwd: str
```

**Common Use Cases:**
- Analytics collection (track which tools are used)
- Error detection (identify failed operations)
- Pattern learning (understand development flows)
- Performance tracking (measure execution times)

## UserPromptSubmit Hook

**When:** User submits a prompt to Claude
**Purpose:** Context injection, intent analysis, trigger detection
**Input Schema:** `UserPromptSubmitInput`

```python
from utils.hook_types import UserPromptSubmitInput

# Fields available:
- session_id: str
- prompt: str           # User's input text
- cwd: str
```

**Output Schema:** `UserPromptContextResponse`

```python
from utils.hook_types import UserPromptContextResponse

# Inject context into prompt:
return UserPromptContextResponse.create_context(
    context="[[ ultrathink ]]",
    debug_info={"api_mode": True}
)
```

**Common Use Cases:**
- Trigger phrase detection ("go ahead" → switch to implementation mode)
- API mode management (auto-enable ultrathink)
- Context injection (add system reminders)
- Intent analysis (understand user goals)

## SessionEnd Hook

**When:** Session terminates
**Purpose:** Cleanup, finalization, logging
**Input Schema:** `SessionEndInput`

```python
from utils.hook_types import SessionEndInput

# Fields available:
- session_id: str
- cwd: str
- hook_event_name: str   # Always "SessionEnd"
```

**Common Use Cases:**
- Write session summaries
- Close database connections
- Archive logs
- Generate reports

## Stop Hook

**When:** User stops Claude's response
**Purpose:** Track interruptions, cleanup partial work
**Input Schema:** `StopInput`

```python
from utils.hook_types import StopInput

# Fields available:
- session_id: str
- cwd: str
- hook_event_name: str   # Always "Stop"
```

**Common Use Cases:**
- Log interruption events
- Clean up partial operations
- Track user satisfaction signals

## Notification Hook

**When:** Claude sends a notification
**Purpose:** Track notifications, log events
**Input Schema:** `NotificationInput`

```python
from utils.hook_types import NotificationInput

# Fields available:
- session_id: str
- notification_text: str
- cwd: str
- hook_event_name: str   # Always "Notification"
```

**Common Use Cases:**
- Log notification events
- Track notification patterns
- Analyze user interactions
