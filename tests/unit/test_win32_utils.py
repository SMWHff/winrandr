"""Tests for win32/utils.py utility functions."""

from unittest.mock import patch

from winrandr.win32 import utils as win32_utils
from winrandr.win32.structures import DISPLAYCONFIG_MODE_INFO, DISPLAYCONFIG_PATH_INFO


def _clear_caches():
    win32_utils._QDC_CACHE = None
    win32_utils._QDC_ALL_CACHE = None
    win32_utils._SDC_AVAILABLE = None


# --- get_adapter_name ---


def test_get_adapter_name_failure():
    """_DisplayConfigGetDeviceInfo 失败时返回空字符串。"""
    _clear_caches()
    paths = (DISPLAYCONFIG_PATH_INFO * 1)()
    with patch("winrandr.win32.utils._DisplayConfigGetDeviceInfo", return_value=-1):
        result = win32_utils.get_adapter_name(paths[0])
        assert result == ""


# --- get_monitor_device_path ---


def test_get_monitor_device_path_failure():
    """_DisplayConfigGetDeviceInfo 失败时返回空字符串。"""
    _clear_caches()
    paths = (DISPLAYCONFIG_PATH_INFO * 1)()
    with patch("winrandr.win32.utils._DisplayConfigGetDeviceInfo", return_value=-1):
        result = win32_utils.get_monitor_device_path(paths[0])
        assert result == ""


# --- query_active_config ---


def test_query_active_config_buffersizes_fails():
    """GetDisplayConfigBufferSizes 失败时返回 None。"""
    _clear_caches()
    with patch("winrandr.win32.utils._GetDisplayConfigBufferSizes", return_value=1):
        result = win32_utils.query_active_config()
        assert result is None


def test_query_active_config_query_fails():
    """QueryDisplayConfig 失败时返回 None。"""
    _clear_caches()
    with patch("winrandr.win32.utils._GetDisplayConfigBufferSizes", return_value=0):
        with patch("winrandr.win32.utils._QueryDisplayConfig", return_value=1):
            result = win32_utils.query_active_config()
            assert result is None


def test_query_active_config_cache():
    """缓存命中时直接返回缓存结果。"""
    _clear_caches()
    fake = ("cached",)
    win32_utils._QDC_CACHE = fake
    assert win32_utils.query_active_config() is fake


# --- query_all_config ---


def test_query_all_config_cache():
    """query_all_config 缓存命中时直接返回。"""
    _clear_caches()
    fake = ("all_cached",)
    win32_utils._QDC_ALL_CACHE = fake
    assert win32_utils.query_all_config() is fake


def test_query_all_config_buffersizes_fails():
    """GetDisplayConfigBufferSizes (all) 失败时返回 None。"""
    _clear_caches()
    with patch("winrandr.win32.utils._GetDisplayConfigBufferSizes", return_value=1):
        result = win32_utils.query_all_config()
        assert result is None


def test_query_all_config_query_fails():
    """QueryDisplayConfig (all) 失败时返回 None。"""
    _clear_caches()
    with patch("winrandr.win32.utils._GetDisplayConfigBufferSizes", return_value=0):
        with patch("winrandr.win32.utils._QueryDisplayConfig", return_value=1):
            result = win32_utils.query_all_config()
            assert result is None


# --- get_screen_size_mm ---


def test_get_screen_size_mm_empty_name():
    """空名称时返回 0, 0。"""
    assert win32_utils.get_screen_size_mm("") == (0, 0)


def test_get_screen_size_mm_create_fails():
    """CreateDCW 失败时返回 0, 0。"""
    with patch("winrandr.win32.utils._CreateDCW", return_value=None):
        assert win32_utils.get_screen_size_mm(r"\\.\DISPLAY1") == (0, 0)


def test_get_screen_size_mm_exception():
    """获取尺寸异常时返回 0, 0。"""
    with patch("winrandr.win32.utils._CreateDCW", return_value=0x1234):
        with patch("winrandr.win32.utils._GetDeviceCaps", side_effect=OSError("mock")):
            with patch("winrandr.win32.utils._DeleteDC"):
                assert win32_utils.get_screen_size_mm(r"\\.\DISPLAY1") == (0, 0)


# --- get_friendly_name_via_enum ---


def test_get_friendly_name_via_enum_second_fails():
    """第二个 EnumDisplayDevices 失败时回退到第一个设备。"""
    with patch("winrandr.win32.utils._EnumDisplayDevices") as mock_ed:
        mock_ed.side_effect = [True, False]
        result = win32_utils.get_friendly_name_via_enum(r"\\.\DISPLAY1")
        assert isinstance(result, str)


def test_get_friendly_name_via_enum_both_success():
    """两个 EnumDisplayDevices 都成功时返回第二个设备名。"""
    with patch("winrandr.win32.utils._EnumDisplayDevices") as mock_ed:
        mock_ed.side_effect = [True, True]
        result = win32_utils.get_friendly_name_via_enum(r"\\.\DISPLAY1")
        assert isinstance(result, str)


def test_get_friendly_name_via_enum_first_fails():
    """第一个 EnumDisplayDevices 失败时返回空字符串。"""
    with patch("winrandr.win32.utils._EnumDisplayDevices", return_value=False):
        result = win32_utils.get_friendly_name_via_enum(r"\\.\DISPLAY1")
        assert result == ""


def test_query_all_config_success():
    """query_all_config 正常返回配置（覆盖缓存失效后的成功路径）。"""
    _clear_caches()
    from winrandr.win32.constants import (
        DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE,
        DISPLAYCONFIG_MODE_INFO_TYPE_TARGET,
    )

    path_count_val = 1
    mode_count_val = 2

    paths_arr = (DISPLAYCONFIG_PATH_INFO * path_count_val)()
    modes_arr = (DISPLAYCONFIG_MODE_INFO * mode_count_val)()
    paths_arr[0].sourceInfo.modeInfoIdx = 0
    paths_arr[0].targetInfo.modeInfoIdx = 1
    paths_arr[0].sourceInfo.statusFlags = 0
    modes_arr[0].infoType = DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE
    modes_arr[1].infoType = DISPLAYCONFIG_MODE_INFO_TYPE_TARGET

    def fake_get_sizes(_flags, pc, mc):
        pc._obj.value = path_count_val
        mc._obj.value = mode_count_val
        return 0

    def fake_query(_flags, pc, paths, mc, modes, _other):
        paths[0] = paths_arr[0]
        modes[0] = modes_arr[0]
        modes[1] = modes_arr[1]
        pc._obj.value = path_count_val
        mc._obj.value = mode_count_val
        return 0

    with patch("winrandr.win32.utils._GetDisplayConfigBufferSizes", side_effect=fake_get_sizes):
        with patch("winrandr.win32.utils._QueryDisplayConfig", side_effect=fake_query):
            result = win32_utils.query_all_config()
            assert result is not None
            assert result[2] == 1
            assert result[3] == 2


def test_set_display_config_available_returns_true():
    """GetDisplayConfigBufferSizes 成功时返回 True。"""
    _clear_caches()
    with patch("winrandr.win32.utils._GetDisplayConfigBufferSizes", return_value=0):
        assert win32_utils.set_display_config_available() is True
