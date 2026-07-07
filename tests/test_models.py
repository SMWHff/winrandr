"""测试数据模型。"""

from dataclasses import asdict
from winrandr.models import DisplayInfo, DisplayMode


def test_display_mode_defaults():
    m = DisplayMode(width=1920, height=1080, refresh_rate=60.0)
    assert m.width == 1920
    assert m.height == 1080
    assert m.refresh_rate == 60.0
    assert m.is_current is False
    assert m.is_preferred is False


def test_display_mode_current():
    m = DisplayMode(1920, 1080, 60.0, is_current=True, is_preferred=True)
    assert m.is_current
    assert m.is_preferred


def test_display_info_defaults():
    d = DisplayInfo(name="DISPLAY1", friendly_name="Test Monitor")
    assert d.name == "DISPLAY1"
    assert d.connected is True
    assert d.width == 0
    assert d.height == 0
    assert d.modes == []


def test_display_info_with_modes():
    modes = [
        DisplayMode(1920, 1080, 60.0, is_current=True),
        DisplayMode(1280, 720, 30.0),
    ]
    d = DisplayInfo(
        name="DISPLAY1", friendly_name="Test",
        connected=True, width=1920, height=1080,
        position_x=0, position_y=0, is_primary=True,
        modes=modes,
    )
    assert d.is_primary
    assert len(d.modes) == 2
    assert d.modes[0].is_current


def test_display_info_json():
    d = DisplayInfo(name="DISPLAY1", friendly_name="Test")
    data = asdict(d)
    assert data["name"] == "DISPLAY1"
    assert isinstance(data["modes"], list)


def test_display_info_rotation():
    d = DisplayInfo(name="DISPLAY1", friendly_name="Test", rotation=90)
    assert d.rotation == 90


def test_display_info_disconnected():
    d = DisplayInfo(
        name="DISPLAY2", friendly_name="", connected=False,
        width=0, height=0,
    )
    assert not d.connected
    assert d.width == 0
