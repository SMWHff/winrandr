# xrandr 使用参考

`xrandr` 是 X11 RandR（Resize and Rotate）扩展的命令行接口，用于查询和修改显示器配置。

## 命令概要

```
xrandr [--help] [--display name] [-q] [-v] [--verbose] [--dryrun]
       [--screen snum] [--q1] [--q12] [--current] [--noprimary]
       [--panning wxh[+x+y[/...]]] [--scale x[y]] [--scale-from wxh]
       [--transform a,b,c,d,e,f,g,h,i] [--primary] [--prop]
       [--fb wxh] [--fbmm wxh] [--dpi dpi] [--dpi from-output]
       [--newmode name mode] [--rmmode name] [--addmode output name]
       [--delmode output name]
       [--output output] [--auto] [--mode mode] [--preferred] [--pos xxy]
       [--rate rate] [--reflect x|y|xy] [--rotate normal|left|right|inverted]
       [--left-of output] [--right-of output] [--above output]
       [--below output] [--same-as output] [--set property value]
       [--off] [--crtc crtc] [--gamma r[:g[:b]]] [--brightness brightness]
       [--listproviders] [--setprovideroutputsource p s]
       [--setprovideroffloadsink p s] [--listmonitors]
       [--listactivemonitors] [--setmonitor name geo outputs] [--delmonitor name]
```

## 全局选项

| 选项 | 说明 |
|------|------|
| `--help` | 打印帮助信息 |
| `-v`, `--version` | 打印版本号 |
| `--verbose` | 详细输出：显示伽马/亮度近似值，报告配置过程 |
| `-q`, `--query` | 查询当前显示状态 |
| `--dryrun` | 预演模式，不实际更改 |
| `--nograb` | 不锁定屏幕（获取的数据可能过时） |
| `-d`, `--display name` | 选择 X display |
| `--screen snum` | 选择 X screen |
| `--q1` | 强制使用 RandR 1.1 协议 |
| `--q12` | 强制使用 RandR 1.2 协议 |

## 查询选项

| 选项 | 说明 |
|------|------|
| `--current` | 返回当前配置（不重新探测硬件） |
| `--prop` | 显示输出属性 |

## 单显示器配置

| 选项 | 说明 |
|------|------|
| `--output name` | 选择要配置的显示器 |
| `--auto` | 启用已连接显示器（首选分辨率），关闭已断开的 |
| `--mode WxH` | 设置分辨率 |
| `--preferred` | 使用首选分辨率 |
| `--rate Hz` | 设置刷新率 |
| `--pos XxY` | 设置桌面位置 |
| `--rotate normal\|left\|right\|inverted` | 设置旋转（normal=0°, left=90°, inverted=180°, right=270°） |
| `--reflect normal\|x\|y\|xy` | 镜像翻转 |
| `--left-of output` | 放在另一显示器左侧 |
| `--right-of output` | 放在另一显示器右侧 |
| `--above output` | 放在另一显示器上方 |
| `--below output` | 放在另一显示器下方 |
| `--same-as output` | 镜像另一显示器（同位置） |
| `--primary` | 设为主显示器 |
| `--off` | 关闭显示器 |

## 伽马与亮度

| 选项 | 说明 |
|------|------|
| `--gamma r[:g[:b]]` | 伽马校正（浮点数，三个通道独立） |
| `--brightness val` | 软件亮度倍增（0.1~2.0，乘以伽马表） |

## 变换与缩放

| 选项 | 说明 |
|------|------|
| `--scale x[y]` | 缩放输出（>1 压缩，<1 放大） |
| `--scale-from WxH` | 从指定帧缓冲区域缩放 |
| `--transform a,b,c,d,e,f,g,h,i` | 3×3 变换矩阵（透视校正、梯形校正） |
| `--filter bilinear\|nearest` | 缩放滤镜 |

## 虚拟桌面

| 选项 | 说明 |
|------|------|
| `--fb WxH` | 设置帧缓冲总大小 |
| `--fbmm WxH` | 设置物理尺寸（mm） |
| `--dpi dpi` | 设置 DPI |
| `--panning WxH[+X+Y[/...]]` | 设置平移参数 |

## 自定义模式

| 选项 | 说明 |
|------|------|
| `--newmode name clock hdisp hs hsync htotal vdisp vs vsync vtotal [flags]` | 添加自定义模式（用 `cvt` 工具生成） |
| `--rmmode name` | 删除模式 |
| `--addmode output name` | 为输出添加模式 |
| `--delmode output name` | 从输出删除模式 |

## 多 GPU

| 选项 | 说明 |
|------|------|
| `--listproviders` | 列出显卡提供商 |
| `--setprovideroutputsource p s` | 设置输出源 |
| `--setprovideroffloadsink p s` | 设置渲染卸载目标 |

## 常用示例

**基本查询：**
```bash
xrandr -q
```

**设置分辨率刷新率：**
```bash
xrandr --output HDMI-1 --mode 1920x1080 --rate 60
```

**双屏左右排列：**
```bash
xrandr --output eDP-1 --auto --output HDMI-1 --auto --right-of eDP-1
```

**镜像：**
```bash
xrandr --output HDMI-1 --same-as eDP-1
```

**旋转：**
```bash
xrandr --output HDMI-1 --rotate left
```

**自定义模式：**
```bash
cvt 1920 1080 60
xrandr --newmode "1920x1080_60.00" 173.00 1920 2048 2248 2576 1080 1083 1088 1120 -hsync +vsync
xrandr --addmode HDMI-1 "1920x1080_60.00"
xrandr --output HDMI-1 --mode "1920x1080_60.00"
```

**亮度：**
```bash
xrandr --output eDP-1 --brightness 0.7
```

**伽马（红/绿/蓝独立）：**
```bash
xrandr --output eDP-1 --gamma 1.0:0.9:0.8
```

**关闭：**
```bash
xrandr --output VGA-1 --off
```

**梯形校正（投影仪）：**
```bash
xrandr --output VGA-1 --transform 1.24,0.16,-124,0,1.24,0,0,0.000316,1
```

## 输出格式

```
Screen 0: minimum 320 x 200, current 1920 x 1080, maximum 8192 x 8192
eDP-1 connected 1920x1080+0+0 (normal) 309mm x 174mm
   1920x1080     60.00*+  48.00
   1680x1050     60.00
   1280x1024     60.00
   1024x768      60.00
HDMI-1 disconnected
```

标记说明：
- `*` = 当前模式
- `+` = 推荐模式
- `connected` = 已连接
- `disconnected` = 未连接

## winrandr 对照表

| xrandr | winrandr | 状态 |
|--------|----------|------|
| `xrandr` | `winrandr` | ✅ |
| `--listmodes` | `--listmodes` | ✅ |
| `--output name` | `--output name` | ✅ |
| `--mode WxH` | `--mode WxH` | ✅ |
| `--rate Hz` | `--rate Hz` | ✅ |
| `--pos XxY` | `--pos XxY` | ✅ |
| `--rotate` | `--rotate` | ✅ |
| `--primary` | `--primary` | ✅ |
| `--off` | `--off` | ✅ |
| `--brightness` | `--brightness` | ✅ |
| `--reflect xy` | `--reflect xy` | ✅ |
| `--gamma r:g:b` | `--gamma` | ✅ |
| `--left-of / --right-of` | `--left-of / --right-of` | ✅ |
| `--above / --below` | `--above / --below` | ✅ |
| `--same-as` | `--same-as` | ✅ |
| `--reflect x / --reflect y` | — | ❌ 无标准 Win32 API |
| `--scale / --transform` | — | ❌ 无标准 Win32 API |
| `--fb` | — | ❌ 无标准 Win32 API |
| `--panning` | — | ❌ 无标准 Win32 API |
| `--newmode / --addmode` | — | ❌ 无标准 Win32 API |
| `--listproviders` | — | ❌ 无标准 Win32 API |
