"""Tests for main() CLI entry point with mocked Win32 API."""

import subprocess
import sys as _sys
import pytest
from unittest.mock import patch
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
        with patch("winrandr.cli_handlers.set_resolution", return_value=True) as mock_set:
            with patch("sys.argv", ["winrandr", "--output", "DISPLAY1", "--mode", "1920x1080", "--dry-run"]):
                cli_main()
            assert mock_set.called is False

def test_main_dryrun_alias():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli_handlers.set_resolution", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "-m", "1920x1080", "--dryrun"]):
                cli_main()
            assert mock_fn.called is False

def test_main_dry_run_set_position():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli_handlers.set_position", return_value=True) as mock_set:
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
            with patch("winrandr.cli_handlers.set_resolution", return_value=True) as mock_set:
                with patch("sys.argv", ["winrandr", "--noprimary", "-o", "DISPLAY1", "-m", "1920x1080", "--dry-run"]):
                    cli_main()
                assert mock_set.called is False

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
    with patch("winrandr.cli_handlers.list_displays", return_value=[disp]):
        with patch("sys.argv", ["winrandr", "--listmodes"]):
            cli_main()

def test_main_listmodes_json():
    dm = DisplayMode(1920, 1080, 60.0, True, True)
    disp = _fake_display(modes=[dm])
    with patch("winrandr.cli_handlers.list_displays", return_value=[disp]):
        with patch("sys.argv", ["winrandr", "--listmodes", "--json"]):
            cli_main()

def test_main_listmodes_with_output():
    dm = DisplayMode(1920, 1080, 60.0, True, True)
    disp = _fake_display(modes=[dm])
    with patch("winrandr.cli_handlers.list_displays", return_value=[disp]):
        with patch("sys.argv", ["winrandr", "--listmodes", "--output", "DISPLAY1"]):
            cli_main()

def test_main_listmodes_invalid_output():
    dm = DisplayMode(1920, 1080, 60.0, True, True)
    disp = _fake_display(modes=[dm])
    with patch("winrandr.cli_handlers.list_displays", return_value=[disp]):
        with patch("winrandr.cli_handlers.list_providers", return_value=[]):
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
        with patch("winrandr.cli_handlers.set_auto", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "--auto", "--dry-run"]):
                cli_main()
            assert mock_fn.called is False

def test_main_dry_run_rotate():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli_handlers.set_rotation", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "--rotate", "inverted", "--dry-run"]):
                cli_main()
            assert mock_fn.called is False

def test_main_dry_run_primary():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli_handlers.set_primary", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "--primary", "--dry-run"]):
                cli_main()
            assert mock_fn.called is False

def test_main_dry_run_preferred():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli_handlers.set_preferred_resolution", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "--preferred", "--dry-run"]):
                cli_main()
            assert mock_fn.called is False

def test_main_dry_run_off():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli_handlers.set_off", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "--off", "--dry-run"]):
                cli_main()
            assert mock_fn.called is False

def test_main_dry_run_brightness():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli_handlers.set_brightness", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "--brightness", "0.8", "--dry-run"]):
                cli_main()
            assert mock_fn.called is False

def test_main_dry_run_gamma():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli_handlers.set_gamma", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "--gamma", "1.0:0.9:0.8", "--dry-run"]):
                cli_main()
            assert mock_fn.called is False

def test_main_dry_run_reflect_xy():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli_handlers.set_reflect", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "--reflect", "xy", "--dry-run"]):
                cli_main()
            assert mock_fn.called is False

def test_main_dry_run_relative():
    d2 = _fake_display("DISPLAY2", position_x=1920)
    with patch("winrandr.cli.list_displays", return_value=[_fake_display(), d2]):
        with patch("winrandr.cli_handlers.set_position_relative", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "--left-of", "DISPLAY2", "--dry-run"]):
                cli_main()
            assert mock_fn.called is False

def test_main_dry_run_mode_with_rate():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli_handlers.set_resolution", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "-m", "1920x1080", "-r", "60", "--dry-run"]):
                cli_main()
            assert mock_fn.called is False

def test_main_set_resolution_called():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli_handlers.set_resolution", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "-m", "1920x1080"]):
                cli_main()
            assert mock_fn.called is True

def test_main_set_position_called():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli_handlers.set_position", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "-p", "1920x0"]):
                cli_main()
            assert mock_fn.called is True

def test_main_set_primary_called():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli_handlers.set_primary", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "--primary"]):
                cli_main()
            assert mock_fn.called is True

def test_main_set_off_called():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli_handlers.set_off", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "--off"]):
                cli_main()
            assert mock_fn.called is True

def test_main_set_brightness_called():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli_handlers.set_brightness", return_value=True) as mock_fn:
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
    with patch("winrandr.cli_handlers.list_displays", return_value=[]):
        with patch("sys.argv", ["winrandr", "--listmodes"]):
            cli_main()


def test_main_noprimary_failure():
    """set_noprimary 失败时应退出。"""
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.set_noprimary", return_value=False):
            with patch("sys.argv", ["winrandr", "--noprimary"]):
                with pytest.raises(SystemExit):
                    cli_main()


def test_entry_point_version():
    """python -m winrandr --version 应正常退出。"""
    result = subprocess.run(
        [_sys.executable, "-m", "winrandr", "--version"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    assert "winrandr" in result.stdout

def test_cli_entry_guard():
    """覆盖 cli.py 入口守卫（if __name__ == '__main__'）。"""
    import runpy
    from pathlib import Path
    cli_path = Path(__file__).parent.parent.parent / "winrandr" / "cli.py"
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


# ---- Profile CLI integration ----

def test_main_list_profiles_empty():
    """--list-profiles 无存档时应输出提示。"""
    with patch("winrandr.profiles.list_profiles", return_value=[]):
        with patch("sys.argv", ["winrandr", "--list-profiles"]):
            cli_main()


def test_main_list_profiles_with_data():
    """--list-profiles 有存档时应正常输出。"""
    profiles_data = [{
        "name": "docked", "display_count": 2,
        "displays": ["DISPLAY1(1920x1080)", "DISPLAY2(1440x900)"],
        "created": "2026-07-08T00:00:00", "version": "0.3.6",
    }]
    with patch("winrandr.profiles.list_profiles", return_value=profiles_data):
        with patch("sys.argv", ["winrandr", "--list-profiles"]):
            cli_main()


def test_main_list_profiles_json():
    """--list-profiles --json 应正常输出。"""
    with patch("winrandr.profiles.list_profiles", return_value=[]):
        with patch("sys.argv", ["winrandr", "--list-profiles", "--json"]):
            cli_main()


def test_main_save_profile():
    """--save-profile 应调用 save_profile。"""
    with patch("winrandr.profiles.save_profile", return_value=True) as mock_fn:
        with patch("sys.argv", ["winrandr", "--save-profile", "docked"]):
            cli_main()
        assert mock_fn.called is True


def test_main_save_profile_failure():
    """--save-profile 失败时应退出。"""
    with patch("winrandr.profiles.save_profile", return_value=False):
        with pytest.raises(SystemExit):
            with patch("sys.argv", ["winrandr", "--save-profile", "docked"]):
                cli_main()


def test_main_load_profile():
    """--load-profile 应调用 load_profile。"""
    with patch("winrandr.profiles.load_profile", return_value=True) as mock_fn:
        with patch("sys.argv", ["winrandr", "--load-profile", "docked"]):
            cli_main()
        assert mock_fn.called is True


def test_main_load_profile_dry_run():
    """--load-profile --dry-run 应调用 diff_profile。"""
    with patch("winrandr.profiles.diff_profile", return_value=["预览行1"]) as mock_fn:
        with patch("sys.argv", ["winrandr", "--load-profile", "docked", "--dry-run"]):
            cli_main()
        assert mock_fn.called is True


def test_main_delete_profile():
    """--delete-profile 应调用 delete_profile。"""
    with patch("winrandr.profiles.delete_profile", return_value=True) as mock_fn:
        with patch("sys.argv", ["winrandr", "--delete-profile", "docked"]):
            cli_main()
        assert mock_fn.called is True


def test_main_delete_profile_failure():
    """--delete-profile 失败时应退出。"""
    with patch("winrandr.profiles.delete_profile", return_value=False):
        with pytest.raises(SystemExit):
            with patch("sys.argv", ["winrandr", "--delete-profile", "docked"]):
                cli_main()


def test_main_save_profile_empty_name():
    """--save-profile 空名应报错退出。"""
    with pytest.raises(SystemExit):
        with patch("sys.argv", ["winrandr", "--save-profile", ""]):
            cli_main()


def test_main_load_profile_empty_name():
    """--load-profile 空名应报错退出。"""
    with pytest.raises(SystemExit):
        with patch("sys.argv", ["winrandr", "--load-profile", ""]):
            cli_main()


def test_main_delete_profile_empty_name():
    """--delete-profile 空名应报错退出。"""
    with pytest.raises(SystemExit):
        with patch("sys.argv", ["winrandr", "--delete-profile", ""]):
            cli_main()


def test_main_load_profile_failure():
    """--load-profile 失败时应退出。"""
    with patch("winrandr.profiles.load_profile", return_value=False):
        with pytest.raises(SystemExit):
            with patch("sys.argv", ["winrandr", "--load-profile", "docked"]):
                cli_main()


def test_main_identify():
    """--identify 应调用 identify_display。"""
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli_handlers.identify_display", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "--identify"]):
                cli_main()
            assert mock_fn.called is True


def test_main_list_profiles_no_display_names():
    """profile 记录中 displays 为空列表时不应加 [...] 后缀。"""
    profiles_data = [{
        "name": "empty", "display_count": 1,
        "displays": [],
        "created": "2026-07-08T00:00:00", "version": "0.3.6",
    }]
    with patch("winrandr.profiles.list_profiles", return_value=profiles_data):
        with patch("sys.argv", ["winrandr", "--list-profiles"]):
            cli_main()


# ---- Global brightness / gamma (no --output) ----

def test_main_brightness_global():
    """--brightness 不带 --output 应应用到所有已连接显示器。"""
    d1 = _fake_display("DISPLAY1", position_x=0)
    d2 = _fake_display("DISPLAY2", position_x=1920)
    with patch("winrandr.cli.list_displays", return_value=[d1, d2]):
        with patch("winrandr.cli_handlers.set_brightness", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "--brightness", "0.8"]):
                cli_main()
            assert mock_fn.call_count == 2


def test_main_brightness_global_dry_run():
    """--brightness --dry-run 不带 --output 应模拟不实际调用。"""
    d1 = _fake_display("DISPLAY1", position_x=0)
    with patch("winrandr.cli.list_displays", return_value=[d1]):
        with patch("winrandr.cli_handlers.set_brightness", return_value=True) as mock_fn:
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
        with patch("winrandr.cli_handlers.set_gamma", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "--gamma", "1.0:0.9:0.8"]):
                cli_main()
            assert mock_fn.call_count == 2


def test_main_brightness_with_output_still_works():
    """--brightness 带 --output 仍只应用到指定显示器。"""
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli_handlers.set_brightness", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "--brightness", "0.8"]):
                cli_main()
            assert mock_fn.called is True


def test_main_global_op_requires_output_for_other_ops():
    """全局操作中混用了需要 --output 的操作时应报错。"""
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with pytest.raises(SystemExit):
            with patch("sys.argv", ["winrandr", "--brightness", "0.8", "--mode", "1920x1080"]):
                cli_main()
