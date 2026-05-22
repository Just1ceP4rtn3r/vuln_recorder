# Pane Border Highlight for Display Steps

## Problem

When `vuln-recorder` plays back scenario steps, `printf` commands output step
titles (e.g. "Step 1: Locate vulnerable function") into tmux panes. These
titles need to stand out in the screen recording, but injecting extra shell
commands (like `echo` borders) fails because `tmux send-keys` sends characters
one-by-one — single quotes get mangled and escape sequences break.

## Solution

Use tmux's native pane styling to highlight the border during display steps.
No shell commands are injected; only `tmux set-option` calls toggle the border
appearance.

## Design

### Trigger

A step is classified as a "display step" when its `command` field starts with
`printf` (matching the existing `_is_display_command` check).

### Highlight sequence

For each display step, the engine does this:

1. **Before** sending the command — set the pane's border to a bright,
   attention-grabbing style via `tmux set-option -p`:
   - `pane-border-style` → `fg=brightred,bold`
2. Send the original `printf` command unchanged.
3. Wait `step['wait']` seconds (unchanged).
4. **After** the wait — restore the pane's border to default:
   - `pane-border-style` → `default`

### Implementation changes

**`engine.py`**:

- Remove `BORDER_WIDTH` constant and `_border_command` method.
- Add `_highlight_pane(pane, style)` that calls a new method on
  `TerminalOrchestrator`.
- Simplify the step loop: highlight before, send command, wait, unhighlight.

**`terminal.py`**:

- Add `set_pane_border_style(pane_name, style)` method that runs:
  ```
  tmux -L <socket> set-option -p -t <session>.<idx> pane-border-style <style>
  ```

### Non-display steps

Non-display steps (e.g. `clear`, `curl`, `sleep`) are unaffected — no border
change, no extra commands, identical behavior to before.

### Edge cases

- If `set-option` fails (unsupported tmux version), it is non-fatal. The step
  still plays; only the highlight is lost.
- Consecutive display steps: border stays highlighted (second highlight is
  idempotent), then unhighlighted after the last one.

## Out of scope

- Changing pane background colour (may hurt text readability).
- Modifying pane title text during steps.
- Any changes to `scenario.yaml` format or existing printf commands.
