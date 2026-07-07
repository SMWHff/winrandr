"""测试常量与旋转映射的完整性。"""

from winrandr.constants import (
    ROTATION_MAP, ROTATION_NAMES, ROTATION_FROM_NAME, ROTATION_DEGREES,
    DISPLAYCONFIG_PATH_MODE_IDX_INVALID,
    CDS_UPDATEREGISTRY, DISP_CHANGE_SUCCESSFUL, ENUM_CURRENT_SETTINGS,
)


def test_rotation_maps_consistent():
    """验证四个旋转映射表之间的一致性。"""
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
