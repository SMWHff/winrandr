<div align="center">

# winrandr

**Windows 上的 xrandr 替代工具**

通过 Win32 API 管理显示器布局、分辨率、刷新率、旋转、亮度、伽马校正等

[![Version](https://img.shields.io/github/v/release/SMWHff/winrandr?color=blue&label=version)](https://github.com/SMWHff/winrandr/releases)
[![License](https://img.shields.io/github/license/SMWHff/winrandr?color=green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12%20|%203.13-blue)](pyproject.toml)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey)]()

</div>

## 概述

`winrandr` 是 Linux `xrandr` 的 Windows 替代品，提供相同的命令行体验，用于查询和配置多显示器设置。

```bash
# 查询显示器
winrandr

# 设置分辨率和刷新率
winrandr --output DISPLAY1 --mode 1920x1080 --rate 60

# 双屏布局
winrandr --output DISPLAY1 --pos 0x0 --primary
winrandr --output DISPLAY2 --pos 1920x0 --left-of DISPLAY1

# 图像调节
winrandr --output DISPLAY1 --brightness 0.8 --gamma 1.0:0.9:0.8
```

## 安装

### 下载 exe（推荐）

从 [Releases](https://github.com/SMWHff/winrandr/releases) 下载 `winrandr.exe`，放入 PATH 目录即可使用。

### pip 安装

```bash
pip install winrandr
```

### 源码运行

```bash
git clone https://github.com/SMWHff/winrandr.git
cd winrandr
uv run python -m winrandr --help
```

## 功能

### 显示器查询

| 命令 | 说明 |
|------|------|
| `winrandr` | 列出所有显示器（类 xrandr 风格） |
| `winrandr --output DISPLAY1` | 查询指定显示器 |
| `winrandr --listmodes` | 列出所有可用分辨率 |
| `winrandr --prop` | 显示显示器扩展属性（设备 ID、状态标志等） |
| `winrandr --json` | JSON 格式输出（脚本解析用） |

输出示例：

```
Screen 0: minimum 320 x 200, current 1920 x 1080, maximum 32767 x 32767

DISPLAY1 connected primary 1920x1080+0+0 (normal left inverted right) 527mm x 296mm
   1920x1080     60.00*+
   1680x1050     60.00
   1280x1024     60.02
   ...

DISPLAY2 disconnected
```

标记说明：`*` = 当前模式，`+` = 首选模式，旋转列表 `(normal left inverted right)` 表示所有支持方向

### 显示器配置

| 命令 | 说明 |
|------|------|
| `--output NAME` | 选择显示器 |
| `--mode WxH` | 设置分辨率 |
| `--rate Hz` | 设置刷新率 |
| `--preferred` | 恢复首选分辨率 |
| `--pos XxY` | 设置桌面位置 |
| `--rotate DIR` | 旋转（normal/left/right/inverted） |
| `--primary` | 设为主显示器 |
| `--off` | 关闭显示器 |

### 相对定位

| 命令 | 说明 |
|------|------|
| `--left-of REF` | 放在参考显示器左侧 |
| `--right-of REF` | 放在参考显示器右侧 |
| `--above REF` | 放在参考显示器上方 |
| `--below REF` | 放在参考显示器下方 |
| `--same-as REF` | 与参考显示器同位置（镜像） |

### 图像调节

| 命令 | 说明 |
|------|------|
| `--brightness VAL` | 亮度（0.1–2.0，1.0 正常） |
| `--gamma R:G:B` | 伽马校正（如 1.0:0.9:0.8） |
| `--reflect xy` | 镜像翻转（等同旋转 180°） |
| `--auto` | 启用显示器并使用首选分辨率 |
| `--dry-run` | 模拟操作，不实际更改配置 |

### 其他

| 命令 | 说明 |
|------|------|
| `--verbose, -v` | DEBUG 级别日志 |
| `--version` | 显示版本号 |
| `--help` | 显示帮助 |
| `--listproviders` | 列出 GPU 适配器 |
| `--listmonitors` | 带编号的显示器列表 |
| `--json` | JSON 格式输出（脚本解析用） |

## 与 xrandr 对照

| xrandr | winrandr | 状态 |
|--------|----------|------|
| `xrandr` | `winrandr` | ✅ |
| `--mode WxH` | `--mode WxH` | ✅ |
| `--rate Hz` | `--rate Hz` | ✅ |
| `--pos XxY` | `--pos XxY` | ✅ |
| `--rotate` | `--rotate` | ✅ |
| `--primary` | `--primary` | ✅ |
| `--off` | `--off` | ✅ |
| `--brightness` | `--brightness` | ✅ |
| `--gamma r:g:b` | `--gamma R:G:B` | ✅ |
| `--reflect xy` | `--reflect xy` | ✅ |
| `--left-of / --right-of` | `--left-of / --right-of` | ✅ |
| `--above / --below` | `--above / --below` | ✅ |
| `--same-as` | `--same-as` | ✅ |
| `--preferred` | `--preferred` | ✅ |
| `--auto` | `--auto` | ✅ |
| `--dry-run` | `--dry-run` | ✅ |
| `--listproviders` | `--listproviders` | ✅ |
| `--listmonitors` | `--listmonitors` | ✅ |
| `--reflect x\|y` | — | ❌ 无标准 Win32 API |
| `--scale / --transform` | — | ❌ 无标准 Win32 API |
| `--fb / --panning` | — | ❌ 无标准 Win32 API |

## 自动补全

```powershell
# PowerShell 临时加载
. ./scripts/completions.ps1

# 永久生效
Add-Content $PROFILE "`n. 'C:\path\to\winrandr\scripts\completions.ps1'"
```

## 从源码构建

```bash
bash scripts/build.sh
# exe 输出到 dist/winrandr.exe
```

依赖 [uv](https://docs.astral.sh/uv/) 和 Nuitka（首次构建自动下载）。

## 测试

```bash
bash scripts/test.sh        # 集成测试
uv run pytest tests/ -v     # 单元测试（66 项）
```

## 技术栈

- **语言**: Python（零外部依赖，仅标准库）
- **API**: Win32 `QueryDisplayConfig` / `SetDisplayConfig` / `ChangeDisplaySettingsEx` + GDI
- **绑定**: `ctypes` 直接调用 Win32 API
- **打包**: Nuitka 编译为单文件 exe

## 项目结构

```
winrandr/
├── cli.py              命令行入口 + 主流程编排
├── api.py              公开 API（查询、分辨率、扩展属性）
├── formatter.py        xrandr 风格格式化输出
├── models.py           数据模型 (DisplayInfo, DisplayMode)
├── features/
│   ├── gamma.py        亮度与伽马校正
│   └── layout.py       布局管理（位置、旋转、主屏、关闭、相对定位）
└── win32/              底层 Win32 绑定层
    ├── constants.py    Win32 API 常量与旋转映射
    ├── structures.py   ctypes 结构体定义
    └── bindings.py     Win32 API 函数绑定 + 内部工具
```

## 已知限制

- 虚拟显示器驱动（如 OrayIddDriver/向日葵）可能破坏 `SetDisplayConfig` API，导致布局相关功能不可用（分辨率调整不受影响）
- `--brightness` / `--gamma` 使用 `SetDeviceGammaRamp`，在某些驱动或远程桌面环境中不可用
- 单轴镜像翻转（`--reflect x/y`）无标准 Win32 API 支持

## 许可

[MIT](LICENSE)
