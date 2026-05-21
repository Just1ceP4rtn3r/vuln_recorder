import pytest
import yaml
from pathlib import Path
from vuln_recorder.scenario import Scenario


@pytest.fixture
def valid_yaml(tmp_path):
    data = {
        'name': 'Test Vulnerability',
        'description': 'A test scenario',
        'display': {'width': 1920, 'height': 1080},
        'tmux': {
            'session_name': 'test-session',
            'layout': 'even-horizontal',
            'panes': [
                {'name': 'attacker'},
                {'name': 'victim'},
            ],
        },
        'steps': [
            {'pane': 'attacker', 'command': 'echo hello', 'wait': 2},
            {'pane': 'victim', 'command': 'echo world', 'wait': 1},
        ],
    }
    yaml_file = tmp_path / 'test.yaml'
    with open(yaml_file, 'w') as f:
        yaml.dump(data, f)
    return str(yaml_file)


def test_load_valid_scenario(valid_yaml):
    s = Scenario(valid_yaml)
    data = s.load()
    assert data['name'] == 'Test Vulnerability'
    assert data['description'] == 'A test scenario'
    assert len(data['steps']) == 2
    assert data['display']['width'] == 1920


def test_load_missing_name(tmp_path):
    yaml_file = tmp_path / 'bad.yaml'
    with open(yaml_file, 'w') as f:
        yaml.dump({'description': 'x', 'display': {}, 'tmux': {}, 'steps': []}, f)
    s = Scenario(str(yaml_file))
    with pytest.raises(ValueError, match="Missing required field: name"):
        s.load()


def test_load_missing_description(tmp_path):
    yaml_file = tmp_path / 'bad.yaml'
    with open(yaml_file, 'w') as f:
        yaml.dump({'name': 'x', 'display': {}, 'tmux': {}, 'steps': []}, f)
    s = Scenario(str(yaml_file))
    with pytest.raises(ValueError, match="Missing required field: description"):
        s.load()


def test_load_missing_display_subfield(tmp_path):
    data = {
        'name': 'Test',
        'description': 'desc',
        'display': {'width': 1920},
        'tmux': {
            'session_name': 's',
            'layout': 'even-horizontal',
            'panes': [{'name': 'a'}],
        },
        'steps': [{'pane': 'a', 'command': 'echo', 'wait': 1}],
    }
    yaml_file = tmp_path / 'bad.yaml'
    with open(yaml_file, 'w') as f:
        yaml.dump(data, f)
    s = Scenario(str(yaml_file))
    with pytest.raises(ValueError, match="display.height"):
        s.load()


def test_load_missing_tmux_subfield(tmp_path):
    data = {
        'name': 'Test',
        'description': 'desc',
        'display': {'width': 1920, 'height': 1080},
        'tmux': {'session_name': 's'},
        'steps': [],
    }
    yaml_file = tmp_path / 'bad.yaml'
    with open(yaml_file, 'w') as f:
        yaml.dump(data, f)
    s = Scenario(str(yaml_file))
    with pytest.raises(ValueError, match="tmux.layout"):
        s.load()


def test_load_invalid_pane_reference(tmp_path):
    data = {
        'name': 'Test',
        'description': 'desc',
        'display': {'width': 1920, 'height': 1080},
        'tmux': {
            'session_name': 's',
            'layout': 'even-horizontal',
            'panes': [{'name': 'attacker'}],
        },
        'steps': [{'pane': 'nonexistent', 'command': 'echo', 'wait': 1}],
    }
    yaml_file = tmp_path / 'bad.yaml'
    with open(yaml_file, 'w') as f:
        yaml.dump(data, f)
    s = Scenario(str(yaml_file))
    with pytest.raises(ValueError, match="pane 'nonexistent' not found"):
        s.load()


def test_load_missing_step_field(tmp_path):
    data = {
        'name': 'Test',
        'description': 'desc',
        'display': {'width': 1920, 'height': 1080},
        'tmux': {
            'session_name': 's',
            'layout': 'even-horizontal',
            'panes': [{'name': 'a'}],
        },
        'steps': [{'pane': 'a', 'command': 'echo'}],
    }
    yaml_file = tmp_path / 'bad.yaml'
    with open(yaml_file, 'w') as f:
        yaml.dump(data, f)
    s = Scenario(str(yaml_file))
    with pytest.raises(ValueError, match="missing 'wait'"):
        s.load()


def test_load_default_color_depth(tmp_path):
    data = {
        'name': 'Test',
        'description': 'desc',
        'display': {'width': 1920, 'height': 1080},
        'tmux': {
            'session_name': 's',
            'layout': 'even-horizontal',
            'panes': [{'name': 'a'}],
        },
        'steps': [{'pane': 'a', 'command': 'echo', 'wait': 1}],
    }
    yaml_file = tmp_path / 'test.yaml'
    with open(yaml_file, 'w') as f:
        yaml.dump(data, f)
    s = Scenario(str(yaml_file))
    result = s.load()
    assert result['display'].get('color_depth', 24) == 24


def test_load_empty_yaml(tmp_path):
    yaml_file = tmp_path / 'empty.yaml'
    yaml_file.write_text('')
    s = Scenario(str(yaml_file))
    with pytest.raises(ValueError, match="empty"):
        s.load()
