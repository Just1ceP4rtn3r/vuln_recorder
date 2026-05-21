import signal
from unittest.mock import patch, MagicMock
from vuln_recorder.xvfb import XvfbManager


@patch('vuln_recorder.xvfb.time.sleep')
@patch('vuln_recorder.xvfb.subprocess.Popen')
@patch('vuln_recorder.xvfb.os.path.exists', return_value=False)
def test_start_launches_xvfb(mock_exists, mock_popen, mock_sleep):
    mock_popen.return_value = MagicMock()
    xvfb = XvfbManager(display=":99", width=1920, height=1080)
    display = xvfb.start()
    assert display == ":99"
    mock_popen.assert_called_once()
    cmd = mock_popen.call_args[0][0]
    assert cmd[0] == "Xvfb"
    assert ":99" in cmd
    assert "1920x1080x24" in cmd
    assert "-ac" in cmd
    assert "-noreset" in cmd


@patch('vuln_recorder.xvfb.time.sleep')
@patch('vuln_recorder.xvfb.subprocess.Popen')
@patch('vuln_recorder.xvfb.os.path.exists')
def test_start_auto_increments_display(mock_exists, mock_popen, mock_sleep):
    mock_exists.side_effect = lambda p: 'X99-lock' in p
    mock_popen.return_value = MagicMock()
    xvfb = XvfbManager(display=":99")
    display = xvfb.start()
    assert display == ":100"
    cmd = mock_popen.call_args[0][0]
    assert ":100" in cmd


@patch('vuln_recorder.xvfb.time.sleep')
@patch('vuln_recorder.xvfb.subprocess.Popen')
@patch('vuln_recorder.xvfb.os.path.exists', return_value=False)
def test_get_display(mock_exists, mock_popen, mock_sleep):
    mock_popen.return_value = MagicMock()
    xvfb = XvfbManager(display=":42")
    assert xvfb.get_display() == ":42"


@patch('vuln_recorder.xvfb.time.sleep')
@patch('vuln_recorder.xvfb.subprocess.Popen')
@patch('vuln_recorder.xvfb.os.path.exists', return_value=False)
def test_stop_sends_sigterm(mock_exists, mock_popen, mock_sleep):
    mock_process = MagicMock()
    mock_process.poll.return_value = None
    mock_popen.return_value = mock_process
    xvfb = XvfbManager()
    xvfb.start()
    xvfb.stop()
    mock_process.send_signal.assert_called_with(signal.SIGTERM)
    mock_process.wait.assert_called_once()


@patch('vuln_recorder.xvfb.time.sleep')
@patch('vuln_recorder.xvfb.subprocess.Popen')
@patch('vuln_recorder.xvfb.os.path.exists', return_value=False)
def test_stop_without_start_is_noop(mock_exists, mock_popen, mock_sleep):
    xvfb = XvfbManager()
    xvfb.stop()  # Should not raise


@patch('vuln_recorder.xvfb.time.sleep')
@patch('vuln_recorder.xvfb.subprocess.Popen')
@patch('vuln_recorder.xvfb.os.path.exists', return_value=False)
def test_stop_idempotent(mock_exists, mock_popen, mock_sleep):
    mock_process = MagicMock()
    mock_process.poll.return_value = None
    mock_popen.return_value = mock_process
    xvfb = XvfbManager()
    xvfb.start()
    xvfb.stop()
    xvfb.stop()  # Second call should be safe
    assert mock_process.send_signal.call_count == 1
