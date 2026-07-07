# winrandr — 使用指南

Windows 上的 xrandr 替代工具，通过 Win32 API 管理显示器布局、分辨率、刷新率和旋转方向。

## 安装

### 下载 exe

从 Releases 下载 `winrandr.exe` 放入 PATH 目录。

### pip 安装

```bash
pip install winrandr
```

### 源码运行

```bash
git clone <repo>
cd winrandr
uv run python -m winrandr
```

## 用法

### 列出显示器

```bash
winrandr
```

输出（类 xrandr 风格）：

```
Screen 0: current 1920 x 1080

 *DISPLAY1 connected 1920x1080+4+0 (normal) (Generic PnP Monitor)
   60.0 Hz

  DISPLAY2 disconnected
```

- `*` = 主显示器
- `connected` / `disconnected` = 连接状态
- `1920x1080+4+0` = 分辨率 1920×1080，桌面位置 (4, 0)
- `normal` = 旋转方向

### 列出可用分辨率

```bash
winrandr --listmodes
```

输出：

```
Screen 0: current 1920 x 1080

 *DISPLAY1 connected 1920x1080+4+0 (normal) (Generic PnP Monitor)
   1920x1080  60.00*
   1680x1050  59.95
   1280x1024  60.02
   ...
```

- `*` = 当前使用模式
- `+` = 推荐模式

### 设置分辨率

```bash
winrandr --output DISPLAY1 --mode 1920x1080
winrandr --output DISPLAY1 --mode 1920x1080 --rate 60
```

### 设置桌面位置

```bash
winrandr --output DISPLAY1 --pos 0x0
winrandr --output DISPLAY2 --pos 1920x0     # 放在 DISPLAY1 右侧
```

### 设置旋转

```bash
winrandr --output DISPLAY1 --rotate normal     # 0°
winrandr --output DISPLAY1 --rotate left       # 90°
winrandr --output DISPLAY1 --rotate inverted   # 180°
winrandr --output DISPLAY1 --rotate right      # 270°
```

### 设为主显示器

```bash
winrandr --output DISPLAY1 --primary
```

### 首选分辨率

```bash
winrandr --output DISPLAY1 --preferred
```

恢复到注册表中保存的默认分辨率和刷新率。

### 自动配置

```bash
winrandr --output DISPLAY1 --auto            # 启用显示器并使用首选分辨率
```

等效于 xrandr `--auto`，启用指定显示器并设置为首选分辨率。与 `--dry-run` 联用可模拟操作。

### 模拟操作

```bash
winrandr --output DISPLAY1 --mode 1920x1080 --dry-run   # 只显示将执行的操作，不实际更改
winrandr --output DISPLAY1 --auto --dry-run
```

`--dry-run` 可加在任何修改操作前，输出模拟信息但不实际调用 Win32 API。用于安全预览配置变更。

### 列出 GPU 适配器

```bash
winrandr --listproviders
```

输出：
```
Providers:
  Provider 0: Intel(R) HD Graphics 630 (\\.\DISPLAY1)
  Provider 1: OrayIddDriver Device (\\.\DISPLAY3)
```

列出所有 GPU 适配器和虚拟显示驱动。

### 关闭显示器

```bash
winrandr --output DISPLAY1 --off
```

### Shell 自动补全（PowerShell）

```powershell
. ./scripts/completions.ps1
# 或永久生效：
Add-Content $PROFILE "`n. 'C:\path\to\winrandr\scripts\completions.ps1'"
```

支持参数名、显示器名（从 `winrandr --json` 动态获取）的 Tab 补全。

### JSON 输出

```bash
winrandr --json
winrandr --listmodes --json
```

适用于脚本解析，输出所有显示器信息及可用模式的完整 JSON。

### 设置亮度

```bash
winrandr --output DISPLAY1 --brightness 0.8    # 调暗
winrandr --output DISPLAY1 --brightness 1.0    # 正常
winrandr --output DISPLAY1 --brightness 1.2    # 调亮
```

通过伽马校正实现，范围 0.1~2.0。与 xrandr --brightness 行为一致。

### 镜像翻转

```bash
winrandr --output DISPLAY1 --reflect xy        # 等同旋转 180°
```

注意：Windows 仅支持 `xy`（双向翻转），`x` 和 `y` 暂不支持。

### 详细模式

```bash
winrandr --verbose
winrandr -v --listmodes
```

开启 DEBUG 级别日志，输出到 stderr 和 `logs/winrandr.log`，便于调试问题。

### 伽马校正

```bash
winrandr --output DISPLAY1 --gamma 1.0:0.9:0.8    # 红 1.0, 绿 0.9, 蓝 0.8
winrandr --output DISPLAY1 --gamma 0.8             # 三通道统一 0.8
```

三通道独立伽马校正，与 xrandr `--gamma` 行为一致。接受 `R:G:B` 或单一值格式。

### 相对定位

```bash
winrandr --output DISPLAY1 --left-of DISPLAY2      # DISPLAY1 放在 DISPLAY2 左侧
winrandr --output DISPLAY1 --right-of DISPLAY2     # DISPLAY1 放在 DISPLAY2 右侧
winrandr --output DISPLAY1 --above DISPLAY2        # DISPLAY1 放在 DISPLAY2 上方
winrandr --output DISPLAY1 --below DISPLAY2        # DISPLAY1 放在 DISPLAY2 下方
winrandr --output DISPLAY1 --same-as DISPLAY2      # DISPLAY1 与 DISPLAY2 同位置（镜像）
```

以上选项互斥，与 xrandr `--left-of` / `--right-of` / `--above` / `--below` / `--same-as` 行为一致。

## 显示器名称

- 标准名称：`DISPLAY1`、`DISPLAY2`
- 可省略 `\\.\` 前缀
- 虚拟显示器（如向日葵）可能使用非标准名

## 构建 exe

```bash
bash scripts/build.sh
```

依赖 `uv`，首次构建自动下载 MinGW。

## 日志

日志文件：`logs/winrandr.log`
