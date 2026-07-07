"""CLI 入口：argparse 解析 + xrandr 风格输出格式化。"""
import argparse
import sys
import os
import logging

from winrandr import __version__
from winrandr.api import (
    list_displays, set_resolution, set_preferred_resolution,
    set_position, set_position_relative, set_rotation,
    set_primary, set_off, set_brightness, set_gamma, set_reflect,
    set_auto, list_providers, get_display_props,
)
from winrandr.win32.constants import ROTATION_FROM_NAME
from winrandr.formatter import format_displays, format_monitor_list, _short_name

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

def _normalize_name(name: str) -> str:
    n = name.strip().upper()
    prefix = "\\\\.\\"
    if n.startswith(prefix):
        return n
    if n.startswith("DISPLAY"):
        return prefix + n
    return prefix + "DISPLAY" + n if n.isdigit() else name

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
    parser.add_argument("-q", "--query", action="store_true", help="查询当前显示状态")
    parser.add_argument("--current", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--prop", action="store_true", help="显示显示器扩展属性（设备 ID、状态标志等）")
    parser.add_argument("--dry-run", "--dryrun", action="store_true", help="模拟操作，不实际更改配置")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细日志输出（调试用）")
    parser.add_argument("--output", "-o", help="显示器名（如 DISPLAY1）")
    parser.add_argument("--auto", action="store_true", help="启用显示器并使用首选分辨率")
    parser.add_argument("--mode", "-m", help="分辨率（如 1920x1080）")
    parser.add_argument("-s", "--size", help=argparse.SUPPRESS)
    parser.add_argument(
        "--orientation",
        choices=["normal", "inverted", "left", "right", "0", "1", "2", "3"],
        help=argparse.SUPPRESS,
    )
    parser.add_argument("--rate", "-r", type=float, help="刷新率（Hz）")
    parser.add_argument("--pos", "-p", help="桌面位置（如 0x0, +1920+0; 负数用 --pos=-1920x0）")
    parser.add_argument(
        "--rotate", choices=["normal", "left", "right", "inverted"],
        help="旋转方向",
    )
    parser.add_argument("--primary", action="store_true", help="设为主显示器")
    parser.add_argument("--preferred", action="store_true", help="设为注册表首选分辨率")
    parser.add_argument("--off", action="store_true", help="关闭显示器")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出显示器信息")
    parser.add_argument(
        "--brightness", type=float, metavar="VAL",
        help="亮度值（0.1-2.0，1.0 为正常）",
    )
    parser.add_argument(
        "--reflect", choices=["normal", "x", "y", "xy"],
        help="镜像翻转（仅 xy 支持，等同于旋转 180°）",
    )
    parser.add_argument("-x", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("-y", action="store_true", help=argparse.SUPPRESS)
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
    parser.add_argument("--listproviders", action="store_true", help="列出 GPU 适配器")
    parser.add_argument("--listmonitors", action="store_true", help="列出带编号的显示器列表")
    parser.add_argument("--listactivemonitors", action="store_true", help=argparse.SUPPRESS)
    return parser

def _fail(msg: str):
    print(f"错误: {msg}", file=sys.stderr)
    sys.exit(1)

def main():
    parser = _build_parser()
    args = parser.parse_args()

    _setup_logging()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 兼容别名转换（必须在 mod_ops 判断之前）
    if args.size and not args.mode:
        args.mode = args.size
    if args.orientation and not args.rotate:
        args.rotate = args.orientation.replace("0", "normal").replace("1", "normal") \
            .replace("2", "inverted").replace("3", "left") \
            if args.orientation in ("0", "1", "2", "3") else args.orientation
    if args.listactivemonitors:
        args.listmonitors = True
    if args.reflect == "normal":
        args.reflect = None
    if args.x and args.y:
        args.reflect = "xy"
    elif args.x:
        args.reflect = "x"
    elif args.y:
        args.reflect = "y"

    mod_ops = [args.mode, args.pos, args.rotate, args.primary, args.preferred,
               args.off, args.brightness, args.reflect, args.gamma,
               args.left_of, args.right_of, args.above, args.below, args.same_as,
               args.auto]

    if args.listproviders:
        providers = list_providers()
        if not providers:
            print("未检测到 GPU 适配器。")
        else:
            print("Providers:")
            for i, p in enumerate(providers):
                print(f"  Provider {i}: {p['string']} ({p['name']})")
        return

    if args.listmonitors:
        displays = list_displays()
        if not displays:
            print("未检测到显示器。")
        else:
            print(format_monitor_list(displays))
        return

    if not any(mod_ops):
        displays = list_displays()
        if not displays:
            print("未检测到活动显示器。")
            sys.exit(1)
        if args.output:
            device_name = _normalize_name(args.output)
            displays = [d for d in displays if d.name == device_name]
            if not displays:
                _fail(f"未找到显示器: {args.output}")
        if args.prop:
            for d in displays:
                d.properties = get_display_props(d.name)
        if args.json:
            from dataclasses import asdict
            import json
            print(json.dumps([asdict(d) for d in displays],
                             indent=2, ensure_ascii=False))
        else:
            print(format_displays(displays))
        return

    if not args.output:
        parser.error("--output 为必填参数")

    device_name = _normalize_name(args.output)

    if args.auto:
        if not args.dry_run:
            if not set_auto(device_name):
                _fail("自动配置失败")
        print(f"已启用 {args.output}（首选分辨率）")

    if args.mode:
        if "x" not in args.mode.lower():
            parser.error("--mode 格式必须为 WIDTHxHEIGHT（如 1920x1080）")
        parts = args.mode.lower().split("x")
        try:
            width, height = int(parts[0]), int(parts[1])
        except ValueError:
            parser.error("--mode 格式错误")
        rate = args.rate or 0
        if not args.dry_run:
            if not set_resolution(device_name, width, height, rate):
                _fail("设置分辨率失败")
        print(f"已设置 {args.output} 为 {width}x{height}" +
              (f" @ {rate}Hz" if rate else ""))

    if args.pos:
        p = args.pos.strip()
        if "x" not in p.lower():
            parser.error("--pos 格式必须为 XxY（如 0x0 或 +1920+0）")
        parts = p.lower().split("x")
        if len(parts) != 2:
            parser.error("--pos 格式错误")
        try:
            x, y = int(parts[0].lstrip("+")), int(parts[1].lstrip("+"))
        except ValueError:
            parser.error("--pos 格式错误")
        if not args.dry_run:
            if not set_position(device_name, x, y):
                _fail("设置位置失败（SDC 可能不可用）")
        print(f"已将 {args.output} 移动到 ({x}, {y})")

    if args.rotate:
        deg = ROTATION_FROM_NAME[args.rotate]
        if not args.dry_run:
            if not set_rotation(device_name, deg):
                _fail("设置旋转失败（SDC 可能不可用）")
        print(f"已将 {args.output} 旋转为 {args.rotate} ({deg}°)")

    if args.primary:
        if not args.dry_run:
            if not set_primary(device_name):
                _fail("设置主显示器失败（SDC 可能不可用）")
        print(f"已将 {args.output} 设为主显示器")

    if args.preferred:
        if not args.dry_run:
            if not set_preferred_resolution(device_name):
                _fail("设置首选分辨率失败")
        print(f"已将 {args.output} 设为首选分辨率")

    if args.off:
        if not args.dry_run:
            if not set_off(device_name):
                _fail("关闭显示器失败（SDC 可能不可用）")
        print(f"已关闭 {args.output}")

    if args.brightness is not None:
        if args.brightness < 0.1 or args.brightness > 2.0:
            print(f"警告: 亮度值 {args.brightness} 超出建议范围 0.1-2.0", file=sys.stderr)
        if not args.dry_run:
            if not set_brightness(device_name, args.brightness):
                _fail("设置亮度失败（伽马表可能不可用）")
        print(f"已将 {args.output} 亮度设为 {args.brightness}")

    if args.reflect:
        if args.reflect in ("x", "y"):
            _fail(f"单轴镜像翻转（-{args.reflect}）在 Windows 上无标准 API 支持")
        if not args.dry_run:
            if not set_reflect(device_name, args.reflect):
                _fail("设置镜像翻转失败")
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
        if not args.dry_run:
            if not set_gamma(device_name, r, g, b):
                _fail("设置伽马校正失败（伽马表可能不可用）")
        print(f"已将 {args.output} 伽马设为 {r}:{g}:{b}")

    rel_map = {
        "left_of": "left-of", "right_of": "right-of",
        "above": "above", "below": "below", "same_as": "same-as",
    }
    for attr, relation in rel_map.items():
        ref = getattr(args, attr, None)
        if ref:
            if not args.dry_run:
                if not set_position_relative(device_name, ref, relation):
                    _fail("相对定位失败（SDC 可能不可用）")
            print(f"已将 {args.output} 放在 {ref} 的 {relation}")
            break

if __name__ == "__main__":
    main()
