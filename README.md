# vuln-recorder

自动化漏洞验证录屏工具。通过 YAML 场景文件描述攻击步骤，在虚拟 X11 显示上通过 xterm + tmux 执行命令，同时用 ffmpeg 录屏输出 MP4 视频。

## 环境依赖

### 系统工具

| 工具 | 用途 | 安装 |
|------|------|------|
| Xvfb | 虚拟 X11 显示服务器 | `sudo apt install xvfb` |
| xterm | 终端模拟器 | `sudo apt install xterm` |
| tmux | 终端复用器（多窗格） | `sudo apt install tmux` |
| ffmpeg | 屏幕录制 (x11grab → H.264) | `sudo apt install ffmpeg` |

### Python 依赖

```
pip install -r requirements.txt
```

或手动安装：

```
pip install PyYAML
```

### 验证依赖

```
python -m vuln_recorder check
```

输出 `All dependencies are installed.` 表示就绪。

### 测试环境

本项目在以下环境验证通过：

- **OS**: Ubuntu 22.04 LTS (x86_64)
- **Python**: 3.10
- **Xvfb**: 21.1
- **xterm**: 370
- **tmux**: 3.3a
- **ffmpeg**: 4.4.2
- **显示**: 虚拟 X11（无需物理显示器）

## 安装

```bash
git clone <repo-url>
cd vuln-recorder
pip install -e .
```

安装后即可使用 `vuln-recorder` 命令，或通过 `python -m vuln_recorder` 运行。

## 使用方法

### 基本命令

```bash
# 检查依赖是否齐全
python -m vuln_recorder check

# 预览场景（仅解析 YAML，不执行）
python -m vuln_recorder run scenario.yaml --dry-run

# 执行录屏，输出到默认 output/ 目录
python -m vuln_recorder run scenario.yaml

# 指定输出目录
python -m vuln_recorder run scenario.yaml --output /tmp/my-recording
```

### 输出结构

每次录屏生成一个目录，包含：

```
output/
└── my-scenario-name/        # 从 name 字段自动生成 slug
    ├── recording.mp4         # H.264 视频文件
    └── scenario.yaml         # 场景文件副本（用于归档）
```

## 场景文件格式

场景文件为 YAML 格式，描述录屏的完整配置。以下是一个完整示例：

```yaml
name: "Example Vulnerability Demo"
description: "演示某个漏洞的利用过程"

display:
  width: 1920
  height: 1080
  color_depth: 24       # 可选，默认 24

tmux:
  session_name: "example-session"
  layout: "main-horizontal"    # optional, defaults to main-horizontal
  panes:
    - name: "env"
    - name: "attacker"
    - name: "target"

steps:
  - pane: "env"
    command: "# === 漏洞演示开始 ==="
    wait: 2
  - pane: "attacker"
    command: "curl -s http://target/api/exploit"
    wait: 3
  - pane: "target"
    command: "# 目标已被攻破"
    wait: 2
```

### 字段说明

#### 顶层字段（全部必填）

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 场景名称，同时用于生成输出目录名（空格替换为 `-`，转小写） |
| `description` | string | 场景描述 |
| `display` | object | 虚拟显示器配置 |
| `tmux` | object | 终端布局配置 |
| `steps` | array | 按顺序执行的命令步骤列表 |

#### display（虚拟显示器）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `width` | int | 是 | 显示器像素宽度，如 `1920`、`1280`、`800` |
| `height` | int | 是 | 显示器像素高度，如 `1080`、`720`、`600` |
| `color_depth` | int | 否 | 色深，默认 `24` |

xterm 以最大化模式启动，自动填满整个虚拟显示区域。字体使用 Monospace 14pt，保证录制清晰可读。

#### tmux（终端布局）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `session_name` | string | 是 | tmux 会话名称，需全局唯一（录制期间不能有同名会话） |
| `layout` | string | 否 | 窗格布局策略，默认 `main-horizontal`，见下表 |
| `panes` | array | 是 | 窗格列表，每个元素需包含 `name` 字段 |

**可选布局：**

| 布局值 | 效果 | 适用场景 |
|--------|------|----------|
| `even-horizontal` | 等宽竖分（左中右） | 多个角色并排对比 |
| `even-vertical` | 等高横分（上中下） | 日志、命令输出等纵向排列 |
| `main-horizontal` | 上方大窗格 + 下方等分小窗格 | 主操作区 + 辅助信息 |
| `main-vertical` | 左侧大窗格 + 右侧等分小窗格 | 主操作区 + 辅助信息 |
| `tiled` | 尽量填满矩形区域的均匀分布 | 4+ 个窗格 |
| `custom` | 不应用任何布局，保持 split-window 的默认结果 | 完全自定义 |

布局效果示意：

```
even-horizontal (3 panes)    even-vertical (3 panes)     main-horizontal (3 panes)
┌──────┬──────┬──────┐       ┌────────────────────┐      ┌────────────────────┐
│      │      │      │       │                    │      │                    │
│  1   │  2   │  3   │       │         1          │      │         1          │
│      │      │      │       ├────────────────────┤      ├──────────┬─────────┤
│      │      │      │       │         2          │      │     2    │    3    │
└──────┴──────┴──────┘       ├────────────────────┤      └──────────┴─────────┘
                               │         3          │
                               └────────────────────┘
```

4-panel variants:

```
even-horizontal (4 panes)    even-vertical (4 panes)     main-horizontal (4 panes)
┌─────┬─────┬─────┬─────┐   ┌────────────────────┐     ┌────────────────────┐
│     │     │     │     │   │         1          │     │         1          │
│  1  │  2  │  3  │  4  │   ├────────────────────┤     ├──────┬─────┬──────┤
│     │     │     │     │   │         2          │     │  2   │  3  │  4   │
└─────┴─────┴─────┴─────┘   ├────────────────────┤     └──────┴─────┴──────┘
                              │         3          │
                              ├────────────────────┤     main-vertical (4 panes)
                              │         4          │     ┌────────┬─────────┐
                              └────────────────────┘     │        │    2    │
                                                         │   1    ├─────────┤
tiled (4 panes)                                          │        │    3    │
┌──────────┬──────────┐                                  │        ├─────────┤
│     1    │     2    │                                  │        │    4    │
├──────────┼──────────┤                                  └────────┴─────────┘
│     3    │     4    │
└──────────┴──────────┘
```

#### steps（执行步骤）

每个步骤包含三个字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `pane` | string | 是 | 目标窗格名称，必须与 `tmux.panes[].name` 对应 |
| `command` | string | 是 | 要执行的命令，以 `Enter` 发送到 tmux 窗格 |
| `wait` | int/float | 是 | 执行后等待秒数，用于等待命令输出完成后再进入下一步 |

**命令技巧：**

- 以 `#` 开头的命令会作为注释显示在终端中（shell 不执行），适合做步骤说明
- 命令会通过 `tmux send-keys` 发送，支持管道、变量替换等 shell 特性
- 多行命令使用 YAML 的 `>-` 折叠标量：

```yaml
steps:
  - pane: "attacker"
    command: >-
      curl -sk -X POST https://target/api/login
      -H 'Content-Type: application/json'
      -d '{"username":"admin","password":"pass"}'
    wait: 3
```

### 终端输出最佳实践

录制时终端中显示的内容直接构成最终视频的信息传达。请遵循以下准则：

**步骤编号格式（强制）：** 终端中的每条步骤提示**必须**使用 `步骤N: 描述` 格式，让人一眼就能跟上当前进度。严禁无编号的散乱提示。

```yaml
# 正确 ✓
steps:
  - pane: "environment"
    command: "printf '\\033[1;36m步骤1: 初始化攻击环境\\033[0m'"
    wait: 5
  - pane: "attacker"
    command: "printf '\\033[33m步骤2: 识别目标系统漏洞\\033[0m'"
    wait: 5
  - pane: "attacker"
    command: "printf '\\033[31m步骤3: 执行漏洞利用\\033[0m'"
    wait: 5
  - pane: "victim"
    command: "printf '\\033[31m步骤4: 未授权操作成功 — 用户已删除\\033[0m'"
    wait: 5

# 错误 ✗  — 不要这样写
steps:
  - pane: "attacker"
    command: "echo 'Scanning target...'"
  - pane: "attacker"
    command: "echo 'Exploit executed'"
```

**文字简洁：** 每个步骤描述用一句话概括当前操作，控制在 1-2 行以内，不要写长段落。

**彩色高亮：** 使用 ANSI 转义码为步骤提示上色，提升视频可读性：
- `\033[1;36m` — 青色粗体（信息/标题/环境类步骤）
- `\033[33m` — 黄色（侦察/扫描类步骤）
- `\033[31m` — 红色（攻击/警告/关键结果）
- `\033[32m` — 绿色（成功/完成）
- `\033[1m` — 粗体（强调）
- `\033[0m` — 重置颜色

**停留时间：** 每条步骤提示在屏幕上至少停留 **5 秒**（`wait: 5`），确保观众有足够时间阅读。关键攻击步骤建议 8-10 秒。

## 示例场景

`examples/` 目录包含完整的示例：

```
examples/
├── openplc-delete-user.yaml   # 场景文件（3窗格，彩色步骤输出）
└── demo-recording.mp4         # 对应的录制输出视频
```

```bash
# 预览
python -m vuln_recorder run examples/openplc-delete-user.yaml --dry-run

# 录制
python -m vuln_recorder run examples/openplc-delete-user.yaml --output /tmp/demo
```

更多场景文件位于 `scenarios/`，测试用场景位于 `tests/fixtures/`。

## 项目结构

```
vuln-recorder/
├── vuln_recorder/          # 核心模块
│   ├── __main__.py          # python -m 入口
│   ├── cli.py               # 命令行参数解析
│   ├── engine.py            # 主编排器（串联所有组件）
│   ├── scenario.py          # YAML 场景解析与校验
│   ├── xvfb.py              # Xvfb 虚拟显示管理
│   ├── recorder.py          # ffmpeg x11grab 录屏
│   └── terminal.py          # xterm + tmux 终端编排
├── tests/                   # 测试套件
│   ├── fixtures/            # 测试用场景文件
│   ├── test_cli.py          # CLI 单元测试
│   ├── test_engine.py       # Engine 单元测试
│   ├── test_scenario.py     # 场景解析测试
│   ├── test_terminal.py     # 终端编排测试
│   ├── test_xvfb.py         # Xvfb 管理测试
│   ├── test_recorder.py     # 录屏测试
│   ├── test_integration.py  # 集成测试
│   └── test_smoke.py        # 端到端冒烟测试
├── examples/                 # 示例（YAML + 录制视频）
│   ├── openplc-delete-user.yaml
│   └── demo-recording.mp4
├── scenarios/                # 场景文件
│   └── openplc-delete-user.yaml
├── setup.py
├── requirements.txt
└── README.md
```

## 运行测试

```bash
# 单元测试（无需系统依赖，< 1 秒）
python -m pytest tests/test_cli.py tests/test_engine.py tests/test_scenario.py \
  tests/test_terminal.py tests/test_xvfb.py tests/test_recorder.py \
  tests/test_integration.py -v

# 完整测试套件（含冒烟测试，需要 Xvfb/ffmpeg/xterm/tmux，约 90 秒）
python -m pytest tests/ -v
```
