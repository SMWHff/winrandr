# winrandr

Windows 上的 xrandr 替代工具。通过 Win32 API 管理显示器布局、分辨率、刷新率、旋转、亮度、伽马校正等。

```bash
winrandr                              # 列出所有显示器
winrandr --output DISPLAY1 --mode 1920x1080 --rate 60   # 设置分辨率
winrandr --output DISPLAY1 --left-of DISPLAY2           # 相对定位
winrandr --output DISPLAY1 --brightness 0.8             # 调亮度
winrandr --output DISPLAY1 --gamma 1.0:0.9:0.8          # 伽马校正
```

[详细文档](docs/usage.md) · [xrandr 对照](docs/xrandr-reference.md) · [架构设计](docs/architecture.md)

## 安装

```bash
pip install winrandr
# 或从源码运行
uv run python -m winrandr --help
```

## 特性

- 零外部依赖（仅 Python 标准库 + ctypes）
- 类 xrandr 命令行界面
- JSON 输出（`--json`）
- 支持：分辨率、位置、旋转、主屏、开关、亮度、伽马、相对定位
