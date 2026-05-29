import subprocess


class Recorder:
    def __init__(self, display: str, output_path: str, resolution: str, fps: int = 30):
        self.display = display
        self.output_path = output_path
        self.resolution = resolution
        self.fps = fps
        self._process = None
        self._stderr_file = None

    def start(self):
        import time

        cmd = [
            "ffmpeg", "-y",
            "-f", "x11grab",
            "-video_size", self.resolution,
            "-framerate", str(self.fps),
            "-i", self.display,
            "-c:v", "libx264",
            "-profile:v", "high",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            "-crf", "18",
            self.output_path,
        ]
        self._stderr_file = open(self.output_path + ".log", "w")
        self._process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=self._stderr_file,
        )
        time.sleep(0.5)
        if self._process.poll() is not None:
            self._stderr_file.close()
            raise RuntimeError(
                f"FFmpeg exited immediately (code {self._process.returncode}). "
                f"Check {self.output_path}.log for details."
            )

    def stop(self):
        if self._process and self._process.poll() is None:
            self._process.stdin.write(b'q')
            self._process.stdin.flush()
            self._process.wait()
        self._process = None
        if self._stderr_file:
            self._stderr_file.close()
            self._stderr_file = None

    def is_recording(self) -> bool:
        return self._process is not None and self._process.poll() is None
