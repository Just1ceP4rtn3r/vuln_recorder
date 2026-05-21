import shutil
from unittest.mock import patch, MagicMock

import pytest

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
    mock_terminal_cls.return_value = mock_terminal

    output_dir = str(tmp_path / "output")
    engine = Engine("test.yaml", output_dir)
    result = engine.run()

    mock_scenario_cls.assert_called_with("test.yaml")
    mock_scenario.load.assert_called_once()
    mock_xvfb.start.assert_called_once()
    mock_recorder.start.assert_called_once()
    mock_terminal.create_session.assert_called_once()

    assert mock_terminal.send_keys.call_count == 2
    mock_terminal.send_keys.assert_any_call('attacker', 'echo hello')
    mock_terminal.send_keys.assert_any_call('victim', 'echo pwned')

    mock_recorder.stop.assert_called_once()
    mock_xvfb.stop.assert_called_once()

    assert 'test-vuln' in result


@patch('vuln_recorder.engine.shutil.copy')
@patch('vuln_recorder.engine.atexit')
@patch('vuln_recorder.engine.time.sleep')
@patch('vuln_recorder.engine.TerminalOrchestrator')
@patch('vuln_recorder.engine.Recorder')
@patch('vuln_recorder.engine.XvfbManager')
@patch('vuln_recorder.engine.Scenario')
@patch('vuln_recorder.engine.shutil.which', return_value="/usr/bin/tool")
def test_run_uses_output_dir_from_scenario(mock_which, mock_scenario_cls, mock_xvfb_cls,
                                            mock_recorder_cls, mock_terminal_cls,
                                            mock_sleep, mock_atexit, mock_copy, tmp_path):
    mock_scenario = MagicMock()
    mock_scenario_cls.return_value = mock_scenario
    mock_scenario.load.return_value = {
        'name': 'Test',
        'description': 'desc',
        'output_dir': 'custom-dir',
        'display': {'width': 1920, 'height': 1080},
        'tmux': {
            'session_name': 's',
            'layout': 'even-horizontal',
            'panes': [{'name': 'a'}],
        },
        'steps': [{'pane': 'a', 'command': 'echo', 'wait': 1}],
    }

    mock_xvfb = MagicMock()
    mock_xvfb.start.return_value = ":99"
    mock_xvfb_cls.return_value = mock_xvfb

    mock_recorder = MagicMock()
    mock_recorder_cls.return_value = mock_recorder

    mock_terminal = MagicMock()
    mock_terminal_cls.return_value = mock_terminal

    output_dir = str(tmp_path / "output")
    engine = Engine("test.yaml", output_dir)
    result = engine.run()

    assert 'custom-dir' in result


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

    engine = Engine("test.yaml", str(tmp_path / "output"))
    result = engine.run()

    mock_terminal.send_keys.assert_not_called()
    mock_recorder.stop.assert_called_once()
    assert 'empty-steps' in result


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
    mock_terminal_cls.return_value = mock_terminal

    engine = Engine("test.yaml", str(tmp_path / "output"))
    engine.run()

    mock_copy.assert_called_once()
    src, dst = mock_copy.call_args[0]
    assert src == "test.yaml"
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
