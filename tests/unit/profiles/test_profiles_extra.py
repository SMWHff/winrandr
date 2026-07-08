"""Tests for profile — extra coverage and edge cases."""

import json
import os
import sys
import tempfile
from unittest.mock import patch

import pytest

from winrandr.models import DisplayInfo, DisplayMode
from winrandr.profiles import (
    _load_all,
    _save_all,
    delete_profile,
    diff_profile,
    load_profile,
    save_profile,
)


def _make_display(name="DISPLAY1", x=0, y=0, w=1920, h=1080, rr=60.0, rot=0, primary=True) -> DisplayInfo:
    dm = DisplayMode(w, h, rr, True, True)
    return DisplayInfo(
        name=rf"\\.\{name}",
        friendly_name="Test",
        connected=True,
        width=w,
        height=h,
        refresh_rate=rr,
        position_x=x,
        position_y=y,
        is_primary=primary,
        rotation=rot,
        width_mm=527,
        height_mm=296,
        modes=[dm],
    )


@pytest.fixture
def temp_profiles(monkeypatch):
    """用临时文件覆盖配置路径。"""
    tmp = tempfile.mkdtemp()
    pf = os.path.join(tmp, "profiles.json")
    monkeypatch.setattr("winrandr.profiles._PROFILES_FILE", pf)
    return pf


# ---- CLI integration ----


def test_list_profiles_json_output(temp_profiles, capsys):
    """--list-profiles --json 应输出合法 JSON。"""
    _save_all({"a": {"displays": [{"name": "D1"}], "created": "2026-01-01", "version": "1"}})
    from winrandr.cli import main

    sys.argv = ["winrandr", "--list-profiles", "--json"]
    main()
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data) == 1
    assert data[0]["name"] == "a"


# ---- JSON 序列化完整性 ----


def test_profile_json_roundtrip(temp_profiles):
    d1 = _make_display("DISPLAY1", 0, 0, 1920, 1080, 60.0, 0, True)
    with patch("winrandr.profiles.list_displays", return_value=[d1]):
        save_profile("roundtrip")

    with open(temp_profiles, encoding="utf-8") as f:
        raw = json.load(f)
    assert "roundtrip" in raw
    entry = raw["roundtrip"]
    assert entry["displays"][0]["width"] == 1920
    assert entry["displays"][0]["is_primary"] is True


# ---- Coverage for uncovered branches ----


def test_save_all_oserror(temp_profiles):
    """_save_all 写入失败（OSError）时应返回 False 且不抛异常。"""
    with patch("builtins.open", side_effect=OSError("disk full")):
        assert _save_all({"x": {"displays": []}}) is False


def test_save_profile_save_all_fails(temp_profiles):
    """save_profile 中 _save_all 失败时应返回 False。"""
    d1 = _make_display("DISPLAY1")
    with patch("winrandr.profiles.list_displays", return_value=[d1]):
        with patch("winrandr.profiles._save_all", return_value=False):
            assert save_profile("test") is False


def test_delete_profile_save_all_fails(temp_profiles):
    """delete_profile 中 _save_all 失败时应返回 False。"""
    _save_all({"delme": {"displays": []}})
    with patch("winrandr.profiles._save_all", return_value=False):
        assert delete_profile("delme") is False


def test_diff_profile_primary_change(temp_profiles):
    """diff_profile 检测到 is_primary 变化时应输出「设为主显示器」。"""
    config = {
        "p": {
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
            "version": "0.3.6",
        },
    }
    _save_all(config)
    cur = _make_display("DISPLAY1", 0, 0, 1920, 1080, 60.0, 0, primary=False)
    with patch("winrandr.profiles.list_displays", return_value=[cur]):
        lines = diff_profile("p")
        assert "设为主显示器" in " ".join(lines)


def test_load_profile_set_position_fails(temp_profiles):
    """load_profile 中 set_position 失败时应继续执行后续操作。"""
    config = {
        "p": {
            "displays": [
                {
                    "name": r"\\.\DISPLAY1",
                    "x": 0,
                    "y": 0,
                    "width": 1920,
                    "height": 1080,
                    "refresh_rate": 60.0,
                    "rotation": 0,
                    "is_primary": False,
                }
            ],
            "created": "",
            "version": "",
        }
    }
    _save_all(config)
    with patch("winrandr.profiles.list_displays", return_value=[_make_display()]):
        with patch("winrandr.profiles.set_auto", return_value=True):
            with patch("winrandr.profiles.set_position", return_value=False):
                with patch("winrandr.profiles.set_rotation", return_value=True):
                    with patch("winrandr.profiles.set_resolution", return_value=True):
                        assert load_profile("p") is False


def test_load_profile_set_rotation_fails(temp_profiles):
    """load_profile 中 set_rotation 失败时应继续执行后续操作。"""
    config = {
        "p": {
            "displays": [
                {
                    "name": r"\\.\DISPLAY1",
                    "x": 0,
                    "y": 0,
                    "width": 1920,
                    "height": 1080,
                    "refresh_rate": 60.0,
                    "rotation": 90,
                    "is_primary": False,
                }
            ],
            "created": "",
            "version": "",
        }
    }
    _save_all(config)
    with patch("winrandr.profiles.list_displays", return_value=[_make_display()]):
        with patch("winrandr.profiles.set_auto", return_value=True):
            with patch("winrandr.profiles.set_position", return_value=True):
                with patch("winrandr.profiles.set_rotation", return_value=False):
                    with patch("winrandr.profiles.set_resolution", return_value=True):
                        assert load_profile("p") is False


def test_load_profile_set_resolution_fails(temp_profiles):
    """load_profile 中 set_resolution 失败时应继续执行后续操作。"""
    config = {
        "p": {
            "displays": [
                {
                    "name": r"\\.\DISPLAY1",
                    "x": 0,
                    "y": 0,
                    "width": 1920,
                    "height": 1080,
                    "refresh_rate": 60.0,
                    "rotation": 0,
                    "is_primary": False,
                }
            ],
            "created": "",
            "version": "",
        }
    }
    _save_all(config)
    with patch("winrandr.profiles.list_displays", return_value=[_make_display()]):
        with patch("winrandr.profiles.set_auto", return_value=True):
            with patch("winrandr.profiles.set_position", return_value=True):
                with patch("winrandr.profiles.set_rotation", return_value=True):
                    with patch("winrandr.profiles.set_resolution", return_value=False):
                        assert load_profile("p") is False


def test_load_profile_set_primary_fails(temp_profiles):
    """load_profile 中 set_primary 失败时仍应返回 False。"""
    config = {
        "p": {
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
            "created": "",
            "version": "",
        }
    }
    _save_all(config)
    with patch("winrandr.profiles.list_displays", return_value=[_make_display()]):
        with patch("winrandr.profiles.set_auto", return_value=True):
            with patch("winrandr.profiles.set_position", return_value=True):
                with patch("winrandr.profiles.set_rotation", return_value=True):
                    with patch("winrandr.profiles.set_resolution", return_value=True):
                        with patch("winrandr.profiles.set_primary", return_value=False):
                            assert load_profile("p") is False


# ---- _load_all / _save_all ----


def test_load_all_missing(temp_profiles):
    assert _load_all() == {}


def test_load_all_corrupt(temp_profiles):
    with open(temp_profiles, "w") as f:
        f.write("not json")
    assert _load_all() == {}


def test_save_and_load(temp_profiles):
    data = {"test": {"displays": [], "created": "now", "version": "0.3.5"}}
    assert _save_all(data) is True
    assert _load_all() == data


# ---- delete_profile ----


def test_delete_profile_not_found(temp_profiles):
    assert delete_profile("nonexistent") is False


def test_delete_profile_success(temp_profiles):
    _save_all({"delme": {"displays": []}})
    assert delete_profile("delme") is True
    assert _load_all() == {}
