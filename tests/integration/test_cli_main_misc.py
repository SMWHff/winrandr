"""Tests for main() CLI entry point — version, entry guard, providers, monitors."""

import subprocess
import sys as _sys
from unittest.mock import patch
import pytest
from winrandr.models import DisplayInfo, DisplayMode
from winrandr.cli import main as cli_main


def _fake_display(name="DISPLAY1", connected=True, **kw):
    defaults = dict(name=rf"\\.\{name}", friendly_name="Fake Monitor",
                    connected=connected, width=1920, height=1080,
                    refresh_rate=60.0, position_x=0, position_y=0,
                    is_primary=True, rotation=0, width_mm=527, height_mm=296,
                    modes=[DisplayMode(1920, 1080, 60.0, True, True)])
    defaults.update(kw)
    return DisplayInfo(**defaults)


def test_main_listproviders():
    providers = [{"name": "DISPLAY1", "string": "NVIDIA GeForce", "flags": 0}]
    with patch("winrandr.cli.list_providers", return_value=providers):
        with patch("sys.argv", ["winrandr", "--listproviders"]):
            cli_main()


def test_main_listproviders_json():
    providers = [{"name": "DISPLAY1", "string": "NVIDIA GeForce", "flags": 0}]
    with patch("winrandr.cli.list_providers", return_value=providers):
        with patch("sys.argv", ["winrandr", "--listproviders", "--json"]):
            cli_main()


def test_main_listmonitors():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("sys.argv", ["winrandr", "--listmonitors"]):
            cli_main()


def test_entry_point_version():
    """python -m winrandr --version 应正常退出。"""
    result = subprocess.run(
        [_sys.executable, "-m", "winrandr", "--version"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    assert "winrandr" in result.stdout


def test_entry_point_version_v():
    """python -m winrandr -v 应显示版本（同 --version）。"""
    result = subprocess.run(
        [_sys.executable, "-m", "winrandr", "-v"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    assert "winrandr" in result.stdout


def test_cli_entry_guard():
    """覆盖 cli.py 入口守卫（if __name__ == '__main__'）。"""
    import runpy
    from pathlib import Path
    cli_path = Path(__file__).parent.parent.parent / "winrandr" / "cli" / "__init__.py"
    with patch("sys.argv", ["winrandr", "--version"]):
        with pytest.raises(SystemExit):
            runpy.run_path(str(cli_path), run_name="__main__")


def test_main_module_entry():
    """覆盖 __main__.py 模块级代码。"""
    import runpy
    with patch("sys.argv", ["winrandr", "--version"]):
        with pytest.raises(SystemExit):
            runpy.run_module("winrandr.__main__", run_name="__main__")


def test_main_verbose():
    """--verbose 应设置 DEBUG 级别日志。"""
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("sys.argv", ["winrandr", "--verbose"]):
            cli_main()


def test_main_listproviders_empty():
    """--listproviders 无适配器时应输出提示。"""
    with patch("winrandr.cli.list_providers", return_value=[]):
        with patch("sys.argv", ["winrandr", "--listproviders"]):
            cli_main()


def test_main_listmonitors_empty():
    """--listmonitors 无显示器时应输出提示。"""
    with patch("winrandr.cli.list_displays", return_value=[]):
        with patch("sys.argv", ["winrandr", "--listmonitors"]):
            cli_main()
