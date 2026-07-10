"""配置存档 diff 与 preview 测试（真实硬件 + temp file 隔离）。"""

from winrandr.profiles import (
    _load_all,
    _save_all,
    diff_profile,
    preview_save,
    save_profile,
)

# ---- diff_profile ----


def test_diff_profile_not_found(temp_profiles):
    lines = diff_profile("nonexistent")
    assert "未找到存档" in lines[0]


def test_diff_profile_all_match(temp_profiles):
    """保存当前配置后 diff，应显示无变更。"""
    save_profile("m")
    lines = diff_profile("m")
    assert "无变更" in " ".join(lines) or "未连接" in " ".join(lines)


def test_diff_profile_with_changes(temp_profiles):
    """保存当前配置、修改存档中位置后 diff，应检测到变更。"""
    save_profile("m")
    data = _load_all()
    if "m" in data and data["m"]["displays"]:
        data["m"]["displays"][0]["x"] = 9999
        _save_all(data)
    lines = diff_profile("m")
    assert any("位置" in ln or "分辨率" in ln or "旋转" in ln or "设为主" in ln or "取消主" in ln for ln in lines)


def test_diff_profile_not_connected(temp_profiles):
    """存档中的显示器未连接时应有提示。"""
    _save_all(
        {
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
    )
    lines = diff_profile("m")
    assert "未连接" in " ".join(lines)


# ---- preview_save ----


def test_preview_save_with_displays():
    """基于真实显示器数据预览保存。"""
    lines = preview_save()
    assert len(lines) > 0
    assert "将保存" in lines[0]


def test_preview_save_dry_run_integration():
    """--save-profile --dry-run 集成测试。"""
    import sys as _sys

    from winrandr.cli import main

    old_argv = _sys.argv
    _sys.argv = ["winrandr", "--save-profile", "test", "--dry-run"]
    try:
        main()
    except SystemExit:
        pass
    finally:
        _sys.argv = old_argv
