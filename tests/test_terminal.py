from unittest.mock import patch, MagicMock
from vuln_recorder.terminal import TerminalOrchestrator


def _mock_run_factory(stdout=""):
    """Create mock subprocess.run returning returncode=0 and given stdout."""
    def run_impl(*args, **kwargs):
        result = MagicMock()
        result.returncode = 0
        result.stdout = stdout
        return result
    return run_impl


@patch('vuln_recorder.terminal.time.sleep')
@patch('vuln_recorder.terminal.subprocess.run', side_effect=_mock_run_factory(stdout="1\n2\n3"))
@patch('vuln_recorder.terminal.subprocess.Popen')
def test_create_session_starts_xterm_with_tmux(mock_popen, mock_run, mock_sleep):
    mock_popen.return_value = MagicMock()

    panes = [{'name': 'env'}, {'name': 'attacker'}, {'name': 'victim'}]
    term = TerminalOrchestrator(":99", "test-session", panes, "even-horizontal")
    term.create_session()

    mock_popen.assert_called_once()
    xterm_cmd = mock_popen.call_args[0][0]
    assert xterm_cmd[0] == "xterm"
    assert "-display" in xterm_cmd
    assert ":99" in xterm_cmd
    assert "-maximized" in xterm_cmd
    assert "-fa" in xterm_cmd
    assert "Monospace" in xterm_cmd
    assert "-fs" in xterm_cmd
    assert "14" in xterm_cmd
    assert "tmux" in xterm_cmd
    assert "-L" in xterm_cmd
    assert "vr-test-session" in xterm_cmd
    assert "new-session" in xterm_cmd
    assert "test-session" in xterm_cmd


@patch('vuln_recorder.terminal.time.sleep')
@patch('vuln_recorder.terminal.subprocess.run', side_effect=_mock_run_factory(stdout="1\n2\n3"))
@patch('vuln_recorder.terminal.subprocess.Popen')
def test_create_session_splits_panes(mock_popen, mock_run, mock_sleep):
    mock_popen.return_value = MagicMock()

    panes = [{'name': 'env'}, {'name': 'attacker'}, {'name': 'victim'}]
    term = TerminalOrchestrator(":99", "test-session", panes, "custom")
    term.create_session()

    split_calls = [c for c in mock_run.call_args_list if 'split-window' in str(c)]
    assert len(split_calls) == 2  # 3 panes = 2 splits


@patch('vuln_recorder.terminal.time.sleep')
@patch('vuln_recorder.terminal.subprocess.run', side_effect=_mock_run_factory(stdout="1\n2"))
@patch('vuln_recorder.terminal.subprocess.Popen')
def test_create_session_applies_layout(mock_popen, mock_run, mock_sleep):
    mock_popen.return_value = MagicMock()

    panes = [{'name': 'a'}, {'name': 'b'}]
    term = TerminalOrchestrator(":99", "test-session", panes, "even-horizontal")
    term.create_session()

    layout_calls = [c for c in mock_run.call_args_list if 'select-layout' in str(c)]
    assert len(layout_calls) == 1
    layout_cmd = layout_calls[0][0][0]
    assert "even-horizontal" in layout_cmd


@patch('vuln_recorder.terminal.time.sleep')
@patch('vuln_recorder.terminal.subprocess.run', side_effect=_mock_run_factory(stdout="1\n2"))
@patch('vuln_recorder.terminal.subprocess.Popen')
def test_custom_layout_skips_select_layout(mock_popen, mock_run, mock_sleep):
    mock_popen.return_value = MagicMock()

    panes = [{'name': 'a'}, {'name': 'b'}]
    term = TerminalOrchestrator(":99", "test-session", panes, "custom")
    term.create_session()

    layout_calls = [c for c in mock_run.call_args_list if 'select-layout' in str(c)]
    assert len(layout_calls) == 0


@patch('vuln_recorder.terminal.time.sleep')
@patch('vuln_recorder.terminal.subprocess.run', side_effect=_mock_run_factory(stdout="1\n2\n3"))
@patch('vuln_recorder.terminal.subprocess.Popen')
def test_send_keys_targets_correct_pane(mock_popen, mock_run, mock_sleep):
    mock_popen.return_value = MagicMock()

    panes = [{'name': 'env'}, {'name': 'attacker'}, {'name': 'victim'}]
    term = TerminalOrchestrator(":99", "test-session", panes, "custom")
    term.create_session()

    mock_run.reset_mock()
    mock_run.side_effect = _mock_run_factory(stdout="")
    term.send_keys("victim", "echo pwned")

    mock_run.assert_called_once_with(
        ["tmux", "-L", "vr-test-session", "send-keys",
         "-t", "test-session.3", "echo pwned", "Enter"]
    )


@patch('vuln_recorder.terminal.time.sleep')
@patch('vuln_recorder.terminal.subprocess.run', side_effect=_mock_run_factory(stdout="1\n2"))
@patch('vuln_recorder.terminal.subprocess.Popen')
def test_send_keys_first_pane(mock_popen, mock_run, mock_sleep):
    mock_popen.return_value = MagicMock()

    panes = [{'name': 'env'}, {'name': 'attacker'}]
    term = TerminalOrchestrator(":99", "test-session", panes, "custom")
    term.create_session()

    mock_run.reset_mock()
    mock_run.side_effect = _mock_run_factory(stdout="")
    term.send_keys("env", "whoami")

    mock_run.assert_called_once_with(
        ["tmux", "-L", "vr-test-session", "send-keys",
         "-t", "test-session.1", "whoami", "Enter"]
    )


@patch('vuln_recorder.terminal.subprocess.run')
def test_destroy_session(mock_run):
    mock_run.return_value = MagicMock()
    term = TerminalOrchestrator(":99", "test-session", [], "custom")
    term.destroy_session()
    mock_run.assert_called_once_with(
        ["tmux", "-L", "vr-test-session", "kill-session", "-t", "test-session"]
    )


@patch('vuln_recorder.terminal.time.sleep')
@patch('vuln_recorder.terminal.subprocess.run', side_effect=_mock_run_factory(stdout="1"))
@patch('vuln_recorder.terminal.subprocess.Popen')
def test_single_pane_no_splits(mock_popen, mock_run, mock_sleep):
    mock_popen.return_value = MagicMock()

    panes = [{'name': 'only'}]
    term = TerminalOrchestrator(":99", "test-session", panes, "custom")
    term.create_session()

    split_calls = [c for c in mock_run.call_args_list if 'split-window' in str(c)]
    assert len(split_calls) == 0


@patch('vuln_recorder.terminal.time.sleep')
@patch('vuln_recorder.terminal.subprocess.run', side_effect=_mock_run_factory(stdout="1\n2\n3\n4"))
@patch('vuln_recorder.terminal.subprocess.Popen')
def test_four_panes_three_splits(mock_popen, mock_run, mock_sleep):
    mock_popen.return_value = MagicMock()

    panes = [{'name': 'a'}, {'name': 'b'}, {'name': 'c'}, {'name': 'd'}]
    term = TerminalOrchestrator(":99", "test-session", panes, "custom")
    term.create_session()

    split_calls = [c for c in mock_run.call_args_list if 'split-window' in str(c)]
    assert len(split_calls) == 3


def test_send_keys_unknown_pane_raises():
    term = TerminalOrchestrator(":99", "test-session", [{'name': 'a'}], "custom")
    term._pane_map = {'a': 1}
    import pytest
    with pytest.raises(ValueError, match="Unknown pane: 'nonexistent'"):
        term.send_keys("nonexistent", "echo")


@patch('vuln_recorder.terminal.time.sleep')
@patch('vuln_recorder.terminal.subprocess.run', side_effect=_mock_run_factory(stdout="1\n2"))
@patch('vuln_recorder.terminal.subprocess.Popen')
def test_send_keys_comment_command(mock_popen, mock_run, mock_sleep):
    mock_popen.return_value = MagicMock()

    panes = [{'name': 'a'}, {'name': 'b'}]
    term = TerminalOrchestrator(":99", "test-session", panes, "custom")
    term.create_session()

    mock_run.reset_mock()
    mock_run.side_effect = _mock_run_factory(stdout="")
    term.send_keys("a", "# === Vulnerability Demo ===")

    mock_run.assert_called_once_with(
        ["tmux", "-L", "vr-test-session", "send-keys",
         "-t", "test-session.1", "# === Vulnerability Demo ===", "Enter"]
    )


@patch('vuln_recorder.terminal.time.sleep')
@patch('vuln_recorder.terminal.subprocess.run', side_effect=_mock_run_factory(stdout="1"))
@patch('vuln_recorder.terminal.subprocess.Popen')
def test_send_keys_special_chars(mock_popen, mock_run, mock_sleep):
    mock_popen.return_value = MagicMock()

    panes = [{'name': 'a'}]
    term = TerminalOrchestrator(":99", "test-session", panes, "custom")
    term.create_session()

    mock_run.reset_mock()
    mock_run.side_effect = _mock_run_factory(stdout="")
    term.send_keys("a", "echo 'hello world' | grep -i test")

    mock_run.assert_called_once_with(
        ["tmux", "-L", "vr-test-session", "send-keys",
         "-t", "test-session.1", "echo 'hello world' | grep -i test", "Enter"]
    )


@patch('vuln_recorder.terminal.time.sleep')
@patch('vuln_recorder.terminal.subprocess.run')
@patch('vuln_recorder.terminal.subprocess.Popen')
def test_create_session_timeout(mock_popen, mock_run, mock_sleep):
    import pytest
    mock_popen.return_value = MagicMock()

    def run_never_ready(*args, **kwargs):
        result = MagicMock()
        result.returncode = 1  # has-session always fails
        result.stdout = ""
        return result
    mock_run.side_effect = run_never_ready

    panes = [{'name': 'a'}]
    term = TerminalOrchestrator(":99", "test-session", panes, "custom")
    with pytest.raises(RuntimeError, match="Timed out"):
        term.create_session()


@patch('vuln_recorder.terminal.time.sleep')
@patch('vuln_recorder.terminal.subprocess.run', side_effect=_mock_run_factory(stdout="1\n2"))
@patch('vuln_recorder.terminal.subprocess.Popen')
def test_socket_name_derived_from_session(mock_popen, mock_run, mock_sleep):
    mock_popen.return_value = MagicMock()

    term = TerminalOrchestrator(":99", "my-session", [{'name': 'a'}], "custom")
    assert term._socket_name == "vr-my-session"
