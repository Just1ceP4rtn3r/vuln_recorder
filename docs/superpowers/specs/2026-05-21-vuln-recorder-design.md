# Vuln Recorder - 自动化漏洞验证录制工具设计文档

**日期**: 2026-05-21
**状态**: 已批准

## 概述

vuln-recorder 是一个 Python 工具，用于自动化漏洞验证过程并将其录制为 MP4 视频文件。工具通过 Xvfb 虚拟显示 + xterm + tmux 分屏 + ffmpeg 屏幕抓取的组合，在无头环境中生成包含多角色视角的漏洞验证视频证据。

## 架构

```
YAML 剧本 → 剧本引擎 → 终端编排器 → tmux send-keys (向各窗格注入命令)
                                     ↓
Xvfb :99 → xterm → tmux 分屏布局 → 视觉输出 (虚拟屏幕)
                                     ↓
                        ffmpeg X11grab → MP4 文件
```

### 组件

| 组件 | 职责 |
|------|------|
| `cli.py` | CLI 入口，解析命令行参数 |
| `engine.py` | 主控引擎，编排完整流程 |
| `xvfb.py` | Xvfb 虚拟显示的启动/停止 |
| `recorder.py` | ffmpeg 录制进程的启动/停止 |
| `terminal.py` | tmux 会话创建、分屏布局、命令注入 |
| `scenario.py` | YAML 剧本文件的解析和验证 |

### 执行流程

```
engine.run()
  ├── scenario.load(yaml_path)          # 解析剧本
  ├── check_dependencies()               # 检查 Xvfb, ffmpeg, xterm, tmux
  ├── xvfb.start(display, resolution)   # 启动虚拟显示
  ├── recorder.start(display, output)    # 启动 ffmpeg 录制
  ├── terminal.create_session(config)    # 创建 tmux 分屏会话
  ├── for step in steps:
  │     terminal.send_keys(pane, cmd)    # 向目标窗格发送命令
  │     time.sleep(step.wait)            # 固定等待
  ├── recorder.stop()                    # 等待 ffmpeg 正常关闭
  ├── xvfb.stop()                        # 关闭虚拟显示
  └── 输出录制文件路径
```

## 剧本文件格式

YAML 格式，每个漏洞场景一个文件。

```yaml
name: "漏洞名称"
description: "漏洞描述"
output_dir: "输出目录名"

display:
  width: 1920
  height: 1080
  color_depth: 24    # 默认 24

tmux:
  session_name: "session 名称"
  layout: "custom"   # 布局类型
  panes:
    - name: "environment"
      position: "top-left"
    - name: "attacker"
      position: "top-right"
    - name: "victim"
      position: "bottom"

steps:
  - pane: "目标窗格名称"
    command: "要执行的命令"
    wait: 3           # 等待秒数
```

### 剧本字段说明

**顶层字段**:
- `name` (必填): 漏洞名称，用于输出目录和日志
- `description` (必填): 漏洞描述
- `output_dir` (可选): 输出目录名，默认用 name 的 slug 化形式

**display 部分**:
- `width` (必填): 虚拟显示宽度
- `height` (必填): 虚拟显示高度
- `color_depth` (可选): 色深，默认 24

**tmux 部分**:
- `session_name` (必填): tmux 会话名
- `layout` (必填): 布局类型 (`custom`, `even-horizontal`, `even-vertical`, `main-horizontal`)
- `panes` (必填): 窗格列表，每个窗格有 `name` 和 `position`

**steps 部分**:
- `pane` (必填): 目标窗格名称，必须与 tmux.panes 中的 name 匹配
- `command` (必填): 要在窗格中执行的命令。以 `#` 开头的为注释行（显示但不执行）
- `wait` (必填): 命令执行后等待的秒数

## 项目结构

```
vuln-recorder/
├── vuln_recorder/
│   ├── __init__.py
│   ├── __main__.py         # python -m vuln_recorder 入口
│   ├── cli.py              # CLI (argparse)
│   ├── engine.py           # 主控引擎
│   ├── xvfb.py             # Xvfb 管理
│   ├── recorder.py         # ffmpeg 录制管理
│   ├── terminal.py         # tmux 终端编排
│   └── scenario.py         # YAML 剧本解析
├── scenarios/
│   └── openplc-delete-user.yaml   # 示例剧本
├── output/                  # 录制输出 (gitignored)
├── requirements.txt         # PyYAML
└── setup.py
```

## 模块详细设计

### xvfb.py

```python
class XvfbManager:
    def __init__(self, display=":99", width=1920, height=1080, color_depth=24):
        ...

    def start(self):
        """启动 Xvfb 进程。如果指定 display 已被占用，自动递增尝试下一个。"""
        # Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset
        # 检查 /tmp/.X99-lock 是否存在来判断占用

    def stop(self):
        """发送 SIGTERM 并等待进程退出。"""

    def get_display(self) -> str:
        """返回实际使用的 display 编号。"""
```

### recorder.py

```python
class Recorder:
    def __init__(self, display: str, output_path: str, resolution: str, fps: int = 30):
        ...

    def start(self):
        """启动 ffmpeg 录制进程。"""
        # ffmpeg -y -f x11grab -video_size {resolution} -framerate {fps}
        #   -i {display} -c:v libx264 -preset medium -crf 18 {output_path}
        # stdin=subprocess.PIPE (用于后续发送 'q' 停止)

    def stop(self):
        """向 ffmpeg stdin 发送 'q' 字符，等待进程正常退出。"""

    def is_recording(self) -> bool:
        """检查 ffmpeg 进程是否仍在运行。"""
```

### terminal.py

```python
class TerminalOrchestrator:
    def __init__(self, display: str, session_name: str, panes: list, layout: str):
        ...

    def create_session(self):
        """在虚拟显示上启动 xterm，在其中创建 tmux 会话并分屏。"""
        # 1. DISPLAY=:99 xterm -e "tmux new-session -s {session_name}" &
        # 2. 等待 tmux 会话就绪
        # 3. 根据 layout 和 panes 数量执行 tmux split-window
        # 4. 记录 pane index 与 pane name 的映射关系

    def send_keys(self, pane_name: str, command: str):
        """向指定窗格发送命令。"""
        # tmux send-keys -t {session_name}:0.{pane_index} '{command}' Enter

    def destroy_session(self):
        """销毁 tmux 会话。"""
        # tmux kill-session -t {session_name}
```

### scenario.py

```python
class Scenario:
    def __init__(self, yaml_path: str):
        ...

    def load(self) -> dict:
        """加载并验证 YAML 剧本文件。"""
        # 验证必要字段: name, steps, tmux, display
        # 验证 steps 中的 pane 名称与 tmux.panes 匹配
        # 返回结构化 dict

    @staticmethod
    def validate(scenario: dict) -> list[str]:
        """返回验证错误列表。"""
```

### engine.py

```python
class Engine:
    def __init__(self, scenario_path: str, output_dir: str = "output", **kwargs):
        ...

    def run(self):
        """执行完整录制流程。"""
        # 1. 解析剧本
        # 2. 检查依赖
        # 3. 启动 Xvfb
        # 4. 启动 ffmpeg
        # 5. 创建 tmux 会话
        # 6. 按步骤执行
        # 7. 停止 ffmpeg
        # 8. 停止 Xvfb
        # 9. 报告输出路径

    def check_dependencies(self):
        """检查 Xvfb, ffmpeg, xterm, tmux 是否可用。"""

    def cleanup(self):
        """清理所有子进程。"""
```

### cli.py

```python
# 用法:
# python -m vuln_recorder run <scenario.yaml> [--output DIR] [--display :99] [--resolution 1920x1080] [--fps 30]
# python -m vuln_recorder check  # 检查依赖是否安装
# python -m vuln_recorder run <scenario.yaml> --dry-run  # 只解析剧本，不执行
```

## 依赖

**系统依赖**:
- Xvfb
- ffmpeg (需 libx264 编码器)
- xterm
- tmux >= 3.0

**Python 依赖**:
- PyYAML

## 错误处理

- 启动前检查所有依赖工具是否存在于 PATH 中
- 任何子进程启动失败时，清理已启动的其他子进程
- ffmpeg 录制失败时保留部分输出文件（不自动删除）
- Xvfb display 占用时自动尝试下一个编号
- 支持 `--dry-run` 模式：只解析剧本和检查依赖，不实际执行
- `cleanup()` 在 engine 中注册为 atexit handler，确保异常退出时也能清理

## 输出

录制完成后输出文件结构：
```
output/
└── openplc-delete-user/
    ├── recording.mp4          # 视频录制
    └── scenario.yaml          # 使用的剧本文件副本
```
