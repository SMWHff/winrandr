# winrandr — 使用指南

Windows 上的 xrandr 替代工具，通过 Win32 API 管理显示器布局、分辨率、刷新率和旋转方向。

## 安装

### 下载 exe

从 Releases 下载 `winrandr.exe` 放入 PATH 目录。

### pip 安装（暂不支持）

`winrandr` 尚未发布到 PyPI。请使用 exe 或源码方式运行。

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
Screen 0: minimum 320 x 200, current 1920 x 1080, maximum 32767 x 32767

DISPLAY1 connected primary 1920x1080+0+0 (normal left inverted right) 527mm x 296mm
   1920x1080     60.00*+
   1680x1050     60.00
   1280x1024     60.02
   ...

DISPLAY2 disconnected
```

- `*` = 当前模式
- `+` = 推荐/首选模式
- `(normal left inverted right)` = 所有支持方向
- `1920x1080+0+0` = 分辨率 1920×1080，桌面位置 (0, 0)
- `527mm x 296mm` = 物理尺寸

### 列出可用分辨率

```bash
winrandr --listmodes
```

输出：

```
DISPLAY1:
   1920x1080     60.00*+   59.94
   1680x1050     59.95
   1280x1024     60.02
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

### Shell 自动补全

**PowerShell：**
```powershell
. ./scripts/completions/completions.ps1
# 或永久生效：
Add-Content $PROFILE "`n. 'C:\path\to\winrandr\scripts\completions.ps1'"
```

**Bash / Zsh（WSL / Cygwin / Git Bash）：**
```bash
source scripts/completions/completions.bash
# 永久生效：
echo "source '$(pwd)/scripts/completions/completions.bash'" >> ~/.bashrc
```

支持参数名和显示器名的 Tab 补全，显示器名从工具实际输出动态获取。

### 扩展属性

```bash
winrandr --prop
```

输出包含显示器设备 ID、状态标志、适配器路径等扩展信息：

```
Screen 0: current 1924 x 1080, dpi 93x93

 *DISPLAY1 connected 1920x1080+4+0 (normal) 527mm x 296mm (Generic PnP Monitor)
     60.0 Hz
    device id: MONITOR\AOC2411\{...}
    state flags: attached
    adapter: PCI\VEN_8086&DEV_5912\...
```

### JSON 输出

```bash
winrandr --json
winrandr --listmodes --json
winrandr --prop --json         # 包含扩展属性
```

适用于脚本解析，输出所有显示器信息及可用模式的完整 JSON。

### 设置亮度

```bash
winrandr --output DISPLAY1 --brightness 0.8    # 调暗指定显示器
winrandr --brightness 0.7                      # 批量调暗所有已连接显示器
winrandr --output DISPLAY1 --brightness 1.0    # 正常
winrandr --output DISPLAY1 --brightness 1.2    # 调亮
```

通过伽马校正实现，范围 0.1~2.0。与 xrandr --brightness 行为一致。不带 `--output` 时应用到所有已连接显示器。

### 镜像翻转

```bash
winrandr --output DISPLAY1 --reflect xy        # 等同旋转 180°
```

注意：Windows 仅支持 `xy`（双向翻转），`x` 和 `y` 暂不支持。

### 详细模式

```bash
winrandr --verbose
winrandr --verbose --listmodes
```

开启 DEBUG 级别日志，输出到 stderr 和 `logs/winrandr.log`，便于调试问题。

### 伽马校正

```bash
winrandr --output DISPLAY1 --gamma 1.0:0.9:0.8    # 红 1.0, 绿 0.9, 蓝 0.8
winrandr --gamma 0.8                               # 批量设置所有显示器
winrandr --output DISPLAY1 --gamma 0.8             # 三通道统一 0.8
```

三通道独立伽马校正，与 xrandr `--gamma` 行为一致。接受 `R:G:B` 或单一值格式。不带 `--output` 时应用到所有已连接显示器。

### 相对定位

```bash
winrandr --output DISPLAY1 --left-of DISPLAY2      # DISPLAY1 放在 DISPLAY2 左侧
winrandr --output DISPLAY1 --right-of DISPLAY2     # DISPLAY1 放在 DISPLAY2 右侧
winrandr --output DISPLAY1 --above DISPLAY2        # DISPLAY1 放在 DISPLAY2 上方
winrandr --output DISPLAY1 --below DISPLAY2        # DISPLAY1 放在 DISPLAY2 下方
winrandr --output DISPLAY1 --same-as DISPLAY2      # DISPLAY1 与 DISPLAY2 同位置（镜像）
```

以上选项互斥，与 xrandr `--left-of` / `--right-of` / `--above` / `--below` / `--same-as` 行为一致。

### 配置存档（Profile）

保存/恢复显示器布局，方便在不同场景间切换（比如外接显示器 docking 和单独使用笔记本）。

```bash
winrandr --save-profile docked                     # 保存当前布局为存档
winrandr --save-profile docked --dry-run           # 预览将保存的配置，不实际写入
winrandr --load-profile docked                     # 恢复存档布局
winrandr --load-profile docked --dry-run           # 预览变更，不实际执行
winrandr --list-profiles                           # 列出所有存档
winrandr --list-profiles --json                    # JSON 格式输出
winrandr --delete-profile docked                   # 删除存档
```

存档保存在 `%APPDATA%\winrandr\profiles.json`。恢复时按顺序执行启用显示器、设置位置、旋转、分辨率，最后设置主显示器。跳过的显示器会输出警告。

### 闪屏识别显示器

```bash
winrandr --identify --output DISPLAY1             # 闪 3 次白屏识别显示器
```

通过伽马校正表快速切换全白/全黑来闪烁指定显示器，2 秒后自动恢复。

## 显示器名称

- 标准名称：`DISPLAY1`、`DISPLAY2`
- 可省略 `\\.\` 前缀
- 虚拟显示器（如向日葵）可能使用非标准名

## 构建 exe

```bash
bash scripts/build/build.sh
```

依赖 `uv`，首次构建自动下载 zig 编译器。

## 日志

日志文件：`logs/winrandr.log`
