"""CLI handler 非 dry-run 与 API 失败路径测试。"""

from argparse import Namespace
from unittest.mock import patch

import pytest

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


# --- reflect / relative API 失败 ---


def test_reflect_api_failure():
    with patch("winrandr.cli.handlers.set_reflect", return_value=False):
        with pytest.raises(SystemExit):
            _handle_reflect(_ns(reflect="xy", dry_run=False), DN)


def test_relative_api_failure():
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


# --- _handle_night_mode (non-dry-run & failure) ---


def test_night_mode_non_dry_run_light():
    """Non dry-run with preset light: calls set_night_mode with strength=0.2."""
    with patch("winrandr.cli.handlers.set_night_mode", return_value=True) as mock_fn:
        _handle_night_mode(_ns(night_mode="light", dry_run=False), DN)
        mock_fn.assert_called_once_with(DN, 0.2)


def test_night_mode_non_dry_run_medium():
    """Non dry-run with preset medium: calls set_night_mode with strength=0.5."""
    with patch("winrandr.cli.handlers.set_night_mode", return_value=True) as mock_fn:
        _handle_night_mode(_ns(night_mode="medium", dry_run=False), DN)
        mock_fn.assert_called_once_with(DN, 0.5)


def test_night_mode_non_dry_run_heavy():
    """Non dry-run with preset heavy: calls set_night_mode with strength=0.8."""
    with patch("winrandr.cli.handlers.set_night_mode", return_value=True) as mock_fn:
        _handle_night_mode(_ns(night_mode="heavy", dry_run=False), DN)
        mock_fn.assert_called_once_with(DN, 0.8)


def test_night_mode_non_dry_run_numeric():
    """Non dry-run with numeric string: calls set_night_mode with parsed float."""
    with patch("winrandr.cli.handlers.set_night_mode", return_value=True) as mock_fn:
        _handle_night_mode(_ns(night_mode="0.3", dry_run=False), DN)
        mock_fn.assert_called_once_with(DN, 0.3)


def test_night_mode_api_failure():
    """API returns False -> SystemExit."""
    with patch("winrandr.cli.handlers.set_night_mode", return_value=False):
        with pytest.raises(SystemExit):
            _handle_night_mode(_ns(night_mode="light", dry_run=False), DN)
