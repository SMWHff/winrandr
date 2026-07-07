"""测试格式化输出。"""

from winrandr.formatter import _short_name, format_displays
from winrandr.models import DisplayInfo, DisplayMode


def test_short_name():
    assert _short_name(r"\\.\DISPLAY1") == "DISPLAY1"
    assert _short_name("DISPLAY1") == "DISPLAY1"


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
    assert "Screen 0: current 1920 x 1080" in out
    assert "DISPLAY1" in out
    assert "connected" in out
    assert "1920x1080" in out
    assert "primary" in out
    assert "60.00*+" in out  # modes always shown now


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
                "adapter": "PCI\\VEN_1234",
            },
        ),
    ]
    out = format_displays(displays)
    assert "device id: MONITOR\\TEST123" in out
    assert "state flags: attached, primary" in out
    assert "adapter: PCI\\VEN_1234" in out


def test_format_displays_non_primary():
    """非主显示器不带 primary 关键字。"""
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
    assert "primary" not in out.split("\n")[2]  # display line doesn't have primary
