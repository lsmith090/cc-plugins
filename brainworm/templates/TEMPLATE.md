---
task: [prefix]-[descriptive-name]
branch: feature/[name]|fix/[name]|experiment/[name]|none
submodule: [submodule-path]|none  # e.g., "one-mit" for frontend, "none" for main repo
status: pending|in-progress|completed|blocked
created: YYYY-MM-DD
modules: [list of services/modules involved]
session_id: [current-session-id]
correlation_id: [brainworm-correlation-id]
---

# [Human-Readable Title]

## Problem/Goal
[Clear description of what we're solving/building]

## Success Criteria
- [ ] Specific, measurable outcome
- [ ] Another concrete goal

## Context Files
<!-- Added by context-gathering agent or manually -->
- @service/file.py:123-145  # Specific lines
- @other/module.py          # Whole file  
- patterns/auth-flow        # Pattern reference

## Analytics Insights
<!-- Populated by brainworm analytics for similar tasks -->
- Similar task success patterns: [pattern-description]
- Recommended approach based on historical data
- Estimated complexity and timeline from analytics

## User Notes
<!-- Any specific notes or requirements from the developer -->

## Work Log
<!-- Updated as work progresses -->
- [YYYY-MM-DD] Started task, initial research