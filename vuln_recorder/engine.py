import atexit
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .scenario import Scenario
from .xvfb import XvfbManager
from .recorder import Recorder
from .terminal import TerminalOrchestrator


class Engine:
    def __init__(self, scenario_path: str):
        self.scenario_path = scenario_path
        self.xvfb = None
        self.recorder = None
        self.terminal = None

    def run(self) -> str:
        scenario = Scenario(self.scenario_path)
        data = scenario.load()

        self.check_dependencies()

        scenario_dir = Path(self.scenario_path).resolve().parent
        run_dir = scenario_dir / "record"
        run_dir.mkdir(parents=True, exist_ok=True)

        shutil.copy(self.scenario_path, run_dir / "scenario.yaml")

        display_cfg = data['display']
        self.xvfb = XvfbManager(
            width=display_cfg['width'],
            height=display_cfg['height'],
            color_depth=display_cfg.get('color_depth', 24),
        )
        display = self.xvfb.start()
        atexit.register(self.cleanup)

        try:
            resolution = f"{display_cfg['width']}x{display_cfg['height']}"
            output_path = str(run_dir / "recording.mp4")
            self.recorder = Recorder(display, output_path, resolution)
            self.recorder.start()
            time.sleep(1)

            tmux_cfg = data['tmux']
            self.terminal = TerminalOrchestrator(
                display, tmux_cfg['session_name'],
                tmux_cfg['panes'], tmux_cfg['layout'],
            )
            self.terminal.create_session()

            captured_steps = []
            for i, step in enumerate(data['steps']):
                self.terminal.send_keys(step['pane'], step['command'])
                time.sleep(step['wait'])
                output = self.terminal.capture_pane(step['pane'])
                captured_steps.append({
                    'step': i,
                    'pane': step['pane'],
                    'command': step['command'],
                    'output': output,
                })

            outputs_data = {
                'scenario': data['name'],
                'captured_at': datetime.now(timezone.utc).isoformat(),
                'steps': captured_steps,
            }
            outputs_file = run_dir / "scenario-outputs.yaml"
            with open(outputs_file, 'w') as f:
                yaml.dump(outputs_data, f, default_flow_style=False, allow_unicode=True)

            self.recorder.stop()
            self.xvfb.stop()
        except Exception:
            self.cleanup()
            raise

        return str(run_dir)

    def check_dependencies(self):
        missing = []
        for tool in ['Xvfb', 'ffmpeg', 'xterm', 'tmux']:
            if not shutil.which(tool):
                missing.append(tool)
        if missing:
            raise RuntimeError(f"Missing dependencies: {', '.join(missing)}")

    def cleanup(self):
        if self.recorder:
            self.recorder.stop()
        if self.terminal:
            self.terminal.destroy_session()
        if self.xvfb:
            self.xvfb.stop()
