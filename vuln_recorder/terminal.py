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
            "-e", "tmux", "-L", self._socket_name,
            "new-session", "-s", self.session_name,
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

        for i in range(1, len(self.panes)):
            subprocess.run(self._tmux("split-window", "-t", self.session_name))
            time.sleep(0.2)

        if self.layout != "custom":
            subprocess.run(self._tmux("select-layout", "-t", self.session_name, self.layout))

        result = subprocess.run(
            self._tmux("list-panes", "-t", self.session_name, "-F", "#{pane_index}"),
            capture_output=True, text=True,
        )
        pane_indices = [line for line in result.stdout.strip().split('\n') if line]
        for i, pane in enumerate(self.panes):
            self._pane_map[pane['name']] = pane_indices[i]

    def send_keys(self, pane_name: str, command: str):
        if pane_name not in self._pane_map:
            raise ValueError(f"Unknown pane: '{pane_name}'. Available: {list(self._pane_map.keys())}")
        subprocess.run(self._tmux(
            "send-keys",
            "-t", f"{self.session_name}.{self._pane_map[pane_name]}",
            command, "Enter",
        ))

    def destroy_session(self):
        subprocess.run(self._tmux("kill-session", "-t", self.session_name))
