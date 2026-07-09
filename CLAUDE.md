# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 构建、测试与运行

```bash
# 安装依赖
uv sync --dev

# 运行（开发模式）
bash scripts/dev/run.sh
bash scripts/dev/run.sh --output DISPLAY1 --mode 1920x1080 --rate 60

# Lint 检查
bash scripts/dev/lint.sh

# 运行测试
bash scripts/dev/test.sh                    # 集成测试（导入检查 + pytest + 覆盖率）
uv run pytest tests/test_cli.py -v      # 单个测试文件
uv run pytest tests/test_cli.py::test_parser_basic -v  # 单个测试

# 构建单文件 exe（输出到 dist/winrandr.exe）
bash scripts/build/build.sh

# 构建 exe（清除 Nuitka 缓存后重建，变更包结构时必须）
uv run nuitka --clean-cache=all && rm -rf dist/* && bash scripts/build/build.sh
```

**注意：** 变更包结构（新增/删除/移动 .py 文件）后，必须清除 Nuitka 缓存再构建，否则 exe 中可能包含旧代码。

## 架构分层

```
main.py                   简易入口，转发到 winrandr.cli（主要用 `python -m winrandr`）
winrandr/                 核心包
├── __init__.py           版本号 + 公开 API 重导出
├── __main__.py           python -m winrandr 入口
├── cli/                   CLI 子包（argparse + 操作处理函数）
│   ├── __init__.py        主流程编排 main()
│   ├── parser.py          argparse 参数解析器
│   ├── common.py          CLI 通用工具函数（日志/参数校验/辅助）
│   └── handlers.py        CLI 操作处理函数（模式/位置/旋转/亮度等）
├── api.py                公开 API：list_displays / set_resolution 等
├── edid.py               EDID 读取与解析（注册表 + 二进制解析）
├── formatter.py          xrandr 风格格式化输出
├── models.py             数据模型 (DisplayInfo, DisplayMode)
├── profiles.py           配置存档管理（保存/恢复显示器布局）
├── features/
│   ├── __init__.py
│   ├── gamma.py          伽马校正、亮度与夜览模式（SetDeviceGammaRamp）
│   ├── layout.py         位置/旋转/主屏/关闭/相对定位（SetDisplayConfig）
│   └── resolution.py     分辨率/刷新率枚举与设置（ChangeDisplaySettingsEx）
└── win32/                底层 Win32 绑定层
    ├── __init__.py       子包统一 re-export
    ├── constants.py      Win32 API 常量 + 旋转映射表
    ├── structures.py     ctypes 结构体定义（DISPLAYCONFIG_*、DEVMODE 等）
    ├── bindings.py       Win32 API 函数绑定 (ctypes 声明)
    └── utils.py          内部工具函数 (查询/过滤/应用配置)

tests/                    测试（438 项，100% 覆盖率）
├── conftest.py           共享测试夹具（_fake_display 工厂）
├── unit/                 单元测试
│   ├── test_win32_utils.py   Win32 工具函数测试
│   ├── cli/                  CLI 参数/工具/处理器测试（6 文件）
│   ├── formatter/            格式化输出测试（2 文件）
│   ├── profiles/             配置存档测试（3 文件）
│   └── win32/               Win32 底层测试（2 文件）
├── features/             功能模块测试（gamma/layout/resolution）
└── integration/          集成测试
    ├── cli/                   CLI 入口测试（5 文件）
    ├── test_api.py            API 函数
    ├── test_edid.py           EDID 解析
    └── test_models.py         数据模型

scripts/
├── WinRandr.psm1         PowerShell 模块（20 个 cmdlet）
├── dev/
│   ├── run.sh            uv run -m winrandr 快捷脚本
│   ├── lint.sh           Lint 检查（ruff + 导入验证）
│   ├── test.sh           集成测试脚本（导入 + lint + pytest + 覆盖率）
│   └── setup.sh          一键初始化（check uv, sync, verify）
├── build/
│   ├── build.sh          构建 exe（Nuitka，入口 winrandr 包）
│   └── clean.sh          清理构建缓存和 __pycache__
└── completions/
    ├── completions.ps1   PowerShell Tab 补全
    └── completions.bash  Bash/Zsh Tab 补全

.github/
├── workflows/
│   ├── test.yml           GitHub Actions CI（4 Python 版本矩阵，已关闭自动触发）
│   └── release.yml        发布构建（Nuitka 打包 exe + GitHub Release）
└── PULL_REQUEST_TEMPLATE.md  PR 模板
```

## Win32 API 选型

| 操作 | API | 文件 |
|------|-----|------|
| 查询显示器 | `QueryDisplayConfig(QDC_ONLY_ACTIVE_PATHS)` | utils.py |
| 列可用模式 | `EnumDisplaySettings` 遍历 | features/resolution.py |
| 改分辨率 | `ChangeDisplaySettingsEx(CDS_UPDATEREGISTRY)` | features/resolution.py |
| 改位置/旋转/主屏/关闭 | `SetDisplayConfig` + SDC flags | features/layout.py |
| 读物理尺寸 | `CreateDCW` + `GetDeviceCaps(HORZSIZE/VERTSIZE)` | utils.py |
| 亮度和伽马 | `GetDeviceGammaRamp` / `SetDeviceGammaRamp` | features/gamma.py |
| 查适配器/设备路径 | `DisplayConfigGetDeviceInfo` (SOURCE_NAME/TARGET_NAME/ADAPTER_NAME) | utils.py |
| 查连接类型 | `DISPLAYCONFIG_TARGET_DEVICE_NAME.targetFlags` 解析 | utils.py → api.py |

## 关键设计决策

- **ctypes 而非 pywin32**：零外部依赖，仅需 Python 标准库
- **两条 API 路线**：改分辨率用 `ChangeDisplaySettingsEx`（更可靠）；布局变更用 `SetDisplayConfig`（功能更全）
- **去重策略**：Windows 可能为同一显示器返回多条 QDC 路径，按 GDI 设备名去重
- **回退机制**：QDC mode 数组可能不含当前 target mode 的刷新率，此时用 `EnumDisplaySettings` 获取
- **虚拟驱动屏蔽**：OrayIddDriver 可能破坏 `SetDisplayConfig`，通过 `apply_filtered()` 过滤无效路径
- **夜览模式**：利用 `SetDeviceGammaRamp` 计算蓝光过滤伽马表，支持 `light/medium/heavy` 或 0.0–1.0 强度
- **连接类型检测**：通过 `DISPLAYCONFIG_TARGET_DEVICE_NAME.targetFlags` 低 8 位判断 HDMI/DP/USB-C/DVI/VGA

## xrandr 兼容清单
```
root@Linux:~# xrandr --help
usage: xrandr [options]
  where options are:
  --display <display> or -d <display>
  --help
  -o <normal,inverted,left,right,0,1,2,3>
            or --orientation <normal,inverted,left,right,0,1,2,3>
  -q        or --query
  -s <size>/<width>x<height> or --size <size>/<width>x<height>
  -r <rate> or --rate <rate> or --refresh <rate>
  -v        or --version
  -x        (reflect in x)
  -y        (reflect in y)
  --screen <screen>
  --verbose
  --current
  --dryrun
  --nograb
  --prop or --properties
  --fb <width>x<height>
  --fbmm <width>x<height>
  --dpi <dpi>/<output>
  --output <output>
      --auto
      --mode <mode>
      --preferred
      --pos <x>x<y>
      --rate <rate> or --refresh <rate>
      --reflect normal,x,y,xy
      --rotate normal,inverted,left,right
      --left-of <output>
      --right-of <output>
      --above <output>
      --below <output>
      --same-as <output>
      --set <property> <value>
      --scale <x>x<y>
      --scale-from <w>x<h>
      --transform <a>,<b>,<c>,<d>,<e>,<f>,<g>,<h>,<i>
      --off
      --crtc <crtc>
      --panning <w>x<h>[+<x>+<y>[/<track:w>x<h>+<x>+<y>[/<border:l>/<t>/<r>/<b>]]]
      --gamma <r>:<g>:<b>
      --brightness <value>
      --primary
  --noprimary
  --newmode <name> <clock MHz>
            <hdisp> <hsync-start> <hsync-end> <htotal>
            <vdisp> <vsync-start> <vsync-end> <vtotal>
            [flags...]
            Valid flags: +HSync -HSync +VSync -VSync
                         +CSync -CSync CSync Interlace DoubleScan
  --rmmode <name>
  --addmode <output> <name>
  --delmode <output> <name>
  --listproviders
  --setprovideroutputsource <prov-xid> <source-xid>
  --setprovideroffloadsink <prov-xid> <sink-xid>
  --listmonitors
  --listactivemonitors
  --setmonitor <name> {auto|<w>/<mmw>x<h>/<mmh>+<x>+<y>} {none|<output>,<output>,...}
  --delmonitor <name>
```
**已实现：** 查询/列模式/分辨率/刷新率/位置/旋转/主屏/关闭/亮度/伽马/夜览模式/镜像翻转(xy)/相对定位/首选分辨率/auto/dry-run/GPU 列表/扩展属性/JSON 输出/listmonitors/连接类型/profiles

**不支持（无标准 Win32 API）：** `--reflect x|y` 单轴、`--scale`、`--transform`、`--fb`、`--panning`

## 代码规范

- 每文件 ≤300 行（Python），≤400 行（静态语言）
- 蛇形命名（函数、变量），Windows SDK 结构体全大写
- 下划线前缀 `_` 表示内部函数
- 日志消息用中文写
- 每层文件夹文件数 ≤8 个
- 禁止循环依赖、数据泥团、过度设计等坏味道
