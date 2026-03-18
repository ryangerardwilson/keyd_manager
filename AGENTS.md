# keyd_manager Agent Guide

## Workspace Defaults
- Follow `/home/ryan/Documents/agent_context/CLI_TUI_STYLE_GUIDE.md` for CLI taste and help shape.
- Follow `/home/ryan/Documents/agent_context/CANONICAL_REFERENCE_IMPLEMENTATION_FOR_CLI_AND_TUI_APPS.md` where it usefully applies to launcher and installer behavior.

## Scope
- `keyd_manager` is only for the managed sticky-keys `keyd` config.
- Keep it focused on three flows:
  - open the managed config in an editor
  - install/apply that config into `/etc/keyd/`
  - inspect `keyd.service` status
- Do not expand this into a generic keyboard remapping suite unless the user explicitly asks.

## Storage
- The editable config lives at `~/.config/keyd_manager/keyd.config`.
- Seed that file from `assets/keyd.config` when it does not exist yet.
- Keep mutable state out of the repo.
