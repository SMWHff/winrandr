"""xrandr 风格的显示器信息格式化输出。"""

from collections import defaultdict

from winrandr.models import DisplayInfo, DisplayMode
from winrandr.win32.constants import ROTATION_MAP, ROTATION_NAMES

_ALL_ROTATIONS = "normal left inverted right"


def short_name(name: str) -> str:
    return name.replace("\\\\.\\", "").strip()


def format_monitor_list(displays: list[DisplayInfo]) -> str:
    """--listmonitors 格式：带编号的显示器列表。"""
    connected = [d for d in displays if d.connected]
    lines = [f"Monitors: {len(connected)}"]
    for i, d in enumerate(connected):
        name = short_name(d.name)
        pri = "*" if d.is_primary else " "
        mm_w = d.width_mm or 0
        mm_h = d.height_mm or 0
        lines.append(
            f" {i}: +{pri}{name} {d.width}/{mm_w}x{d.height}/{mm_h}+{d.position_x}+{d.position_y}  {name}",
        )
    return "\n".join(lines)


def _rotation_part(degrees: int) -> str:
    """构建 xrandr 风格的旋转信息片段。"""
    if degrees == 0:
        return f"({_ALL_ROTATIONS})"
    name = ROTATION_NAMES.get(ROTATION_MAP.get(degrees, 1), "normal")
    return f"{name} ({_ALL_ROTATIONS})"


def format_displays(displays: list[DisplayInfo]) -> str:
    """以标准 xrandr 风格输出显示器信息。"""
    lines = []

    if displays:
        connected = [d for d in displays if d.connected]
        if connected:
            max_x = max(d.position_x + d.width for d in connected)
            max_y = max(d.position_y + d.height for d in connected)
            lines.append(
                f"Screen 0: minimum 320 x 200, current {max_x} x {max_y}, maximum 32767 x 32767",
            )
        else:
            lines.append("Screen 0: minimum 320 x 200, current (no active displays), maximum 32767 x 32767")
        lines.append("")

    for d in displays:
        name = short_name(d.name)
        status = "connected" if d.connected else "disconnected"

        if d.connected:
            primary = "primary " if d.is_primary else ""
            mm = ""
            if d.width_mm and d.height_mm:
                mm = f" {d.width_mm}mm x {d.height_mm}mm"

            # 旋转时交换宽高显示
            if d.rotation in (90, 270):
                disp_w, disp_h = d.height, d.width
            else:
                disp_w, disp_h = d.width, d.height

            lines.append(
                f"{name} {status} {primary}{disp_w}x{disp_h}"
                f"+{d.position_x}+{d.position_y} {_rotation_part(d.rotation)}{mm}",
            )
            if d.modes:
                fmt_modes(lines, d.modes)
        else:
            lines.append(f"{name} {status}")

        if d.properties:
            _fmt_props(lines, d.properties)

        lines.append("")

    return "\n".join(lines)


def _fmt_props(lines: list[str], props: dict[str, str]) -> None:
    """格式化扩展属性。"""
    for key, val in props.items():
        label = key.replace("_", " ")
        lines.append(f"\t{label}: {val}")


def fmt_modes(lines: list[str], modes: list[DisplayMode]) -> None:
    """格式化模式列表，类似 xrandr 的显示方式。"""
    grouped = defaultdict(list)
    for m in modes:
        grouped[(m.width, m.height)].append(m)

    for (w, h), mlist in sorted(grouped.items()):
        rates = []
        for m in sorted(mlist, key=lambda x: -x.refresh_rate):
            tag = ""
            if m.is_current:
                tag += "*"
            if m.is_preferred:
                tag += "+"
            rates.append(f"{m.refresh_rate:.2f}{tag}")
        res_str = f"{w}x{h}"
        lines.append(f"   {res_str:<13s} {' '.join(rates)}")
