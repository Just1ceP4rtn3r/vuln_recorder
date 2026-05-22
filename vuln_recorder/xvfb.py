import os
import signal
import subprocess
import time


class XvfbManager:
    def __init__(self, display=":99", width=1920, height=1080, color_depth=24):
        self.display = display
        self.width = width
        self.height = height
        self.color_depth = color_depth
        self._process = None

    def start(self) -> str:
        display_num = int(self.display.lstrip(':'))
        for _ in range(100):
            lock_file = f"/tmp/.X{display_num}-lock"
            if os.path.exists(lock_file):
                display_num += 1
                continue
            break
        else:
            raise RuntimeError("Could not find an available display after 100 attempts")

        self.display = f":{display_num}"
        cmd = [
            "Xvfb", self.display,
            "-screen", "0", f"{self.width}x{self.height}x{self.color_depth}",
            "-ac", "+extension", "GLX", "+render", "-noreset",
        ]
        self._process = subprocess.Popen(cmd)
        for _ in range(50):
            result = subprocess.run(
                ["xdpyinfo", "-display", self.display],
                capture_output=True,
            )
            if result.returncode == 0:
                break
            time.sleep(0.1)
        else:
            self.stop()
            raise RuntimeError(f"Xvfb display {self.display} not ready after 5s")
        return self.display

    def stop(self):
        if self._process and self._process.poll() is None:
            self._process.send_signal(signal.SIGTERM)
            self._process.wait()
        self._process = None

    def get_display(self) -> str:
        return self.display
