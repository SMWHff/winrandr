"""Tests for features/resolution.py with mocked Win32 API."""

from unittest.mock import patch


def test_enumerate_modes_empty():
    """EnumDisplaySettings 返回 False 时返回空列表。"""
    from winrandr.features.resolution import enumerate_modes

    with patch("winrandr.features.resolution._EnumDisplaySettings", return_value=0):
        modes = enumerate_modes("DISPLAY1", 1920, 1080, 60.0)
        assert modes == []


def test_enumerate_modes_fractional_refresh_rates():
    """QDC 报告的 59.94 应与 EnumDisplaySettings 的 60 匹配。"""
    from ctypes import sizeof

    from winrandr.features.resolution import enumerate_modes
    from winrandr.win32.structures import DEVMODE

    def fake_enum(_name, _i, dm_ptr):
        dm_ptr._obj.dmSize = sizeof(DEVMODE)
        if _i == 0:
            dm_ptr._obj.dmPelsWidth = 1920
            dm_ptr._obj.dmPelsHeight = 1080
            dm_ptr._obj.dmDisplayFrequency = 60
            return 1
        return 0  # 无更多模式

    with patch("winrandr.features.resolution._EnumDisplaySettings", side_effect=fake_enum):
        # cur_refresh=59.94 模拟 QDC 报告分数刷新率
        modes = enumerate_modes("DISPLAY1", 1920, 1080, 59.94)
        assert len(modes) == 1
        assert modes[0].is_current is True


def test_enumerate_modes_skips_invalid():
    """无效尺寸（frequency=0）的 mode 应跳过（覆盖 33->44 分支）。"""
    from ctypes import sizeof

    from winrandr.features.resolution import enumerate_modes
    from winrandr.win32.structures import DEVMODE

    def fake_enum(_name, _i, dm_ptr):
        dm_ptr._obj.dmSize = sizeof(DEVMODE)
        if _i == 0:
            dm_ptr._obj.dmPelsWidth = 1920
            dm_ptr._obj.dmPelsHeight = 1080
            dm_ptr._obj.dmDisplayFrequency = 60
            return 1
        if _i == 1:
            dm_ptr._obj.dmPelsWidth = 800
            dm_ptr._obj.dmPelsHeight = 600
            dm_ptr._obj.dmDisplayFrequency = 0  # 无效频率
            return 1
        return 0  # 无更多模式

    with patch("winrandr.features.resolution._EnumDisplaySettings", side_effect=fake_enum):
        modes = enumerate_modes("DISPLAY1", 1920, 1080, 60.0)
        assert len(modes) == 1
        assert modes[0].width == 1920
        assert modes[0].refresh_rate == 60.0


def test_set_resolution_success():
    from winrandr.features.resolution import set_resolution

    with patch("winrandr.features.resolution._EnumDisplaySettings", return_value=1):
        with patch("winrandr.features.resolution._ChangeDisplaySettingsEx", return_value=0):
            assert set_resolution(r"\\.\DISPLAY1", 1920, 1080, 60.0) is True


def test_set_resolution_failure():
    from winrandr.features.resolution import set_resolution

    with patch("winrandr.features.resolution._EnumDisplaySettings", return_value=1):
        with patch("winrandr.features.resolution._ChangeDisplaySettingsEx", return_value=-2):
            assert set_resolution(r"\\.\DISPLAY1", 1920, 1080) is False


def test_set_resolution_enum_fails():
    from winrandr.features.resolution import set_resolution

    with patch("winrandr.features.resolution._EnumDisplaySettings", return_value=0):
        assert set_resolution(r"\\.\DISPLAY1", 1920, 1080) is False


def test_set_preferred_resolution_success():
    from winrandr.features.resolution import set_preferred_resolution

    with patch("winrandr.features.resolution._EnumDisplaySettings", return_value=1):
        with patch("winrandr.features.resolution._ChangeDisplaySettingsEx", return_value=0):
            assert set_preferred_resolution(r"\\.\DISPLAY1") is True


def test_set_preferred_resolution_no_registry():
    from winrandr.features.resolution import set_preferred_resolution

    with patch("winrandr.features.resolution._EnumDisplaySettings", return_value=0):
        assert set_preferred_resolution(r"\\.\DISPLAY1") is False


def test_set_auto_delegates():
    from winrandr.features.resolution import set_auto

    with patch("winrandr.features.resolution.set_preferred_resolution", return_value=True) as mock_fn:
        assert set_auto(r"\\.\DISPLAY1") is True
        mock_fn.assert_called_once_with(r"\\.\DISPLAY1")
