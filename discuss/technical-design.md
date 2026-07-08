# winrandr 技术方案

## 背景

Windows 缺少命令行多显示器管理工具。Linux 有 `xrandr`，macOS 有 `displayplacer`。目标：对标 `xrandr` 的 Windows 版单文件 exe，零外部依赖。

## 选型

### 语言

| 方案 | 优点 | 缺点 |
|------|------|------|
| Python + Nuitka | 开发快，ctypes 直接调 Win32 API | exe ~3.4 MB |
| C + MinGW | exe ~100 KB | 结构体对齐手动处理，开发周期长 |
| Rust + windows-rs | 类型安全，exe 较小 | 用户不熟悉 Rust 生态 |

### API

| API | 时代 | 特点 |
|-----|------|------|
| `ChangeDisplaySettingsEx` | Win98~ | 仅分辨率/刷新率 |
| `QueryDisplayConfig`/`SetDisplayConfig` | Vista+ | 完整（位置/旋转/拓扑） |

混合策略：`ChangeDisplaySettingsEx` 改分辨率，`SetDisplayConfig` 改位置/旋转/主屏。

## 难点与对策

### 1. QueryDisplayConfig 返回大量无效路径

虚拟显示器驱动（向日葵 OrayIddDriver）产生 30+ 条路径，大部分 mode 索引越界，且破坏 SetDisplayConfig 调用。

**对策**：
- 按 GDI 名去重 + mode 数组越界时回退 `EnumDisplaySettings`
- `apply_filtered()` 过滤掉具有无效 mode 索引和类型不匹配的路径
- `set_display_config_available()` 检测 SDC 是否可用（被 OrayIddDriver 破坏时自动禁用相关功能）

### 2. DISPLAYCONFIG_TARGET_DEVICE_NAME 调用失败

`DisplayConfigGetDeviceInfo(GET_TARGET_NAME)` 在该系统上返回 `ERROR_INVALID_PARAMETER`。

**对策**：回退到 `EnumDisplayDevices` 获取适配器/监视器名称。

### 3. DEVMODE 结构体布局

DEVMODE 含打印/显示共用的 union（16 字节），字段偏移必须精确。

**对策**：使用显示专用分支（`dmPosition` + `dmDisplayOrientation` + `dmDisplayFixedOutput`），确保 `dmPelsWidth` 等字段偏移正确。

## 编译

Nuitka `--onefile` 将 Python → C → exe 打包为单文件：

```bash
# Python ≥ 3.13 使用 zig 编译器
nuitka --standalone --onefile --assume-yes-for-downloads winrandr

# Python ≤ 3.12 使用 MinGW
nuitka --standalone --onefile --mingw64 --assume-yes-for-downloads winrandr
```

首次构建自动下载 zig 或 MinGW（取决于 Python 版本）。

## 未来扩展

- [x] `--reflect xy` 镜像翻转（GDI）
- [ ] `--reflect x` / `--reflect y`（需要 GPU 私有 API）
- [x] `--brightness` 亮度调节（伽马校正，类 xrandr）
- [x] `--output` JSON 格式
- [x] 物理尺寸显示（GDI GetDeviceCaps）
- [ ] `--scale` / `--transform` 缩放变换
- [ ] `--fb` 设置帧缓冲大小
- [x] EDID 信息读取（从注册表 `SYSTEM\CurrentControlSet\Enum\DISPLAY\{id}\{instance}\Device Parameters` 读取并解析）
- [ ] 配置文件持久化
