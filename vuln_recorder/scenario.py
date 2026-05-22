import yaml
from pathlib import Path

REQUIRED_TOP_FIELDS = ['name', 'description', 'display', 'tmux', 'steps']
REQUIRED_DISPLAY_FIELDS = ['width', 'height']
REQUIRED_TMUX_FIELDS = ['session_name', 'panes']
REQUIRED_STEP_FIELDS = ['pane', 'command', 'wait']


class Scenario:
    def __init__(self, yaml_path: str):
        self.yaml_path = Path(yaml_path)

    def load(self) -> dict:
        with open(self.yaml_path) as f:
            data = yaml.safe_load(f)
        errors = Scenario.validate(data)
        if errors:
            raise ValueError(f"Invalid scenario: {'; '.join(errors)}")
        data['tmux'].setdefault('layout', 'main-horizontal')
        return data

    @staticmethod
    def validate(data: dict) -> list[str]:
        if data is None:
            return ["Scenario file is empty"]

        errors = []

        for field in REQUIRED_TOP_FIELDS:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        if errors:
            return errors

        for field in REQUIRED_DISPLAY_FIELDS:
            if field not in data['display']:
                errors.append(f"Missing display.{field}")

        for field in REQUIRED_TMUX_FIELDS:
            if field not in data['tmux']:
                errors.append(f"Missing tmux.{field}")

        if errors:
            return errors

        if not data['tmux']['panes'] or not isinstance(data['tmux']['panes'], list):
            errors.append("tmux.panes must be a non-empty list")
            return errors

        pane_names = [p.get('name') for p in data['tmux']['panes']]
        if None in pane_names:
            errors.append("Each tmux pane must have a 'name' field")
            return errors
        for i, step in enumerate(data['steps']):
            for field in REQUIRED_STEP_FIELDS:
                if field not in step:
                    errors.append(f"Step {i}: missing '{field}'")
            if 'pane' in step and step['pane'] not in pane_names:
                errors.append(
                    f"Step {i}: pane '{step['pane']}' not found in tmux.panes"
                )

        return errors
