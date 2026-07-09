"""Tests for profile save/load/list/delete."""

import os
import tempfile
from unittest.mock import patch

import pytest

from winrandr.models import DisplayInfo, DisplayMode
from winrandr.profiles import (
    _load_all,
    _save_all,
    list_profiles,
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


# ---- save_profile ----


def test_save_profile_no_displays(temp_profiles):
    with patch("winrandr.profiles.list_displays", return_value=[]):
        assert save_profile("test") is False


def test_save_profile_success(temp_profiles):
    d1 = _make_display("DISPLAY1", 0, 0, 1920, 1080, 60.0, 0, True)
    d2 = _make_display("DISPLAY2", 1920, 0, 1440, 900, 59.0, 0, False)
    with patch("winrandr.profiles.list_displays", return_value=[d1, d2]):
        assert save_profile("docked") is True

    data = _load_all()
    assert "docked" in data
    assert len(data["docked"]["displays"]) == 2
    assert data["docked"]["displays"][0]["name"] == r"\\.\DISPLAY1"
    assert data["docked"]["displays"][0]["width"] == 1920


def test_save_profile_overwrite(temp_profiles):
    d1 = _make_display("DISPLAY1")
    with patch("winrandr.profiles.list_displays", return_value=[d1]):
        assert save_profile("cfg") is True
    with patch("winrandr.profiles.list_displays", return_value=[d1]):
        assert save_profile("cfg") is True


# ---- load_profile ----


def test_load_profile_not_found(temp_profiles):
    assert load_profile("nonexistent") is False


def test_load_profile_success(temp_profiles):
    config = {
        "myprofile": {
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
        with patch("winrandr.profiles.set_noprimary", return_value=True) as snp:
            with patch("winrandr.profiles.set_auto", return_value=True) as sa:
                with patch("winrandr.profiles.set_position", return_value=True):
                    with patch("winrandr.profiles.set_rotation", return_value=True):
                        with patch("winrandr.profiles.set_resolution", return_value=True):
                            with patch("winrandr.profiles.set_primary", return_value=True) as sp:
                                assert load_profile("myprofile") is True
                                snp.assert_called_once()
                                sa.assert_called_once_with(r"\\.\DISPLAY1")
                                sp.assert_called_once_with(r"\\.\DISPLAY1")


def test_load_profile_display_not_connected(temp_profiles):
    config = {
        "p": {
            "displays": [
                {
                    "name": r"\\.\DISPLAY3",
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

    with patch("winrandr.profiles.list_displays", return_value=[_make_display("DISPLAY1")]):
        with patch("winrandr.profiles.set_noprimary", return_value=True):
            with patch("winrandr.profiles.set_auto") as sa:
                assert load_profile("p") is True  # skips DISPLAY3, no error
                sa.assert_not_called()


def test_load_profile_set_noprimary_fails(temp_profiles):
    """set_noprimary 失败时应返回 False 而非静默成功。"""
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
            "version": "0.3.5",
        },
    }
    _save_all(config)

    with patch("winrandr.profiles.list_displays", return_value=[_make_display()]):
        with patch("winrandr.profiles.set_noprimary", return_value=False):
            with patch("winrandr.profiles.set_auto", return_value=True):
                with patch("winrandr.profiles.set_position", return_value=True):
                    with patch("winrandr.profiles.set_rotation", return_value=True):
                        with patch("winrandr.profiles.set_resolution", return_value=True):
                            with patch("winrandr.profiles.set_primary", return_value=True):
                                assert load_profile("p") is False


def test_load_profile_set_auto_fails(temp_profiles):
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
            "created": "2026-01-01T00:00:00",
            "version": "0.3.5",
        },
    }
    _save_all(config)

    with patch("winrandr.profiles.list_displays", return_value=[_make_display()]):
        with patch("winrandr.profiles.set_noprimary", return_value=True):
            with patch("winrandr.profiles.set_auto", return_value=False):
                with patch("winrandr.profiles.set_position") as sp:
                    assert load_profile("p") is False
                    sp.assert_not_called()


# ---- list_profiles ----


def test_list_profiles_empty(temp_profiles):
    assert list_profiles() == []


def test_list_profiles(temp_profiles):
    data = {
        "a": {"displays": [{"name": "D1"}], "created": "2026-01-01", "version": "1"},
        "b": {"displays": [{"name": "D1"}, {"name": "D2"}], "created": "2026-06-01", "version": "2"},
    }
    _save_all(data)
    result = list_profiles()
    assert len(result) == 2
    assert result[0]["name"] == "a"
    assert result[0]["display_count"] == 1
    assert result[1]["name"] == "b"
    assert result[1]["display_count"] == 2


def test_list_profiles_with_resolution(temp_profiles):
    """带分辨率信息的存档应显示 DISPLAY1(1920x1080) 格式。"""
    _save_all(
        {
            "p": {
                "displays": [
                    {"name": r"\\.\DISPLAY1", "width": 1920, "height": 1080},
                    {"name": r"\\.\DISPLAY2", "width": 1440, "height": 900},
                ],
                "created": "2026-01-01",
                "version": "1",
            }
        }
    )
    result = list_profiles()
    assert len(result[0]["displays"]) == 2
    assert "DISPLAY1(1920x1080)" in result[0]["displays"]
    assert "DISPLAY2(1440x900)" in result[0]["displays"]
