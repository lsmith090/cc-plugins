---
allowed-tools: Bash(uv run:*)
description: Toggle API mode (enables/disables automatic ultrathink)
---

!`uv run .brainworm/scripts/api_mode.py $ARGUMENTS`

API mode configuration updated. The change will take effect in your next message.

- **API mode enabled**: Ultrathink disabled to save tokens (manual control with `[[ ultrathink ]]`)
- **API mode disabled**: Ultrathink automatically enabled for best performance (Max mode)