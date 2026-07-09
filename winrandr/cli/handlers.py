"""CLI 操作处理函数。"""

import sys
from argparse import Namespace

from winrandr.api import (
    identify_display,
    list_displays,
    set_auto,
    set_brightness,
    set_gamma,
    set_night_mode,
    set_off,
    set_position,
    set_position_relative,
    set_preferred_resolution,
    set_primary,
    set_reflect,
    set_resolution,
    set_rotation,
)
from winrandr.cli.common import _fail, _list_available_displays, _msg, _normalize_name
from winrandr.formatter import fmt_modes
from winrandr.win32.constants import ROTATION_FROM_NAME


def _handle_auto(args: Namespace, dn: str) -> None:
    if not args.dry_run and not set_auto(dn):
        _fail("自动配置失败", ["请确认显示器连接正常", "尝试使用 --mode 手动指定分辨率"])
    _msg(args, f"已启用 {args.output}（首选分辨率）")


def _handle_mode(args: Namespace, dn: str) -> None:
    if "x" not in args.mode.lower():
        _fail("--mode 格式必须为 WIDTHxHEIGHT（如 1920x1080）")
    try:
        w, h = map(int, args.mode.lower().split("x"))
    except ValueError:
        _fail("--mode 格式错误", ["正确格式: WIDTHxHEIGHT（如 1920x1080）"])
    rate = args.rate or 0
    if not args.dry_run and not set_resolution(dn, w, h, rate):
        _fail(
            "设置分辨率失败",
            [
                "请确认显示器支持该分辨率",
                "运行 'winrandr --listmodes' 查看可用模式",
                "使用 --verbose 查看详细日志",
            ],
        )
    _msg(args, f"已设置 {args.output} 为 {w}x{h}{' @ ' + str(rate) + 'Hz' if rate else ''}")


def _handle_pos(args: Namespace, dn: str) -> None:
    p = args.pos.strip().lower()
    if "x" not in p:
        p = p.lstrip("+")
        if "+" in p:
            xs = p.split("+")
            if len(xs) == 2 and xs[0].lstrip("-").isdigit() and xs[1].lstrip("-").isdigit():
                p = f"{xs[0]}x{xs[1]}"
    p = p.lstrip("+").split("x")
    if len(p) != 2:
        _fail("--pos 格式必须为 XxY（如 1920x0、+1920x0）")
    try:
        x, y = int(p[0]), int(p[1])
    except ValueError:
        _fail("--pos 格式错误", ["正确格式: XxY（如 1920x0 或 +1920+0）"])
    if not args.dry_run and not set_position(dn, x, y):
        _fail("设置位置失败", ["某些虚拟显示器驱动（如向日葵）可能干扰此功能", "使用 --verbose 查看详细日志"])
    _msg(args, f"已将 {args.output} 移动到 ({x}, {y})")


def _handle_rotate(args: Namespace, dn: str) -> None:
    deg = ROTATION_FROM_NAME[args.rotate]
    if not args.dry_run and not set_rotation(dn, deg):
        _fail(
            "设置旋转失败",
            [
                "某些虚拟显示器驱动（如向日葵）可能干扰此功能",
                "请确认显示器支持旋转",
                "使用 --verbose 查看详细日志",
            ],
        )
    _msg(args, f"已将 {args.output} 旋转为 {args.rotate} ({deg}°)")


def _handle_primary(args: Namespace, dn: str) -> None:
    if not args.dry_run and not set_primary(dn):
        _fail("设置主显示器失败", ["某些虚拟显示器驱动（如向日葵）可能干扰此功能", "使用 --verbose 查看详细日志"])
    _msg(args, f"已将 {args.output} 设为主显示器")


def _handle_preferred(args: Namespace, dn: str) -> None:
    if not args.dry_run and not set_preferred_resolution(dn):
        _fail(
            "设置首选分辨率失败",
            [
                "该显示器可能未注册首选分辨率",
                "使用 --mode 手动指定分辨率",
                "使用 --verbose 查看详细日志",
            ],
        )
    _msg(args, f"已将 {args.output} 设为首选分辨率")


def _handle_off(args: Namespace, dn: str) -> None:
    if not args.dry_run and not set_off(dn):
        _fail(
            "关闭显示器失败",
            [
                "某些虚拟显示器驱动（如向日葵）可能干扰此功能",
                "请确认指定了正确的显示器名称",
                "使用 --verbose 查看详细日志",
            ],
        )
    _msg(args, f"已关闭 {args.output}")


def _handle_brightness(args: Namespace, dn: str) -> None:
    if not 0.1 <= args.brightness <= 2.0:
        print(f"警告: 亮度值 {args.brightness} 超出建议范围 0.1-2.0", file=sys.stderr)
    if not args.dry_run and not set_brightness(dn, args.brightness):
        _fail("设置亮度失败", ["某些驱动或远程桌面环境不支持亮度调节", "使用 --verbose 查看详细日志"])
    _msg(args, f"已将 {args.output} 亮度设为 {args.brightness}")


def _handle_night_mode(args: Namespace, dn: str) -> None:
    val = args.night_mode
    if val in ("light", "medium", "heavy"):
        strength = {"light": 0.2, "medium": 0.5, "heavy": 0.8}[val]
    else:
        try:
            strength = float(val)
        except (ValueError, TypeError):
            _fail("--night-mode 参数无效", ["使用 light(20%)/medium(50%)/heavy(80%) 或数值 0.0-1.0"])
        if not 0.0 <= strength <= 1.0:
            _fail("夜间模式强度必须在 0.0-1.0 之间")
    if not args.dry_run and not set_night_mode(dn, strength):
        _fail("设置夜间模式失败", ["某些驱动或远程桌面环境不支持伽马校正", "使用 --verbose 查看详细日志"])
    _msg(args, f"已将 {args.output} 的蓝光强度减弱 {int(strength * 100)}%")


def _handle_reflect(args: Namespace, dn: str) -> None:
    if args.reflect in ("x", "y"):
        _fail(f"单轴镜像翻转（-{args.reflect}）在 Windows 上无标准 API 支持")
    if not args.dry_run and not set_reflect(dn, args.reflect):
        _fail("设置镜像翻转失败", ["请使用 --reflect xy（等同于旋转 180°）", "单轴反射在 Windows 上无标准 API 支持"])
    _msg(args, f"已将 {args.output} 设为 {args.reflect} 镜像翻转")


def _handle_gamma(args: Namespace, dn: str) -> None:
    try:
        vals = [float(x) for x in args.gamma.split(":")]
    except ValueError:
        _fail("--gamma 格式错误，使用 R:G:B 或单一值")
    if len(vals) == 1:
        r = g = b = vals[0]
    elif len(vals) == 3:
        r, g, b = vals
    else:
        _fail("--gamma 格式错误，使用 R:G:B 或单一值")
    if not args.dry_run and not set_gamma(dn, r, g, b):
        _fail("设置伽马校正失败", ["某些驱动或远程桌面环境不支持伽马校正", "使用 --verbose 查看详细日志"])
    _msg(args, f"已将 {args.output} 伽马设为 {r}:{g}:{b}")


def _handle_listmodes(args: Namespace, as_json: bool = False) -> None:
    displays = list_displays()
    if not displays:
        print("未检测到显示器。")
        return
    if args.output:
        dn = _normalize_name(args.output)
        displays = [d for d in displays if d.name == dn]
        if not displays:
            _fail(f"未找到显示器: {args.output}", [_list_available_displays()])
    if as_json:
        import json
        from dataclasses import asdict

        print(json.dumps([asdict(d) for d in displays], indent=2, ensure_ascii=False))
        return
    for d in displays:
        sn = d.name.replace("\\\\.\\", "")
        print(f"{sn}:")
        lines: list[str] = []
        fmt_modes(lines, d.modes)
        for line in lines:
            print(line)
        print()


def _handle_identify(args: Namespace, dn: str) -> None:
    if not args.dry_run and not identify_display(dn):
        _fail("识别显示器失败", ["某些驱动或远程桌面环境不支持伽马校正操作", "使用 --verbose 查看详细日志"])
    _msg(args, f"已对 {args.output} 执行闪屏识别")


def _handle_relative(args: Namespace, dn: str) -> None:
    _relations = (
        ("left_of", "left-of"),
        ("right_of", "right-of"),
        ("above", "above"),
        ("below", "below"),
        ("same_as", "same-as"),
    )
    for attr, rel in _relations:
        ref = getattr(args, attr, None)
        if ref:
            if not args.dry_run and not set_position_relative(dn, ref, rel):
                _fail(
                    "相对定位失败",
                    [
                        "检查显示器名称是否正确",
                        "某些虚拟显示器驱动（如向日葵）可能干扰此功能",
                        "使用 --verbose 查看详细日志",
                    ],
                )
            _msg(args, f"已将 {args.output} 放在 {ref} 的 {rel}")
            return
