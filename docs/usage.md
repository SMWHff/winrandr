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

### 关闭显示器

```bash
winrandr --output DISPLAY1 --off
```

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
