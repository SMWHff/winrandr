"""格式化输出边缘 case 测试。"""

from winrandr.formatter import _fmt_props, _rotation_part, fmt_modes, format_displays, format_monitor_list
from winrandr.models import DisplayInfo, DisplayMode


def test_format_displays_all_disconnected():
    displays = [
        DisplayInfo(
            name=r"\\.\DISPLAY1",
            friendly_name="",
            connected=False,
            width=0,
            height=0,
            refresh_rate=0.0,
            position_x=0,
            position_y=0,
            is_primary=False,
            rotation=0,
            width_mm=0,
            height_mm=0,
            modes=[],
        ),
        DisplayInfo(
            name=r"\\.\DISPLAY2",
            friendly_name="",
            connected=False,
            width=0,
            height=0,
            refresh_rate=0.0,
            position_x=0,
            position_y=0,
            is_primary=False,
            rotation=0,
            width_mm=0,
            height_mm=0,
            modes=[],
        ),
    ]
    out = format_displays(displays)
    for d in ("DISPLAY1", "DISPLAY2", "disconnected"):
        assert d in out
    assert "no active displays" in out


def test_format_displays_rotated_270():
    displays = [
        DisplayInfo(
            name=r"\\.\DISPLAY1",
            friendly_name="",
            connected=True,
            width=1920,
            height=1080,
            refresh_rate=60.0,
            position_x=0,
            position_y=0,
            rotation=270,
            is_primary=False,
            width_mm=527,
            height_mm=296,
            modes=[DisplayMode(1920, 1080, 60.0, is_current=True, is_preferred=True)],
        )
    ]
    out = format_displays(displays)
    assert "1080x1920" in out


def test_format_displays_multiple_connected():
    displays = [
        DisplayInfo(
            name=r"\\.\DISPLAY1",
            friendly_name="",
            connected=True,
            width=1920,
            height=1080,
            position_x=0,
            position_y=0,
            is_primary=True,
            rotation=0,
            width_mm=527,
            height_mm=296,
            modes=[DisplayMode(1920, 1080, 60.0)],
        ),
        DisplayInfo(
            name=r"\\.\DISPLAY2",
            friendly_name="",
            connected=True,
            width=1280,
            height=1024,
            position_x=1920,
            position_y=0,
            is_primary=False,
            rotation=0,
            width_mm=0,
            height_mm=0,
            modes=[DisplayMode(1280, 1024, 60.0)],
        ),
    ]
    out = format_displays(displays)
    assert "current 3200 x 1080" in out
    assert "primary" in out.split("\n")[2]
    assert "DISPLAY2" in out


def test_format_displays_no_modes():
    displays = [
        DisplayInfo(
            name=r"\\.\DISPLAY1",
            friendly_name="",
            connected=True,
            width=1920,
            height=1080,
            refresh_rate=60.0,
            position_x=0,
            position_y=0,
            is_primary=False,
            rotation=0,
            width_mm=527,
            height_mm=296,
            modes=[],
        )
    ]
    out = format_displays(displays)
    assert "DISPLAY1 connected" in out
    assert "1920x1080" in out


def test_format_monitor_list_no_connected():
    displays = [
        DisplayInfo(
            name=r"\\.\DISPLAY1",
            friendly_name="",
            connected=False,
            width=0,
            height=0,
            refresh_rate=0.0,
            position_x=0,
            position_y=0,
            is_primary=False,
            rotation=0,
            width_mm=0,
            height_mm=0,
            modes=[],
        )
    ]
    out = format_monitor_list(displays)
    assert "Monitors: 0" in out


def test_fmt_props_empty():
    lines = []
    _fmt_props(lines, {})
    assert lines == []


def test_fmt_props_with_data():
    lines = []
    _fmt_props(lines, {"device_id": "TEST\\123", "state_flags": "attached"})
    assert "device id: TEST\\123" in lines[0]
    assert "state flags: attached" in lines[1]


def test_fmt_modes_empty():
    lines = ["preexisting"]
    fmt_modes(lines, [])
    assert len(lines) == 1


def test_format_displays_single_disconnected():
    d = DisplayInfo(
        name=r"\\.\DISPLAY1",
        friendly_name="",
        connected=False,
        width=0,
        height=0,
        refresh_rate=0.0,
        position_x=0,
        position_y=0,
        is_primary=False,
        rotation=0,
        width_mm=0,
        height_mm=0,
        modes=[],
    )
    out = format_displays([d])
    assert "Screen 0:" in out
    assert "no active displays" in out
    assert "DISPLAY1 disconnected" in out


def test_rotation_part_normal():
    assert "(normal left inverted right)" in _rotation_part(0)


def test_rotation_part_left():
    result = _rotation_part(90)
    assert "left" in result
    assert "(normal left inverted right)" in result


def test_rotation_part_inverted():
    result = _rotation_part(180)
    assert "inverted" in result


def test_rotation_part_right():
    result = _rotation_part(270)
    assert "right" in result


def test_rotation_part_unknown():
    result = _rotation_part(45)
    assert "(normal left inverted right)" in result
