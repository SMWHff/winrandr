"""Win32 工具函数——配置应用与缓存相关测试。"""

from unittest.mock import patch

from winrandr.win32 import utils as win32_utils
from winrandr.win32.structures import DISPLAYCONFIG_MODE_INFO, DISPLAYCONFIG_PATH_INFO


def _clear_caches():
    win32_utils._QDC_CACHE = None
    win32_utils._QDC_ALL_CACHE = None
    win32_utils._SDC_AVAILABLE = None


# --- apply_config ---


def test_apply_config_uses_default_flags():
    _clear_caches()
    paths = (DISPLAYCONFIG_PATH_INFO * 1)()
    modes = (DISPLAYCONFIG_MODE_INFO * 1)()
    with patch("winrandr.win32.utils._SetDisplayConfig", return_value=0) as mock_sdc:
        assert win32_utils.apply_config(paths, 1, modes, 1) is True
        args = mock_sdc.call_args[0]
        assert args[0] == 1
        assert args[1] is paths
        assert args[2] == 1
        assert args[3] is modes


def test_apply_config_failure():
    _clear_caches()
    paths = (DISPLAYCONFIG_PATH_INFO * 1)()
    modes = (DISPLAYCONFIG_MODE_INFO * 1)()
    with patch("winrandr.win32.utils._SetDisplayConfig", return_value=5):
        assert win32_utils.apply_config(paths, 1, modes, 1, flags=0) is False


def test_apply_config_unknown_error():
    _clear_caches()
    paths = (DISPLAYCONFIG_PATH_INFO * 1)()
    modes = (DISPLAYCONFIG_MODE_INFO * 1)()
    with patch("winrandr.win32.utils._SetDisplayConfig", return_value=999):
        assert win32_utils.apply_config(paths, 1, modes, 1, flags=0) is False


# --- set_display_config_available ---


def test_set_display_config_available_cache():
    _clear_caches()
    win32_utils._SDC_AVAILABLE = True
    assert win32_utils.set_display_config_available() is True


def test_set_display_config_available_exception():
    _clear_caches()
    with patch("winrandr.win32.utils._GetDisplayConfigBufferSizes", side_effect=OSError("mock")):
        assert win32_utils.set_display_config_available() is False
        assert win32_utils._SDC_AVAILABLE is False


# --- find_path_idx ---


def test_find_path_idx_not_found():
    _clear_caches()
    paths = (DISPLAYCONFIG_PATH_INFO * 2)()
    with patch("winrandr.win32.utils.get_gdi_name", side_effect=[r"\\.\DISPLAY1", r"\\.\DISPLAY2"]):
        result = win32_utils.find_path_idx(paths, 2, r"\\.\DISPLAY99")
        assert result is None


def test_find_path_idx_found():
    _clear_caches()
    paths = (DISPLAYCONFIG_PATH_INFO * 2)()
    with patch("winrandr.win32.utils.get_gdi_name", side_effect=[r"\\.\DISPLAY1", r"\\.\DISPLAY2"]):
        result = win32_utils.find_path_idx(paths, 2, r"\\.\DISPLAY2")
        assert result == 1


# --- apply_filtered ---


def test_apply_filtered_empty_paths():
    _clear_caches()
    paths = (DISPLAYCONFIG_PATH_INFO * 2)()
    modes = (DISPLAYCONFIG_MODE_INFO * 1)()
    result = win32_utils.apply_filtered(paths, 2, modes, 0)
    assert result is False


def test_apply_filtered_success():
    _clear_caches()
    paths = (DISPLAYCONFIG_PATH_INFO * 1)()
    modes = (DISPLAYCONFIG_MODE_INFO * 2)()

    from winrandr.win32.constants import (
        DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE,
        DISPLAYCONFIG_MODE_INFO_TYPE_TARGET,
    )

    paths[0].sourceInfo.modeInfoIdx = 0
    paths[0].targetInfo.modeInfoIdx = 1
    modes[0].infoType = DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE
    modes[1].infoType = DISPLAYCONFIG_MODE_INFO_TYPE_TARGET

    with patch("winrandr.win32.utils.apply_config", return_value=True) as mock_ac:
        assert win32_utils.apply_filtered(paths, 1, modes, 2) is True
        mock_ac.assert_called_once()
        args = mock_ac.call_args[0]
        assert len(args[0]) == 1


# --- _invalidate_qdc_cache ---


def test_invalidate_qdc_cache():
    _clear_caches()
    win32_utils._QDC_CACHE = "something"
    win32_utils._QDC_ALL_CACHE = "else"
    win32_utils._invalidate_qdc_cache()
    assert win32_utils._QDC_CACHE is None
    assert win32_utils._QDC_ALL_CACHE is None
