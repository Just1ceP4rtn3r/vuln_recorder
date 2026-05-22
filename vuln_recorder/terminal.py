import subprocess
import time


class TerminalOrchestrator:
    def __init__(self, display: str, session_name: str, panes: list, layout: str):
        self.display = display
        self.session_name = session_name
        self.panes = panes
        self.layout = layout
        self._pane_map = {}
        self._socket_name = f"vr-{session_name}"

    def _tmux(self, *args):
        return ["tmux", "-L", self._socket_name] + list(args)

    def create_session(self):
        subprocess.Popen([
            "xterm", "-display", self.display,
            "-maximized", "-fa", "Monospace", "-fs", "12",
            "-e", "tmux", "-L", self._socket_name,
            "new-session", "-s", self.session_name, "/bin/bash",
        ])
        for _ in range(50):
            result = subprocess.run(
                self._tmux("has-session", "-t", self.session_name),
                capture_output=True,
            )
            if result.returncode == 0:
                break
            time.sleep(0.1)
        else:
            raise RuntimeError(f"Timed out waiting for tmux session '{self.session_name}'")

        subprocess.run(self._tmux("set-option", "-t", self.session_name, "default-shell", "/bin/bash"))

        for i in range(1, len(self.panes)):
            subprocess.run(self._tmux("split-window", "-h", "-t", self.session_name))
            time.sleep(0.2)

        if self.layout != "custom":
            subprocess.run(self._tmux("select-layout", "-t", self.session_name, self.layout))

        subprocess.run(self._tmux("set-option", "-t", self.session_name, "pane-border-status", "top"))
        subprocess.run(self._tmux("set-option", "-t", self.session_name, "pane-border-format", " #{pane_title} "))

        result = subprocess.run(
            self._tmux("list-panes", "-t", self.session_name, "-F", "#{pane_index}"),
            capture_output=True, text=True,
        )
        pane_indices = [line for line in result.stdout.strip().split('\n') if line]
        for i, pane in enumerate(self.panes):
            self._pane_map[pane['name']] = pane_indices[i]
        for pane_name, pane_idx in self._pane_map.items():
            subprocess.run(self._tmux("select-pane", "-t", f"{self.session_name}.{pane_idx}", "-T", pane_name))

    def send_keys(self, pane_name: str, command: str):
        if pane_name not in self._pane_map:
            raise ValueError(f"Unknown pane: '{pane_name}'. Available: {list(self._pane_map.keys())}")
        subprocess.run(self._tmux(
            "send-keys",
            "-t", f"{self.session_name}.{self._pane_map[pane_name]}",
            command, "Enter",
        ))

    def capture_pane(self, pane_name: str) -> str:
        if pane_name not in self._pane_map:
            raise ValueError(f"Unknown pane: '{pane_name}'. Available: {list(self._pane_map.keys())}")
        result = subprocess.run(
            self._tmux(
                "capture-pane",
                "-t", f"{self.session_name}.{self._pane_map[pane_name]}",
                "-p", "-S", "-100",
            ),
            capture_output=True, text=True,
        )
        return result.stdout.rstrip()

    def set_pane_style(self, pane_name: str, style: str):
        if pane_name not in self._pane_map:
            raise ValueError(f"Unknown pane: '{pane_name}'. Available: {list(self._pane_map.keys())}")
        subprocess.run(self._tmux(
            "set-option", "-p",
            "-t", f"{self.session_name}.{self._pane_map[pane_name]}",
            "window-style", style,
        ))

    def destroy_session(self):
        subprocess.run(self._tmux("kill-session", "-t", self.session_name))
