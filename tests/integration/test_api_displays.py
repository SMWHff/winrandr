"""Tests for public API functions — list_displays and list_providers."""

from unittest.mock import patch

from winrandr.api import list_displays, list_providers


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


# --- list_providers ---


def test_list_providers_empty():
    with patch("winrandr.api._EnumDisplayDevices", return_value=False):
        assert list_providers() == []
