"""xrandr 风格的显示器信息格式化输出。"""

from winrandr.constants import ROTATION_FROM_NAME


def _short_name(name: str) -> str:
    return name.replace("\\\\.\\", "").strip()


def format_displays(displays) -> str:
    """以标准 xrandr 风格输出显示器信息。"""
    lines = []

    if displays:
        connected = [d for d in displays if d.connected]
        if connected:
            max_x = max(d.position_x + d.width for d in connected)
            max_y = max(d.position_y + d.height for d in connected)
            lines.append(
                f"Screen 0: minimum 320 x 200, current {max_x} x {max_y},"
                f" maximum 32767 x 32767"
            )
        else:
            lines.append("Screen 0: minimum 320 x 200, current (no active displays),"
                         " maximum 32767 x 32767")
        lines.append("")

    for d in displays:
        name = _short_name(d.name)
        status = "connected" if d.connected else "disconnected"

        if d.connected:
            primary = "primary " if d.is_primary else ""
            mm = ""
            if d.width_mm and d.height_mm:
                mm = f" {d.width_mm}mm x {d.height_mm}mm"
            lines.append(
                f"{name} {status} {primary}{d.width}x{d.height}"
                f"+{d.position_x}+{d.position_y} (normal){mm}"
            )
            if d.modes:
                _fmt_modes(lines, d.modes)
        else:
            lines.append(f"{name} {status}")

        if d.properties:
            _fmt_props(lines, d.properties)

        lines.append("")

    return "\n".join(lines)


def _fmt_props(lines: list[str], props: dict) -> None:
    """格式化扩展属性。"""
    for key, val in props.items():
        label = key.replace("_", " ")
        lines.append(f"\t{label}: {val}")


def _fmt_modes(lines: list[str], modes) -> None:
    """格式化模式列表，类似 xrandr 的显示方式。"""
    from collections import defaultdict

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
