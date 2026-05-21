from unittest.mock import patch, MagicMock

import pytest

from vuln_recorder.cli import main


@patch('vuln_recorder.cli.Engine')
def test_run_command(mock_engine_cls, capsys):
    mock_engine = MagicMock()
    mock_engine.run.return_value = "/tmp/output/test"
    mock_engine_cls.return_value = mock_engine

    with patch('sys.argv', ['vuln_recorder', 'run', 'test.yaml']):
        main()

    mock_engine_cls.assert_called_with('test.yaml', 'output')
    captured = capsys.readouterr()
    assert '/tmp/output/test' in captured.out


@patch('vuln_recorder.cli.Engine')
def test_run_command_with_output_dir(mock_engine_cls, capsys):
    mock_engine = MagicMock()
    mock_engine.run.return_value = "/custom/output/test"
    mock_engine_cls.return_value = mock_engine

    with patch('sys.argv', ['vuln_recorder', 'run', 'test.yaml', '--output', '/custom/output']):
        main()

    mock_engine_cls.assert_called_with('test.yaml', '/custom/output')


@patch('vuln_recorder.cli.Scenario')
def test_dry_run(mock_scenario_cls, capsys):
    mock_scenario = MagicMock()
    mock_scenario.load.return_value = {
        'name': 'Test',
        'steps': [{'pane': 'a', 'command': 'echo', 'wait': 1}],
    }
    mock_scenario_cls.return_value = mock_scenario

    with patch('sys.argv', ['vuln_recorder', 'run', 'test.yaml', '--dry-run']):
        main()

    mock_scenario_cls.assert_called_with('test.yaml')
    captured = capsys.readouterr()
    assert 'Dry run' in captured.out


@patch('vuln_recorder.cli.Engine')
def test_check_command_success(mock_engine_cls, capsys):
    mock_engine = MagicMock()
    mock_engine_cls.return_value = mock_engine

    with patch('sys.argv', ['vuln_recorder', 'check']):
        main()

    mock_engine.check_dependencies.assert_called_once()
    captured = capsys.readouterr()
    assert 'All dependencies' in captured.out


@patch('vuln_recorder.cli.Engine')
def test_check_command_missing_deps(mock_engine_cls):
    mock_engine = MagicMock()
    mock_engine.check_dependencies.side_effect = RuntimeError("Missing dependencies: ffmpeg")
    mock_engine_cls.return_value = mock_engine

    with patch('sys.argv', ['vuln_recorder', 'check']):
        with pytest.raises(SystemExit):
            main()


def test_no_command_prints_help(capsys):
    with patch('sys.argv', ['vuln_recorder']):
        main()

    captured = capsys.readouterr()
    assert 'usage' in captured.out.lower() or 'vuln_recorder' in captured.out


@patch('vuln_recorder.cli.Scenario')
def test_dry_run_shows_step_count(mock_scenario_cls, capsys):
    mock_scenario = MagicMock()
    mock_scenario.load.return_value = {
        'name': 'CountTest',
        'steps': [{'pane': 'a', 'command': 'echo', 'wait': 1}] * 5,
    }
    mock_scenario_cls.return_value = mock_scenario

    with patch('sys.argv', ['vuln_recorder', 'run', 'test.yaml', '--dry-run']):
        main()

    captured = capsys.readouterr()
    assert 'CountTest' in captured.out
    assert 'Steps: 5' in captured.out


@patch('vuln_recorder.cli.Engine')
def test_check_missing_stderr_output(mock_engine_cls):
    mock_engine = MagicMock()
    mock_engine.check_dependencies.side_effect = RuntimeError("Missing dependencies: ffmpeg, xterm")
    mock_engine_cls.return_value = mock_engine

    with patch('sys.argv', ['vuln_recorder', 'check']):
        with pytest.raises(SystemExit):
            main()


@patch('vuln_recorder.cli.Engine')
def test_run_prints_output_path(mock_engine_cls, capsys):
    mock_engine = MagicMock()
    mock_engine.run.return_value = "/home/user/output/test-vuln"
    mock_engine_cls.return_value = mock_engine

    with patch('sys.argv', ['vuln_recorder', 'run', 'test.yaml']):
        main()

    captured = capsys.readouterr()
    assert '/home/user/output/test-vuln' in captured.out


@patch('vuln_recorder.cli.Engine')
def test_run_with_default_output_dir(mock_engine_cls):
    mock_engine = MagicMock()
    mock_engine.run.return_value = "output/test"
    mock_engine_cls.return_value = mock_engine

    with patch('sys.argv', ['vuln_recorder', 'run', 'scenario.yaml']):
        main()

    mock_engine_cls.assert_called_with('scenario.yaml', 'output')


@patch('vuln_recorder.cli.Engine')
def test_check_success_no_stderr(mock_engine_cls, capsys):
    mock_engine = MagicMock()
    mock_engine_cls.return_value = mock_engine

    with patch('sys.argv', ['vuln_recorder', 'check']):
        main()

    captured = capsys.readouterr()
    assert captured.err == ""
