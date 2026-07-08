"""Tests for main() CLI entry point with mocked Win32 API."""

from unittest.mock import patch

import pytest

from winrandr.cli import main as cli_main
from winrandr.models import DisplayInfo, DisplayMode


def _fake_display(name="DISPLAY1", connected=True, **kw):
    defaults = dict(name=rf"\\.\{name}", friendly_name="Fake Monitor",
                    connected=connected, width=1920, height=1080,
                    refresh_rate=60.0, position_x=0, position_y=0,
                    is_primary=True, rotation=0, width_mm=527, height_mm=296,
                    modes=[DisplayMode(1920, 1080, 60.0, True, True)])
    defaults.update(kw)
    return DisplayInfo(**defaults)

def test_main_query_show_displays():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("sys.argv", ["winrandr"]):
            cli_main()

def test_main_current():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("sys.argv", ["winrandr", "--current"]):
            cli_main()

def test_main_dry_run_set_resolution():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.handlers.set_resolution", return_value=True) as mock_set:
            with patch("sys.argv", ["winrandr", "--output", "DISPLAY1", "--mode", "1920x1080", "--dry-run"]):
                cli_main()
            assert mock_set.called is False

def test_main_dryrun_alias():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.handlers.set_resolution", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "-m", "1920x1080", "--dryrun"]):
                cli_main()
            assert mock_fn.called is False

def test_main_dry_run_set_position():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.handlers.set_position", return_value=True) as mock_set:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "-p", "1920x0", "--dry-run"]):
                cli_main()
            assert mock_set.called is False

def test_main_invalid_output():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display("DISPLAY1")]):
        with patch("winrandr.cli.list_providers", return_value=[]):
            with pytest.raises(SystemExit):
                with patch("sys.argv", ["winrandr", "--output", "DISPLAY99", "--mode", "1920x1080"]):
                    cli_main()

def test_main_noprimary_standalone():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.set_noprimary", return_value=True) as mock_set:
            with patch("sys.argv", ["winrandr", "--noprimary", "--dry-run"]):
                cli_main()
            assert mock_set.called is False

def test_main_noprimary_with_mode():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.set_noprimary", return_value=True):
            with patch("winrandr.cli.handlers.set_resolution", return_value=True) as mock_set:
                with patch("sys.argv", ["winrandr", "--noprimary", "-o", "DISPLAY1", "-m", "1920x1080", "--dry-run"]):
                    cli_main()
                assert mock_set.called is False

def test_main_query_with_output():
    d2 = _fake_display("DISPLAY2", position_x=1920)
    with patch("winrandr.cli.list_displays", return_value=[_fake_display(), d2]):
        with patch("sys.argv", ["winrandr", "--output", "DISPLAY2"]):
            cli_main()

def test_main_query_json():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("sys.argv", ["winrandr", "--json"]):
            cli_main()

def test_main_query_prop():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.get_display_props", return_value={"device_id": "TEST"}):
            with patch("sys.argv", ["winrandr", "--prop"]):
                cli_main()

def test_main_listmodes():
    dm = DisplayMode(1920, 1080, 60.0, True, True)
    disp = _fake_display(modes=[dm])
    with patch("winrandr.cli.handlers.list_displays", return_value=[disp]):
        with patch("sys.argv", ["winrandr", "--listmodes"]):
            cli_main()

def test_main_listmodes_json():
    dm = DisplayMode(1920, 1080, 60.0, True, True)
    disp = _fake_display(modes=[dm])
    with patch("winrandr.cli.handlers.list_displays", return_value=[disp]):
        with patch("sys.argv", ["winrandr", "--listmodes", "--json"]):
            cli_main()

def test_main_listmodes_with_output():
    dm = DisplayMode(1920, 1080, 60.0, True, True)
    disp = _fake_display(modes=[dm])
    with patch("winrandr.cli.handlers.list_displays", return_value=[disp]):
        with patch("sys.argv", ["winrandr", "--listmodes", "--output", "DISPLAY1"]):
            cli_main()

def test_main_listmodes_invalid_output():
    dm = DisplayMode(1920, 1080, 60.0, True, True)
    disp = _fake_display(modes=[dm])
    with patch("winrandr.cli.handlers.list_displays", return_value=[disp]):
        with patch("winrandr.cli.handlers.list_providers", return_value=[]):
            with pytest.raises(SystemExit):
                with patch("sys.argv", ["winrandr", "--listmodes", "--output", "DISPLAY99"]):
                    cli_main()

def test_main_query_no_displays():
    with patch("winrandr.cli.list_displays", return_value=[]):
        with pytest.raises(SystemExit):
            with patch("sys.argv", ["winrandr"]):
                cli_main()

def test_main_dry_run_auto():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.handlers.set_auto", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "--auto", "--dry-run"]):
                cli_main()
            assert mock_fn.called is False

def test_main_dry_run_rotate():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.handlers.set_rotation", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "--rotate", "inverted", "--dry-run"]):
                cli_main()
            assert mock_fn.called is False

def test_main_dry_run_primary():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.handlers.set_primary", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "--primary", "--dry-run"]):
                cli_main()
            assert mock_fn.called is False

def test_main_dry_run_preferred():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.handlers.set_preferred_resolution", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "--preferred", "--dry-run"]):
                cli_main()
            assert mock_fn.called is False

def test_main_dry_run_off():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.handlers.set_off", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "--off", "--dry-run"]):
                cli_main()
            assert mock_fn.called is False

def test_main_dry_run_brightness():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.handlers.set_brightness", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "--brightness", "0.8", "--dry-run"]):
                cli_main()
            assert mock_fn.called is False

def test_main_dry_run_gamma():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.handlers.set_gamma", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "--gamma", "1.0:0.9:0.8", "--dry-run"]):
                cli_main()
            assert mock_fn.called is False

def test_main_dry_run_reflect_xy():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.handlers.set_reflect", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "--reflect", "xy", "--dry-run"]):
                cli_main()
            assert mock_fn.called is False

def test_main_dry_run_relative():
    d2 = _fake_display("DISPLAY2", position_x=1920)
    with patch("winrandr.cli.list_displays", return_value=[_fake_display(), d2]):
        with patch("winrandr.cli.handlers.set_position_relative", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "--left-of", "DISPLAY2", "--dry-run"]):
                cli_main()
            assert mock_fn.called is False

def test_main_dry_run_mode_with_rate():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.handlers.set_resolution", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "-m", "1920x1080", "-r", "60", "--dry-run"]):
                cli_main()
            assert mock_fn.called is False

def test_main_set_resolution_called():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.handlers.set_resolution", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "-m", "1920x1080"]):
                cli_main()
            assert mock_fn.called is True

def test_main_set_position_called():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.handlers.set_position", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "-p", "1920x0"]):
                cli_main()
            assert mock_fn.called is True

def test_main_set_primary_called():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.handlers.set_primary", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "--primary"]):
                cli_main()
            assert mock_fn.called is True

def test_main_set_off_called():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.handlers.set_off", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "--off"]):
                cli_main()
            assert mock_fn.called is True

def test_main_set_brightness_called():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.handlers.set_brightness", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "--brightness", "0.8"]):
                cli_main()
            assert mock_fn.called is True

def test_main_query_prop_json():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.get_display_props", return_value={"device_id": "TEST"}):
            with patch("sys.argv", ["winrandr", "--prop", "--json"]):
                cli_main()

def test_main_listmonitors_json():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("sys.argv", ["winrandr", "--listmonitors", "--json"]):
            cli_main()

def test_main_listmodes_no_displays():
    with patch("winrandr.cli.handlers.list_displays", return_value=[]):
        with patch("sys.argv", ["winrandr", "--listmodes"]):
            cli_main()


def test_main_noprimary_failure():
    """set_noprimary 失败时应退出。"""
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.set_noprimary", return_value=False):
            with patch("sys.argv", ["winrandr", "--noprimary"]):
                with pytest.raises(SystemExit):
                    cli_main()


def test_main_query_output_not_found():
    """查询模式中指定不存在的 --output 应报错退出。"""
    with patch("winrandr.cli.list_displays", return_value=[_fake_display("DISPLAY1")]):
        with patch("winrandr.cli.list_providers", return_value=[]):
            with pytest.raises(SystemExit):
                with patch("sys.argv", ["winrandr", "--output", "DISPLAY99"]):
                    cli_main()

def test_main_missing_output_for_modop():
    """修改操作缺少 --output 应报错退出。"""
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with pytest.raises(SystemExit):
            with patch("sys.argv", ["winrandr", "--mode", "1920x1080"]):
                cli_main()
