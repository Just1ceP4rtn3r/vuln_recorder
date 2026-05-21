from unittest.mock import patch, MagicMock, call
from vuln_recorder.terminal import TerminalOrchestrator


@patch('vuln_recorder.terminal.time.sleep')
@patch('vuln_recorder.terminal.subprocess.run')
@patch('vuln_recorder.terminal.subprocess.Popen')
def test_create_session_starts_xterm_with_tmux(mock_popen, mock_run, mock_sleep):
    mock_popen.return_value = MagicMock()
    mock_run.return_value = MagicMock()

    panes = [{'name': 'env'}, {'name': 'attacker'}, {'name': 'victim'}]
    term = TerminalOrchestrator(":99", "test-session", panes, "even-horizontal")
    term.create_session()

    mock_popen.assert_called_once()
    xterm_cmd = mock_popen.call_args[0][0]
    assert xterm_cmd[0] == "xterm"
    assert "-display" in xterm_cmd
    assert ":99" in xterm_cmd


@patch('vuln_recorder.terminal.time.sleep')
@patch('vuln_recorder.terminal.subprocess.run')
@patch('vuln_recorder.terminal.subprocess.Popen')
def test_create_session_splits_panes(mock_popen, mock_run, mock_sleep):
    mock_popen.return_value = MagicMock()
    mock_run.return_value = MagicMock()

    panes = [{'name': 'env'}, {'name': 'attacker'}, {'name': 'victim'}]
    term = TerminalOrchestrator(":99", "test-session", panes, "custom")
    term.create_session()

    split_calls = [c for c in mock_run.call_args_list if 'split-window' in str(c)]
    assert len(split_calls) == 2  # 3 panes = 2 splits


@patch('vuln_recorder.terminal.time.sleep')
@patch('vuln_recorder.terminal.subprocess.run')
@patch('vuln_recorder.terminal.subprocess.Popen')
def test_create_session_applies_layout(mock_popen, mock_run, mock_sleep):
    mock_popen.return_value = MagicMock()
    mock_run.return_value = MagicMock()

    panes = [{'name': 'a'}, {'name': 'b'}]
    term = TerminalOrchestrator(":99", "test-session", panes, "even-horizontal")
    term.create_session()

    layout_calls = [c for c in mock_run.call_args_list if 'select-layout' in str(c)]
    assert len(layout_calls) == 1
    layout_cmd = layout_calls[0][0][0]
    assert "even-horizontal" in layout_cmd


@patch('vuln_recorder.terminal.time.sleep')
@patch('vuln_recorder.terminal.subprocess.run')
@patch('vuln_recorder.terminal.subprocess.Popen')
def test_custom_layout_skips_select_layout(mock_popen, mock_run, mock_sleep):
    mock_popen.return_value = MagicMock()
    mock_run.return_value = MagicMock()

    panes = [{'name': 'a'}, {'name': 'b'}]
    term = TerminalOrchestrator(":99", "test-session", panes, "custom")
    term.create_session()

    layout_calls = [c for c in mock_run.call_args_list if 'select-layout' in str(c)]
    assert len(layout_calls) == 0


@patch('vuln_recorder.terminal.time.sleep')
@patch('vuln_recorder.terminal.subprocess.run')
@patch('vuln_recorder.terminal.subprocess.Popen')
def test_send_keys_targets_correct_pane(mock_popen, mock_run, mock_sleep):
    mock_popen.return_value = MagicMock()
    mock_run.return_value = MagicMock()

    panes = [{'name': 'env'}, {'name': 'attacker'}, {'name': 'victim'}]
    term = TerminalOrchestrator(":99", "test-session", panes, "custom")
    term.create_session()

    mock_run.reset_mock()
    term.send_keys("victim", "echo pwned")

    mock_run.assert_called_once_with(
        ["tmux", "send-keys", "-t", "test-session:0.2", "echo pwned", "Enter"]
    )


@patch('vuln_recorder.terminal.time.sleep')
@patch('vuln_recorder.terminal.subprocess.run')
@patch('vuln_recorder.terminal.subprocess.Popen')
def test_send_keys_first_pane(mock_popen, mock_run, mock_sleep):
    mock_popen.return_value = MagicMock()
    mock_run.return_value = MagicMock()

    panes = [{'name': 'env'}, {'name': 'attacker'}]
    term = TerminalOrchestrator(":99", "test-session", panes, "custom")
    term.create_session()

    mock_run.reset_mock()
    term.send_keys("env", "whoami")

    mock_run.assert_called_once_with(
        ["tmux", "send-keys", "-t", "test-session:0.0", "whoami", "Enter"]
    )


@patch('vuln_recorder.terminal.subprocess.run')
def test_destroy_session(mock_run):
    mock_run.return_value = MagicMock()
    term = TerminalOrchestrator(":99", "test-session", [], "custom")
    term.destroy_session()
    mock_run.assert_called_once_with(
        ["tmux", "kill-session", "-t", "test-session"]
    )
