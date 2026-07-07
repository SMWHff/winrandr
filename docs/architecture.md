# winrandr — 架构设计

## 整体架构

```
main.py                   简易入口，转发到 winrandr.cli
winrandr/                 核心包
├── __init__.py           版本号 + 公开 API 重导出
├── __main__.py           python -m winrandr 入口
├── cli.py                argparse + 主流程编排
├── api.py                公开 API (12 函数，含子模块 re-export)
├── formatter.py          xrandr 风格格式化输出
├── models.py             数据模型 (DisplayInfo, DisplayMode)
├── features/
│   ├── gamma.py          伽马校正与亮度
│   └── layout.py         位置/旋转/主屏/关闭
└── win32/                底层 Win32 绑定层
    ├── constants.py      Win32 API 常量 + 旋转映射表
    ├── structures.py     ctypes 结构体定义
    └── bindings.py       Win32 API 函数绑定 + 内部工具函数
```

## 文件职责

### main.py
- 保持为兼容入口，单纯委托给 `winrandr.cli.main()`

### winrandr/cli.py
- argparse 参数解析
- 主流程编排（查询/配置/相对定位/图像调节）
- 日志初始化

### winrandr/api.py
- `list_displays` / `set_resolution` / `set_preferred_resolution`（查询与分辨率）
- 12 个公开函数（其中 8 个委托给 `features/` 子模块）
- `set_position_relative`（相对定位，使用 `list_displays` 计算坐标）
- `set_auto`（启用显示器并设首选分辨率）
- `get_display_props` / `list_providers`（扩展属性与 GPU 列表）
- 模式枚举（`_enumerate_modes`）

### winrandr/formatter.py
- `format_displays`：xrandr 风格显示器信息输出
- `format_monitor_list`：--listmonitors 格式输出
- 旋转信息格式化（`_rotation_part`）

### winrandr/features/gamma.py
- `set_brightness`：单值伽马倍增调亮度
- `set_gamma`：三通道独立伽马校正

### winrandr/features/layout.py
- `set_position`：绝对定位
- `set_rotation`：旋转（0/90/180/270）
- `set_primary`：设为主显示器
- `set_off`：关闭显示器
- `set_reflect`：镜像翻转（仅 xy = 旋转 180°）

### winrandr/win32/bindings.py
- 所有 Win32 API 的 ctypes 函数绑定
- 内部工具函数（`get_gdi_name`、`query_active_config` 等）
- `apply_filtered`：过滤虚拟显示器幽灵路径

### winrandr/win32/structures.py
- 与 Windows SDK 对齐的 ctypes 结构体
- 结构体对齐自动遵循 x64 MSVC ABI

### winrandr/win32/constants.py
- Win32 常量
- 旋转角度映射表（`ROTATION_MAP` / `ROTATION_NAMES` / `ROTATION_DEGREES`）
- `DISP_CHANGE_*` 错误码与中文消息映射

## 公开 API

| 函数 | 参数 | 功能 |
|------|------|------|
| `list_displays()` | 无 | 返回 `list[DisplayInfo]`（含所有可用模式） |
| `set_resolution(name, w, h, rr)` | 设备名、宽、高、刷新率 | 改分辨率 |
| `set_preferred_resolution(name)` | 设备名 | 恢复注册表首选分辨率 |
| `set_auto(name)` | 设备名 | 启用显示器并使用首选分辨率（`--auto`） |
| `set_position(name, x, y)` | 设备名、X、Y | 改桌面位置 |
| `set_position_relative(name, ref, rel)` | 设备名、参考名、关系 | 相对定位 |
| `set_rotation(name, deg)` | 设备名、角度 | 改旋转 |
| `set_primary(name)` | 设备名 | 设为主显示器 |
| `set_off(name)` | 设备名 | 禁用显示器 |
| `set_brightness(name, val)` | 设备名、亮度值 | 伽马校正调亮度 |
| `set_gamma(name, r, g, b)` | 设备名、红/绿/蓝乘数 | 伽马校正（三通道独立） |
| `set_reflect(name, axis)` | 设备名、轴 (x/y/xy) | 镜像翻转（仅 xy） |

## Win32 API 映射

| 操作 | API | 文件 |
|------|-----|------|
| 查询显示器 | `QueryDisplayConfig(QDC_ONLY_ACTIVE_PATHS)` | bindings.py |
| 列可用模式 | `EnumDisplaySettings` 遍历 | api.py |
| 改分辨率 | `ChangeDisplaySettingsEx(CDS_UPDATEREGISTRY)` | api.py |
| 改位置/旋转/主屏/关闭 | `SetDisplayConfig` + SDC flags | features/layout.py |
| 读物理尺寸 | `CreateDCW` + `GetDeviceCaps(HORZSIZE/VERTSIZE)` | bindings.py |
| 亮度和伽马 | `GetDeviceGammaRamp` / `SetDeviceGammaRamp` | features/gamma.py |
| 查适配器/设备路径 | `DisplayConfigGetDeviceInfo` (SOURCE/TARGET/ADAPTER_NAME) | bindings.py |

### 改分辨率流程

```
EnumDisplaySettings(获取当前 DEVMODE)
  → 修改 dmPelsWidth/Height/Frequency
  → ChangeDisplaySettingsEx(CDS_UPDATEREGISTRY)
```

### 布局变更流程

```
QueryDisplayConfig(获取当前配置)
  → 修改 paths/modes
  → filter_valid_paths(过滤 OrayIddDriver 幽灵路径)
  → SetDisplayConfig(SDC_APPLY | ...)
```

## 关键设计决策

- **ctypes 而非 pywin32**：零外部依赖，仅需 Python 标准库
- **两条 API 路线**：改分辨率用 `ChangeDisplaySettingsEx`（更可靠）；布局变更用 `SetDisplayConfig`（功能更全）
- **去重策略**：Windows 可能为同一显示器返回多条 QDC 路径，按 GDI 设备名去重
- **回退机制**：QDC mode 数组可能不含当前 target mode 的刷新率，此时用 `EnumDisplaySettings` 获取
- **虚拟驱动屏蔽**：OrayIddDriver 可能破坏 `SetDisplayConfig`，通过 `apply_filtered()` 过滤无效路径

## 与 xrandr 兼容对照

参见 README.md 中的完整对照表。已实现功能：

- 查询/列模式/分辨率/刷新率/位置/旋转/主屏/关闭
- 亮度/伽马/镜像翻转(xy)/相对定位/首选分辨率
- auto/dry-run/GPU 列表/扩展属性/JSON 输出/listmonitors
- `-q`/`--prop`/`--current`/`-x`/`-y`/`--orientation` 等兼容参数

不支持（无标准 Win32 API）：
- `--reflect x|y` 单轴、`--scale`、`--transform`、`--fb`、`--panning`

## 已知限制

- `DisplayConfigGetDeviceInfo(GET_TARGET_NAME)` 在某些系统上失败，回退到 `EnumDisplayDevices`
- 虚拟显示器驱动（OrayIddDriver）可能污染 `QueryDisplayConfig`/`SetDisplayConfig` 数据，导致位置/旋转/主屏/关闭功能不可用
- 物理尺寸通过 GDI GetDeviceCaps 获取，虚拟显示器可能返回 0
- `SetDeviceGammaRamp`（--brightness）在某些驱动/远程桌面上不可用
- `--reflect x` / `--reflect y` 没有标准 Win32 API 支持
