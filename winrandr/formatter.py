"""xrandr 风格的显示器信息格式化输出。"""

from winrandr.constants import ROTATION_FROM_NAME


def _short_name(name: str) -> str:
    return name.replace("\\\\.\\", "").strip()


def format_displays(displays, list_modes: bool = False) -> str:
    """以类 xrandr 风格输出显示器信息。"""
    lines = []

    if displays:
        connected = [d for d in displays if d.connected]
        dpi_info = ""
        if connected:
            max_x = max(d.position_x + d.width for d in connected)
            max_y = max(d.position_y + d.height for d in connected)
            for d in connected:
                if d.width_mm and d.height_mm:
                    dpi_x = round(d.width / (d.width_mm / 25.4))
                    dpi_y = round(d.height / (d.height_mm / 25.4))
                    dpi_info = f", dpi {dpi_x}x{dpi_y}"
                    break
            lines.append(f"Screen 0: current {max_x} x {max_y}{dpi_info}")
        else:
            lines.append("Screen 0: current (no active displays)")
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

        if d.properties:
            _fmt_props(lines, d.properties)

        lines.append("")

    return "\n".join(lines)


def _fmt_props(lines: list[str], props: dict) -> None:
    """格式化扩展属性。"""
    for key, val in props.items():
        label = key.replace("_", " ")
        lines.append(f"    {label}: {val}")


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
        lines.append(f"   {w}x{h}  {' '.join(rates)}")
