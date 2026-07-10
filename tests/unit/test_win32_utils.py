"""Tests for win32/utils.py utility functions — 真实硬件测试。"""

from winrandr.win32 import utils as win32_utils
from winrandr.win32.structures import DISPLAYCONFIG_PATH_INFO


def _clear_caches():
    win32_utils._QDC_CACHE = None
    win32_utils._QDC_ALL_CACHE = None
    win32_utils._SDC_AVAILABLE = None


def _real_config():
    config = win32_utils.query_active_config()
    if config is None or config[2] == 0:
        return None
    return config


def test_get_adapter_name_failure():
    """不存在的路径应返回空字符串。"""
    path = (DISPLAYCONFIG_PATH_INFO * 1)()[0]
    result = win32_utils.get_adapter_name(path)
    assert result == ""


def test_get_monitor_device_path_failure():
    """不存在的路径应返回空字符串。"""
    path = (DISPLAYCONFIG_PATH_INFO * 1)()[0]
    result = win32_utils.get_monitor_device_path(path)
    assert result == ""


def test_query_active_config_success():
    """真实 query_active_config 应返回有效配置或 None。"""
    _clear_caches()
    result = win32_utils.query_active_config()
    if result is not None:
        paths, modes, path_count, mode_count = result
        assert path_count >= 0
        assert mode_count >= 0
        assert hasattr(paths, "__len__")
        assert hasattr(modes, "__len__")


def test_query_active_config_cache():
    """缓存命中时直接返回缓存结果。"""
    _clear_caches()
    fake = ("cached",)
    win32_utils._QDC_CACHE = fake
    assert win32_utils.query_active_config() is fake


def test_query_all_config_cache():
    """query_all_config 缓存命中时直接返回。"""
    _clear_caches()
    fake = ("all_cached",)
    win32_utils._QDC_ALL_CACHE = fake
    assert win32_utils.query_all_config() is fake


def test_query_all_config_success():
    """真实 query_all_config 应返回有效配置或 None。"""
    _clear_caches()
    result = win32_utils.query_all_config()
    if result is not None:
        _paths, _modes, path_count, mode_count = result
        assert path_count >= 0
        assert mode_count >= 0


def test_get_screen_size_mm_empty_name():
    """空名称时返回 0, 0。"""
    assert win32_utils.get_screen_size_mm("") == (0, 0)


def test_get_screen_size_mm_real():
    """真实 GDI 名应返回物理尺寸或 0,0。"""
    config = _real_config()
    if config is None:
        return
    path = config[0][0]
    gdi = win32_utils.get_gdi_name(path)
    if gdi:
        w, h = win32_utils.get_screen_size_mm(gdi)
        assert w >= 0
        assert h >= 0


def test_get_friendly_name_via_enum_real():
    """真实 GDI 名应返回友好名称或空字符串。"""
    config = _real_config()
    if config is None:
        return
    path = config[0][0]
    gdi = win32_utils.get_gdi_name(path)
    if gdi:
        name = win32_utils.get_friendly_name_via_enum(gdi)
        assert isinstance(name, str)


def test_get_friendly_name_via_enum_failure():
    """不存在的 GDI 名应返回空字符串。"""
    result = win32_utils.get_friendly_name_via_enum(r"\\.\NONEXISTENT")
    assert result == ""


def test_get_adapter_name_real():
    """真实路径应返回非空适配器名或空字符串。"""
    config = _real_config()
    if config is None:
        return
    path = config[0][0]
    result = win32_utils.get_adapter_name(path)
    assert isinstance(result, str)


def test_get_monitor_device_path_real():
    """真实路径应返回设备路径或空字符串。"""
    config = _real_config()
    if config is None:
        return
    path = config[0][0]
    result = win32_utils.get_monitor_device_path(path)
    assert isinstance(result, str)


def test_get_resolution_refresh_via_enum_real():
    """真实 GDI 名应返回分辨率/刷新率或零值。"""
    config = _real_config()
    if config is None:
        return
    path = config[0][0]
    gdi = win32_utils.get_gdi_name(path)
    if gdi:
        w, h, rr, _bpp = win32_utils.get_resolution_refresh_via_enum(gdi)
        assert isinstance(w, int) and w >= 0
        assert isinstance(h, int) and h >= 0
        assert isinstance(rr, float) and rr >= 0


def test_set_display_config_available():
    """SDC 可用性检测应返回布尔值。"""
    _clear_caches()
    result = win32_utils.set_display_config_available()
    assert isinstance(result, bool)


def test_get_screen_size_mm_dc_none():
    """CreateDCW 返回 None 时 get_screen_size_mm 应返回 (0,0)。"""
    from unittest.mock import patch

    with patch("winrandr.win32.utils._CreateDCW", return_value=None):
        result = win32_utils.get_screen_size_mm(r"\\.\DISPLAY1")
    assert result == (0, 0)


def test_get_screen_size_mm_oserror():
    """CreateDCW 抛出 OSError 时 get_screen_size_mm 应返回 (0,0)。"""
    from unittest.mock import patch

    with patch("winrandr.win32.utils._CreateDCW", side_effect=OSError("access denied")):
        result = win32_utils.get_screen_size_mm(r"\\.\DISPLAY1")
    assert result == (0, 0)


def test_get_resolution_refresh_via_enum_failure():
    """EnumDisplaySettings 失败时应返回零值。"""
    from unittest.mock import patch

    with patch("winrandr.win32.utils._EnumDisplaySettings", return_value=0):
        w, h, rr, bpp = win32_utils.get_resolution_refresh_via_enum(r"\\.\DISPLAY1")
    assert (w, h, rr, bpp) == (0, 0, 0.0, 32)
