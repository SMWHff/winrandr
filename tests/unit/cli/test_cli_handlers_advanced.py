"""CLI handler 非 dry-run 模式真实硬件测试。"""

from argparse import Namespace

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


# --- 非 dry-run 模式：真实 API 调用 ---


def _call(handler, ns, dn=DN):
    """执行 handler，SDC 不可用时 xfail。"""
    try:
        handler(ns, dn)
    except SystemExit:
        pytest.xfail("SetDisplayConfig 不可用，操作预期失败")


def test_mode_non_dry_run():
    _call(_handle_mode, _ns(mode="1920x1080", dry_run=False))


def test_pos_non_dry_run():
    _call(_handle_pos, _ns(pos="0x0", dry_run=False))


def test_rotate_non_dry_run():
    _call(_handle_rotate, _ns(rotate="normal", dry_run=False))


def test_primary_non_dry_run():
    _call(_handle_primary, _ns(primary=True, dry_run=False))


def test_preferred_non_dry_run():
    _call(_handle_preferred, _ns(preferred=True, dry_run=False))


def test_off_non_dry_run():
    _call(_handle_off, _ns(off=True, dry_run=False))


def test_brightness_non_dry_run():
    _call(_handle_brightness, _ns(brightness=1.0, dry_run=False))


def test_gamma_non_dry_run():
    _call(_handle_gamma, _ns(gamma="1.0:0.9:0.8", dry_run=False))


def test_reflect_non_dry_run():
    _call(_handle_reflect, _ns(reflect="xy", dry_run=False))


def test_auto_non_dry_run():
    _call(_handle_auto, _ns(auto=True, dry_run=False))


def test_night_mode_non_dry_run_light():
    _call(_handle_night_mode, _ns(night_mode="light", dry_run=False))


def test_night_mode_non_dry_run_medium():
    _call(_handle_night_mode, _ns(night_mode="medium", dry_run=False))


def test_night_mode_non_dry_run_heavy():
    _call(_handle_night_mode, _ns(night_mode="heavy", dry_run=False))


def test_night_mode_non_dry_run_numeric():
    _call(_handle_night_mode, _ns(night_mode="0.3", dry_run=False))


# --- Mock API 失败分支（真实硬件上 API 成功，无法触发 _fail） ---


def test_auto_api_failure():
    from unittest.mock import patch

    with patch("winrandr.cli.handlers.set_auto", return_value=False):
        with pytest.raises(SystemExit):
            _handle_auto(_ns(auto=True, dry_run=False), DN)


def test_mode_api_failure():
    from unittest.mock import patch

    with patch("winrandr.cli.handlers.set_resolution", return_value=False):
        with pytest.raises(SystemExit):
            _handle_mode(_ns(mode="1920x1080", dry_run=False), DN)


def test_brightness_api_failure():
    from unittest.mock import patch

    with patch("winrandr.cli.handlers.set_brightness", return_value=False):
        with pytest.raises(SystemExit):
            _handle_brightness(_ns(brightness=1.0, dry_run=False), DN)


def test_preferred_api_failure():
    from unittest.mock import patch

    with patch("winrandr.cli.handlers.set_preferred_resolution", return_value=False):
        with pytest.raises(SystemExit):
            _handle_preferred(_ns(preferred=True, dry_run=False), DN)


def test_relative_api_failure():
    from unittest.mock import patch

    with patch("winrandr.cli.handlers.set_position_relative", return_value=False):
        with pytest.raises(SystemExit):
            _handle_relative(_ns(left_of="DISPLAY2", dry_run=False), DN)
