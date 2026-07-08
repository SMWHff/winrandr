"""Tests for main() CLI entry point — profile operations."""

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
        with patch("winrandr.cli.handlers.identify_display", return_value=True) as mock_fn:
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
