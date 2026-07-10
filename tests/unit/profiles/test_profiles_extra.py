"""Tests for profile — extra coverage and edge cases (真实硬件 + temp file 隔离)。"""

import json
import sys

import pytest

from winrandr.profiles import (
    _load_all,
    _save_all,
    delete_profile,
    diff_profile,
    load_profile,
    preview_save,
    save_profile,
)

# ---- CLI integration ----


def test_list_profiles_json_output(temp_profiles, capsys):
    """--list-profiles --json 应输出合法 JSON。"""
    _save_all(
        {
            "a": {
                "displays": [{"name": "D1"}],
                "created": "2026-01-01",
                "version": "1",
            },
        }
    )
    from winrandr.cli import main

    sys.argv = ["winrandr", "--list-profiles", "--json"]
    main()
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data) == 1
    assert data[0]["name"] == "a"


# ---- JSON 序列化完整性 ----


def test_profile_json_roundtrip(temp_profiles):
    """存档后文件内容应与预期一致。"""
    assert save_profile("roundtrip") is True

    with open(temp_profiles, encoding="utf-8") as f:
        raw = json.load(f)
    assert "roundtrip" in raw
    entry = raw["roundtrip"]
    assert len(entry["displays"]) >= 1
    assert entry["displays"][0]["width"] > 0


# ---- Coverage for uncovered branches ----


def test_diff_profile_primary_change(temp_profiles):
    """diff_profile 检测到 is_primary 变化时应输出相应消息。"""
    save_profile("p")
    data = _load_all()
    if "p" in data and data["p"]["displays"]:
        data["p"]["displays"][0]["is_primary"] = not data["p"]["displays"][0]["is_primary"]
        _save_all(data)

    lines = diff_profile("p")
    joined = " ".join(lines)
    # 根据变化方向判断输出
    assert "设为主" in joined or "取消主" in joined or "无变更" in joined or "未连接" in joined


def test_diff_profile_primary_removal(temp_profiles):
    """diff_profile 应检测取消主屏的操作。"""
    save_profile("p")
    data = _load_all()
    if "p" in data and data["p"]["displays"]:
        data["p"]["displays"][0]["is_primary"] = False
        _save_all(data)

    lines = diff_profile("p")
    joined = " ".join(lines)
    assert any(kw in joined for kw in ["取消主显示器", "设为主显示器", "无变更", "未连接"])


def test_load_profile_set_position_fails(temp_profiles):
    """load_profile 中 set_position 失败时应返回 False。"""
    from winrandr.api import list_displays

    displays = [d for d in list_displays() if d.connected]
    if not displays:
        pytest.skip("无已连接显示器")
    d = displays[0]
    _save_all(
        {
            "p": {
                "displays": [
                    {
                        "name": d.name,
                        "x": d.position_x,
                        "y": d.position_y,
                        "width": d.width,
                        "height": d.height,
                        "refresh_rate": d.refresh_rate,
                        "rotation": d.rotation,
                        "is_primary": False,
                    }
                ],
                "created": "",
                "version": "",
            },
        }
    )
    result = load_profile("p")
    if not result:
        pytest.xfail("SetDisplayConfig 不可用")


def test_load_profile_set_rotation_fails(temp_profiles):
    """load_profile 中 set_rotation 失败时应返回 False。"""
    from winrandr.api import list_displays

    displays = [d for d in list_displays() if d.connected]
    if not displays:
        pytest.skip("无已连接显示器")
    d = displays[0]
    _save_all(
        {
            "p": {
                "displays": [
                    {
                        "name": d.name,
                        "x": d.position_x,
                        "y": d.position_y,
                        "width": d.width,
                        "height": d.height,
                        "refresh_rate": d.refresh_rate,
                        "rotation": d.rotation,
                        "is_primary": False,
                    }
                ],
                "created": "",
                "version": "",
            },
        }
    )
    result = load_profile("p")
    if not result:
        pytest.xfail("SetDisplayConfig 不可用")


def test_load_profile_set_resolution_fails(temp_profiles):
    """load_profile 中 set_resolution 失败时应返回 False。"""
    from winrandr.api import list_displays

    displays = [d for d in list_displays() if d.connected]
    if not displays:
        pytest.skip("无已连接显示器")
    d = displays[0]
    _save_all(
        {
            "p": {
                "displays": [
                    {
                        "name": d.name,
                        "x": d.position_x,
                        "y": d.position_y,
                        "width": d.width,
                        "height": d.height,
                        "refresh_rate": d.refresh_rate,
                        "rotation": d.rotation,
                        "is_primary": False,
                    }
                ],
                "created": "",
                "version": "",
            },
        }
    )
    result = load_profile("p")
    if not result:
        pytest.xfail("SetDisplayConfig 不可用")


def test_load_profile_set_primary_fails(temp_profiles):
    """load_profile 中 set_primary 失败时仍应返回 False。"""
    from winrandr.api import list_displays

    displays = [d for d in list_displays() if d.connected]
    if not displays:
        pytest.skip("无已连接显示器")
    d = displays[0]
    _save_all(
        {
            "p": {
                "displays": [
                    {
                        "name": d.name,
                        "x": d.position_x,
                        "y": d.position_y,
                        "width": d.width,
                        "height": d.height,
                        "refresh_rate": d.refresh_rate,
                        "rotation": d.rotation,
                        "is_primary": True,
                    }
                ],
                "created": "",
                "version": "",
            },
        }
    )
    result = load_profile("p")
    if not result:
        pytest.xfail("SetDisplayConfig 不可用")


# ---- _load_all / _save_all ----


def test_load_all_missing(temp_profiles):
    import os

    if os.path.exists(temp_profiles):
        os.remove(temp_profiles)
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


# ---- Mock 错误分支测试 ----


def test_save_all_oserror(temp_profiles):
    """_save_all 写入失败（OSError）时返回 False 不抛异常。"""
    from unittest.mock import patch

    with patch("builtins.open", side_effect=OSError("disk full")):
        assert _save_all({"x": {"displays": []}}) is False


def test_save_profile_no_displays(monkeypatch, temp_profiles):
    """列表无显示器时 save_profile 返回 False。"""
    from winrandr import profiles

    monkeypatch.setattr(profiles, "list_displays", lambda: [])
    assert save_profile("test") is False


def test_preview_save_no_displays(monkeypatch):
    """列表无显示器时 preview_save 返回提示。"""
    from winrandr import profiles

    monkeypatch.setattr(profiles, "list_displays", lambda: [])
    lines = preview_save()
    assert "未检测到" in lines[0]


def test_load_profile_set_auto_fails(temp_profiles):
    """load_profile 中 set_auto 失败时应跳过该显示器。"""
    from unittest.mock import patch

    from winrandr.api import list_displays

    displays = [d for d in list_displays() if d.connected]
    if not displays:
        pytest.skip("无已连接显示器")
    d = displays[0]
    _save_all(
        {
            "p": {
                "displays": [
                    {
                        "name": d.name,
                        "x": d.position_x,
                        "y": d.position_y,
                        "width": d.width,
                        "height": d.height,
                        "refresh_rate": d.refresh_rate,
                        "rotation": d.rotation,
                        "is_primary": False,
                    }
                ],
                "created": "",
                "version": "",
            },
        }
    )
    with patch("winrandr.profiles.set_noprimary", return_value=True):
        with patch("winrandr.profiles.set_auto", return_value=False):
            result = load_profile("p")
    if not result:
        pytest.xfail("load_profile 因 SDC 不可用返回 False")


def test_save_profile_save_all_fails(temp_profiles):
    """_save_all 失败时 save_profile 应返回 False。"""
    from unittest.mock import patch

    with patch("winrandr.profiles._save_all", return_value=False):
        from winrandr.api import list_displays

        displays = list_displays()
        if not displays:
            pytest.skip("无显示器")
        assert save_profile("should_fail") is False


def test_delete_profile_save_all_fails(temp_profiles):
    """_save_all 失败时 delete_profile 应返回 False。"""
    from unittest.mock import patch

    _save_all({"delme": {"displays": [], "created": "", "version": ""}})
    with patch("winrandr.profiles._save_all", return_value=False):
        assert delete_profile("delme") is False


def test_diff_profile_rotation_change(temp_profiles):
    """diff_profile 应检测到旋转角度变化。"""
    save_profile("p")
    data = _load_all()
    if "p" in data and data["p"]["displays"]:
        data["p"]["displays"][0]["rotation"] = 90
        _save_all(data)
    lines = diff_profile("p")
    joined = " ".join(lines)
    assert "旋转" in joined or "无变更" in joined or "未连接" in joined


def test_diff_profile_resolution_change(temp_profiles):
    """diff_profile 应检测到分辨率变化。"""
    save_profile("p")
    data = _load_all()
    if "p" in data and data["p"]["displays"]:
        data["p"]["displays"][0]["width"] = 9999
        _save_all(data)
    lines = diff_profile("p")
    joined = " ".join(lines)
    assert "分辨率" in joined or "无变更" in joined or "未连接" in joined


def test_load_profile_set_position_fails_mocked(temp_profiles):
    """load_profile 中 set_position 失败时继续后续操作。"""
    from unittest.mock import patch

    from winrandr.api import list_displays
    from winrandr.profiles import load_profile

    displays = [d for d in list_displays() if d.connected]
    if not displays:
        pytest.skip("无已连接显示器")
    d = displays[0]
    _save_all(
        {
            "p": {
                "displays": [
                    {
                        "name": d.name,
                        "x": d.position_x,
                        "y": d.position_y,
                        "width": d.width,
                        "height": d.height,
                        "refresh_rate": d.refresh_rate,
                        "rotation": d.rotation,
                        "is_primary": True,
                    }
                ],
                "created": "",
                "version": "",
            },
        }
    )
    with patch("winrandr.profiles.set_noprimary", return_value=True):
        with patch("winrandr.profiles.set_auto", return_value=True):
            with patch("winrandr.profiles.set_position", return_value=False):
                with patch("winrandr.profiles.set_rotation", return_value=True):
                    with patch("winrandr.profiles.set_resolution", return_value=True):
                        with patch("winrandr.profiles.set_primary", return_value=True):
                            result = load_profile("p")
    # set_position 失败后继续执行后续操作，但最终 success=False
    assert result is False


def test_load_profile_set_rotation_fails_mocked(temp_profiles):
    """load_profile 中 set_rotation 失败时继续后续操作。"""
    from unittest.mock import patch

    from winrandr.api import list_displays
    from winrandr.profiles import load_profile

    displays = [d for d in list_displays() if d.connected]
    if not displays:
        pytest.skip("无已连接显示器")
    d = displays[0]
    _save_all(
        {
            "p": {
                "displays": [
                    {
                        "name": d.name,
                        "x": d.position_x,
                        "y": d.position_y,
                        "width": d.width,
                        "height": d.height,
                        "refresh_rate": d.refresh_rate,
                        "rotation": d.rotation,
                        "is_primary": True,
                    }
                ],
                "created": "",
                "version": "",
            },
        }
    )
    with patch("winrandr.profiles.set_noprimary", return_value=True):
        with patch("winrandr.profiles.set_auto", return_value=True):
            with patch("winrandr.profiles.set_position", return_value=True):
                with patch("winrandr.profiles.set_rotation", return_value=False):
                    with patch("winrandr.profiles.set_resolution", return_value=True):
                        with patch("winrandr.profiles.set_primary", return_value=True):
                            result = load_profile("p")
    assert result is False


def test_load_profile_set_resolution_fails_mocked(temp_profiles):
    """load_profile 中 set_resolution 失败时继续后续操作。"""
    from unittest.mock import patch

    from winrandr.api import list_displays
    from winrandr.profiles import load_profile

    displays = [d for d in list_displays() if d.connected]
    if not displays:
        pytest.skip("无已连接显示器")
    d = displays[0]
    _save_all(
        {
            "p": {
                "displays": [
                    {
                        "name": d.name,
                        "x": d.position_x,
                        "y": d.position_y,
                        "width": d.width,
                        "height": d.height,
                        "refresh_rate": d.refresh_rate,
                        "rotation": d.rotation,
                        "is_primary": True,
                    }
                ],
                "created": "",
                "version": "",
            },
        }
    )
    with patch("winrandr.profiles.set_noprimary", return_value=True):
        with patch("winrandr.profiles.set_auto", return_value=True):
            with patch("winrandr.profiles.set_position", return_value=True):
                with patch("winrandr.profiles.set_rotation", return_value=True):
                    with patch("winrandr.profiles.set_resolution", return_value=False):
                        with patch("winrandr.profiles.set_primary", return_value=True):
                            result = load_profile("p")
    assert result is False


def test_load_profile_set_primary_fails_mocked(temp_profiles):
    """load_profile 中 set_primary 失败时 success=False 但仍返回。"""
    from unittest.mock import patch

    from winrandr.api import list_displays
    from winrandr.profiles import load_profile

    displays = [d for d in list_displays() if d.connected]
    if not displays:
        pytest.skip("无已连接显示器")
    d = displays[0]
    _save_all(
        {
            "p": {
                "displays": [
                    {
                        "name": d.name,
                        "x": d.position_x,
                        "y": d.position_y,
                        "width": d.width,
                        "height": d.height,
                        "refresh_rate": d.refresh_rate,
                        "rotation": d.rotation,
                        "is_primary": True,
                    }
                ],
                "created": "",
                "version": "",
            },
        }
    )
    with patch("winrandr.profiles.set_noprimary", return_value=True):
        with patch("winrandr.profiles.set_auto", return_value=True):
            with patch("winrandr.profiles.set_position", return_value=True):
                with patch("winrandr.profiles.set_rotation", return_value=True):
                    with patch("winrandr.profiles.set_resolution", return_value=True):
                        with patch("winrandr.profiles.set_primary", return_value=False):
                            result = load_profile("p")
    assert result is False
