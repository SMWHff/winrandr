# winrandr — 架构设计

## 整体架构

```
main.py  ──→  winrandr/
              ├── cli.py          argparse + 输出格式化
              ├── api.py          公开 API (8 函数)
              ├── models.py       数据模型 (DisplayInfo, DisplayMode)
              ├── bindings.py     Win32 函数绑定 + 内部工具
              ├── structures.py   ctypes 结构体
              └── constants.py    常量
```

## 文件职责

### main.py
- 保持为兼容入口，单纯委托给 `winrandr.cli.main()`

### winrandr/cli.py
- argparse 参数解析
- xrandr 风格格式化输出
- 日志初始化

### winrandr/api.py
- `DisplayInfo` / `DisplayMode` 数据模型
- 6 个公开函数
- 模式枚举（`_enumerate_modes`）

### winrandr/bindings.py
- 所有 Win32 API 的 ctypes 函数绑定
- 内部工具函数（`get_gdi_name`、`query_active_config` 等）

### winrandr/structures.py
- 与 Windows SDK 对齐的 ctypes 结构体
- 结构体对齐自动遵循 x64 MSVC ABI

### winrandr/constants.py
- Win32 常量
- 旋转角度映射表

## 公开 API

| 函数 | 参数 | 功能 |
|------|------|------|
| `list_displays()` | 无 | 返回 `list[DisplayInfo]`（含所有可用模式） |
| `set_resolution(name, w, h, rr)` | 设备名、宽、高、刷新率 | 改分辨率 |
| `set_position(name, x, y)` | 设备名、X、Y | 改桌面位置 |
| `set_rotation(name, deg)` | 设备名、角度 | 改旋转 |
| `set_primary(name)` | 设备名 | 设为主显示器 |
| `set_off(name)` | 设备名 | 禁用显示器 |
| `set_brightness(name, val)` | 设备名、亮度值 | 伽马校正调亮度 |
| `set_reflect(name, axis)` | 设备名、轴 (x/y/xy) | 镜像翻转（仅 xy） |

## Win32 API 映射

### 查询 → QueryDisplayConfig
```
GetDisplayConfigBufferSizes → QueryDisplayConfig
  → DisplayConfigGetDeviceInfo(GET_SOURCE_NAME) → GDI 名
  → EnumDisplayDevices → 友好名称
  → EnumDisplaySettings 遍历 → 所有可用模式
```

### 改分辨率 → ChangeDisplaySettingsEx
```
EnumDisplaySettings(获取当前 DEVMODE)
  → 修改 dmPelsWidth/Height/Frequency
  → ChangeDisplaySettingsEx(CDS_UPDATEREGISTRY)
```

### 改位置/旋转/主屏/关闭 → SetDisplayConfig
```
QueryDisplayConfig(获取当前配置)
  → 修改 paths/modes
  → SetDisplayConfig(SDC_APPLY | SDC_USE_SUPPLIED_DISPLAY_CONFIG)
```

## xrandr 输出对照

| xrandr | winrandr | 状态 |
|--------|----------|------|
| `xrandr` | `winrandr` | ✓ 列表 |
| `xrandr --listmodes` | `winrandr --listmodes` | ✓ 模式列表 |
| `xrandr --output eDP-1 --mode 1920x1080` | `winrandr --output DISPLAY1 --mode 1920x1080` | ✓ |
| `xrandr --output eDP-1 --rate 60` | `winrandr --output DISPLAY1 --rate 60` | ✓ |
| `xrandr --output eDP-1 --pos 0x0` | `winrandr --output DISPLAY1 --pos 0x0` | ✓ |
| `xrandr --output eDP-1 --rotate normal` | `winrandr --output DISPLAY1 --rotate normal` | ✓ |
| `xrandr --output eDP-1 --primary` | `winrandr --output DISPLAY1 --primary` | ✓ |
| `xrandr --output eDP-1 --off` | `winrandr --output DISPLAY1 --off` | ✓ |
| `xrandr --output eDP-1 --brightness 0.8` | `winrandr --output DISPLAY1 --brightness 0.8` | ✓ |
| `xrandr --output eDP-1 --reflect xy` | `winrandr --output DISPLAY1 --reflect xy` | ✓ (xy 仅) |
| `xrandr --output eDP-1 --reflect x` | 暂不支持 | - |
| `xrandr --output eDP-1 --scale` | 未实现 | - |
| `xrandr --fb` | 未实现 | - |

## 已知限制

- `DisplayConfigGetDeviceInfo(GET_TARGET_NAME)` 在某些系统上失败，回退到 `EnumDisplayDevices`
- 虚拟显示器驱动（OrayIddDriver）可能污染 `QueryDisplayConfig`/`SetDisplayConfig` 数据，导致位置/旋转/主屏/关闭功能不可用
- 物理尺寸通过 GDI GetDeviceCaps 获取，虚拟显示器可能返回 0
- `SetDeviceGammaRamp`（--brightness）在某些驱动/远程桌面上不可用
- `--reflect x` / `--reflect y` 没有标准 Win32 API 支持
