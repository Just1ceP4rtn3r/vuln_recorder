import subprocess
import time


class TerminalOrchestrator:
    def __init__(self, display: str, session_name: str, panes: list, layout: str):
        self.display = display
        self.session_name = session_name
        self.panes = panes
        self.layout = layout
        self._pane_map = {}

    def create_session(self):
        subprocess.Popen([
            "xterm", "-display", self.display,
            "-e", "tmux", "new-session", "-s", self.session_name,
        ])
        time.sleep(0.5)

        for i in range(1, len(self.panes)):
            subprocess.run([
                "tmux", "split-window", "-t", self.session_name,
            ])
            time.sleep(0.2)

        if self.layout != "custom":
            subprocess.run([
                "tmux", "select-layout", "-t", self.session_name, self.layout,
            ])

        for i, pane in enumerate(self.panes):
            self._pane_map[pane['name']] = i

    def send_keys(self, pane_name: str, command: str):
        if pane_name not in self._pane_map:
            raise ValueError(f"Unknown pane: '{pane_name}'. Available: {list(self._pane_map.keys())}")
        pane_index = self._pane_map[pane_name]
        subprocess.run([
            "tmux", "send-keys",
            "-t", f"{self.session_name}:0.{pane_index}",
            command, "Enter",
        ])

    def destroy_session(self):
        subprocess.run([
            "tmux", "kill-session", "-t", self.session_name,
        ])
