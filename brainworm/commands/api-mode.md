---
allowed-tools: Bash(.brainworm/plugin-launcher:*)
description: Toggle API mode (enables/disables automatic ultrathink)
---

!`.brainworm/plugin-launcher api_mode.py $ARGUMENTS`

API mode configuration updated. The change will take effect in your next message.

- **API mode enabled**: Ultrathink disabled to save tokens (manual control with `[[ ultrathink ]]`)
- **API mode disabled**: Ultrathink automatically enabled for best performance (Max mode)
