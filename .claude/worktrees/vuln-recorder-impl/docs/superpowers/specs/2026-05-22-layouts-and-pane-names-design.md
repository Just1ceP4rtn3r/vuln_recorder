# Layouts, Pane Names & Output Guidelines

## Summary

Expose tmux's existing 4-panel layout presets via fixture YAMLs, set `main-horizontal` as the default layout, add pane title display, and document terminal output best practices.

## Changes

### 1. Make `layout` optional with `main-horizontal` default

**File:** `vuln_recorder/scenario.py`

Remove `layout` from `REQUIRED_TMUX_FIELDS`. After validation, if `layout` is missing from the YAML's `tmux` section, set it to `"main-horizontal"`. No changes to `terminal.py` or `engine.py`.

### 2. Add 4-panel fixture YAMLs

**Directory:** `tests/fixtures/`

Five new fixture files, each with 4 panes (`top-left`, `top-right`, `bottom-left`, `bottom-right`) and simple echo commands:

- `four_pane_tiled.yaml` — tiled layout (2x2 grid)
- `four_pane_main_horizontal.yaml` — main-horizontal layout
- `four_pane_main_vertical.yaml` — main-vertical layout
- `four_pane_even_horizontal.yaml` — even-horizontal layout
- `four_pane_even_vertical.yaml` — even-vertical layout

### 3. Add pane title display

**File:** `vuln_recorder/terminal.py`

In `create_session`, after building the pane map, iterate over the mapped panes and call `tmux select-pane -T "{pane_name}"` for each. This displays the pane's role (e.g. "attacker", "victim", "environment") in the tmux pane border during recording.

### 4. Update README

- Add 4-panel ASCII diagrams for all 5 tmux presets alongside existing 3-panel diagrams
- Document that `layout` is optional and defaults to `main-horizontal`
- Add a "Terminal Output Best Practices" section:
  - Natural language output in panes must follow step summaries from the report
  - Keep text concise — do not write paragraphs
  - Use ANSI color codes to highlight key information (e.g. `\033[31m` for red alerts, `\033[32m` for green success)
  - Each output must remain visible for at least 5 seconds before the next action

### 5. Add tests

**File:** `tests/test_terminal.py`

- Test that `select-pane -T` is called for each pane name with correct title
- Test that 4-pane fixtures produce 3 `split-window` calls and 1 `select-layout` call
- Test that `layout` defaults to `main-horizontal` when omitted from YAML
