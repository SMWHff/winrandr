"""Tests for features/resolution.py — 真实硬件测试。"""

from tests.conftest import _main_display, _write_op
from winrandr.api import enumerate_modes, list_displays
from winrandr.features.resolution import set_auto, set_preferred_resolution, set_resolution

# --- 只读：enumerate_modes ---


def test_enumerate_modes_real():
    """真实显示器应返回有效模式列表。"""
    d = _main_display(list_displays())
    if d is None:
        return
    modes = enumerate_modes(d.name, d.width, d.height, d.refresh_rate)
    assert isinstance(modes, list)
    if modes:
        m = modes[0]
        assert m.width > 0
        assert m.height > 0
        assert m.refresh_rate > 0


def test_enumerate_modes_current_detected():
    """验证当前模式被标记为 is_current。"""
    d = _main_display(list_displays())
    if d is None:
        return
    modes = enumerate_modes(d.name, d.width, d.height, d.refresh_rate)
    current = [m for m in modes if m.is_current]
    assert len(current) >= 1, "应至少有一个模式被标记为当前模式"


def test_enumerate_modes_nonexistent():
    """不存在显示器的 enumerate_modes 应返回空列表。"""
    modes = enumerate_modes(r"\\.\NONEXISTENT", 1920, 1080, 60.0)
    assert modes == []


# --- 写操作（profile_backup + xfail） ---


def test_set_resolution_real(profile_backup):
    """真实分辨率设置：使用当前分辨率作为参数。"""
    d = _main_display(list_displays())
    if d is None:
        return
    _write_op(set_resolution, d.name, d.width, d.height, d.refresh_rate)


def test_set_preferred_resolution_real(profile_backup):
    """真实首选分辨率设置。"""
    d = _main_display(list_displays())
    if d is None:
        return
    _write_op(set_preferred_resolution, d.name)


def test_set_auto_real(profile_backup):
    """真实 auto 设置。"""
    d = _main_display(list_displays())
    if d is None:
        return
    _write_op(set_auto, d.name)


# --- Mock 错误分支测试 ---


def test_set_resolution_change_fails():
    """ChangeDisplaySettingsEx 非成功时应返回 False。"""
    from unittest.mock import patch

    with patch("winrandr.features.resolution._ChangeDisplaySettingsEx", return_value=1):  # 非成功
        assert set_resolution(r"\\.\DISPLAY1", 1920, 1080) is False


def test_set_preferred_resolution_no_registry():
    """EnumDisplaySettings 注册表查找失败时应返回 False。"""
    from unittest.mock import patch

    with patch("winrandr.features.resolution._EnumDisplaySettings", return_value=0):
        assert set_preferred_resolution(r"\\.\DISPLAY1") is False
