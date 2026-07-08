"""Tests for public API functions (winrandr.api)."""

from unittest.mock import patch

from winrandr.api import (
    get_display_props,
    list_displays,
    list_providers,
    set_position_relative,
)
from winrandr.models import DisplayInfo

# --- list_displays ---

def test_list_displays_empty():
    with patch("winrandr.api.query_active_config", return_value=None):
        assert list_displays() == []

def test_list_displays_source_fallback():
    """source modeInfoIdx 无效时回退到 EnumDisplaySettings 获取分辨率。"""
    from winrandr.win32.constants import DISPLAYCONFIG_PATH_MODE_IDX_INVALID
    from winrandr.win32.structures import (
        DISPLAYCONFIG_MODE_INFO,
        DISPLAYCONFIG_PATH_INFO,
    )
    paths = (DISPLAYCONFIG_PATH_INFO * 1)()
    modes = (DISPLAYCONFIG_MODE_INFO * 1)()
    paths[0].sourceInfo.modeInfoIdx = DISPLAYCONFIG_PATH_MODE_IDX_INVALID
    paths[0].targetInfo.modeInfoIdx = DISPLAYCONFIG_PATH_MODE_IDX_INVALID
    paths[0].sourceInfo.statusFlags = 0x01
    with patch("winrandr.api.query_active_config", return_value=(paths, modes, 1, 1)):
        with patch("winrandr.api.get_gdi_name", return_value=r"\\.\DISPLAY1"):
            with patch("winrandr.api.get_resolution_refresh_via_enum", return_value=(1920, 1080, 60.0, 32)):
                with patch("winrandr.api.get_friendly_name_via_enum", return_value=""):
                    with patch("winrandr.api.get_screen_size_mm", return_value=(0, 0)):
                        with patch("winrandr.api.enumerate_modes", return_value=[]):
                            result = list_displays()
                            assert len(result) == 1
                            assert result[0].width == 1920
                            assert result[0].height == 1080


# --- set_position_relative ---

def _disp(name="DISPLAY1", x=0, y=0, w=1920, h=1080):
    return DisplayInfo(
        name=rf"\\.\{name}", friendly_name="", connected=True,
        width=w, height=h, refresh_rate=60.0,
        position_x=x, position_y=y,
        is_primary=False, rotation=0, width_mm=0, height_mm=0, modes=[],
    )


def test_list_displays_refresh_fallback():
    """vSyncFreq.Denominator == 0 时回退到 EnumDisplaySettings 获取刷新率。"""
    from winrandr.win32.constants import (
        DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE,
        DISPLAYCONFIG_MODE_INFO_TYPE_TARGET,
    )
    from winrandr.win32.structures import (
        DISPLAYCONFIG_MODE_INFO,
        DISPLAYCONFIG_PATH_INFO,
    )
    paths = (DISPLAYCONFIG_PATH_INFO * 1)()
    modes = (DISPLAYCONFIG_MODE_INFO * 2)()
    paths[0].sourceInfo.modeInfoIdx = 0
    paths[0].targetInfo.modeInfoIdx = 1
    paths[0].sourceInfo.statusFlags = 0x01
    paths[0].targetInfo.rotation = 1
    modes[0].infoType = DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE
    modes[0]._union.sourceMode.width = 1920
    modes[0]._union.sourceMode.height = 1080
    modes[0]._union.sourceMode.position.x = 0
    modes[0]._union.sourceMode.position.y = 0
    modes[1].infoType = DISPLAYCONFIG_MODE_INFO_TYPE_TARGET
    modes[1]._union.targetMode.targetVideoSignalInfo.vSyncFreq.Denominator = 0
    with patch("winrandr.api.query_active_config", return_value=(paths, modes, 1, 2)):
        with patch("winrandr.api.get_gdi_name", return_value=r"\\.\DISPLAY1"):
            with patch("winrandr.api.get_resolution_refresh_via_enum", return_value=(1920, 1080, 144.0, 32)):
                with patch("winrandr.api.get_friendly_name_via_enum", return_value=""):
                    with patch("winrandr.api.get_screen_size_mm", return_value=(0, 0)):
                        with patch("winrandr.api.enumerate_modes", return_value=[]):
                            result = list_displays()
                            assert len(result) == 1
                            assert result[0].refresh_rate == 144.0

def test_rel_position_target_not_found():
    with patch("winrandr.api.list_displays", return_value=[]):
        assert set_position_relative(r"\\.\DISPLAY1", r"\\.\DISPLAY2", "right-of") is False

def test_rel_position_ref_not_found():
    with patch("winrandr.api.list_displays", return_value=[_disp("DISPLAY1")]):
        assert set_position_relative(r"\\.\DISPLAY1", r"\\.\DISPLAY2", "right-of") is False

def test_rel_position_right_of():
    with patch("winrandr.api.set_position", return_value=True) as mock_sp:
        with patch("winrandr.api.list_displays", return_value=[_disp("DISPLAY1"), _disp("DISPLAY2", x=1920)]):
            assert set_position_relative(r"\\.\DISPLAY1", r"\\.\DISPLAY2", "right-of") is True
            mock_sp.assert_called_once_with(r"\\.\DISPLAY1", 1920 + 1920, 0)

def test_rel_position_left_of():
    with patch("winrandr.api.set_position", return_value=True) as mock_sp:
        with patch("winrandr.api.list_displays", return_value=[_disp("DISPLAY1", w=1920), _disp("DISPLAY2", x=1920)]):
            assert set_position_relative(r"\\.\DISPLAY1", r"\\.\DISPLAY2", "left-of") is True
            mock_sp.assert_called_once_with(r"\\.\DISPLAY1", 1920 - 1920, 0)

def test_rel_position_below():
    with patch("winrandr.api.set_position", return_value=True) as mock_sp:
        with patch("winrandr.api.list_displays", return_value=[_disp("DISPLAY1"), _disp("DISPLAY2", x=0, y=1080)]):
            assert set_position_relative(r"\\.\DISPLAY1", r"\\.\DISPLAY2", "below") is True
            mock_sp.assert_called_once_with(r"\\.\DISPLAY1", 0, 1080 + 1080)

def test_rel_position_above():
    with patch("winrandr.api.set_position", return_value=True) as mock_sp:
        displays = [_disp("DISPLAY1", h=1080), _disp("DISPLAY2", x=0, y=1080)]
        with patch("winrandr.api.list_displays", return_value=displays):
            assert set_position_relative(r"\\.\DISPLAY1", r"\\.\DISPLAY2", "above") is True
            mock_sp.assert_called_once_with(r"\\.\DISPLAY1", 0, 1080 - 1080)

def test_rel_position_same_as():
    with patch("winrandr.api.set_position", return_value=True) as mock_sp:
        with patch("winrandr.api.list_displays", return_value=[_disp("DISPLAY1"), _disp("DISPLAY2", x=1920, y=100)]):
            assert set_position_relative(r"\\.\DISPLAY1", r"\\.\DISPLAY2", "same-as") is True
            mock_sp.assert_called_once_with(r"\\.\DISPLAY1", 1920, 100)

def test_rel_position_disconnected_ref_skipped():
    """断开连接的参考显示器应忽略，导致未找到。"""
    d_conn = _disp("DISPLAY1")
    d_disc = _disp("DISPLAY2", x=1920)
    d_disc.connected = False
    with patch("winrandr.api.set_position", return_value=True) as mock_sp:
        with patch("winrandr.api.list_displays", return_value=[d_conn, d_disc]):
            assert set_position_relative(r"\\.\DISPLAY1", r"\\.\DISPLAY2", "right-of") is False
            assert mock_sp.called is False

def test_rel_position_short_name():
    """不带 \\\\.\\ 前缀的短名也应匹配。"""
    with patch("winrandr.api.set_position", return_value=True) as mock_sp:
        with patch("winrandr.api.list_displays", return_value=[_disp("DISPLAY1"), _disp("DISPLAY2", x=1920)]):
            assert set_position_relative("DISPLAY1", "DISPLAY2", "right-of") is True
            mock_sp.assert_called_once()
            args = mock_sp.call_args[0]
            assert "DISPLAY1" in args[0]
            assert "DISPLAY2" not in args[0]

def test_list_displays_refresh_from_qdc():
    """vSyncFreq.Denominator 非零时从 QDC 直接获取刷新率。"""
    from winrandr.win32.constants import (
        DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE,
        DISPLAYCONFIG_MODE_INFO_TYPE_TARGET,
    )
    from winrandr.win32.structures import (
        DISPLAYCONFIG_MODE_INFO,
        DISPLAYCONFIG_PATH_INFO,
    )
    paths = (DISPLAYCONFIG_PATH_INFO * 1)()
    modes = (DISPLAYCONFIG_MODE_INFO * 2)()
    paths[0].sourceInfo.modeInfoIdx = 0
    paths[0].targetInfo.modeInfoIdx = 1
    paths[0].sourceInfo.statusFlags = 0x01
    paths[0].targetInfo.rotation = 1
    modes[0].infoType = DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE
    modes[0]._union.sourceMode.width = 1920
    modes[0]._union.sourceMode.height = 1080
    modes[1].infoType = DISPLAYCONFIG_MODE_INFO_TYPE_TARGET
    modes[1]._union.targetMode.targetVideoSignalInfo.vSyncFreq.Denominator = 1000
    modes[1]._union.targetMode.targetVideoSignalInfo.vSyncFreq.Numerator = 60000
    with patch("winrandr.api.query_active_config", return_value=(paths, modes, 1, 2)):
        with patch("winrandr.api.get_gdi_name", return_value=r"\\.\DISPLAY1"):
            with patch("winrandr.api.get_friendly_name_via_enum", return_value=""):
                with patch("winrandr.api.get_screen_size_mm", return_value=(0, 0)):
                    with patch("winrandr.api.enumerate_modes", return_value=[]):
                        result = list_displays()
                        assert len(result) == 1
                        assert result[0].refresh_rate == 60.0


def test_rel_position_invalid_relation():
    """无效的相对位置关系应返回 False。"""
    with patch("winrandr.api.list_displays", return_value=[_disp("DISPLAY1"), _disp("DISPLAY2", x=1920)]):
        assert set_position_relative(r"\\.\DISPLAY1", r"\\.\DISPLAY2", "invalid") is False


# --- list_providers ---

def test_list_providers_empty():
    with patch("winrandr.api._EnumDisplayDevices", return_value=False):
        assert list_providers() == []


# --- get_display_props ---

def test_get_display_props_empty():
    """当 EnumDisplayDevices 和 query_all_config 均失败时返回空 dict。"""
    with patch("winrandr.api._EnumDisplayDevices", return_value=False):
        with patch("winrandr.api.query_all_config", return_value=None):
            with patch("winrandr.api.get_edid", return_value=None):
                props = get_display_props(r"\\.\DISPLAY1")
                assert props == {}


def test_get_display_props_no_device_id():
    """EnumDisplayDevices 成功但 DeviceID 为空时不应设 device_id。"""
    def fake_enum(_name, _idx, dd_ptr, _flags):
        dd_ptr._obj.DeviceID = ""
        dd_ptr._obj.StateFlags = 0
        return True
    from winrandr.win32.structures import DISPLAYCONFIG_PATH_INFO
    paths = (DISPLAYCONFIG_PATH_INFO * 1)()
    with patch("winrandr.api._EnumDisplayDevices", side_effect=fake_enum):
        with patch("winrandr.api.query_all_config", return_value=(paths, None, 1, 0)):
            with patch("winrandr.api.get_gdi_name", return_value=r"\\.\DISPLAY1"):
                with patch("winrandr.api.get_adapter_name", return_value=""):
                    with patch("winrandr.api.get_monitor_device_path", return_value=""):
                        with patch("winrandr.api.get_edid", return_value=None):
                            props = get_display_props(r"\\.\DISPLAY1")
                            assert "device_id" not in props
                            assert "state_flags" not in props
                            assert "adapter" not in props
                            assert "monitor_path" not in props


def test_get_display_props_no_path_match():
    """query_all_config 有数据但无路径匹配时不应设 adapter/monitor_path。"""
    def fake_enum(_name, _idx, dd_ptr, _flags):
        dd_ptr._obj.DeviceID = r"MONITOR\ABC123"
        dd_ptr._obj.StateFlags = 0x05
        return True
    from winrandr.win32.structures import DISPLAYCONFIG_PATH_INFO
    paths = (DISPLAYCONFIG_PATH_INFO * 1)()
    with patch("winrandr.api._EnumDisplayDevices", side_effect=fake_enum):
        with patch("winrandr.api.query_all_config", return_value=(paths, None, 1, 0)):
            with patch("winrandr.api.get_gdi_name", return_value=r"\\.\DISPLAY99"):  # 不匹配
                with patch("winrandr.api.get_edid", return_value=None):
                    props = get_display_props(r"\\.\DISPLAY1")
                    assert "adapter" not in props
                    assert "monitor_path" not in props
    """get_display_props 完整成功路径。"""
    from winrandr.win32.structures import DISPLAYCONFIG_PATH_INFO
    paths = (DISPLAYCONFIG_PATH_INFO * 1)()

    def fake_enum(_name, _idx, dd_ptr, _flags):
        dd_ptr._obj.DeviceID = r"MONITOR\ABC123\SomeExtra"
        dd_ptr._obj.StateFlags = 0x05  # attached + primary
        return True

    with patch("winrandr.api._EnumDisplayDevices", side_effect=fake_enum):
        with patch("winrandr.api.query_all_config",
                   return_value=(paths, None, 1, 0)):
            with patch("winrandr.api.get_gdi_name", return_value=r"\\.\DISPLAY1"):
                with patch("winrandr.api.get_adapter_name", return_value="GPU0"):
                    with patch("winrandr.api.get_monitor_device_path", return_value=r"\\.\DEVICE123"):
                        with patch("winrandr.api.get_edid", return_value={"edid_name": "TestMonitor"}):
                            props = get_display_props(r"\\.\DISPLAY1")
                            assert props["device_id"] == r"MONITOR\ABC123\SomeExtra"
                            assert "attached" in props["state_flags"]
                            assert "primary" in props["state_flags"]
                            assert props["adapter"] == "GPU0"
                            assert props["monitor_path"] == r"\\.\DEVICE123"
                            assert props["edid_name"] == "TestMonitor"
