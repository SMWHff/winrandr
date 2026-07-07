"""CLI 入口：argparse 解析 + xrandr 风格输出格式化。"""

import argparse
import sys
import os
import logging

from winrandr import __version__
from winrandr.api import (
    list_displays, set_resolution, set_position,
    set_position_relative, set_rotation, set_primary,
    set_off, set_brightness, set_gamma, set_reflect,
)
from winrandr.constants import ROTATION_FROM_NAME


def _setup_logging():
    log_dir = os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
    )
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "winrandr.log"), encoding="utf-8"),
            logging.StreamHandler(sys.stderr),
        ],
    )


def _short_name(name: str) -> str:
    return name.replace("\\\\.\\", "").strip()


def _normalize_name(name: str) -> str:
    n = name.strip().upper()
    prefix = "\\\\.\\"
    if n.startswith(prefix):
        return n
    if n.startswith("DISPLAY"):
        return prefix + n
    return prefix + "DISPLAY" + n if n.isdigit() else name


def _format_displays(displays, list_modes: bool = False):
    """以类 xrandr 风格输出显示器信息。"""
    lines = []

    # 计算总虚拟桌面大小
    if displays:
        max_x = max((d.position_x + d.width) for d in displays if d.connected)
        max_y = max((d.position_y + d.height) for d in displays if d.connected)
        lines.append(f"Screen 0: current {max_x} x {max_y}")
        lines.append("")

    for d in displays:
        name = _short_name(d.name)
        primary = "*" if d.is_primary else " "
        status = "connected" if d.connected else "disconnected"
        friendly = f" ({d.friendly_name})" if d.friendly_name else ""

        if d.connected:
            rot_name = next(
                (k for k, v in ROTATION_FROM_NAME.items() if v == d.rotation), "normal"
            )
            mm = f" {d.width_mm}mm x {d.height_mm}mm" if d.width_mm and d.height_mm else ""
            lines.append(
                f" {primary}{name} {status} {d.width}x{d.height}+{d.position_x}+{d.position_y}"
                f" ({rot_name}){mm}{friendly}"
            )
        else:
            lines.append(f" {primary}{name} {status}{friendly}")

        if d.connected and list_modes and d.modes:
            _fmt_modes(lines, d.modes)
        elif d.connected and not list_modes:
            rr_str = f"  {d.refresh_rate} Hz" if d.refresh_rate > 0 else ""
            if rr_str:
                lines.append(f"   {rr_str}")

        lines.append("")

    return "\n".join(lines)


def _fmt_modes(lines, modes):
    """格式化模式列表，类似 xrandr 的显示方式。"""
    from collections import defaultdict

    # 按分辨率分组
    grouped = defaultdict(list)
    for m in modes:
        grouped[(m.width, m.height)].append(m)

    for (w, h), mlist in sorted(grouped.items()):
        rates = []
        has_cur = any(m.is_current for m in mlist)
        for m in sorted(mlist, key=lambda x: -x.refresh_rate):
            tag = ""
            if m.is_current:
                tag += "*"
            if has_cur:
                tag += "+" if m.is_preferred else ""
            rates.append(f"{m.refresh_rate:.2f}{tag}")
        lines.append(f"   {w}x{h}  {' '.join(rates)}")


def _build_parser():
    parser = argparse.ArgumentParser(
        description="winrandr — 类 xrandr 的 Windows 显示配置工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  winrandr                             列出所有显示器
  winrandr --listmodes                 列出所有显示器及其可用分辨率
  winrandr --output DISPLAY1 --mode 1920x1080
  winrandr --output DISPLAY1 --mode 1920x1080 --rate 60
  winrandr --output DISPLAY1 --pos 0x0
  winrandr --output DISPLAY1 --rotate normal
  winrandr --output DISPLAY1 --primary
  winrandr --output DISPLAY1 --off
  winrandr --output DISPLAY1 --gamma 1.0:0.9:0.8
  winrandr --output DISPLAY1 --left-of DISPLAY2
  winrandr --output DISPLAY1 --right-of DISPLAY2
  winrandr --output DISPLAY1 --above DISPLAY2
  winrandr --output DISPLAY1 --below DISPLAY2
  winrandr --output DISPLAY1 --same-as DISPLAY2
        """,
    )
    parser.add_argument("--version", action="version", version=f"winrandr {__version__}")
    parser.add_argument("--listmodes", action="store_true", help="列出每个显示器所有可用分辨率")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细日志输出（调试用）")
    parser.add_argument("--output", "-o", help="显示器名（如 DISPLAY1）")
    parser.add_argument("--mode", "-m", help="分辨率（如 1920x1080）")
    parser.add_argument("--rate", "-r", type=float, help="刷新率（Hz）")
    parser.add_argument("--pos", "-p", help="桌面位置（如 0x0 或 +1920+0）")
    parser.add_argument(
        "--rotate", choices=["normal", "left", "right", "inverted"],
        help="旋转方向",
    )
    parser.add_argument("--primary", action="store_true", help="设为主显示器")
    parser.add_argument("--off", action="store_true", help="关闭显示器")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出显示器信息")
    parser.add_argument(
        "--brightness", type=float, metavar="VAL",
        help="亮度值（0.1-2.0，1.0 为正常）",
    )
    parser.add_argument(
        "--reflect", choices=["x", "y", "xy"],
        help="镜像翻转（仅 xy 支持，等同于旋转 180°）",
    )
    parser.add_argument(
        "--gamma", metavar="R:G:B",
        help="伽马校正（如 1.0:0.9:0.8，三通道独立）",
    )
    # 相对定位（互斥）
    rel_group = parser.add_mutually_exclusive_group()
    rel_group.add_argument("--left-of", metavar="REF", help="放在参考显示器左侧")
    rel_group.add_argument("--right-of", metavar="REF", help="放在参考显示器右侧")
    rel_group.add_argument("--above", metavar="REF", help="放在参考显示器上方")
    rel_group.add_argument("--below", metavar="REF", help="放在参考显示器下方")
    rel_group.add_argument("--same-as", metavar="REF", help="与参考显示器同位置（镜像）")
    return parser


def main():
    parser = _build_parser()
    args = parser.parse_args()

    _setup_logging()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    mod_ops = [args.mode, args.pos, args.rotate, args.primary, args.off,
               args.brightness, args.reflect, args.gamma,
               args.left_of, args.right_of, args.above, args.below, args.same_as]

    if not any(mod_ops):
        displays = list_displays()
        if not displays:
            print("未检测到活动显示器。")
            sys.exit(1)
        if args.json:
            from dataclasses import asdict
            import json
            print(json.dumps([asdict(d) for d in displays],
                             indent=2, ensure_ascii=False))
        else:
            print(_format_displays(displays, list_modes=args.listmodes))
        return

    if not args.output:
        parser.error("--output 为必填参数")

    device_name = _normalize_name(args.output)

    if args.mode:
        if "x" not in args.mode.lower():
            parser.error("--mode 格式必须为 WIDTHxHEIGHT（如 1920x1080）")
        parts = args.mode.lower().split("x")
        try:
            width, height = int(parts[0]), int(parts[1])
        except ValueError:
            parser.error("--mode 格式错误")
        rate = args.rate or 0
        if not set_resolution(device_name, width, height, rate):
            sys.exit(1)
        print(f"已设置 {args.output} 为 {width}x{height}" +
              (f" @ {rate}Hz" if rate else ""))

    if args.pos:
        p = args.pos.replace("+", " ").strip()
        if "x" not in p:
            parser.error("--pos 格式必须为 XxY（如 0x0 或 +1920+0）")
        parts = p.split("x")
        try:
            x, y = int(parts[0].strip()), int(parts[1].strip())
        except ValueError:
            parser.error("--pos 格式错误")
        if not set_position(device_name, x, y):
            sys.exit(1)
        print(f"已将 {args.output} 移动到 ({x}, {y})")

    if args.rotate:
        deg = ROTATION_FROM_NAME[args.rotate]
        if not set_rotation(device_name, deg):
            sys.exit(1)
        print(f"已将 {args.output} 旋转为 {args.rotate} ({deg}°)")

    if args.primary:
        if not set_primary(device_name):
            sys.exit(1)
        print(f"已将 {args.output} 设为主显示器")

    if args.off:
        if not set_off(device_name):
            sys.exit(1)
        print(f"已关闭 {args.output}")

    if args.brightness is not None:
        if not set_brightness(device_name, args.brightness):
            sys.exit(1)
        print(f"已将 {args.output} 亮度设为 {args.brightness}")

    if args.reflect:
        if not set_reflect(device_name, args.reflect):
            sys.exit(1)
        print(f"已将 {args.output} 设为 {args.reflect} 镜像翻转")

    if args.gamma:
        parts = args.gamma.split(":")
        try:
            vals = [float(x) for x in parts]
        except ValueError:
            parser.error("--gamma 格式错误，使用 R:G:B 或单一值")
        if len(vals) == 1:
            r = g = b = vals[0]
        elif len(vals) == 3:
            r, g, b = vals
        else:
            parser.error("--gamma 格式错误，使用 R:G:B 或单一值")
        if not set_gamma(device_name, r, g, b):
            sys.exit(1)
        print(f"已将 {args.output} 伽马设为 {r}:{g}:{b}")

    rel_map = {
        "left_of": "left-of", "right_of": "right-of",
        "above": "above", "below": "below", "same_as": "same-as",
    }
    for attr, relation in rel_map.items():
        ref = getattr(args, attr, None)
        if ref:
            if not set_position_relative(device_name, ref, relation):
                sys.exit(1)
            print(f"已将 {args.output} 放在 {ref} 的 {relation}")
            break

if __name__ == "__main__":
    main()
