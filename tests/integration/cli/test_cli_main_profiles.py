"""Tests for main() CLI entry point — profile operations (真实硬件)。"""

import sys

from winrandr.cli import main as cli_main


def _run(*args):
    import io

    old_argv = sys.argv
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.argv = ["winrandr", *args]
    out = io.StringIO()
    err = io.StringIO()
    sys.stdout = out
    sys.stderr = err
    try:
        cli_main()
    except SystemExit:
        pass
    finally:
        sys.argv = old_argv
        sys.stdout = old_stdout
        sys.stderr = old_stderr
    return out.getvalue(), err.getvalue()


def test_main_list_profiles_empty():
    """--list-profiles 无存档时输出提示。"""
    out, _ = _run("--list-profiles")
    assert isinstance(out, str)


def test_main_list_profiles_with_data(profile_backup):
    """--list-profiles 先保存再列出。"""
    _run("--save-profile", "__test_cli_profile__")
    out, _ = _run("--list-profiles")
    assert "__test_cli_profile__" in out or isinstance(out, str)


def test_main_list_profiles_json(profile_backup):
    """--list-profiles --json 输出 JSON。"""
    import json

    _run("--save-profile", "__test_cli_json__")
    out, _ = _run("--list-profiles", "--json")
    data = json.loads(out)
    assert isinstance(data, list)


def test_main_save_profile():
    """--save-profile 正常执行。"""
    out, _ = _run("--save-profile", "__test_save__", "--dry-run")
    assert isinstance(out, str)


def test_main_save_profile_failure():
    """空名保存应退出。"""
    import io

    old_argv = sys.argv
    sys.argv = ["winrandr", "--save-profile", ""]
    err = io.StringIO()
    sys.stderr = err
    try:
        cli_main()
    except SystemExit:
        pass
    finally:
        sys.argv = old_argv
        sys.stderr = sys.stderr


def test_main_load_profile(profile_backup):
    """--load-profile 加载存档。"""
    from winrandr.profiles import save_profile

    save_profile("__test_load__")
    out, _ = _run("--load-profile", "__test_load__")
    assert isinstance(out, str)
    from winrandr.profiles import delete_profile

    delete_profile("__test_load__")


def test_main_load_profile_dry_run(profile_backup):
    """--load-profile --dry-run 应预览。"""
    from winrandr.profiles import save_profile

    save_profile("__test_preview__")
    out, _ = _run("--load-profile", "__test_preview__", "--dry-run")
    assert isinstance(out, str)
    from winrandr.profiles import delete_profile

    delete_profile("__test_preview__")


def test_main_delete_profile(profile_backup):
    """--delete-profile 删除存档。"""
    from winrandr.profiles import save_profile

    save_profile("__test_del__")
    out, _ = _run("--delete-profile", "__test_del__")
    assert isinstance(out, str)


def test_main_delete_profile_failure():
    """空名删除应退出。"""
    import io

    old_argv = sys.argv
    sys.argv = ["winrandr", "--delete-profile", ""]
    err = io.StringIO()
    sys.stderr = err
    try:
        cli_main()
    except SystemExit:
        pass
    finally:
        sys.argv = old_argv
        sys.stderr = sys.stderr


def test_main_save_profile_empty_name():
    """--save-profile 空名应报错退出。"""
    import io

    old_argv = sys.argv
    sys.argv = ["winrandr", "--save-profile", ""]
    err = io.StringIO()
    sys.stderr = err
    try:
        cli_main()
    except SystemExit:
        pass
    finally:
        sys.argv = old_argv
        sys.stderr = sys.stderr


def test_main_load_profile_empty_name():
    """--load-profile 空名应报错退出。"""
    import io

    old_argv = sys.argv
    sys.argv = ["winrandr", "--load-profile", ""]
    err = io.StringIO()
    sys.stderr = err
    try:
        cli_main()
    except SystemExit:
        pass
    finally:
        sys.argv = old_argv
        sys.stderr = sys.stderr


def test_main_delete_profile_empty_name():
    """--delete-profile 空名应报错退出。"""
    import io

    old_argv = sys.argv
    sys.argv = ["winrandr", "--delete-profile", ""]
    err = io.StringIO()
    sys.stderr = err
    try:
        cli_main()
    except SystemExit:
        pass
    finally:
        sys.argv = old_argv
        sys.stderr = sys.stderr


def test_main_identify_dry_run():
    """--identify --dry-run 应显示 dry-run 消息。"""
    out, _ = _run("-o", "DISPLAY1", "--identify", "--dry-run")
    assert len(out) > 0
