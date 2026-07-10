"""Tests for main() CLI entry point (真实硬件)。"""

import sys

from winrandr.cli import main as cli_main


def _run(*args):
    """使用 sys.argv 运行 CLI 并捕获 stdout。"""
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


def test_main_query():
    """基本查询应显示显示器信息。"""
    out, _ = _run()
    assert "DISPLAY" in out or "Display" in out


def test_main_current():
    """--current 应输出当前配置。"""
    out, _ = _run("--current")
    assert len(out) > 0


def test_main_dry_run():
    """--dry-run 应输出 dry-run 消息。"""
    out, _ = _run("--output", "DISPLAY1", "--mode", "1920x1080", "--dry-run")
    assert "dry" in out.lower() or "Dry" in out


def test_main_dryrun_alias():
    """--dryrun 别名应正常。"""
    out, _ = _run("-o", "DISPLAY1", "--mode", "1920x1080", "--dryrun")
    assert "dry" in out.lower() or "Dry" in out


def test_main_invalid_output():
    """无效显示器名应输出错误。"""
    out, err = _run("--output", "NONEXISTENT", "--off")
    combined = out + err
    assert "未找到" in combined or "错误" in combined or "Error" in combined or "not found" in combined.lower()


def test_main_listproviders():
    """--listproviders 应列出 GPU。"""
    out, _ = _run("--listproviders")
    assert len(out) > 0


def test_main_listmonitors():
    """--listmonitors 应列出显示器。"""
    out, _ = _run("--listmonitors")
    assert len(out) > 0


def test_main_verbose():
    """--verbose 应输出调试日志。"""
    import logging

    logging.getLogger("winrandr").setLevel(logging.DEBUG)
    out, _ = _run("--verbose")
    assert len(out) > 0


def test_main_version():
    """--version 应输出版本号。"""
    from winrandr import __version__

    out, _ = _run("--version")
    assert __version__ in out


def test_main_prop():
    """--prop 应输出扩展属性。"""
    out, _ = _run("--output", "DISPLAY1", "--prop")
    assert len(out) > 0


def test_main_json_output():
    """--json 应输出有效 JSON。"""
    import json

    out, _ = _run("--json")
    data = json.loads(out)
    assert isinstance(data, list)


def test_main_modes():
    """--mode 应输出可用模式。"""
    out, _ = _run("--output", "DISPLAY1", "--mode", "1920x1080", "--dry-run")
    assert len(out) > 0


def test_main_pos():
    """--pos 应处理位置参数。"""
    out, _ = _run("--output", "DISPLAY1", "--pos", "0x0", "--dry-run")
    assert len(out) > 0


def test_main_rotate():
    """--rotate 应处理旋转参数。"""
    out, _ = _run("--output", "DISPLAY1", "--rotate", "normal", "--dry-run")
    assert len(out) > 0


def test_main_primary():
    """--primary 应处理主屏参数。"""
    out, _ = _run("--output", "DISPLAY1", "--primary", "--dry-run")
    assert len(out) > 0


def test_main_off():
    """--off 应处理关闭参数。"""
    out, _ = _run("--output", "DISPLAY1", "--off", "--dry-run")
    assert len(out) > 0


def test_main_brightness():
    """--brightness 应处理亮度参数。"""
    out, _ = _run("--output", "DISPLAY1", "--brightness", "0.8", "--dry-run")
    assert len(out) > 0


def test_main_gamma():
    """--gamma 应处理伽马参数。"""
    out, _ = _run("--output", "DISPLAY1", "--gamma", "1.0:0.9:0.8", "--dry-run")
    assert len(out) > 0


def test_main_night_mode():
    """--night-mode 应处理夜览模式参数。"""
    out, _ = _run("--output", "DISPLAY1", "--night-mode", "light", "--dry-run")
    assert len(out) > 0


def test_main_no_output():
    """无 --output 时对 --off 应报错。"""
    out, err = _run("--off")
    combined = out + err
    assert "需要 --output" in combined or "output" in combined.lower() or "错误" in combined
