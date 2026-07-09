"""Tests for public API function get_display_props."""

from unittest.mock import patch

from winrandr.api import get_display_props


def test_get_display_props_connector_type():
    """get_display_props 应包含 connector_type。"""
    from winrandr.win32.structures import DISPLAYCONFIG_PATH_INFO

    paths = (DISPLAYCONFIG_PATH_INFO * 1)()

    def fake_enum(_name, _idx, dd_ptr, _flags):
        dd_ptr._obj.DeviceID = r"MONITOR\ABC123"
        dd_ptr._obj.StateFlags = 0x05
        return True

    with patch("winrandr.api._EnumDisplayDevices", side_effect=fake_enum):
        with patch("winrandr.api.query_all_config", return_value=(paths, None, 1, 0)):
            with patch("winrandr.api.get_gdi_name", return_value=r"\\.\DISPLAY1"):
                with patch("winrandr.api.get_adapter_name", return_value=""):
                    with patch("winrandr.api.get_monitor_device_path", return_value=""):
                        with patch("winrandr.api.get_connector_type", return_value="HDMI"):
                            with patch("winrandr.api.get_edid", return_value=None):
                                props = get_display_props(r"\\.\DISPLAY1")
                                assert props.get("connector_type") == "HDMI"


def test_get_display_props_no_connector_type():
    """get_display_props 当连接类型为空时不应包含 connector_type。"""
    from winrandr.win32.structures import DISPLAYCONFIG_PATH_INFO

    paths = (DISPLAYCONFIG_PATH_INFO * 1)()

    def fake_enum(_name, _idx, dd_ptr, _flags):
        dd_ptr._obj.DeviceID = r"MONITOR\ABC123"
        dd_ptr._obj.StateFlags = 0x05
        return True

    with patch("winrandr.api._EnumDisplayDevices", side_effect=fake_enum):
        with patch("winrandr.api.query_all_config", return_value=(paths, None, 1, 0)):
            with patch("winrandr.api.get_gdi_name", return_value=r"\\.\DISPLAY1"):
                with patch("winrandr.api.get_adapter_name", return_value=""):
                    with patch("winrandr.api.get_monitor_device_path", return_value=""):
                        with patch("winrandr.api.get_connector_type", return_value=""):
                            with patch("winrandr.api.get_edid", return_value=None):
                                props = get_display_props(r"\\.\DISPLAY1")
                                assert "connector_type" not in props


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


def test_get_display_props_full_success():
    """get_display_props 完整成功路径。"""
    from winrandr.win32.structures import DISPLAYCONFIG_PATH_INFO

    paths = (DISPLAYCONFIG_PATH_INFO * 1)()

    def fake_enum(_name, _idx, dd_ptr, _flags):
        dd_ptr._obj.DeviceID = r"MONITOR\ABC123\SomeExtra"
        dd_ptr._obj.StateFlags = 0x05  # attached + primary
        return True

    with patch("winrandr.api._EnumDisplayDevices", side_effect=fake_enum):
        with patch("winrandr.api.query_all_config", return_value=(paths, None, 1, 0)):
            with patch("winrandr.api.get_gdi_name", return_value=r"\\.\DISPLAY1"):
                with patch("winrandr.api.get_adapter_name", return_value="GPU0"):
                    with patch("winrandr.api.get_monitor_device_path", return_value=r"\\.\DEVICE123"):
                        with patch("winrandr.api.get_connector_type", return_value="HDMI"):
                            with patch("winrandr.api.get_edid", return_value={"edid_name": "TestMonitor"}):
                                props = get_display_props(r"\\.\DISPLAY1")
                                assert props["device_id"] == r"MONITOR\ABC123\SomeExtra"
                                assert "attached" in props["state_flags"]
                                assert "primary" in props["state_flags"]
                                assert props["adapter"] == "GPU0"
                                assert props["monitor_path"] == r"\\.\DEVICE123"
                                assert props.get("connector_type") == "HDMI"
                                assert props["edid_name"] == "TestMonitor"
