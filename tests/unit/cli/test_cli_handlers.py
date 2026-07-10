"""Tests for CLI handler functions with dry-run mode."""

from argparse import Namespace

import pytest

from winrandr.cli.common import _msg
from winrandr.cli.handlers import (
    _handle_auto,
    _handle_brightness,
    _handle_gamma,
    _handle_mode,
    _handle_night_mode,
    _handle_off,
    _handle_pos,
    _handle_preferred,
    _handle_primary,
    _handle_reflect,
    _handle_relative,
    _handle_rotate,
)

DN = r"\\.\DISPLAY1"


def _ns(**kwargs) -> Namespace:
    defaults = dict(
        dry_run=True,
        output="DISPLAY1",
        mode=None,
        pos=None,
        rate=None,
        rotate=None,
        primary=None,
        preferred=None,
        off=None,
        brightness=None,
        night_mode=None,
        reflect=None,
        gamma=None,
        identify=False,
        left_of=None,
        right_of=None,
        above=None,
        below=None,
        same_as=None,
    )
    defaults.update(kwargs)
    return Namespace(**defaults)


# --- _handle_mode ---


def test_mode_valid():
    _handle_mode(_ns(mode="1920x1080"), DN)


def test_mode_valid_with_rate():
    _handle_mode(_ns(mode="1920x1080", rate=60), DN)


def test_mode_no_x():
    with pytest.raises(SystemExit):
        _handle_mode(_ns(mode="invalid"), DN)


def test_mode_bad_value():
    with pytest.raises(SystemExit):
        _handle_mode(_ns(mode="abcxdef"), DN)


# --- _handle_pos ---


def test_pos_valid():
    _handle_pos(_ns(pos="0x0"), DN)


def test_pos_plus_prefix():
    _handle_pos(_ns(pos="+1920x+0"), DN)


def test_pos_xrandr_plus_format():
    """xrandr style +1920+0 should be accepted and converted."""
    _handle_pos(_ns(pos="+1920+0"), DN)


def test_pos_negative_y():
    _handle_pos(_ns(pos="1920x-1080"), DN)


def test_pos_no_x():
    with pytest.raises(SystemExit):
        _handle_pos(_ns(pos="invalid"), DN)


def test_pos_xrandr_bad_digits():
    """xrandr 风格 +X+Y 中 X 或 Y 为非数字时应报错（覆盖 126->128 分支）。"""
    with pytest.raises(SystemExit):
        _handle_pos(_ns(pos="+abc+def"), DN)


def test_pos_bad_x():
    with pytest.raises(SystemExit):
        _handle_pos(_ns(pos="abcxdef"), DN)


def test_pos_extra_parts():
    with pytest.raises(SystemExit):
        _handle_pos(_ns(pos="1920x1080x32"), DN)


# --- _handle_gamma ---


def test_gamma_valid():
    _handle_gamma(_ns(gamma="1.0:0.9:0.8"), DN)


def test_gamma_single_value():
    _handle_gamma(_ns(gamma="0.8"), DN)


def test_gamma_bad_format():
    with pytest.raises(SystemExit):
        _handle_gamma(_ns(gamma="abc"), DN)


def test_gamma_wrong_count():
    with pytest.raises(SystemExit):
        _handle_gamma(_ns(gamma="1.0:0.9"), DN)


def test_gamma_set_fails_mocked():
    """_handle_gamma 在 set_gamma 失败时应报错退出。"""
    from unittest.mock import patch

    with patch("winrandr.cli.handlers.set_gamma", return_value=False):
        with pytest.raises(SystemExit):
            _handle_gamma(_ns(gamma="1.0:0.9:0.8", dry_run=False), DN)


# --- _handle_brightness ---


def test_brightness_valid():
    _handle_brightness(_ns(brightness=1.0), DN)


def test_brightness_low():
    _handle_brightness(_ns(brightness=0.05), DN)


# --- _handle_reflect ---


def test_reflect_xy():
    _handle_reflect(_ns(reflect="xy"), DN)


def test_reflect_x_unsupported():
    with pytest.raises(SystemExit):
        _handle_reflect(_ns(reflect="x"), DN)


# --- _handle_relative ---


def test_relative_without_ref():
    """When no relative arg is set, handler should return silently."""
    _handle_relative(_ns(), DN)


def test_relative_with_ref_dry_run():
    """dry-run 模式下带相对定位参数应打印消息不调用 API。"""
    _handle_relative(_ns(left_of="DISPLAY2", dry_run=True), DN)


# --- _handle_auto ---


def test_auto():
    _handle_auto(_ns(auto=True), DN)


# --- _handle_rotate ---


def test_rotate_normal():
    _handle_rotate(_ns(rotate="normal"), DN)


# --- _handle_primary ---


def test_primary():
    _handle_primary(_ns(primary=True), DN)


# --- _handle_preferred ---


def test_preferred():
    _handle_preferred(_ns(preferred=True), DN)


# --- _handle_off ---


def test_off():
    _handle_off(_ns(off=True), DN)


def test_off_dry_run():
    """dry-run 下 _handle_off 不应调用 set_off。"""
    _handle_off(_ns(off=True, dry_run=True), DN)


# --- _msg (dry-run helper) ---


def test_msg_normal(capsys):
    _msg(_ns(dry_run=False), "测试消息")
    out, _ = capsys.readouterr()
    assert out == "测试消息\n"


def test_msg_dry_run(capsys):
    _msg(_ns(dry_run=True), "测试消息")
    out, _ = capsys.readouterr()
    assert out == "(Dry-Run) 测试消息\n"


# --- _handle_night_mode (dry-run) ---


def test_night_mode_light():
    """Preset light should work in dry-run mode."""
    _handle_night_mode(_ns(night_mode="light"), DN)


def test_night_mode_medium():
    """Preset medium should work in dry-run mode."""
    _handle_night_mode(_ns(night_mode="medium"), DN)


def test_night_mode_heavy():
    """Preset heavy should work in dry-run mode."""
    _handle_night_mode(_ns(night_mode="heavy"), DN)


def test_night_mode_numeric():
    """Numeric string 0.3 should work in dry-run mode."""
    _handle_night_mode(_ns(night_mode="0.3"), DN)


def test_night_mode_invalid():
    """Invalid string should raise SystemExit."""
    with pytest.raises(SystemExit):
        _handle_night_mode(_ns(night_mode="invalid"), DN)


def test_night_mode_out_of_range():
    """Out of range numeric string should raise SystemExit."""
    with pytest.raises(SystemExit):
        _handle_night_mode(_ns(night_mode="1.5"), DN)


def test_night_mode_dry_run(capsys):
    """Dry-run mode should print Dry-Run message and NOT call set_night_mode."""
    _handle_night_mode(_ns(night_mode="medium"), DN)
    out, _ = capsys.readouterr()
    assert "Dry-Run" in out
