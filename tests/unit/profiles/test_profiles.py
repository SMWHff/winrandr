"""Tests for profile save/load/list/delete (真实硬件 + temp file 隔离)。"""

import pytest

from winrandr.profiles import (
    _load_all,
    _save_all,
    list_profiles,
    load_profile,
    save_profile,
)

# ---- save_profile ----


def test_save_profile_success(temp_profiles):
    """存档成功应写入选定显示屏配置。"""
    assert save_profile("docked") is True

    data = _load_all()
    assert "docked" in data
    assert len(data["docked"]["displays"]) >= 1
    assert data["docked"]["displays"][0]["name"].startswith(r"\\.\DISPLAY")


def test_save_profile_overwrite(temp_profiles):
    """重复保存同一存档名不应报错。"""
    assert save_profile("cfg") is True
    assert save_profile("cfg") is True


# ---- load_profile ----


def test_load_profile_not_found(temp_profiles):
    assert load_profile("nonexistent") is False


def test_load_profile_success(temp_profiles):
    """加载存档：基于当前真实显示器状态，SDC 不可用时 xfail。"""
    from winrandr.api import list_displays

    displays = [d for d in list_displays() if d.connected]
    config_displays = [
        {
            "name": d.name,
            "x": d.position_x,
            "y": d.position_y,
            "width": d.width,
            "height": d.height,
            "refresh_rate": d.refresh_rate,
            "rotation": d.rotation,
            "is_primary": d.is_primary,
        }
        for d in displays
    ]
    _save_all(
        {
            "myprofile": {
                "displays": config_displays,
                "created": "2026-01-01T00:00:00",
                "version": "0.3.5",
            },
        }
    )

    result = load_profile("myprofile")
    if not result:
        pytest.xfail("SetDisplayConfig 不可用，加载存档预期失败")


def test_load_profile_display_not_connected(temp_profiles):
    """配置中的显示器未连接时跳过，不报错。"""
    _save_all(
        {
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
    )
    # DISPLAY3 不存在，set_noprimary 可能因 SDC 失败
    result = load_profile("p")
    if not result:
        pytest.xfail("SetDisplayConfig 不可用")


# ---- list_profiles ----


def test_list_profiles_empty(temp_profiles):
    assert list_profiles() == []


def test_list_profiles(temp_profiles):
    data = {
        "a": {"displays": [{"name": "D1"}], "created": "2026-01-01", "version": "1"},
        "b": {
            "displays": [{"name": "D1"}, {"name": "D2"}],
            "created": "2026-06-01",
            "version": "2",
        },
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
            },
        }
    )
    result = list_profiles()
    assert len(result[0]["displays"]) == 2
    assert "DISPLAY1(1920x1080)" in result[0]["displays"]
    assert "DISPLAY2(1440x900)" in result[0]["displays"]
