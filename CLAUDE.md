# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 构建、测试与运行

```bash
# 安装依赖
uv sync --dev

# 运行（开发模式）
uv run python -m winrandr
uv run python -m winrandr --output DISPLAY1 --mode 1920x1080 --rate 60

# 运行测试
uv run pytest tests/ -v
uv run pytest tests/test_cli.py -v
uv run pytest tests/test_cli.py::test_parser_basic -v  # 单个测试

# 构建单文件 exe（输出到 dist/winrandr.exe）
uv run nuitka --standalone --onefile --output-dir=dist winrandr

# 构建 exe（清除 Nuitka 缓存后重建，变更包结构时必须）
uv run nuitka --clean-cache=all && rm -rf dist/* && uv run nuitka --standalone --onefile --output-dir=dist winrandr

# 集成测试脚本
bash scripts/test.sh
```

**注意：** 变更包结构（新增/删除/移动 .py 文件）后，必须清除 Nuitka 缓存再构建，否则 exe 中可能包含旧代码。

## 架构分层

```
main.py                   简易入口，转发到 winrandr.cli（主要用 `python -m winrandr`）
winrandr/                 核心包
├── __init__.py           版本号 + 公开 API 重导出
├── __main__.py           python -m winrandr 入口
├── cli.py                CLI 层：argparse 解析 + 主流程编排
├── api.py                公开 API：list_displays / set_resolution 等
├── formatter.py          xrandr 风格格式化输出
├── models.py             数据模型 (DisplayInfo, DisplayMode)
├── features/
│   ├── __init__.py
│   ├── gamma.py          伽马校正与亮度（SetDeviceGammaRamp）
│   └── layout.py         位置/旋转/主屏/关闭/相对定位（SetDisplayConfig）
└── win32/                底层 Win32 绑定层
    ├── __init__.py       子包统一 re-export
    ├── constants.py      Win32 API 常量 + 旋转映射表
    ├── structures.py     ctypes 结构体定义（DISPLAYCONFIG_*、DEVMODE 等）
    └── bindings.py       Win32 API 函数绑定 + 内部工具函数

tests/                    测试
├── test_cli.py           CLI 参数解析测试（44+ 项）
├── test_formatter.py     格式化输出测试
├── test_constants.py     常量与旋转映射一致性测试
└── test_models.py        数据模型测试

scripts/
├── build.sh              构建 exe（引用 main.py，适用 Python<3.13 的 MinGW 路径）
├── test.sh               集成测试脚本
├── run.sh                uv run main.py 快捷脚本
└── completions.ps1       PowerShell Tab 补全
```

## Win32 API 选型

| 操作 | API | 文件 |
|------|-----|------|
| 查询显示器 | `QueryDisplayConfig(QDC_ONLY_ACTIVE_PATHS)` | bindings.py |
| 列可用模式 | `EnumDisplaySettings` 遍历 | api.py |
| 改分辨率 | `ChangeDisplaySettingsEx(CDS_UPDATEREGISTRY)` | api.py |
| 改位置/旋转/主屏/关闭 | `SetDisplayConfig` + SDC flags | features/layout.py |
| 读物理尺寸 | `CreateDCW` + `GetDeviceCaps(HORZSIZE/VERTSIZE)` | bindings.py |
| 亮度和伽马 | `GetDeviceGammaRamp` / `SetDeviceGammaRamp` | features/gamma.py |
| 查适配器/设备路径 | `DisplayConfigGetDeviceInfo` (SOURCE_NAME/TARGET_NAME/ADAPTER_NAME) | bindings.py |

## 关键设计决策

- **ctypes 而非 pywin32**：零外部依赖，仅需 Python 标准库
- **两条 API 路线**：改分辨率用 `ChangeDisplaySettingsEx`（更可靠）；布局变更用 `SetDisplayConfig`（功能更全）
- **去重策略**：Windows 可能为同一显示器返回多条 QDC 路径，按 GDI 设备名去重
- **回退机制**：QDC mode 数组可能不含当前 target mode 的刷新率，此时用 `EnumDisplaySettings` 获取
- **虚拟驱动屏蔽**：OrayIddDriver 可能破坏 `SetDisplayConfig`，通过 `apply_filtered()` 过滤无效路径

## xrandr 兼容清单

**已实现：** 查询/列模式/分辨率/刷新率/位置/旋转/主屏/关闭/亮度/伽马/镜像翻转(xy)/相对定位/首选分辨率/auto/dry-run/GPU 列表/扩展属性/JSON 输出/listmonitors

**不支持（无标准 Win32 API）：** `--reflect x|y` 单轴、`--scale`、`--transform`、`--fb`、`--panning`

## 代码规范

- 每文件 ≤300 行（Python），≤400 行（静态语言）
- 蛇形命名（函数、变量），Windows SDK 结构体全大写
- 下划线前缀 `_` 表示内部函数
- 日志消息用中文写
- 每层文件夹文件数 ≤8 个
- 禁止循环依赖、数据泥团、过度设计等坏味道
