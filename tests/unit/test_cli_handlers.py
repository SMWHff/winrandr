"""Tests for CLI handler functions with dry-run mode."""

from argparse import Namespace
from unittest.mock import patch

import pytest

from winrandr.cli.handlers import (
    _handle_auto,
    _handle_brightness,
    _handle_gamma,
    _handle_mode,
    _handle_off,
    _handle_pos,
    _handle_preferred,
    _handle_primary,
    _handle_reflect,
    _handle_relative,
    _handle_rotate,
    _msg,
    _setup_logging,
)

DN = r"\\.\DISPLAY1"


def _ns(**kwargs) -> Namespace:
    defaults = dict(dry_run=True, output="DISPLAY1",
                    mode=None, pos=None, rate=None, rotate=None,
                    primary=None, preferred=None, off=None,
                    brightness=None, reflect=None, gamma=None,
                    identify=False,
                    left_of=None, right_of=None, above=None, below=None, same_as=None)
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


# --- _msg (dry-run helper) ---

def test_msg_normal(capsys):
    _msg(_ns(dry_run=False), "测试消息")
    out, _ = capsys.readouterr()
    assert out == "测试消息\n"

def test_msg_dry_run(capsys):
    _msg(_ns(dry_run=True), "测试消息")
    out, _ = capsys.readouterr()
    assert out == "(Dry-Run) 测试消息\n"


# --- 非 dry-run 模式：验证 API 实际被调用 ---

def test_mode_non_dry_run():
    with patch("winrandr.cli.handlers.set_resolution", return_value=True) as mock_fn:
        _handle_mode(_ns(mode="1920x1080", dry_run=False), DN)
        assert mock_fn.called is True

def test_pos_non_dry_run():
    with patch("winrandr.cli.handlers.set_position", return_value=True) as mock_fn:
        _handle_pos(_ns(pos="0x0", dry_run=False), DN)
        assert mock_fn.called is True

def test_rotate_non_dry_run():
    with patch("winrandr.cli.handlers.set_rotation", return_value=True) as mock_fn:
        _handle_rotate(_ns(rotate="normal", dry_run=False), DN)
        assert mock_fn.called is True

def test_primary_non_dry_run():
    with patch("winrandr.cli.handlers.set_primary", return_value=True) as mock_fn:
        _handle_primary(_ns(primary=True, dry_run=False), DN)
        assert mock_fn.called is True

def test_preferred_non_dry_run():
    with patch("winrandr.cli.handlers.set_preferred_resolution", return_value=True) as mock_fn:
        _handle_preferred(_ns(preferred=True, dry_run=False), DN)
        assert mock_fn.called is True

def test_off_non_dry_run():
    with patch("winrandr.cli.handlers.set_off", return_value=True) as mock_fn:
        _handle_off(_ns(off=True, dry_run=False), DN)
        assert mock_fn.called is True

def test_brightness_non_dry_run():
    with patch("winrandr.cli.handlers.set_brightness", return_value=True) as mock_fn:
        _handle_brightness(_ns(brightness=1.0, dry_run=False), DN)
        assert mock_fn.called is True

def test_gamma_non_dry_run():
    with patch("winrandr.cli.handlers.set_gamma", return_value=True) as mock_fn:
        _handle_gamma(_ns(gamma="1.0:0.9:0.8", dry_run=False), DN)
        assert mock_fn.called is True

def test_reflect_non_dry_run():
    with patch("winrandr.cli.handlers.set_reflect", return_value=True) as mock_fn:
        _handle_reflect(_ns(reflect="xy", dry_run=False), DN)
        assert mock_fn.called is True

def test_auto_non_dry_run():
    with patch("winrandr.cli.handlers.set_auto", return_value=True) as mock_fn:
        _handle_auto(_ns(auto=True, dry_run=False), DN)
        assert mock_fn.called is True


def test_reflect_api_failure():
    """reflect=xy 但 set_reflect 失败时应退出。"""
    with patch("winrandr.cli.handlers.set_reflect", return_value=False):
        with pytest.raises(SystemExit):
            _handle_reflect(_ns(reflect="xy", dry_run=False), DN)


def test_relative_api_failure():
    """相对定位 API 失败时应退出。"""
    with patch("winrandr.cli.handlers.set_position_relative", return_value=False):
        with pytest.raises(SystemExit):
            _handle_relative(_ns(left_of="DISPLAY2", dry_run=False), DN)


# --- API 调用失败路径（_fail → SystemExit）---

def test_mode_api_failure():
    with patch("winrandr.cli.handlers.set_resolution", return_value=False):
        with pytest.raises(SystemExit):
            _handle_mode(_ns(mode="1920x1080", dry_run=False), DN)

def test_pos_api_failure():
    with patch("winrandr.cli.handlers.set_position", return_value=False):
        with pytest.raises(SystemExit):
            _handle_pos(_ns(pos="0x0", dry_run=False), DN)

def test_rotate_api_failure():
    with patch("winrandr.cli.handlers.set_rotation", return_value=False):
        with pytest.raises(SystemExit):
            _handle_rotate(_ns(rotate="normal", dry_run=False), DN)

def test_primary_api_failure():
    with patch("winrandr.cli.handlers.set_primary", return_value=False):
        with pytest.raises(SystemExit):
            _handle_primary(_ns(primary=True, dry_run=False), DN)

def test_preferred_api_failure():
    with patch("winrandr.cli.handlers.set_preferred_resolution", return_value=False):
        with pytest.raises(SystemExit):
            _handle_preferred(_ns(preferred=True, dry_run=False), DN)

def test_off_api_failure():
    with patch("winrandr.cli.handlers.set_off", return_value=False):
        with pytest.raises(SystemExit):
            _handle_off(_ns(off=True, dry_run=False), DN)

def test_brightness_api_failure():
    with patch("winrandr.cli.handlers.set_brightness", return_value=False):
        with pytest.raises(SystemExit):
            _handle_brightness(_ns(brightness=1.0, dry_run=False), DN)

def test_gamma_api_failure():
    with patch("winrandr.cli.handlers.set_gamma", return_value=False):
        with pytest.raises(SystemExit):
            _handle_gamma(_ns(gamma="1.0:0.9:0.8", dry_run=False), DN)

def test_auto_api_failure():
    with patch("winrandr.cli.handlers.set_auto", return_value=False):
        with pytest.raises(SystemExit):
            _handle_auto(_ns(auto=True, dry_run=False), DN)


def test_setup_logging_first_call():
    """首次调用 _setup_logging 应创建文件和控制台两个处理器。"""
    import logging as _logging
    root = _logging.getLogger()
    old_handlers = root.handlers[:]
    root.handlers.clear()
    try:
        _setup_logging()
        assert len(root.handlers) == 2
    finally:
        for h in root.handlers:
            h.close()
        root.handlers.clear()
        root.handlers.extend(old_handlers)
