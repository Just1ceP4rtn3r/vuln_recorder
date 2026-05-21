from unittest.mock import patch, MagicMock
from vuln_recorder.recorder import Recorder


@patch('vuln_recorder.recorder.subprocess.Popen')
def test_start_launches_ffmpeg(mock_popen):
    mock_popen.return_value = MagicMock()
    recorder = Recorder(":99", "/tmp/test.mp4", "1920x1080", fps=30)
    recorder.start()
    cmd = mock_popen.call_args[0][0]
    assert cmd[0] == "ffmpeg"
    assert "-y" in cmd
    assert "x11grab" in cmd
    assert "1920x1080" in cmd
    assert "30" in cmd
    assert ":99" in cmd
    assert "libx264" in cmd
    assert "medium" in cmd
    assert "18" in cmd
    assert "/tmp/test.mp4" in cmd
    kwargs = mock_popen.call_args[1]
    assert kwargs['stdin'] is not None


@patch('vuln_recorder.recorder.subprocess.Popen')
def test_stop_sends_q(mock_popen):
    mock_process = MagicMock()
    mock_process.poll.return_value = None
    mock_process.stdin = MagicMock()
    mock_popen.return_value = mock_process
    recorder = Recorder(":99", "/tmp/test.mp4", "1920x1080")
    recorder.start()
    recorder.stop()
    mock_process.stdin.write.assert_called_with(b'q')
    mock_process.stdin.flush.assert_called_once()
    mock_process.wait.assert_called_once()


@patch('vuln_recorder.recorder.subprocess.Popen')
def test_stop_without_start_is_noop(mock_popen):
    recorder = Recorder(":99", "/tmp/test.mp4", "1920x1080")
    recorder.stop()  # Should not raise


@patch('vuln_recorder.recorder.subprocess.Popen')
def test_is_recording_before_start(mock_popen):
    recorder = Recorder(":99", "/tmp/test.mp4", "1920x1080")
    assert recorder.is_recording() is False


@patch('vuln_recorder.recorder.subprocess.Popen')
def test_is_recording_after_start(mock_popen):
    mock_process = MagicMock()
    mock_process.poll.return_value = None
    mock_popen.return_value = mock_process
    recorder = Recorder(":99", "/tmp/test.mp4", "1920x1080")
    recorder.start()
    assert recorder.is_recording() is True


@patch('vuln_recorder.recorder.subprocess.Popen')
def test_is_recording_after_stop(mock_popen):
    mock_process = MagicMock()
    mock_process.poll.return_value = None
    mock_process.stdin = MagicMock()
    mock_popen.return_value = mock_process
    recorder = Recorder(":99", "/tmp/test.mp4", "1920x1080")
    recorder.start()
    recorder.stop()
    mock_process.poll.return_value = 0
    assert recorder.is_recording() is False


@patch('vuln_recorder.recorder.subprocess.Popen')
def test_custom_fps_in_command(mock_popen):
    mock_popen.return_value = MagicMock()
    recorder = Recorder(":99", "/tmp/test.mp4", "1920x1080", fps=60)
    recorder.start()
    cmd = mock_popen.call_args[0][0]
    assert "60" in cmd


@patch('vuln_recorder.recorder.subprocess.Popen')
def test_stop_when_process_already_exited(mock_popen):
    mock_process = MagicMock()
    mock_process.poll.return_value = 0  # Already exited
    mock_popen.return_value = mock_process
    recorder = Recorder(":99", "/tmp/test.mp4", "1920x1080")
    recorder.start()
    recorder.stop()  # Should not try to write to stdin
    mock_process.stdin.write.assert_not_called()


@patch('vuln_recorder.recorder.subprocess.Popen')
def test_double_start_replaces_process(mock_popen):
    mock_popen.return_value = MagicMock()
    recorder = Recorder(":99", "/tmp/test.mp4", "1920x1080")
    recorder.start()
    recorder.start()
    assert mock_popen.call_count == 2


@patch('vuln_recorder.recorder.subprocess.Popen')
def test_output_path_in_command(mock_popen):
    mock_popen.return_value = MagicMock()
    recorder = Recorder(":99", "/data/videos/test.mp4", "1280x720")
    recorder.start()
    cmd = mock_popen.call_args[0][0]
    assert "/data/videos/test.mp4" in cmd


@patch('vuln_recorder.recorder.subprocess.Popen')
def test_stdin_pipe_set(mock_popen):
    mock_popen.return_value = MagicMock()
    import subprocess
    recorder = Recorder(":99", "/tmp/test.mp4", "1920x1080")
    recorder.start()
    kwargs = mock_popen.call_args[1]
    assert kwargs['stdin'] == subprocess.PIPE
    assert kwargs['stdout'] == subprocess.DEVNULL
    assert kwargs['stderr'] == subprocess.DEVNULL
