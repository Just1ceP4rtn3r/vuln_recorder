# vuln-recorder: scenario output capture

## Summary

Record terminal output from each scenario step during recording, save as `scenario-outputs.yaml` alongside the video, and print to stdout when done.

## Output directory

All outputs go in `<scenario.yaml parent>/record/`:

```
OpenPLC-Runtime-v4-Unauthorized-User-Deletion/
  scenario.yaml
  CNVD-Report.md
  CNVD-Submission.md
  record/
    recording.mp4
    scenario-outputs.yaml
```

The `--output` CLI flag is removed. Output location is determined by scenario.yaml location.

## scenario-outputs.yaml format

```yaml
scenario: "OpenPLC Unauthorized User Deletion"
captured_at: "2026-05-22T14:30:00+08:00"
steps:
  - step: 0
    pane: environment
    command: "clear"
    output: ""

  - step: 5
    pane: environment
    command: "sleep 15 && curl -sk https://127.0.0.1:8443/api/ping"
    output: "pong"
```

Fields per step:
- `step`: 0-indexed step number from scenario.yaml steps list
- `pane`: pane name from scenario.yaml
- `command`: exact command string from scenario.yaml
- `output`: captured terminal text (empty string if nothing visible)

## Code changes

### terminal.py

Add `capture_pane(pane_name: str) -> str`:
- Run `tmux -L <socket> capture-pane -t <session>.<pane_index> -p -S -100`
- Strip trailing blank lines from captured text
- Return the result string

### engine.py

Modify `run()`:
1. Resolve output dir as `Path(scenario_path).parent / "record"`, create it
2. Copy scenario.yaml into record dir
3. In the step loop, after each `send_keys` + `sleep`, call `capture_pane` and append to a results list
4. After the loop, write `scenario-outputs.yaml` to the record dir
5. Return the output dir path

### cli.py

- Remove `--output` argument from `run` subparser
- After `engine.run()`, read and print the contents of `scenario-outputs.yaml` to stdout

## CLI behavior

```
$ vuln_recorder run path/to/scenario.yaml
```

Prints recording path, then prints the full scenario-outputs.yaml content to stdout.
