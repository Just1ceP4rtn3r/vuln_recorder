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


def test_load_unicode_fields(tmp_path):
    data = {
        'name': 'SQL注入漏洞',
        'description': '测试中文描述 🎉',
        'display': {'width': 1920, 'height': 1080},
        'tmux': {
            'session_name': '测试会话',
            'layout': 'even-horizontal',
            'panes': [{'name': '攻击者'}, {'name': '受害者'}],
        },
        'steps': [
            {'pane': '攻击者', 'command': 'echo 漏洞利用', 'wait': 2},
            {'pane': '受害者', 'command': 'echo 被攻击', 'wait': 1},
        ],
    }
    yaml_file = tmp_path / 'unicode.yaml'
    with open(yaml_file, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True)
    s = Scenario(str(yaml_file))
    result = s.load()
    assert result['name'] == 'SQL注入漏洞'
    assert result['steps'][0]['pane'] == '攻击者'


def test_load_with_output_dir(tmp_path):
    data = {
        'name': 'Test',
        'description': 'desc',
        'output_dir': 'my-custom-dir',
        'display': {'width': 800, 'height': 600},
        'tmux': {
            'session_name': 's',
            'layout': 'custom',
            'panes': [{'name': 'a'}],
        },
        'steps': [{'pane': 'a', 'command': 'echo', 'wait': 1}],
    }
    yaml_file = tmp_path / 'test.yaml'
    with open(yaml_file, 'w') as f:
        yaml.dump(data, f)
    s = Scenario(str(yaml_file))
    result = s.load()
    assert result['output_dir'] == 'my-custom-dir'


def test_load_comment_commands_valid(tmp_path):
    data = {
        'name': 'Test',
        'description': 'desc',
        'display': {'width': 1920, 'height': 1080},
        'tmux': {
            'session_name': 's',
            'layout': 'custom',
            'panes': [{'name': 'a'}],
        },
        'steps': [
            {'pane': 'a', 'command': '# This is a comment', 'wait': 1},
            {'pane': 'a', 'command': 'echo hello', 'wait': 1},
            {'pane': 'a', 'command': '# === Section Title ===', 'wait': 2},
        ],
    }
    yaml_file = tmp_path / 'comments.yaml'
    with open(yaml_file, 'w') as f:
        yaml.dump(data, f)
    s = Scenario(str(yaml_file))
    result = s.load()
    assert result['steps'][0]['command'] == '# This is a comment'
    assert result['steps'][2]['command'] == '# === Section Title ==='


def test_load_explicit_color_depth(tmp_path):
    data = {
        'name': 'Test',
        'description': 'desc',
        'display': {'width': 1920, 'height': 1080, 'color_depth': 16},
        'tmux': {
            'session_name': 's',
            'layout': 'custom',
            'panes': [{'name': 'a'}],
        },
        'steps': [{'pane': 'a', 'command': 'echo', 'wait': 1}],
    }
    yaml_file = tmp_path / 'test.yaml'
    with open(yaml_file, 'w') as f:
        yaml.dump(data, f)
    s = Scenario(str(yaml_file))
    result = s.load()
    assert result['display']['color_depth'] == 16


def test_load_multiple_step_errors_reported(tmp_path):
    data = {
        'name': 'Test',
        'description': 'desc',
        'display': {'width': 1920, 'height': 1080},
        'tmux': {
            'session_name': 's',
            'layout': 'custom',
            'panes': [{'name': 'a'}],
        },
        'steps': [
            {'pane': 'a', 'command': 'echo'},
            {'pane': 'bogus', 'command': 'echo', 'wait': 1},
            {'pane': 'a', 'wait': 1},
        ],
    }
    yaml_file = tmp_path / 'bad.yaml'
    with open(yaml_file, 'w') as f:
        yaml.dump(data, f)
    s = Scenario(str(yaml_file))
    with pytest.raises(ValueError) as exc_info:
        s.load()
    msg = str(exc_info.value)
    assert "missing 'wait'" in msg
    assert "pane 'bogus' not found" in msg
    assert "missing 'command'" in msg


def test_load_missing_panes_list(tmp_path):
    data = {
        'name': 'Test',
        'description': 'desc',
        'display': {'width': 1920, 'height': 1080},
        'tmux': {'session_name': 's', 'layout': 'custom', 'panes': []},
        'steps': [],
    }
    yaml_file = tmp_path / 'bad.yaml'
    with open(yaml_file, 'w') as f:
        yaml.dump(data, f)
    s = Scenario(str(yaml_file))
    with pytest.raises(ValueError, match="non-empty list"):
        s.load()


def test_load_nonexistent_file():
    s = Scenario('/nonexistent/path/scenario.yaml')
    with pytest.raises(FileNotFoundError):
        s.load()


def test_load_many_panes_and_steps(tmp_path):
    panes = [{'name': f'pane-{i}'} for i in range(8)]
    steps = [{'pane': f'pane-{i}', 'command': f'cmd-{i}', 'wait': 1} for i in range(8)]
    data = {
        'name': 'Many Panes',
        'description': 'stress test',
        'display': {'width': 1920, 'height': 1080},
        'tmux': {
            'session_name': 'big',
            'layout': 'custom',
            'panes': panes,
        },
        'steps': steps,
    }
    yaml_file = tmp_path / 'big.yaml'
    with open(yaml_file, 'w') as f:
        yaml.dump(data, f)
    s = Scenario(str(yaml_file))
    result = s.load()
    assert len(result['tmux']['panes']) == 8
    assert len(result['steps']) == 8
