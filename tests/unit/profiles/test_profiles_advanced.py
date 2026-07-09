"""配置存档 diff 与 preview 边缘场景测试。"""

from unittest.mock import patch

from tests.unit.profiles.helpers import _make_display
from winrandr.profiles import (
    _save_all,
    diff_profile,
    preview_save,
)

# ---- diff_profile ----


def test_diff_profile_not_found(temp_profiles):
    lines = diff_profile("nonexistent")
    assert "未找到存档" in lines[0]


def test_diff_profile_all_match(temp_profiles):
    config = {
        "m": {
            "displays": [
                {
                    "name": r"\\.\DISPLAY1",
                    "x": 0,
                    "y": 0,
                    "width": 1920,
                    "height": 1080,
                    "refresh_rate": 60.0,
                    "rotation": 0,
                    "is_primary": True,
                }
            ],
            "created": "2026-01-01T00:00:00",
            "version": "0.3.5",
        },
    }
    _save_all(config)
    with patch("winrandr.profiles.list_displays", return_value=[_make_display()]):
        lines = diff_profile("m")
        assert "无变更" in lines[1]


def test_diff_profile_with_changes(temp_profiles):
    config = {
        "m": {
            "displays": [
                {
                    "name": r"\\.\DISPLAY1",
                    "x": 1920,
                    "y": 0,
                    "width": 2560,
                    "height": 1440,
                    "refresh_rate": 120.0,
                    "rotation": 90,
                    "is_primary": False,
                }
            ],
            "created": "2026-01-01T00:00:00",
            "version": "0.3.5",
        },
    }
    _save_all(config)
    cur = _make_display("DISPLAY1", 0, 0, 1920, 1080, 60.0, 0, True)
    with patch("winrandr.profiles.list_displays", return_value=[cur]):
        lines = diff_profile("m")
        joined = " ".join(lines)
        assert "位置" in joined
        assert "旋转" in joined
        assert "分辨率" in joined


def test_diff_profile_not_connected(temp_profiles):
    config = {
        "m": {
            "displays": [
                {
                    "name": r"\\.\DISPLAY3",
                    "x": 0,
                    "y": 0,
                    "width": 1920,
                    "height": 1080,
                    "refresh_rate": 60.0,
                    "rotation": 0,
                    "is_primary": False,
                }
            ],
            "created": "2026-01-01T00:00:00",
            "version": "0.3.5",
        },
    }
    _save_all(config)
    with patch("winrandr.profiles.list_displays", return_value=[_make_display("DISPLAY1")]):
        lines = diff_profile("m")
        assert "未连接" in " ".join(lines)


# ---- preview_save ----


def test_preview_save_no_displays():
    with patch("winrandr.profiles.list_displays", return_value=[]):
        lines = preview_save()
        assert "未检测到" in lines[0]


def test_preview_save_with_displays():
    d1 = _make_display("DISPLAY1", 0, 0, 1920, 1080, 60.0, 0, True)
    with patch("winrandr.profiles.list_displays", return_value=[d1]):
        lines = preview_save()
        assert "DISPLAY1" in " ".join(lines)
        assert "1920x1080" in " ".join(lines)


def test_preview_save_dry_run_integration():
    d1 = _make_display("DISPLAY1", 0, 0, 1920, 1080, 60.0, 0, True)
    with patch("winrandr.profiles.list_displays", return_value=[d1]):
        with patch("sys.argv", ["winrandr", "--save-profile", "test", "--dry-run"]):
            from winrandr.cli import main

            main()
