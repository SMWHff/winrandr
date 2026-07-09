"""Tests for main() CLI entry point — global brightness/gamma."""

from unittest.mock import patch

import pytest

from tests.conftest import _fake_display
from winrandr.cli import main as cli_main


def test_main_brightness_global():
    """--brightness 不带 --output 应应用到所有已连接显示器。"""
    d1 = _fake_display("DISPLAY1", position_x=0)
    d2 = _fake_display("DISPLAY2", position_x=1920)
    with patch("winrandr.cli.list_displays", return_value=[d1, d2]):
        with patch("winrandr.cli.handlers.set_brightness", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "--brightness", "0.8"]):
                cli_main()
            assert mock_fn.call_count == 2


def test_main_brightness_global_dry_run():
    """--brightness --dry-run 不带 --output 应模拟不实际调用。"""
    d1 = _fake_display("DISPLAY1", position_x=0)
    with patch("winrandr.cli.list_displays", return_value=[d1]):
        with patch("winrandr.cli.handlers.set_brightness", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "--brightness", "0.8", "--dry-run"]):
                cli_main()
            assert mock_fn.called is False


def test_main_brightness_global_no_displays():
    """--brightness 不带 --output 且无显示器时应报错退出。"""
    with patch("winrandr.cli.list_displays", return_value=[]):
        with pytest.raises(SystemExit):
            with patch("sys.argv", ["winrandr", "--brightness", "0.8"]):
                cli_main()


def test_main_gamma_global():
    """--gamma 不带 --output 应应用到所有已连接显示器。"""
    d1 = _fake_display("DISPLAY1")
    d2 = _fake_display("DISPLAY2")
    with patch("winrandr.cli.list_displays", return_value=[d1, d2]):
        with patch("winrandr.cli.handlers.set_gamma", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "--gamma", "1.0:0.9:0.8"]):
                cli_main()
            assert mock_fn.call_count == 2


def test_main_night_mode_global():
    """--night-mode 不带 --output 应应用到所有已连接显示器。"""
    d1 = _fake_display("DISPLAY1")
    d2 = _fake_display("DISPLAY2")
    with patch("winrandr.cli.list_displays", return_value=[d1, d2]):
        with patch("winrandr.cli.handlers.set_night_mode", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "--night-mode", "0.3"]):
                cli_main()
            assert mock_fn.call_count == 2


def test_main_brightness_with_output_still_works():
    """--brightness 带 --output 仍只应用到指定显示器。"""
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.handlers.set_brightness", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "--brightness", "0.8"]):
                cli_main()
            assert mock_fn.called is True


def test_main_global_op_requires_output_for_other_ops():
    """全局操作中混用了需要 --output 的操作时应报错。"""
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with pytest.raises(SystemExit):
            with patch("sys.argv", ["winrandr", "--brightness", "0.8", "--mode", "1920x1080"]):
                cli_main()
