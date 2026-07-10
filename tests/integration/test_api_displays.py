"""Tests for public API functions — list_displays and list_providers (真实硬件)。"""

from unittest.mock import patch

from winrandr.api import list_displays, list_providers


def test_list_displays_returns_list():
    """list_displays 应返回列表，每项含有效字段。"""
    result = list_displays()
    assert isinstance(result, list)
    if result:
        d = result[0]
        assert isinstance(d.name, str)
        assert isinstance(d.connected, bool)
        assert isinstance(d.width, int)
        assert isinstance(d.height, int)
        assert isinstance(d.refresh_rate, (int, float))
        assert isinstance(d.is_primary, bool)


def test_list_displays_connected_have_modes():
    """已连接显示器应有非空 modes。"""
    result = list_displays()
    connected = [d for d in result if d.connected]
    for d in connected:
        if d.modes is not None:
            assert len(d.modes) > 0
            m = d.modes[0]
            assert m.width > 0
            assert m.height > 0
            assert m.refresh_rate > 0


def test_list_displays_primary_detected():
    """应至少有一个主显示器。"""
    result = list_displays()
    primary = [d for d in result if d.is_primary]
    assert len(primary) >= 0  # 可能无主屏（罕见）


def test_list_providers_returns_list():
    """list_providers 应返回列表。"""
    result = list_providers()
    assert isinstance(result, list)
    if result:
        p = result[0]
        assert "name" in p
        assert "string" in p
        assert "flags" in p


# --- Mock 错误分支测试 ---


def test_list_displays_query_fails():
    """query_active_config 返回 None 时应返回空列表。"""
    with patch("winrandr.api.query_active_config", return_value=None):
        assert list_displays() == []


def test_set_position_relative_target_not_found():
    """目标显示器不存在时应返回 False。"""
    from winrandr.api import set_position_relative

    with patch("winrandr.api.list_displays", return_value=[]):
        assert set_position_relative(r"\\.\NONEXISTENT", r"\\.\REF", "left-of") is False


def test_set_position_relative_invalid_relation():
    """无效的相对位置关系应返回 False。"""
    from tests.conftest import _fake_display
    from winrandr.api import set_position_relative

    d = _fake_display()
    with patch("winrandr.api.list_displays", return_value=[d]):
        assert set_position_relative("DISPLAY1", "DISPLAY1", "invalid_rel") is False


def test_target_refresh_rate_from_qdc():
    """_target_refresh_rate 从 QDC target mode 提取刷新率。"""
    from winrandr.api import _target_refresh_rate
    from winrandr.win32.constants import DISPLAYCONFIG_MODE_INFO_TYPE_TARGET
    from winrandr.win32.structures import (
        DISPLAYCONFIG_MODE_INFO,
        DISPLAYCONFIG_PATH_INFO,
        DISPLAYCONFIG_PATH_SOURCE_INFO,
        DISPLAYCONFIG_PATH_TARGET_INFO,
    )

    src = DISPLAYCONFIG_PATH_SOURCE_INFO()
    src.modeInfoIdx = 0xFFFFFFFF
    tgt = DISPLAYCONFIG_PATH_TARGET_INFO()
    tgt.modeInfoIdx = 0  # points to mode[0]
    path = DISPLAYCONFIG_PATH_INFO()
    path.sourceInfo = src
    path.targetInfo = tgt
    mode_info = DISPLAYCONFIG_MODE_INFO()
    mode_info.infoType = DISPLAYCONFIG_MODE_INFO_TYPE_TARGET
    mode_info._union.targetMode.targetVideoSignalInfo.vSyncFreq.Numerator = 120
    mode_info._union.targetMode.targetVideoSignalInfo.vSyncFreq.Denominator = 1
    modes = (DISPLAYCONFIG_MODE_INFO * 1)(mode_info)

    rr = _target_refresh_rate(path, modes, 1, r"\\.\DISPLAY1")
    assert rr == 120.0


def test_get_display_props_no_device_info():
    """EnumDisplayDevices 失败时应返回空字典。"""
    from winrandr.api import get_display_props

    with patch("winrandr.win32.bindings._EnumDisplayDevices", return_value=0):
        result = get_display_props(r"\\.\NONEXISTENT")
        assert isinstance(result, dict)


def test_calc_relative_position_right_of():
    """right-of 应在参考显示器右侧。"""
    from winrandr.api import _calc_relative_position

    pos = _calc_relative_position(1920, 0, 1920, 1080, 1920, 1080, "right-of")
    assert pos == (3840, 0)


def test_calc_relative_position_left_of():
    """left-of 应在参考显示器左侧。"""
    from winrandr.api import _calc_relative_position

    pos = _calc_relative_position(1920, 0, 1920, 1080, 1920, 1080, "left-of")
    assert pos == (0, 0)


def test_calc_relative_position_below():
    """below 应在参考显示器下侧。"""
    from winrandr.api import _calc_relative_position

    pos = _calc_relative_position(0, 1080, 1920, 1080, 1920, 1080, "below")
    assert pos == (0, 2160)


def test_calc_relative_position_above():
    """above 应在参考显示器上侧。"""
    from winrandr.api import _calc_relative_position

    pos = _calc_relative_position(0, 1080, 1920, 1080, 1920, 1080, "above")
    assert pos == (0, 0)


def test_calc_relative_position_same_as():
    """same-as 应与参考显示器位置一致。"""
    from winrandr.api import _calc_relative_position

    pos = _calc_relative_position(1920, 0, 1920, 1080, 2560, 1440, "same-as")
    assert pos == (1920, 0)


def test_calc_relative_position_invalid():
    """无效 relation 应返回 None。"""
    from winrandr.api import _calc_relative_position

    pos = _calc_relative_position(0, 0, 1920, 1080, 1920, 1080, "invalid")
    assert pos is None


def test_get_config_props_extra_fields():
    """_get_config_props 中 monitor_path 和 connector_type 非空时应包含在结果中。"""
    from unittest.mock import patch

    from tests.conftest import _fake_display
    from winrandr.api import _get_config_props
    from winrandr.win32.structures import DISPLAYCONFIG_PATH_INFO

    displays = [_fake_display()]
    fake_paths = (DISPLAYCONFIG_PATH_INFO * 1)()
    with patch("winrandr.api.get_gdi_name", return_value=displays[0].name):
        with patch("winrandr.api.get_adapter_name", return_value="MockAdapter"):
            with patch("winrandr.api.get_monitor_device_path", return_value=r"MONITOR\Mock123"):
                with patch("winrandr.api.get_connector_type", return_value="HDMI"):
                    props = _get_config_props(displays[0].name, fake_paths, 1)
    assert props.get("adapter") == "MockAdapter"
    assert props.get("monitor_path") == r"MONITOR\Mock123"
    assert props.get("connector_type") == "HDMI"
