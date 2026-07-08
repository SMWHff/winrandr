"""测试数据模型与常量。"""

from dataclasses import asdict

from winrandr.models import DisplayInfo, DisplayMode
from winrandr.win32.constants import (
    CDS_UPDATEREGISTRY,
    DISP_CHANGE_SUCCESSFUL,
    DISPLAYCONFIG_PATH_MODE_IDX_INVALID,
    ENUM_CURRENT_SETTINGS,
    ROTATION_DEGREES,
    ROTATION_FROM_NAME,
    ROTATION_MAP,
    ROTATION_NAMES,
)


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


# --- 常量与旋转映射一致性 ---

def test_rotation_maps_consistent():
    for deg, rot_id in ROTATION_MAP.items():
        assert ROTATION_DEGREES[rot_id] == deg
        name = ROTATION_NAMES[rot_id]
        assert ROTATION_FROM_NAME[name] == deg


def test_rotation_all_four():
    assert set(ROTATION_MAP.keys()) == {0, 90, 180, 270}
    assert set(ROTATION_DEGREES.keys()) == {1, 2, 3, 4}
    assert set(ROTATION_NAMES.keys()) == {1, 2, 3, 4}
    assert set(ROTATION_FROM_NAME.keys()) == {"normal", "left", "inverted", "right"}


def test_rotation_names():
    assert ROTATION_FROM_NAME["normal"] == 0
    assert ROTATION_FROM_NAME["left"] == 90
    assert ROTATION_FROM_NAME["inverted"] == 180
    assert ROTATION_FROM_NAME["right"] == 270
    assert ROTATION_NAMES[1] == "normal"
    assert ROTATION_NAMES[2] == "left"
    assert ROTATION_NAMES[3] == "inverted"
    assert ROTATION_NAMES[4] == "right"


def test_invalid_sentinel():
    assert DISPLAYCONFIG_PATH_MODE_IDX_INVALID == 0xFFFFFFFF


def test_display_config_constants():
    assert CDS_UPDATEREGISTRY == 0x00000001
    assert DISP_CHANGE_SUCCESSFUL == 0
    assert ENUM_CURRENT_SETTINGS == 0xFFFFFFFF
