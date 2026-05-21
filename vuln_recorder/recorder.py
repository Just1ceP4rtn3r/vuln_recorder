import subprocess


class Recorder:
    def __init__(self, display: str, output_path: str, resolution: str, fps: int = 30):
        self.display = display
        self.output_path = output_path
        self.resolution = resolution
        self.fps = fps
        self._process = None

    def start(self):
        cmd = [
            "ffmpeg", "-y",
            "-f", "x11grab",
            "-video_size", self.resolution,
            "-framerate", str(self.fps),
            "-i", self.display,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",
            self.output_path,
        ]
        self._process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def stop(self):
        if self._process and self._process.poll() is None:
            self._process.stdin.write(b'q')
            self._process.stdin.flush()
            self._process.wait()
        self._process = None

    def is_recording(self) -> bool:
        return self._process is not None and self._process.poll() is None
