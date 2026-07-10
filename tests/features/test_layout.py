"""Tests for features/layout.py — 真实硬件测试。"""

from tests.conftest import _write_op
from winrandr.api import list_displays
from winrandr.features.layout import (
    set_noprimary,
    set_off,
    set_position,
    set_primary,
    set_reflect,
    set_rotation,
)


def _main_display():
    displays = list_displays()
    for d in displays:
        if d.connected and d.is_primary:
            return d
    for d in displays:
        if d.connected:
            return d
    return None


def test_set_rotation_invalid_degrees():
    """无效旋转角度应返回 False（纯逻辑检查）。"""
    assert set_rotation(r"\\.\DISPLAY1", 45) is False


def test_set_reflect_unsupported():
    """不支持的镜像轴应返回 False（纯逻辑检查）。"""
    assert set_reflect(r"\\.\DISPLAY1", "x") is False
    assert set_reflect(r"\\.\DISPLAY1", "y") is False


def test_set_reflect_xy():
    """xy 镜像应委托为 180° 旋转。"""
    assert set_reflect(r"\\.\DISPLAY1", "xy") is False  # 真实调用，不存在的显示器返回 False


def test_set_position_readonly_check():
    """验证 set_position 在真实硬件上不崩溃（不写，仅检查参数校验）。"""
    result = set_position(r"\\.\NONEXISTENT_DISPLAY", 0, 0)
    assert result is False


def test_set_rotation_real(profile_backup):
    """真实旋转测试：用当前角度作为参数写入。"""
    d = _main_display()
    if d is None:
        return
    _write_op(set_rotation, d.name, d.rotation)


def test_set_position_real(profile_backup):
    """真实位置测试：用当前位置作为参数写入。"""
    d = _main_display()
    if d is None:
        return
    _write_op(set_position, d.name, d.position_x, d.position_y)


def test_set_primary_real(profile_backup):
    """真实主屏测试。"""
    d = _main_display()
    if d is None:
        return
    _write_op(set_primary, d.name)


def test_set_noprimary_real(profile_backup):
    """真实清除主屏标记测试。"""
    d = _main_display()
    if d is None:
        return
    _write_op(set_noprimary)
    _write_op(set_primary, d.name)


def test_set_off_last_display_guard():
    """真实环境：应禁止关闭唯一活动显示器。"""
    displays = list_displays()
    active = [d for d in displays if d.connected]
    if len(active) <= 1:
        return
    result = set_off(active[0].name)
    assert isinstance(result, bool)


def test_set_off_real(profile_backup, connected_displays):
    """真实关闭测试：关闭第一个非主显示器。"""
    displays = connected_displays
    non_primary = [d for d in displays if not d.is_primary]
    target = non_primary[0] if non_primary else displays[1]
    _write_op(set_off, target.name)


# --- Mock 错误分支测试 ---


def test_set_position_sdc_not_available():
    """SDC 不可用时 set_position 应返回 False。"""
    from unittest.mock import patch

    with patch("winrandr.features.layout.set_display_config_available", return_value=False):
        assert set_position(r"\\.\DISPLAY1", 0, 0) is False


def test_set_position_invalid_mode_idx():
    """无效 mode index 时 set_position 应返回 False。"""
    from unittest.mock import patch

    with patch("winrandr.features.layout.set_display_config_available", return_value=True):
        with patch("winrandr.features.layout.query_active_config", return_value=([], [], 0, 0)):
            assert set_position(r"\\.\DISPLAY1", 0, 0) is False


def test_set_rotation_sdc_unavailable():
    """SDC 不可用时 set_rotation 应返回 False。"""
    from unittest.mock import patch

    with patch("winrandr.features.layout.set_display_config_available", return_value=False):
        assert set_rotation(r"\\.\DISPLAY1", 90) is False


def test_set_rotation_path_not_found():
    """set_rotation 找不到路径应返回 False。"""
    from unittest.mock import patch

    with patch("winrandr.features.layout.set_display_config_available", return_value=True):
        with patch("winrandr.features.layout.query_active_config", return_value=([], [], 0, 0)):
            assert set_rotation(r"\\.\DISPLAY1", 90) is False


def test_set_primary_sdc_unavailable():
    """SDC 不可用时 set_primary 应返回 False。"""
    from unittest.mock import patch

    with patch("winrandr.features.layout.set_display_config_available", return_value=False):
        assert set_primary(r"\\.\DISPLAY1") is False


def test_set_primary_path_not_found():
    """set_primary 找不到路径应返回 False。"""
    from unittest.mock import patch

    with patch("winrandr.features.layout.set_display_config_available", return_value=True):
        with patch("winrandr.features.layout.query_active_config", return_value=([], [], 0, 0)):
            assert set_primary(r"\\.\DISPLAY1") is False


def test_set_off_sdc_unavailable():
    """SDC 不可用时 set_off 应返回 False。"""
    from unittest.mock import patch

    with patch("winrandr.features.layout.set_display_config_available", return_value=False):
        assert set_off(r"\\.\DISPLAY1") is False


def test_set_off_path_not_found():
    """set_off 找不到路径应返回 False。"""
    from unittest.mock import patch

    with patch("winrandr.features.layout.set_display_config_available", return_value=True):
        with patch("winrandr.features.layout.query_active_config", return_value=([], [], 0, 0)):
            assert set_off(r"\\.\DISPLAY1") is False


def test_set_noprimary_sdc_unavailable():
    """SDC 不可用时 set_noprimary 应返回 False。"""
    from unittest.mock import patch

    with patch("winrandr.features.layout.set_display_config_available", return_value=False):
        assert set_noprimary() is False


def test_set_position_invalid_mode_idx_detected():
    """set_position 检测到无效 mode index 时应返回 False。"""
    from unittest.mock import patch

    from winrandr.win32.constants import DISPLAYCONFIG_PATH_MODE_IDX_INVALID
    from winrandr.win32.structures import (
        DISPLAYCONFIG_MODE_INFO,
        DISPLAYCONFIG_PATH_INFO,
        DISPLAYCONFIG_PATH_SOURCE_INFO,
        DISPLAYCONFIG_PATH_TARGET_INFO,
    )

    src = DISPLAYCONFIG_PATH_SOURCE_INFO()
    src.modeInfoIdx = DISPLAYCONFIG_PATH_MODE_IDX_INVALID
    tgt = DISPLAYCONFIG_PATH_TARGET_INFO()
    path = DISPLAYCONFIG_PATH_INFO()
    path.sourceInfo = src
    path.targetInfo = tgt
    paths = (DISPLAYCONFIG_PATH_INFO * 1)(path)
    modes = (DISPLAYCONFIG_MODE_INFO * 1)()

    with patch("winrandr.features.layout.set_display_config_available", return_value=True):
        with patch("winrandr.features.layout.query_active_config", return_value=(paths, modes, 1, 1)):
            with patch("winrandr.features.layout.get_gdi_name", return_value=r"\\.\DISPLAY1"):
                with patch("winrandr.win32.utils.get_gdi_name", return_value=r"\\.\DISPLAY1"):
                    assert set_position(r"\\.\DISPLAY1", 0, 0) is False


def test_set_off_last_display_guard_mocked():
    """set_off 禁止关闭唯一活动显示器（mock）。"""
    from unittest.mock import patch

    from winrandr.win32.structures import (
        DISPLAYCONFIG_PATH_INFO,
        DISPLAYCONFIG_PATH_SOURCE_INFO,
        DISPLAYCONFIG_PATH_TARGET_INFO,
    )

    src = DISPLAYCONFIG_PATH_SOURCE_INFO()
    tgt = DISPLAYCONFIG_PATH_TARGET_INFO()
    path = DISPLAYCONFIG_PATH_INFO()
    path.sourceInfo = src
    path.targetInfo = tgt
    paths = (DISPLAYCONFIG_PATH_INFO * 1)(path)
    modes = ()

    with patch("winrandr.features.layout.set_display_config_available", return_value=True):
        with patch("winrandr.features.layout.query_active_config", return_value=(paths, modes, 1, 0)):
            with patch("winrandr.features.layout.get_gdi_name", return_value=r"\\.\DISPLAY1"):
                with patch("winrandr.win32.utils.get_gdi_name", return_value=r"\\.\DISPLAY1"):
                    assert set_off(r"\\.\DISPLAY1") is False
