"""测试格式化输出。"""

from winrandr.formatter import short_name, fmt_modes, _fmt_props, _rotation_part, format_displays, format_monitor_list
from winrandr.models import DisplayInfo, DisplayMode


def testshort_name():
    assert short_name(r"\\.\DISPLAY1") == "DISPLAY1"
    assert short_name("DISPLAY1") == "DISPLAY1"

def test_format_displays_basic():
    displays = [
        DisplayInfo(
            name=r"\\.\DISPLAY1", friendly_name="Generic Monitor",
            width=1920, height=1080, refresh_rate=60.0,
            position_x=0, position_y=0,
            is_primary=True, rotation=0,
            width_mm=527, height_mm=296, connected=True,
            modes=[DisplayMode(1920, 1080, 60.0, is_current=True, is_preferred=True)],
        ),
    ]
    out = format_displays(displays)
    assert "Screen 0:" in out
    assert "minimum 320 x 200" in out
    assert "maximum 32767 x 32767" in out
    assert "1920 x 1080" in out
    assert "DISPLAY1" in out
    assert "connected" in out
    assert "1920x1080" in out
    assert "primary" in out
    assert "60.00*+" in out
    assert "normal left inverted right" in out

def test_format_displays_disconnected():
    displays = [
        DisplayInfo(
            name=r"\\.\DISPLAY1", friendly_name="", connected=False,
            width=0, height=0, refresh_rate=0.0,
            position_x=0, position_y=0,
            is_primary=False, rotation=0,
            width_mm=0, height_mm=0, modes=[],
        ),
    ]
    out = format_displays(displays)
    assert "DISPLAY1" in out
    assert "disconnected" in out
    assert "minimum 320 x 200" in out

def test_format_displays_with_props():
    displays = [
        DisplayInfo(
            name=r"\\.\DISPLAY1", friendly_name="Test Monitor",
            width=1920, height=1080, refresh_rate=60.0,
            position_x=0, position_y=0,
            is_primary=True, rotation=0,
            width_mm=527, height_mm=296, connected=True,
            modes=[DisplayMode(1920, 1080, 60.0, is_current=True, is_preferred=True)],
            properties={
                "device_id": "MONITOR\\TEST123",
                "state_flags": "attached, primary",
            },
        ),
    ]
    out = format_displays(displays)
    assert "device id: MONITOR\\TEST123" in out
    assert "state flags: attached, primary" in out

def test_format_displays_non_primary():
    displays = [
        DisplayInfo(
            name=r"\\.\DISPLAY1", friendly_name="", connected=True,
            width=1920, height=1080, refresh_rate=60.0,
            position_x=0, position_y=0,
            is_primary=False, rotation=0,
            width_mm=527, height_mm=296,
            modes=[DisplayMode(1920, 1080, 60.0, is_current=True, is_preferred=True)],
        ),
    ]
    out = format_displays(displays)
    assert "DISPLAY1 connected 1920x1080+0+0" in out
    assert "primary" not in out.split("\n")[2]

def test_format_displays_rotated_left():
    displays = [
        DisplayInfo(
            name=r"\\.\DISPLAY1", friendly_name="", connected=True,
            width=1920, height=1080, refresh_rate=60.0,
            position_x=0, position_y=0, rotation=90,
            is_primary=False, width_mm=527, height_mm=296,
            modes=[DisplayMode(1920, 1080, 60.0, is_current=True, is_preferred=True)],
        ),
    ]
    out = format_displays(displays)
    assert "1080x1920" in out.split("\n")[2]
    assert "left (normal left inverted right)" in out

def test_format_displays_rotated_inverted():
    displays = [
        DisplayInfo(
            name=r"\\.\DISPLAY1", friendly_name="", connected=True,
            width=1920, height=1080, refresh_rate=60.0,
            position_x=0, position_y=0, rotation=180,
            is_primary=False, width_mm=527, height_mm=296,
            modes=[DisplayMode(1920, 1080, 60.0, is_current=True, is_preferred=True)],
        ),
    ]
    out = format_displays(displays)
    assert "1920x1080" in out.split("\n")[2]
    assert "inverted (normal left inverted right)" in out

def test_format_displays_normal_rotation_list():
    displays = [
        DisplayInfo(
            name=r"\\.\DISPLAY1", friendly_name="", connected=True,
            width=1920, height=1080, refresh_rate=60.0,
            position_x=0, position_y=0, rotation=0,
            is_primary=False, width_mm=527, height_mm=296,
            modes=[DisplayMode(1920, 1080, 60.0, is_current=True, is_preferred=True)],
        ),
    ]
    out = format_displays(displays)
    line = out.split("\n")[2]
    assert "(normal left inverted right)" in line
    assert "normal left inverted right" in line

def test_format_modes_alignment():
    displays = [
        DisplayInfo(
            name=r"\\.\DISPLAY1", friendly_name="", connected=True,
            width=1920, height=1080, refresh_rate=60.0,
            position_x=0, position_y=0,
            is_primary=True, rotation=0,
            width_mm=527, height_mm=296,
            modes=[
                DisplayMode(1920, 1080, 60.0, is_current=True, is_preferred=True),
                DisplayMode(1280, 720, 60.0),
                DisplayMode(1024, 768, 75.0, is_current=False, is_preferred=False),
                DisplayMode(1024, 768, 60.0),
            ],
        ),
    ]
    out = format_displays(displays)
    lines = out.split("\n")
    mode_lines = [line for line in lines if "x" in line and line.strip().startswith("1")]
    for ml in mode_lines:
        parts = ml.strip().split()
        assert len(parts) >= 2

def test_format_monitor_list_basic():
    displays = [
        DisplayInfo(
            name=r"\\.\DISPLAY1", friendly_name="", connected=True,
            width=1920, height=1080, position_x=0, position_y=0,
            is_primary=True, width_mm=527, height_mm=296,
        ),
        DisplayInfo(
            name=r"\\.\DISPLAY2", friendly_name="", connected=True,
            width=1920, height=1080, position_x=1920, position_y=0,
            is_primary=False, width_mm=527, height_mm=296,
        ),
    ]
    out = format_monitor_list(displays)
    assert "Monitors: 2" in out
    assert "DISPLAY1" in out and "DISPLAY2" in out
    assert "+*DISPLAY1" in out
    assert "+ DISPLAY2" in out

def test_fmt_modes_preferred_flag():
    modes = [
        DisplayMode(1920, 1080, 60.0, is_current=True, is_preferred=False),
        DisplayMode(1920, 1080, 59.94, is_current=False, is_preferred=True),
    ]
    lines = []
    fmt_modes(lines, modes)
    out = "\n".join(lines)
    assert "60.00*" in out
    assert "59.94+" in out

def test_format_displays_empty():
    assert format_displays([]) == ""

def test_format_displays_all_disconnected():
    displays = [
        DisplayInfo(name=r"\\.\DISPLAY1", friendly_name="", connected=False,
                    width=0, height=0, refresh_rate=0.0, position_x=0, position_y=0,
                    is_primary=False, rotation=0, width_mm=0, height_mm=0, modes=[]),
        DisplayInfo(name=r"\\.\DISPLAY2", friendly_name="", connected=False,
                    width=0, height=0, refresh_rate=0.0, position_x=0, position_y=0,
                    is_primary=False, rotation=0, width_mm=0, height_mm=0, modes=[]),
    ]
    out = format_displays(displays)
    for d in ("DISPLAY1", "DISPLAY2", "disconnected"):
        assert d in out
    assert "no active displays" in out

def test_format_displays_rotated_270():
    displays = [DisplayInfo(
        name=r"\\.\DISPLAY1", friendly_name="", connected=True,
        width=1920, height=1080, refresh_rate=60.0,
        position_x=0, position_y=0, rotation=270,
        is_primary=False, width_mm=527, height_mm=296,
        modes=[DisplayMode(1920, 1080, 60.0, is_current=True, is_preferred=True)],
    )]
    out = format_displays(displays)
    assert "1080x1920" in out

def test_format_displays_multiple_connected():
    displays = [
        DisplayInfo(name=r"\\.\DISPLAY1", friendly_name="", connected=True,
                    width=1920, height=1080, position_x=0, position_y=0,
                    is_primary=True, rotation=0, width_mm=527, height_mm=296,
                    modes=[DisplayMode(1920, 1080, 60.0)]),
        DisplayInfo(name=r"\\.\DISPLAY2", friendly_name="", connected=True,
                    width=1280, height=1024, position_x=1920, position_y=0,
                    is_primary=False, rotation=0, width_mm=0, height_mm=0,
                    modes=[DisplayMode(1280, 1024, 60.0)]),
    ]
    out = format_displays(displays)
    assert "current 3200 x 1080" in out
    assert "primary" in out.split("\n")[2]
    assert "DISPLAY2" in out

def test_format_displays_no_modes():
    displays = [DisplayInfo(
        name=r"\\.\DISPLAY1", friendly_name="", connected=True,
        width=1920, height=1080, refresh_rate=60.0,
        position_x=0, position_y=0, is_primary=False, rotation=0,
        width_mm=527, height_mm=296, modes=[],
    )]
    out = format_displays(displays)
    assert "DISPLAY1 connected" in out
    assert "1920x1080" in out

def test_format_monitor_list_no_connected():
    displays = [DisplayInfo(
        name=r"\\.\DISPLAY1", friendly_name="", connected=False,
        width=0, height=0, refresh_rate=0.0, position_x=0, position_y=0,
        is_primary=False, rotation=0, width_mm=0, height_mm=0, modes=[],
    )]
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
    d = DisplayInfo(name=r"\\.\DISPLAY1", friendly_name="", connected=False,
                    width=0, height=0, refresh_rate=0.0, position_x=0, position_y=0,
                    is_primary=False, rotation=0, width_mm=0, height_mm=0, modes=[])
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
