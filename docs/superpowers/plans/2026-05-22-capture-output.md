# Scenario Output Capture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Capture terminal output from each scenario step during recording, save as `scenario-outputs.yaml` in the `record/` directory alongside the scenario config, and print it to stdout when done.

**Architecture:** Add `capture_pane()` to `TerminalOrchestrator` using `tmux capture-pane`. Modify `Engine.run()` to call it after each step and write a YAML results file. Change output directory from `--output` flag to `<scenario_dir>/record/`. Update CLI to remove `--output` flag and print the output YAML.

**Tech Stack:** Python 3, PyYAML, subprocess (tmux), pytest

---

### Task 1: Add `capture_pane` to `TerminalOrchestrator`

**Files:**
- Modify: `vuln_recorder/terminal.py`
- Modify: `tests/test_terminal.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_terminal.py`:

```python
@patch('vuln_recorder.terminal.subprocess.run')
def test_capture_pane_returns_stripped_output(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="line1\nline2\n\n\n")

    term = TerminalOrchestrator(":99", "test-session", [{'name': 'a'}], "custom")
    term._pane_map = {'a': '1'}

    result = term.capture_pane('a')

    mock_run.assert_called_once_with(
        ["tmux", "-L", "vr-test-session", "capture-pane",
         "-t", "test-session.1", "-p", "-S", "-100"],
        capture_output=True, text=True,
    )
    assert result == "line1\nline2"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/syncxxx/Documents/vuln-tools/vuln-recorder && python -m pytest tests/test_terminal.py::test_capture_pane_returns_stripped_output -v`
Expected: FAIL with `AttributeError: 'TerminalOrchestrator' object has no attribute 'capture_pane'`

- [ ] **Step 3: Write minimal implementation**

Add to `vuln_recorder/terminal.py`, after `destroy_session`:

```python
def capture_pane(self, pane_name: str) -> str:
    if pane_name not in self._pane_map:
        raise ValueError(f"Unknown pane: '{pane_name}'. Available: {list(self._pane_map.keys())}")
    result = subprocess.run(
        self._tmux(
            "capture-pane",
            "-t", f"{self.session_name}.{self._pane_map[pane_name]}",
            "-p", "-S", "-100",
        ),
        capture_output=True, text=True,
    )
    return result.stdout.rstrip()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/syncxxx/Documents/vuln-tools/vuln-recorder && python -m pytest tests/test_terminal.py::test_capture_pane_returns_stripped_output -v`
Expected: PASS

- [ ] **Step 5: Add edge case test for unknown pane**

Add to `tests/test_terminal.py`:

```python
def test_capture_pane_unknown_pane_raises():
    import pytest
    term = TerminalOrchestrator(":99", "test-session", [{'name': 'a'}], "custom")
    term._pane_map = {'a': '1'}
    with pytest.raises(ValueError, match="Unknown pane: 'nonexistent'"):
        term.capture_pane('nonexistent')
```

- [ ] **Step 6: Run edge case test**

Run: `cd /home/syncxxx/Documents/vuln-tools/vuln-recorder && python -m pytest tests/test_terminal.py::test_capture_pane_unknown_pane_raises -v`
Expected: PASS

- [ ] **Step 7: Add edge case test for empty output**

Add to `tests/test_terminal.py`:

```python
@patch('vuln_recorder.terminal.subprocess.run')
def test_capture_pane_empty_output(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="\n\n\n")

    term = TerminalOrchestrator(":99", "test-session", [{'name': 'a'}], "custom")
    term._pane_map = {'a': '1'}

    result = term.capture_pane('a')
    assert result == ""
```

- [ ] **Step 8: Run empty output test**

Run: `cd /home/syncxxx/Documents/vuln-tools/vuln-recorder && python -m pytest tests/test_terminal.py::test_capture_pane_empty_output -v`
Expected: PASS

- [ ] **Step 9: Run full terminal test suite**

Run: `cd /home/syncxxx/Documents/vuln-tools/vuln-recorder && python -m pytest tests/test_terminal.py -v`
Expected: All tests PASS

- [ ] **Step 10: Commit**

```bash
cd /home/syncxxx/Documents/vuln-tools/vuln-recorder
git add vuln_recorder/terminal.py tests/test_terminal.py
git commit -m "feat: add capture_pane method to TerminalOrchestrator"
```

---

### Task 2: Update `Engine` to capture outputs and change output directory

**Files:**
- Modify: `vuln_recorder/engine.py`
- Modify: `tests/test_engine.py`

- [ ] **Step 1: Write failing test for new output directory behavior**

Add to `tests/test_engine.py`:

```python
@patch('vuln_recorder.engine.shutil.copy')
@patch('vuln_recorder.engine.atexit')
@patch('vuln_recorder.engine.time.sleep')
@patch('vuln_recorder.engine.TerminalOrchestrator')
@patch('vuln_recorder.engine.Recorder')
@patch('vuln_recorder.engine.XvfbManager')
@patch('vuln_recorder.engine.Scenario')
@patch('vuln_recorder.engine.shutil.which', return_value="/usr/bin/tool")
def test_run_uses_record_dir_next_to_scenario(mock_which, mock_scenario_cls, mock_xvfb_cls,
                                                mock_recorder_cls, mock_terminal_cls,
                                                mock_sleep, mock_atexit, mock_copy, tmp_path):
    scenario_file = tmp_path / "my-scenario" / "scenario.yaml"
    scenario_file.parent.mkdir(parents=True, exist_ok=True)
    scenario_file.write_text("dummy")

    mock_scenario = MagicMock()
    mock_scenario_cls.return_value = mock_scenario
    mock_scenario.load.return_value = {
        'name': 'Test',
        'description': 'desc',
        'display': {'width': 640, 'height': 480},
        'tmux': {
            'session_name': 's',
            'layout': 'custom',
            'panes': [{'name': 'a'}],
        },
        'steps': [{'pane': 'a', 'command': 'echo hi', 'wait': 1}],
    }

    mock_xvfb = MagicMock()
    mock_xvfb.start.return_value = ":99"
    mock_xvfb_cls.return_value = mock_xvfb

    mock_recorder = MagicMock()
    mock_recorder_cls.return_value = mock_recorder

    mock_terminal = MagicMock()
    mock_terminal.capture_pane.return_value = "hi"
    mock_terminal_cls.return_value = mock_terminal

    engine = Engine(str(scenario_file))
    result = engine.run()

    assert result == str(tmp_path / "my-scenario" / "record")
    assert (tmp_path / "my-scenario" / "record").is_dir()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/syncxxx/Documents/vuln-tools/vuln-recorder && python -m pytest tests/test_engine.py::test_run_uses_record_dir_next_to_scenario -v`
Expected: FAIL (old code uses `output_dir` parameter and slug-based directory)

- [ ] **Step 3: Write failing test for scenario-outputs.yaml generation**

Add to `tests/test_engine.py`:

```python
import yaml as _yaml

@patch('vuln_recorder.engine.shutil.copy')
@patch('vuln_recorder.engine.atexit')
@patch('vuln_recorder.engine.time.sleep')
@patch('vuln_recorder.engine.TerminalOrchestrator')
@patch('vuln_recorder.engine.Recorder')
@patch('vuln_recorder.engine.XvfbManager')
@patch('vuln_recorder.engine.Scenario')
@patch('vuln_recorder.engine.shutil.which', return_value="/usr/bin/tool")
def test_run_writes_scenario_outputs_yaml(mock_which, mock_scenario_cls, mock_xvfb_cls,
                                           mock_recorder_cls, mock_terminal_cls,
                                           mock_sleep, mock_atexit, mock_copy, tmp_path):
    scenario_file = tmp_path / "vuln" / "scenario.yaml"
    scenario_file.parent.mkdir(parents=True, exist_ok=True)
    scenario_file.write_text("dummy")

    mock_scenario = MagicMock()
    mock_scenario_cls.return_value = mock_scenario
    mock_scenario.load.return_value = {
        'name': 'Test Vuln',
        'description': 'desc',
        'display': {'width': 640, 'height': 480},
        'tmux': {
            'session_name': 's',
            'layout': 'custom',
            'panes': [{'name': 'env'}, {'name': 'attacker'}],
        },
        'steps': [
            {'pane': 'env', 'command': 'echo hello', 'wait': 1},
            {'pane': 'attacker', 'command': 'curl http://test', 'wait': 2},
        ],
    }

    mock_xvfb = MagicMock()
    mock_xvfb.start.return_value = ":99"
    mock_xvfb_cls.return_value = mock_xvfb

    mock_recorder = MagicMock()
    mock_recorder_cls.return_value = mock_recorder

    mock_terminal = MagicMock()
    mock_terminal.capture_pane.side_effect = ["hello", "404 not found"]
    mock_terminal_cls.return_value = mock_terminal

    engine = Engine(str(scenario_file))
    engine.run()

    outputs_file = tmp_path / "vuln" / "record" / "scenario-outputs.yaml"
    assert outputs_file.exists()

    with open(outputs_file) as f:
        data = _yaml.safe_load(f)

    assert data['scenario'] == 'Test Vuln'
    assert 'captured_at' in data
    assert len(data['steps']) == 2
    assert data['steps'][0] == {
        'step': 0, 'pane': 'env', 'command': 'echo hello', 'output': 'hello',
    }
    assert data['steps'][1] == {
        'step': 1, 'pane': 'attacker', 'command': 'curl http://test', 'output': '404 not found',
    }
```

- [ ] **Step 4: Run test to verify it fails**

Run: `cd /home/syncxxx/Documents/vuln-tools/vuln-recorder && python -m pytest tests/test_engine.py::test_run_writes_scenario_outputs_yaml -v`
Expected: FAIL

- [ ] **Step 5: Implement changes to `engine.py`**

Replace the entire content of `vuln_recorder/engine.py` with:

```python
import atexit
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .scenario import Scenario
from .xvfb import XvfbManager
from .recorder import Recorder
from .terminal import TerminalOrchestrator


class Engine:
    def __init__(self, scenario_path: str):
        self.scenario_path = scenario_path
        self.xvfb = None
        self.recorder = None
        self.terminal = None

    def run(self) -> str:
        scenario = Scenario(self.scenario_path)
        data = scenario.load()

        self.check_dependencies()

        scenario_dir = Path(self.scenario_path).resolve().parent
        run_dir = scenario_dir / "record"
        run_dir.mkdir(parents=True, exist_ok=True)

        shutil.copy(self.scenario_path, run_dir / "scenario.yaml")

        display_cfg = data['display']
        self.xvfb = XvfbManager(
            width=display_cfg['width'],
            height=display_cfg['height'],
            color_depth=display_cfg.get('color_depth', 24),
        )
        display = self.xvfb.start()
        atexit.register(self.cleanup)

        try:
            resolution = f"{display_cfg['width']}x{display_cfg['height']}"
            output_path = str(run_dir / "recording.mp4")
            self.recorder = Recorder(display, output_path, resolution)
            self.recorder.start()
            time.sleep(1)

            tmux_cfg = data['tmux']
            self.terminal = TerminalOrchestrator(
                display, tmux_cfg['session_name'],
                tmux_cfg['panes'], tmux_cfg['layout'],
            )
            self.terminal.create_session()

            captured_steps = []
            for i, step in enumerate(data['steps']):
                self.terminal.send_keys(step['pane'], step['command'])
                time.sleep(step['wait'])
                output = self.terminal.capture_pane(step['pane'])
                captured_steps.append({
                    'step': i,
                    'pane': step['pane'],
                    'command': step['command'],
                    'output': output,
                })

            outputs_data = {
                'scenario': data['name'],
                'captured_at': datetime.now(timezone.utc).isoformat(),
                'steps': captured_steps,
            }
            outputs_file = run_dir / "scenario-outputs.yaml"
            with open(outputs_file, 'w') as f:
                yaml.dump(outputs_data, f, default_flow_style=False, allow_unicode=True)

            self.recorder.stop()
            self.xvfb.stop()
        except Exception:
            self.cleanup()
            raise

        return str(run_dir)

    def check_dependencies(self):
        missing = []
        for tool in ['Xvfb', 'ffmpeg', 'xterm', 'tmux']:
            if not shutil.which(tool):
                missing.append(tool)
        if missing:
            raise RuntimeError(f"Missing dependencies: {', '.join(missing)}")

    def cleanup(self):
        if self.recorder:
            self.recorder.stop()
        if self.terminal:
            self.terminal.destroy_session()
        if self.xvfb:
            self.xvfb.stop()
```

- [ ] **Step 6: Run the new tests to verify they pass**

Run: `cd /home/syncxxx/Documents/vuln-tools/vuln-recorder && python -m pytest tests/test_engine.py::test_run_uses_record_dir_next_to_scenario tests/test_engine.py::test_run_writes_scenario_outputs_yaml -v`
Expected: PASS

- [ ] **Step 7: Update existing tests that use old `output_dir` parameter**

The following tests pass `output_dir` to `Engine()` or assert on slug-based paths. Update them:

`test_run_orchestrates_full_flow`: Change `Engine("test.yaml", output_dir)` to `Engine("test.yaml")`. The mock Scenario returns `name: 'Test Vuln'` so the old test asserted `'test-vuln' in result`. Since we now derive the path from the scenario file location, update the assertion. Create a real temp scenario file and assert on `record` in path.

Replace the test body:

```python
@patch('vuln_recorder.engine.shutil.copy')
@patch('vuln_recorder.engine.atexit')
@patch('vuln_recorder.engine.time.sleep')
@patch('vuln_recorder.engine.TerminalOrchestrator')
@patch('vuln_recorder.engine.Recorder')
@patch('vuln_recorder.engine.XvfbManager')
@patch('vuln_recorder.engine.Scenario')
@patch('vuln_recorder.engine.shutil.which', return_value="/usr/bin/tool")
def test_run_orchestrates_full_flow(mock_which, mock_scenario_cls, mock_xvfb_cls,
                                     mock_recorder_cls, mock_terminal_cls,
                                     mock_sleep, mock_atexit, mock_copy, tmp_path):
    scenario_file = tmp_path / "test-vuln" / "scenario.yaml"
    scenario_file.parent.mkdir(parents=True, exist_ok=True)
    scenario_file.write_text("dummy")

    mock_scenario = MagicMock()
    mock_scenario_cls.return_value = mock_scenario
    mock_scenario.load.return_value = {
        'name': 'Test Vuln',
        'description': 'desc',
        'display': {'width': 1920, 'height': 1080, 'color_depth': 24},
        'tmux': {
            'session_name': 'test-sess',
            'layout': 'even-horizontal',
            'panes': [{'name': 'attacker'}, {'name': 'victim'}],
        },
        'steps': [
            {'pane': 'attacker', 'command': 'echo hello', 'wait': 1},
            {'pane': 'victim', 'command': 'echo pwned', 'wait': 2},
        ],
    }

    mock_xvfb = MagicMock()
    mock_xvfb.start.return_value = ":99"
    mock_xvfb_cls.return_value = mock_xvfb

    mock_recorder = MagicMock()
    mock_recorder_cls.return_value = mock_recorder

    mock_terminal = MagicMock()
    mock_terminal.capture_pane.return_value = ""
    mock_terminal_cls.return_value = mock_terminal

    engine = Engine(str(scenario_file))
    result = engine.run()

    mock_scenario_cls.assert_called_with(str(scenario_file))
    mock_scenario.load.assert_called_once()
    mock_xvfb.start.assert_called_once()
    mock_recorder.start.assert_called_once()
    mock_terminal.create_session.assert_called_once()

    assert mock_terminal.send_keys.call_count == 2
    mock_terminal.send_keys.assert_any_call('attacker', 'echo hello')
    mock_terminal.send_keys.assert_any_call('victim', 'echo pwned')

    mock_recorder.stop.assert_called_once()
    mock_xvfb.stop.assert_called_once()

    assert 'record' in result
```

`test_run_uses_output_dir_from_scenario`: This test validated the `output_dir` YAML key overriding the directory. That feature is removed. Delete this test entirely.

`test_run_with_empty_steps`: Update to use scenario file path and remove `output_dir`. Replace:

```python
@patch('vuln_recorder.engine.shutil.copy')
@patch('vuln_recorder.engine.atexit')
@patch('vuln_recorder.engine.time.sleep')
@patch('vuln_recorder.engine.TerminalOrchestrator')
@patch('vuln_recorder.engine.Recorder')
@patch('vuln_recorder.engine.XvfbManager')
@patch('vuln_recorder.engine.Scenario')
@patch('vuln_recorder.engine.shutil.which', return_value="/usr/bin/tool")
def test_run_with_empty_steps(mock_which, mock_scenario_cls, mock_xvfb_cls,
                               mock_recorder_cls, mock_terminal_cls,
                               mock_sleep, mock_atexit, mock_copy, tmp_path):
    scenario_file = tmp_path / "empty-steps" / "scenario.yaml"
    scenario_file.parent.mkdir(parents=True, exist_ok=True)
    scenario_file.write_text("dummy")

    mock_scenario = MagicMock()
    mock_scenario_cls.return_value = mock_scenario
    mock_scenario.load.return_value = {
        'name': 'Empty Steps',
        'description': 'no steps',
        'display': {'width': 640, 'height': 480},
        'tmux': {
            'session_name': 'empty',
            'layout': 'custom',
            'panes': [{'name': 'a'}],
        },
        'steps': [],
    }
    mock_xvfb = MagicMock()
    mock_xvfb.start.return_value = ":99"
    mock_xvfb_cls.return_value = mock_xvfb
    mock_recorder = MagicMock()
    mock_recorder_cls.return_value = mock_recorder
    mock_terminal = MagicMock()
    mock_terminal_cls.return_value = mock_terminal

    engine = Engine(str(scenario_file))
    result = engine.run()

    mock_terminal.send_keys.assert_not_called()
    mock_recorder.stop.assert_called_once()
    assert 'record' in result
```

`test_run_copies_scenario_file`: Update to use scenario file path. Replace:

```python
@patch('vuln_recorder.engine.shutil.copy')
@patch('vuln_recorder.engine.atexit')
@patch('vuln_recorder.engine.time.sleep')
@patch('vuln_recorder.engine.TerminalOrchestrator')
@patch('vuln_recorder.engine.Recorder')
@patch('vuln_recorder.engine.XvfbManager')
@patch('vuln_recorder.engine.Scenario')
@patch('vuln_recorder.engine.shutil.which', return_value="/usr/bin/tool")
def test_run_copies_scenario_file(mock_which, mock_scenario_cls, mock_xvfb_cls,
                                   mock_recorder_cls, mock_terminal_cls,
                                   mock_sleep, mock_atexit, mock_copy, tmp_path):
    scenario_file = tmp_path / "copy-test" / "scenario.yaml"
    scenario_file.parent.mkdir(parents=True, exist_ok=True)
    scenario_file.write_text("dummy")

    mock_scenario = MagicMock()
    mock_scenario_cls.return_value = mock_scenario
    mock_scenario.load.return_value = {
        'name': 'Copy Test',
        'description': 'test copy',
        'display': {'width': 640, 'height': 480},
        'tmux': {'session_name': 's', 'layout': 'custom', 'panes': [{'name': 'a'}]},
        'steps': [{'pane': 'a', 'command': 'echo', 'wait': 1}],
    }
    mock_xvfb = MagicMock()
    mock_xvfb.start.return_value = ":99"
    mock_xvfb_cls.return_value = mock_xvfb
    mock_recorder = MagicMock()
    mock_recorder_cls.return_value = mock_recorder
    mock_terminal = MagicMock()
    mock_terminal.capture_pane.return_value = ""
    mock_terminal_cls.return_value = mock_terminal

    engine = Engine(str(scenario_file))
    engine.run()

    mock_copy.assert_called_once()
    src, dst = mock_copy.call_args[0]
    assert src == str(scenario_file)
    assert str(dst).endswith("scenario.yaml")
```

`test_check_dependencies_all_present`, `test_check_dependencies_missing_tool`, `test_check_dependencies_multiple_missing`, `test_cleanup_stops_all_components`, `test_cleanup_handles_none_components`, `test_cleanup_idempotent`, `test_check_dependencies_reports_all_missing`: These only call `Engine("test.yaml")` with no second arg. Since `Engine.__init__` now takes only `scenario_path`, no changes needed.

- [ ] **Step 8: Run full engine test suite**

Run: `cd /home/syncxxx/Documents/vuln-tools/vuln-recorder && python -m pytest tests/test_engine.py -v`
Expected: All tests PASS

- [ ] **Step 9: Commit**

```bash
cd /home/syncxxx/Documents/vuln-tools/vuln-recorder
git add vuln_recorder/engine.py tests/test_engine.py
git commit -m "feat: capture step outputs and use record/ directory"
```

---

### Task 3: Update CLI to remove `--output` and print outputs YAML

**Files:**
- Modify: `vuln_recorder/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write failing test for new CLI behavior**

Add to `tests/test_cli.py`:

```python
@patch('vuln_recorder.cli.Engine')
def test_run_prints_outputs_yaml(mock_engine_cls, capsys, tmp_path):
    outputs_file = tmp_path / "record" / "scenario-outputs.yaml"
    outputs_file.parent.mkdir(parents=True)
    outputs_file.write_text("scenario: Test\nsteps: []\n")

    mock_engine = MagicMock()
    mock_engine.run.return_value = str(tmp_path / "record")
    mock_engine_cls.return_value = mock_engine

    with patch('sys.argv', ['vuln_recorder', 'run', str(tmp_path / "scenario.yaml")]):
        main()

    mock_engine_cls.assert_called_with(str(tmp_path / "scenario.yaml"))
    captured = capsys.readouterr()
    assert 'scenario: Test' in captured.out
    assert 'steps: []' in captured.out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/syncxxx/Documents/vuln-tools/vuln-recorder && python -m pytest tests/test_cli.py::test_run_prints_outputs_yaml -v`
Expected: FAIL (old CLI doesn't print outputs YAML)

- [ ] **Step 3: Implement CLI changes**

Replace `vuln_recorder/cli.py` with:

```python
import argparse
import sys
from pathlib import Path

from .engine import Engine
from .scenario import Scenario


def main():
    parser = argparse.ArgumentParser(
        prog='vuln_recorder',
        description='Automated vulnerability verification recorder',
    )
    subparsers = parser.add_subparsers(dest='command')

    run_parser = subparsers.add_parser('run', help='Run a scenario')
    run_parser.add_argument('scenario', help='Path to scenario YAML file')
    run_parser.add_argument('--dry-run', action='store_true', help='Parse only, do not execute')

    subparsers.add_parser('check', help='Check dependencies')

    args = parser.parse_args()

    if args.command == 'run':
        if args.dry_run:
            scenario = Scenario(args.scenario)
            data = scenario.load()
            print(f"Scenario: {data['name']}")
            print(f"Steps: {len(data['steps'])}")
            print("Dry run completed successfully.")
            return

        engine = Engine(args.scenario)
        output_dir = engine.run()
        print(f"Recording saved to: {output_dir}")

        outputs_file = Path(output_dir) / "scenario-outputs.yaml"
        if outputs_file.exists():
            print()
            print(outputs_file.read_text())

    elif args.command == 'check':
        engine = Engine('')
        try:
            engine.check_dependencies()
            print("All dependencies are installed.")
        except RuntimeError as e:
            print(str(e), file=sys.stderr)
            sys.exit(1)

    else:
        parser.print_help()
```

- [ ] **Step 4: Run the new test**

Run: `cd /home/syncxxx/Documents/vuln-tools/vuln-recorder && python -m pytest tests/test_cli.py::test_run_prints_outputs_yaml -v`
Expected: PASS

- [ ] **Step 5: Update existing CLI tests**

`test_run_command`: Old test asserts `mock_engine_cls.assert_called_with('test.yaml', 'output')`. New Engine takes one arg. Replace:

```python
@patch('vuln_recorder.cli.Engine')
def test_run_command(mock_engine_cls, capsys, tmp_path):
    mock_engine = MagicMock()
    mock_engine.run.return_value = str(tmp_path / "record")
    mock_engine_cls.return_value = mock_engine

    scenario_path = str(tmp_path / "test.yaml")
    with patch('sys.argv', ['vuln_recorder', 'run', scenario_path]):
        main()

    mock_engine_cls.assert_called_with(scenario_path)
    captured = capsys.readouterr()
    assert 'record' in captured.out
```

`test_run_command_with_output_dir`: Delete this test. `--output` flag is removed.

`test_run_with_default_output_dir`: Delete this test. No more default output dir.

`test_run_prints_output_path`: Update to use new Engine constructor. Replace:

```python
@patch('vuln_recorder.cli.Engine')
def test_run_prints_output_path(mock_engine_cls, capsys, tmp_path):
    mock_engine = MagicMock()
    mock_engine.run.return_value = str(tmp_path / "record")
    mock_engine_cls.return_value = mock_engine

    scenario_path = str(tmp_path / "scenario.yaml")
    with patch('sys.argv', ['vuln_recorder', 'run', scenario_path]):
        main()

    captured = capsys.readouterr()
    assert 'record' in captured.out
```

- [ ] **Step 6: Run full CLI test suite**

Run: `cd /home/syncxxx/Documents/vuln-tools/vuln-recorder && python -m pytest tests/test_cli.py -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
cd /home/syncxxx/Documents/vuln-tools/vuln-recorder
git add vuln_recorder/cli.py tests/test_cli.py
git commit -m "feat: remove --output flag, print scenario-outputs.yaml to stdout"
```

---

### Task 4: Run full test suite and verify

**Files:** None (verification only)

- [ ] **Step 1: Run full test suite**

Run: `cd /home/syncxxx/Documents/vuln-tools/vuln-recorder && python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 2: Verify dry-run still works**

Run: `cd /home/syncxxx/Documents/vuln-tools/vuln-recorder && python -m vuln_recorder run --dry-run /home/syncxxx/Documents/Tests/openplc-runtime/vulnerabilities/cnvd-reports/OpenPLC-Runtime-v4-Unauthorized-User-Deletion/scenario.yaml`
Expected: Prints scenario name, step count, and "Dry run completed successfully."

- [ ] **Step 3: Commit if any fixes were needed**
