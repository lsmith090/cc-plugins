# Event Test Fixtures

Test fixtures for brainworm event validation testing.

## Available Fixtures

### basic_session.json
**Description**: Basic Claude Code session with Read tool execution

**Scenario**:
1. SessionStart
2. PreToolUse (Read)
3. PostToolUse (Read)
4. SessionEnd

**Use cases**:
- Testing basic session lifecycle
- Validating PreToolUse/PostToolUse pairing
- Testing Read tool (non-blocked) execution
- Validating event schema v2.0 compliance

**Event count**: 4 events

---

### daic_blocking_workflow.json
**Description**: DAIC workflow with Write tool blocked in discussion mode, then allowed after mode switch

**Scenario**:
1. SessionStart (discussion mode)
2. PreToolUse (Write) - BLOCKED
3. UserPromptSubmit - trigger phrase detected ("go ahead")
4. PreToolUse (Write) - ALLOWED (implementation mode)
5. PostToolUse (Write)

**Use cases**:
- Testing DAIC enforcement
- Validating tool blocking in discussion mode
- Testing trigger phrase detection
- Validating mode transitions
- Testing Write tool allowed in implementation mode

**Event count**: 5 events

**Key features**:
- Demonstrates blocked tool execution
- Shows trigger phrase detection
- Demonstrates mode switching workflow

---

### multi_tool_workflow.json
**Description**: Multi-tool workflow with Bash, Read, Write, and Edit

**Scenario**:
1. PreToolUse (Bash) → PostToolUse (Bash)
2. PreToolUse (Read) → PostToolUse (Read)
3. PreToolUse (Write) → PostToolUse (Write)
4. PreToolUse (Edit) → PostToolUse (Edit)

**Use cases**:
- Testing multiple tool types
- Validating correlation across different tools
- Testing tool sequence execution
- Validating each tool's PreToolUse/PostToolUse pairing

**Event count**: 8 events (4 tools × 2 hooks each)

**Key features**:
- Each tool has unique correlation_id
- All pre/post hooks properly paired
- Demonstrates realistic development workflow

---

## Using Fixtures in Tests

### Loading Fixture Data

```python
import json
from pathlib import Path

def load_fixture(fixture_name: str) -> dict:
    """Load event fixture by name"""
    fixture_path = Path(__file__).parent / "fixtures" / "events" / f"{fixture_name}.json"
    with open(fixture_path) as f:
        return json.load(f)

# Load basic session fixture
basic_session = load_fixture("basic_session")
events = basic_session["events"]
session_id = basic_session["session_id"]
```

### Example Test Usage

```python
def test_basic_session_validation(db_validator):
    """Test basic session event validation"""
    fixture = load_fixture("basic_session")

    # Insert fixture events into test database
    for event in fixture["events"]:
        insert_event(event)

    # Validate using DatabaseValidator
    db_validator.assert_event_count(fixture["session_id"], expected=4)
    db_validator.assert_all_events_have_required_fields(fixture["session_id"])
    db_validator.assert_correlation_ids_valid(fixture["session_id"])
```

### Correlation Validation Example

```python
def test_correlation_flow(correlation_validator):
    """Test correlation ID flow using fixture"""
    fixture = load_fixture("multi_tool_workflow")
    events = fixture["events"]

    # Validate correlation flow
    correlation_validator.assert_pre_post_paired(events)
    correlation_validator.assert_correlation_flow_valid(events)

    # Analyze flow
    analysis = correlation_validator.analyze_correlation_flow(events)
    assert analysis.paired_count == 4  # 4 tools, each with pre/post pair
```

### DAIC Workflow Testing Example

```python
def test_daic_blocking_workflow(db_validator):
    """Test DAIC blocking using fixture"""
    fixture = load_fixture("daic_blocking_workflow")

    # Get blocked event
    blocked_event = next(
        e for e in fixture["events"]
        if e.get("metadata", {}).get("blocked") == True
    )

    assert blocked_event["tool_name"] == "Write"
    assert "discussion" in blocked_event["metadata"]["block_reason"]

    # Get allowed event after mode switch
    allowed_event = next(
        e for e in fixture["events"]
        if e["hook_name"] == "pre_tool_use" and
           e.get("metadata", {}).get("daic_mode") == "implementation"
    )

    assert allowed_event["tool_name"] == "Write"
    assert not allowed_event["metadata"].get("blocked", False)
```

## Fixture Schema

All fixtures follow this structure:

```json
{
  "description": "Human-readable description",
  "session_id": "Unique session identifier",
  "correlation_id_base": "Base correlation ID for this fixture",
  "events": [
    {
      "session_id": "string",
      "correlation_id": "string",
      "hook_name": "string",
      "tool_name": "string | null",
      "tool_input": "object | null",
      "timestamp_ns": "integer (nanoseconds)",
      "execution_id": "string",
      "schema_version": "2.0",
      "workflow_phase": "string",
      "project_root": "string",
      "logged_at": "ISO 8601 timestamp",
      "metadata": "object (optional)"
    }
  ]
}
```

## Event Schema v2.0

Required fields for all events:
- `session_id`: Session identifier
- `correlation_id`: Correlation identifier for related events
- `hook_name`: Hook that generated the event
- `timestamp_ns`: Event timestamp in nanoseconds
- `execution_id`: Unique execution identifier
- `schema_version`: Must be "2.0"

Optional fields:
- `tool_name`: Tool being used (if applicable)
- `tool_input`: Tool input parameters
- `workflow_phase`: Phase of workflow
- `project_root`: Project root directory
- `logged_at`: Human-readable timestamp
- `metadata`: Additional metadata

## Adding New Fixtures

When creating new fixtures:

1. Use realistic session/correlation IDs
2. Ensure timestamps are chronologically ordered
3. Follow schema v2.0 requirements
4. Include all required fields
5. Use unique execution IDs
6. Document the scenario in the description
7. Update this README with fixture details

## Validation Checklist

New fixtures should pass these validations:
- [ ] All events have required fields
- [ ] Schema version is "2.0"
- [ ] Timestamps are ordered
- [ ] Correlation IDs are valid
- [ ] PreToolUse/PostToolUse are paired
- [ ] session_id is consistent
- [ ] execution_id values are unique
- [ ] JSON is valid and well-formatted
