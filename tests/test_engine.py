import shutil
from unittest.mock import patch, MagicMock

import pytest
import yaml as _yaml

from vuln_recorder.engine import Engine


@patch('vuln_recorder.engine.shutil.which')
def test_check_dependencies_all_present(mock_which):
    mock_which.return_value = "/usr/bin/tool"
    engine = Engine("test.yaml")
    engine.check_dependencies()  # Should not raise


@patch('vuln_recorder.engine.shutil.which')
def test_check_dependencies_missing_tool(mock_which):
    def which_side_effect(tool):
        return None if tool == "ffmpeg" else f"/usr/bin/{tool}"
    mock_which.side_effect = which_side_effect
    engine = Engine("test.yaml")
    with pytest.raises(RuntimeError, match="ffmpeg"):
        engine.check_dependencies()


@patch('vuln_recorder.engine.shutil.which')
def test_check_dependencies_multiple_missing(mock_which):
    mock_which.return_value = None
    engine = Engine("test.yaml")
    with pytest.raises(RuntimeError, match="Xvfb.*ffmpeg.*xterm.*tmux"):
        engine.check_dependencies()


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


@patch('vuln_recorder.engine.shutil.which', return_value="/usr/bin/tool")
def test_cleanup_stops_all_components(mock_which):
    engine = Engine("test.yaml")
    engine.xvfb = MagicMock()
    engine.recorder = MagicMock()
    engine.terminal = MagicMock()

    engine.cleanup()

    engine.recorder.stop.assert_called_once()
    engine.terminal.destroy_session.assert_called_once()
    engine.xvfb.stop.assert_called_once()


@patch('vuln_recorder.engine.shutil.which', return_value="/usr/bin/tool")
def test_cleanup_handles_none_components(mock_which):
    engine = Engine("test.yaml")
    engine.cleanup()  # Should not raise


@patch('vuln_recorder.engine.shutil.which', return_value="/usr/bin/tool")
def test_cleanup_idempotent(mock_which):
    engine = Engine("test.yaml")
    engine.xvfb = MagicMock()
    engine.recorder = MagicMock()
    engine.terminal = MagicMock()
    engine.cleanup()
    engine.cleanup()  # Second call should be safe


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


@patch('vuln_recorder.engine.shutil.which')
def test_check_dependencies_reports_all_missing(mock_which):
    mock_which.return_value = None
    engine = Engine("test.yaml")
    with pytest.raises(RuntimeError) as exc_info:
        engine.check_dependencies()
    msg = str(exc_info.value)
    assert "Xvfb" in msg
    assert "ffmpeg" in msg
    assert "xterm" in msg
    assert "tmux" in msg
