"""Tests for features/gamma.py — 真实硬件测试。"""

from tests.conftest import _write_op
from winrandr.api import list_displays
from winrandr.features.gamma import (
    _reset_gamma_to_identity,
    identify_display,
    set_brightness,
    set_gamma,
    set_night_mode,
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


# --- 参数校验（纯逻辑，不调 Win32 API） ---


def test_set_brightness_negative():
    """负亮度应返回 False。"""
    assert set_brightness(r"\\.\DISPLAY1", -0.5) is False


def test_set_night_mode_strength_negative():
    """strength=-0.1 应返回 False。"""
    assert set_night_mode(r"\\.\DISPLAY1", -0.1) is False


def test_set_night_mode_strength_too_high():
    """strength=1.5 应返回 False。"""
    assert set_night_mode(r"\\.\DISPLAY1", 1.5) is False


# --- 真实只读：identify_display 对不存在显示器应返回 False ---


def test_identify_nonexistent():
    """不存在显示器的 identify 应返回 False。"""
    assert identify_display(r"\\.\NONEXISTENT_DISPLAY") is False


# --- 真实写操作（gamma_reset 保护 + xfail 机制） ---


def test_set_brightness_real(actual_display):
    """真实亮度设置。"""
    _reset_gamma_to_identity(actual_display.name)
    _write_op(set_brightness, actual_display.name, 1.0)
    _reset_gamma_to_identity(actual_display.name)


def test_set_gamma_real(actual_display):
    """真实伽马设置。"""
    _reset_gamma_to_identity(actual_display.name)
    _write_op(set_gamma, actual_display.name, 1.0, 1.0, 1.0)
    _reset_gamma_to_identity(actual_display.name)


def test_set_night_mode_light(actual_display):
    """真实夜览模式（light）。"""
    _reset_gamma_to_identity(actual_display.name)
    try:
        _write_op(set_night_mode, actual_display.name, 0.0)
    finally:
        _reset_gamma_to_identity(actual_display.name)


def test_set_night_mode_medium(actual_display):
    """真实夜览模式（medium）。"""
    _reset_gamma_to_identity(actual_display.name)
    try:
        _write_op(set_night_mode, actual_display.name, 0.5)
    finally:
        _reset_gamma_to_identity(actual_display.name)


def test_set_night_mode_heavy(actual_display):
    """真实夜览模式（heavy）。"""
    _reset_gamma_to_identity(actual_display.name)
    try:
        _write_op(set_night_mode, actual_display.name, 0.8)
    finally:
        _reset_gamma_to_identity(actual_display.name)


def test_identify_real(actual_display):
    """真实 identify（闪屏，使用实际伽马读写）。"""
    _write_op(identify_display, actual_display.name)


# --- Mock 错误分支测试 ---


def test_apply_gamma_create_dc_fails():
    """_CreateDCW 失败应返回 False。"""
    from unittest.mock import patch

    with patch("winrandr.features.gamma._CreateDCW", return_value=None):
        assert set_brightness(r"\\.\DISPLAY1", 1.0) is False


def test_apply_gamma_get_ramp_fails():
    """_GetDeviceGammaRamp 失败应返回 False。"""
    from unittest.mock import patch

    with patch("winrandr.features.gamma._GetDeviceGammaRamp", return_value=0):
        assert set_brightness(r"\\.\DISPLAY1", 1.0) is False


def test_apply_gamma_oserror():
    """_CreateDCW 抛出 OSError 应返回 False。"""
    from unittest.mock import patch

    with patch("winrandr.features.gamma._CreateDCW", side_effect=OSError("access denied")):
        assert set_brightness(r"\\.\DISPLAY1", 1.0) is False


def test_reset_gamma_create_dc_fails():
    """_reset_gamma_to_identity CreateDCW 返回 None 应返回 False。"""
    from unittest.mock import patch

    with patch("winrandr.features.gamma._CreateDCW", return_value=None):
        assert _reset_gamma_to_identity(r"\\.\DISPLAY1") is False


def test_reset_gamma_set_ramp_fails():
    """_reset_gamma_to_identity SetDeviceGammaRamp 失败应返回 False。"""
    from unittest.mock import patch

    with patch("winrandr.features.gamma._SetDeviceGammaRamp", return_value=0):
        assert _reset_gamma_to_identity(r"\\.\DISPLAY1") is False


def test_reset_gamma_oserror():
    """_reset_gamma_to_identity CreateDCW 抛出 OSError 应返回 False。"""
    from unittest.mock import patch

    with patch("winrandr.features.gamma._CreateDCW", side_effect=OSError("access denied")):
        assert _reset_gamma_to_identity(r"\\.\DISPLAY1") is False


def test_identify_display_create_dc_oserror():
    """identify_display CreateDCW 抛出 OSError 应返回 False。"""
    from unittest.mock import patch

    with patch("winrandr.features.gamma._CreateDCW", side_effect=OSError("access denied")):
        assert identify_display(r"\\.\DISPLAY1") is False


def test_identify_display_create_dc_none():
    """identify_display CreateDCW 返回 None 应返回 False。"""
    from unittest.mock import patch

    with patch("winrandr.features.gamma._CreateDCW", return_value=None):
        assert identify_display(r"\\.\DISPLAY1") is False


def test_identify_display_get_ramp_fails():
    """identify_display GetDeviceGammaRamp 失败应返回 False。"""
    from unittest.mock import patch

    fake_dc = 12345
    with patch("winrandr.features.gamma._CreateDCW", return_value=fake_dc):
        with patch("winrandr.features.gamma._GetDeviceGammaRamp", return_value=0):
            assert identify_display(r"\\.\DISPLAY1") is False


def test_identify_display_flash_write_fails():
    """identify_display 闪屏中 _SetDeviceGammaRamp 写失败应中断并返回 False。"""
    from unittest.mock import patch

    fake_dc = 12345
    with patch("winrandr.features.gamma._CreateDCW", return_value=fake_dc):
        with patch("winrandr.features.gamma._GetDeviceGammaRamp", return_value=1):
            with patch("winrandr.features.gamma._SetDeviceGammaRamp", return_value=0) as mock_set:
                with patch("winrandr.features.gamma.time.sleep"):
                    result = identify_display(r"\\.\DISPLAY1", duration=0.1)
    assert result is False
    # 第一次 flash 就失败，只调了 1 次
    assert mock_set.call_count >= 1


def test_identify_display_blank_write_fails():
    """identify_display flash 成功但 blank 写失败应返回 False。"""
    from unittest.mock import patch

    fake_dc = 12345
    call_count = 0

    def _side(*_a):
        nonlocal call_count
        call_count += 1
        # 第 1 次（flash）成功，第 2 次（blank）失败
        return 1 if call_count == 1 else 0

    with patch("winrandr.features.gamma._CreateDCW", return_value=fake_dc):
        with patch("winrandr.features.gamma._GetDeviceGammaRamp", return_value=1):
            with patch("winrandr.features.gamma._SetDeviceGammaRamp", side_effect=_side):
                with patch("winrandr.features.gamma.time.sleep"):
                    result = identify_display(r"\\.\DISPLAY1", duration=0.1)
    assert result is False


def test_set_gamma_failure():
    """set_gamma 在 _apply_gamma 失败时应返回 False。"""
    from unittest.mock import patch

    from winrandr.features.gamma import set_gamma

    with patch("winrandr.features.gamma._CreateDCW", return_value=None):
        assert set_gamma(r"\\.\DISPLAY1", 1.0, 1.0, 1.0) is False
