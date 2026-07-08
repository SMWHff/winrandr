"""CLI 入口：argparse 解析 + xrandr 风格输出格式化。"""
import argparse, sys, os, logging

from winrandr import __version__
from winrandr.api import (
    list_displays, set_resolution, set_preferred_resolution,
    set_position, set_position_relative, set_rotation,
    set_primary, set_off, set_brightness, set_gamma, set_reflect,
    set_noprimary, set_auto, list_providers, get_display_props,
)
from winrandr.win32.constants import ROTATION_FROM_NAME
from winrandr.formatter import format_displays, format_monitor_list


def _setup_logging():
    log_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs"))
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(os.path.join(log_dir, "winrandr.log"), encoding="utf-8"), logging.StreamHandler(sys.stderr)],
    )


def _normalize_name(name: str) -> str:
    n = name.strip().upper()
    prefix = "\\\\.\\"
    if n.startswith(prefix): return n
    if n.startswith("DISPLAY"): return prefix + n
    return prefix + "DISPLAY" + n if n.isdigit() else name


def _build_parser():
    p = argparse.ArgumentParser(description="winrandr — 类 xrandr 的 Windows 显示配置工具", epilog="""示例:
  winrandr                             列出所有显示器
  winrandr --output DISPLAY1 --mode 1920x1080 --rate 60
  winrandr --output DISPLAY1 --pos 0x0 --rotate normal
  winrandr --output DISPLAY1 --primary --off
  winrandr --output DISPLAY1 --left-of DISPLAY2
        """)
    p.add_argument("--version", action="version", version=f"winrandr {__version__}")
    p.add_argument("--listmodes", action="store_true", help="列出每个显示器所有可用分辨率")
    p.add_argument("-q", "--query", action="store_true", help="查询当前显示状态")
    p.add_argument("--current", action="store_true", help=argparse.SUPPRESS)
    p.add_argument("--prop", "--properties", action="store_true", help="显示显示器扩展属性（设备 ID、状态标志等）")
    p.add_argument("--dry-run", "--dryrun", action="store_true", help="模拟操作，不实际更改配置")
    p.add_argument("--verbose", "-v", action="store_true", help="详细日志输出（调试用）")
    p.add_argument("--output", "-o", help="显示器名（如 DISPLAY1）")
    p.add_argument("--auto", action="store_true", help="启用显示器并使用首选分辨率")
    p.add_argument("--mode", "-m", help="分辨率（如 1920x1080）")
    p.add_argument("-s", "--size", help=argparse.SUPPRESS)
    p.add_argument("--orientation", choices=["normal", "inverted", "left", "right", "0", "1", "2", "3"], help=argparse.SUPPRESS)
    p.add_argument("--rate", "-r", "--refresh", type=float, help="刷新率（Hz）")
    p.add_argument("--pos", "-p", help="桌面位置（如 0x0）")
    p.add_argument("--rotate", choices=["normal", "left", "right", "inverted"], help="旋转方向")
    p.add_argument("--primary", action="store_true", help="设为主显示器")
    p.add_argument("--preferred", action="store_true", help="设为注册表首选分辨率")
    p.add_argument("--off", action="store_true", help="关闭显示器")
    p.add_argument("--json", action="store_true", help="以 JSON 格式输出显示器信息")
    p.add_argument("--brightness", type=float, help="亮度值（0.1-2.0，1.0 为正常）")
    p.add_argument("--reflect", choices=["normal", "x", "y", "xy"], help="镜像翻转（仅 xy 支持）")
    p.add_argument("-x", action="store_true", help=argparse.SUPPRESS)
    p.add_argument("-y", action="store_true", help=argparse.SUPPRESS)
    p.add_argument("--gamma", metavar="R:G:B", help="伽马校正（如 1.0:0.9:0.8）")
    rg = p.add_mutually_exclusive_group()
    rg.add_argument("--left-of", metavar="REF", help="放在参考显示器左侧")
    rg.add_argument("--right-of", metavar="REF", help="放在参考显示器右侧")
    rg.add_argument("--above", metavar="REF", help="放在参考显示器上方")
    rg.add_argument("--below", metavar="REF", help="放在参考显示器下方")
    rg.add_argument("--same-as", metavar="REF", help="与参考显示器同位置（镜像）")
    p.add_argument("--noprimary", action="store_true", help="清除所有显示器的主显示器标记")
    p.add_argument("--listproviders", action="store_true", help="列出 GPU 适配器")
    p.add_argument("--listmonitors", action="store_true", help="列出带编号的显示器列表")
    p.add_argument("--listactivemonitors", action="store_true", help=argparse.SUPPRESS)
    p.add_argument("--screen", help=argparse.SUPPRESS)
    p.add_argument("--nograb", action="store_true", help=argparse.SUPPRESS)
    return p


def _fail(msg: str, suggestions: list[str] | None = None):
    print(f"错误: {msg}", file=sys.stderr)
    if suggestions:
        print("建议:", file=sys.stderr)
        for s in suggestions: print(f"  - {s}", file=sys.stderr)
    sys.exit(1)


def _list_available_displays() -> str:
    active = {d.name.replace("\\\\.\\", "") for d in list_displays()}
    all_names = set(active)
    for p in list_providers():
        sn = p["name"].replace("\\\\.\\", "")
        if sn.startswith("DISPLAY"):
            all_names.add(sn)
    def _sort_key(n: str) -> tuple:
        digits = n.replace("DISPLAY", "")
        return (0, int(digits)) if digits.isdigit() else (1, n)
    names = sorted(all_names, key=_sort_key)
    return "可用显示器: " + ", ".join(names) if names else "未检测到显示器"


def _apply_aliases(args):
    if args.size and not args.mode: args.mode = args.size
    if args.orientation and not args.rotate:
        args.rotate = {"0": "normal", "1": "normal", "2": "inverted", "3": "left"}.get(args.orientation, args.orientation)
    if args.listactivemonitors: args.listmonitors = True
    if args.reflect == "normal": args.reflect = None
    if args.x and args.y: args.reflect = "xy"
    elif args.x: args.reflect = "x"
    elif args.y: args.reflect = "y"


def _is_mod_op(args) -> bool:
    return any([args.mode, args.pos, args.rotate, args.primary, args.preferred,
                args.off, args.brightness, args.reflect, args.gamma,
                args.left_of, args.right_of, args.above, args.below, args.same_as,
                args.auto, args.noprimary])


# --- 操作处理函数 ---

def _msg(args, text: str):
    """dry-run 模式下加 (Dry-Run) 前缀。"""
    print(f"(Dry-Run) {text}" if args.dry_run else text)

def _handle_auto(args, dn):
    if not args.dry_run and not set_auto(dn): _fail("自动配置失败", ["请确认显示器连接正常", "尝试使用 --mode 手动指定分辨率"])
    _msg(args, f"已启用 {args.output}（首选分辨率）")

def _handle_mode(args, dn):
    if "x" not in args.mode.lower(): _fail("--mode 格式必须为 WIDTHxHEIGHT（如 1920x1080）")
    try: w, h = map(int, args.mode.lower().split("x"))
    except ValueError: _fail("--mode 格式错误", ["正确格式: WIDTHxHEIGHT（如 1920x1080）"])
    rate = args.rate or 0
    if not args.dry_run and not set_resolution(dn, w, h, rate): _fail("设置分辨率失败", ["请确认显示器支持该分辨率", "运行 'winrandr --listmodes' 查看可用模式", "使用 --verbose 查看详细日志"])
    rate_suffix = f" @ {rate}Hz" if rate else ""
    _msg(args, f"已设置 {args.output} 为 {w}x{h}{rate_suffix}")

def _handle_pos(args, dn):
    p = args.pos.strip().lower()
    # xrandr 兼容：+1920+0 → 1920+0 → 按 + 拆分 → ["1920", "0"]
    if "x" not in p:
        p = p.lstrip("+")
        if "+" in p:
            xs = p.split("+")
            if len(xs) == 2 and xs[0].lstrip("-").isdigit() and xs[1].lstrip("-").isdigit():
                p = f"{xs[0]}x{xs[1]}"
    p = p.lstrip("+").split("x")
    if len(p) != 2: _fail("--pos 格式必须为 XxY（如 1920x0、+1920x0）")
    try: x, y = int(p[0]), int(p[1])
    except ValueError: _fail("--pos 格式错误", ["正确格式: XxY（如 1920x0 或 +1920+0）"])
    if not args.dry_run and not set_position(dn, x, y): _fail("设置位置失败", ["某些虚拟显示器驱动（如向日葵）可能干扰此功能", "使用 --verbose 查看详细日志"])
    _msg(args, f"已将 {args.output} 移动到 ({x}, {y})")

def _handle_rotate(args, dn):
    deg = ROTATION_FROM_NAME[args.rotate]
    if not args.dry_run and not set_rotation(dn, deg): _fail("设置旋转失败", ["某些虚拟显示器驱动（如向日葵）可能干扰此功能", "请确认显示器支持旋转", "使用 --verbose 查看详细日志"])
    _msg(args, f"已将 {args.output} 旋转为 {args.rotate} ({deg}°)")

def _handle_primary(args, dn):
    if not args.dry_run and not set_primary(dn): _fail("设置主显示器失败", ["某些虚拟显示器驱动（如向日葵）可能干扰此功能", "使用 --verbose 查看详细日志"])
    _msg(args, f"已将 {args.output} 设为主显示器")

def _handle_preferred(args, dn):
    if not args.dry_run and not set_preferred_resolution(dn): _fail("设置首选分辨率失败", ["该显示器可能未注册首选分辨率", "使用 --mode 手动指定分辨率", "使用 --verbose 查看详细日志"])
    _msg(args, f"已将 {args.output} 设为首选分辨率")

def _handle_off(args, dn):
    if not args.dry_run and not set_off(dn): _fail("关闭显示器失败", ["某些虚拟显示器驱动（如向日葵）可能干扰此功能", "请确认指定了正确的显示器名称", "使用 --verbose 查看详细日志"])
    _msg(args, f"已关闭 {args.output}")

def _handle_brightness(args, dn):
    if not 0.1 <= args.brightness <= 2.0:
        print(f"警告: 亮度值 {args.brightness} 超出建议范围 0.1-2.0", file=sys.stderr)
    if not args.dry_run and not set_brightness(dn, args.brightness): _fail("设置亮度失败", ["某些驱动或远程桌面环境不支持亮度调节", "使用 --verbose 查看详细日志"])
    _msg(args, f"已将 {args.output} 亮度设为 {args.brightness}")

def _handle_reflect(args, dn):
    if args.reflect in ("x", "y"): _fail(f"单轴镜像翻转（-{args.reflect}）在 Windows 上无标准 API 支持")
    if not args.dry_run and not set_reflect(dn, args.reflect): _fail("设置镜像翻转失败", ["请使用 --reflect xy（等同于旋转 180°）", "单轴反射在 Windows 上无标准 API 支持"])
    _msg(args, f"已将 {args.output} 设为 {args.reflect} 镜像翻转")

def _handle_gamma(args, dn):
    try: vals = [float(x) for x in args.gamma.split(":")]
    except ValueError: _fail("--gamma 格式错误，使用 R:G:B 或单一值")
    if len(vals) == 1: r = g = b = vals[0]
    elif len(vals) == 3: r, g, b = vals
    else: _fail("--gamma 格式错误，使用 R:G:B 或单一值")
    if not args.dry_run and not set_gamma(dn, r, g, b): _fail("设置伽马校正失败", ["某些驱动或远程桌面环境不支持伽马校正", "使用 --verbose 查看详细日志"])
    _msg(args, f"已将 {args.output} 伽马设为 {r}:{g}:{b}")

def _handle_relative(args, dn):
    for attr, rel in (("left_of", "left-of"), ("right_of", "right-of"), ("above", "above"), ("below", "below"), ("same_as", "same-as")):
        ref = getattr(args, attr, None)
        if ref:
            if not args.dry_run and not set_position_relative(dn, ref, rel): _fail("相对定位失败", ["检查显示器名称是否正确", "某些虚拟显示器驱动（如向日葵）可能干扰此功能", "使用 --verbose 查看详细日志"])
            _msg(args, f"已将 {args.output} 放在 {ref} 的 {rel}")
            return


def main():
    parser = _build_parser()
    args = parser.parse_args()
    _setup_logging()
    if args.verbose: logging.getLogger().setLevel(logging.DEBUG)

    _apply_aliases(args)

    # --listproviders / --listmonitors
    if args.listproviders:
        providers = list_providers()
        if not providers: print("未检测到 GPU 适配器。")
        else:
            print("Providers:")
            for i, p in enumerate(providers): print(f"  Provider {i}: {p['string']} ({p['name']})")
        return
    if args.listmonitors:
        displays = list_displays()
        print(format_monitor_list(displays) if displays else "未检测到显示器。")
        return

    # 查询模式
    if not _is_mod_op(args):
        displays = list_displays()
        if not displays: print("未检测到活动显示器。"); sys.exit(1)
        if args.output:
            device_name = _normalize_name(args.output)
            displays = [d for d in displays if d.name == device_name]
            if not displays: _fail(f"未找到显示器: {args.output}", [_list_available_displays()])
        if args.prop:
            for d in displays: d.properties = get_display_props(d.name)
        if args.json:
            from dataclasses import asdict; import json
            print(json.dumps([asdict(d) for d in displays], indent=2, ensure_ascii=False))
        else: print(format_displays(displays))
        return

    # --noprimary 单独使用
    if args.noprimary:
        if not args.dry_run and not set_noprimary(): _fail("清除主显示器标记失败", ["某些虚拟显示器驱动（如向日葵）可能干扰此功能", "使用 --verbose 查看详细日志"])
        _msg(args, "已清除所有显示器的主显示器标记")
        other_ops = [args.mode, args.pos, args.rotate, args.primary, args.preferred,
                     args.off, args.brightness, args.reflect, args.gamma,
                     args.left_of, args.right_of, args.above, args.below, args.same_as, args.auto]
        if not any(op for op in other_ops if op): return

    if not args.output: parser.error("--output 为必填参数")
    device_name = _normalize_name(args.output)
    if not any(d.name == device_name for d in list_displays()):
        _fail(f"未找到显示器: {args.output}", [_list_available_displays()])

    # 调度各操作
    if args.auto: _handle_auto(args, device_name)
    if args.mode: _handle_mode(args, device_name)
    if args.pos: _handle_pos(args, device_name)
    if args.rotate: _handle_rotate(args, device_name)
    if args.primary: _handle_primary(args, device_name)
    if args.preferred: _handle_preferred(args, device_name)
    if args.off: _handle_off(args, device_name)
    if args.brightness is not None: _handle_brightness(args, device_name)
    if args.reflect: _handle_reflect(args, device_name)
    if args.gamma: _handle_gamma(args, device_name)
    _handle_relative(args, device_name)


if __name__ == "__main__": main()
