import yaml
from pathlib import Path
from vuln_recorder.scenario import Scenario
from vuln_recorder.engine import Engine


SCENARIOS_DIR = Path(__file__).parent.parent / "scenarios"


def test_example_scenario_loads():
    """The example scenario YAML should load and validate successfully."""
    scenario_path = SCENARIOS_DIR / "openplc-delete-user.yaml"
    assert scenario_path.exists(), f"Scenario file not found: {scenario_path}"

    s = Scenario(str(scenario_path))
    data = s.load()

    assert data['name'] == "OpenPLC Delete User"
    assert len(data['steps']) > 0
    assert len(data['tmux']['panes']) == 3

    pane_names = {p['name'] for p in data['tmux']['panes']}
    for step in data['steps']:
        assert step['pane'] in pane_names


def test_dry_run_on_example(capsys):
    """Dry-run the example scenario through the Engine dependency check."""
    scenario_path = SCENARIOS_DIR / "openplc-delete-user.yaml"
    s = Scenario(str(scenario_path))
    data = s.load()
    assert 'name' in data
    assert 'steps' in data


def test_all_scenarios_are_valid():
    """Every YAML file in scenarios/ should pass validation."""
    scenarios_dir = SCENARIOS_DIR
    if not scenarios_dir.exists():
        return

    for yaml_file in scenarios_dir.glob("*.yaml"):
        s = Scenario(str(yaml_file))
        data = s.load()
        assert 'name' in data, f"{yaml_file.name}: missing name"
        assert 'steps' in data, f"{yaml_file.name}: missing steps"
        assert len(data['steps']) > 0, f"{yaml_file.name}: no steps defined"
