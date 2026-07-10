"""CLI error branch tests with mock（异常分支，无法通过真实硬件触发）。"""

import sys as _sys
from unittest.mock import patch


def _run(*args):
    import io

    from winrandr.cli import main as cli_main

    old_argv = _sys.argv
    old_stdout = _sys.stdout
    old_stderr = _sys.stderr
    _sys.argv = ["winrandr", *args]
    out = io.StringIO()
    err = io.StringIO()
    _sys.stdout = out
    _sys.stderr = err
    try:
        cli_main()
    except SystemExit:
        pass
    finally:
        _sys.argv = old_argv
        _sys.stdout = old_stdout
        _sys.stderr = old_stderr
    return out.getvalue(), err.getvalue()


def test_listproviders_empty_mocked():
    """list_providers 返回空列表时显示提示（无法真实移除 GPU）。"""
    with patch("winrandr.cli.list_providers", return_value=[]):
        out, _ = _run("--listproviders")
    assert "未检测到" in out


def test_listmonitors_empty_mocked():
    """list_displays 返回空列表时显示提示（无法真实断开所有显示器）。"""
    with patch("winrandr.cli.list_displays", return_value=[]):
        out, _ = _run("--listmonitors")
    assert "未检测到" in out


def test_save_profile_failure_mocked():
    """save_profile 返回 False 时应报错退出。"""
    with patch("winrandr.cli.save_profile", return_value=False):
        with patch("winrandr.cli.list_displays", return_value=[]):
            _, err = _run("--save-profile", "test_fail")
    assert "失败" in err


def test_delete_profile_failure_mocked():
    """delete_profile 返回 False 时应报错退出。"""
    with patch("winrandr.cli.delete_profile", return_value=False):
        _, err = _run("--delete-profile", "test_fail")
    assert "失败" in err


def test_query_no_displays_mocked():
    """list_displays 返回空时查询应退出。"""
    with patch("winrandr.cli.list_displays", return_value=[]):
        out, _ = _run()
    assert "未检测到" in out


def test_query_output_not_found_mocked():
    """--output 指定不存在的显示器时应报错。"""
    from tests.conftest import _fake_display

    fake = _fake_display(name=r"\\.\DISPLAY99")
    with patch("winrandr.cli.list_displays", return_value=[fake]):
        _, err = _run("--output", "DISPLAY1")
    assert "未找到" in err


def test_list_profiles_empty_mocked():
    """list_profiles 返回空列表时显示提示。"""
    with patch("winrandr.cli.list_profiles", return_value=[]):
        out, _ = _run("--list-profiles")
    assert "暂无存档" in out


def test_global_ops_no_displays_mocked():
    """全局亮度/伽马操作无已连接显示器时应报错。"""
    from argparse import Namespace

    from winrandr.cli import _handle_global_ops

    with patch("winrandr.cli.list_displays", return_value=[]):
        with patch("winrandr.cli._fail") as mock_fail:
            _handle_global_ops(Namespace(output=None, brightness=0.5, gamma=None, night_mode=None))
    mock_fail.assert_called_once()


def test_dispatch_display_ops_auto_preferred_reflect():
    """_dispatch_display_ops 分发 auto/preferred/reflect。"""
    from argparse import Namespace
    from unittest.mock import patch

    from winrandr.cli import _dispatch_display_ops

    args = Namespace(
        auto=True,
        mode=None,
        pos=None,
        rotate=None,
        primary=None,
        preferred=True,
        off=None,
        brightness=None,
        night_mode=None,
        reflect="xy",
        gamma=None,
        identify=False,
    )
    with patch("winrandr.cli._handle_auto") as m_auto:
        with patch("winrandr.cli._handle_preferred") as m_pref:
            with patch("winrandr.cli._handle_reflect") as m_refl:
                _dispatch_display_ops(args, r"\\.\DISPLAY1")
    m_auto.assert_called_once()
    m_pref.assert_called_once()
    m_refl.assert_called_once()


def test_listmodes_dispatch_mocked():
    """--listmodes 经 main 调度到 _handle_listmodes。"""
    from unittest.mock import patch

    with patch("winrandr.cli._handle_listmodes") as mock_handle:
        with patch("winrandr.cli.list_displays", return_value=[]):
            _run("--listmodes")
    mock_handle.assert_called_once()


def test_noprimary_only_mocked():
    """--noprimary 且无其他 mod op 时返回 True。"""
    from argparse import Namespace
    from unittest.mock import patch

    from winrandr.cli import _handle_noprimary_only

    args = Namespace(
        dry_run=False,
        noprimary=True,
        auto=None,
        mode=None,
        pos=None,
        rotate=None,
        primary=None,
        preferred=None,
        off=None,
        brightness=None,
        night_mode=None,
        gamma=None,
        reflect=None,
        identify=False,
    )
    with patch("winrandr.cli.set_noprimary", return_value=False):
        with patch("winrandr.cli._fail"):
            result = _handle_noprimary_only(args)
    assert result is True


def test_noprimary_only_dry_run_mocked():
    """--noprimary --dry-run 应跳过 set_noprimary。"""
    from argparse import Namespace
    from unittest.mock import patch

    from winrandr.cli import _handle_noprimary_only

    args = Namespace(
        dry_run=True,
        noprimary=True,
        auto=None,
        mode=None,
        pos=None,
        rotate=None,
        primary=None,
        preferred=None,
        off=None,
        brightness=None,
        night_mode=None,
        gamma=None,
        reflect=None,
        identify=False,
    )
    with patch("winrandr.cli.set_noprimary") as mock_set:
        result = _handle_noprimary_only(args)
    assert result is True
    mock_set.assert_not_called()


def test_noprimary_only_has_other_ops():
    """_handle_noprimary_only 有其他操作时返回 False。"""
    from argparse import Namespace
    from unittest.mock import patch

    from winrandr.cli import _handle_noprimary_only

    args = Namespace(
        dry_run=False,
        noprimary=True,
        auto=True,
        mode=None,
        pos=None,
        rotate=None,
        primary=None,
        preferred=None,
        off=None,
        brightness=None,
        night_mode=None,
        gamma=None,
        reflect=None,
        identify=False,
    )
    with patch("winrandr.cli.set_noprimary", return_value=True):
        result = _handle_noprimary_only(args)
    assert result is False


def test_list_profiles_with_display_names_mocked():
    """list_profiles 含显示器名时格式输出。"""
    from argparse import Namespace
    from unittest.mock import patch

    from winrandr.cli import _handle_list_profiles

    mock_profiles = [
        {"name": "test", "created": "2026-01-01", "display_count": 1, "displays": ["DISPLAY1(1920x1080)"]},
    ]
    with patch("winrandr.cli.list_profiles", return_value=mock_profiles):
        _handle_list_profiles(Namespace(json=False, list_profiles=True))


def test_list_profiles_empty_display_names_mocked():
    """list_profiles 无显示器名时跳过格式添加。"""
    from argparse import Namespace
    from unittest.mock import patch

    from winrandr.cli import _handle_list_profiles

    mock_profiles = [
        {"name": "test", "created": "2026-01-01", "display_count": 0, "displays": []},
    ]
    with patch("winrandr.cli.list_profiles", return_value=mock_profiles):
        _handle_list_profiles(Namespace(json=False, list_profiles=True))


def test_main_noprimary_only_return():
    """main() 中 --noprimary 无其他操作时提前返回。"""
    with patch("winrandr.cli.set_noprimary", return_value=True):
        _run("--noprimary")
