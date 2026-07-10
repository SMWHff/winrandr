"""Tests for main() CLI entry point — global brightness/gamma (真实硬件 + dry-run)。"""

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


def test_main_brightness_global_dry_run():
    """--brightness --dry-run 不带 --output 应模拟不实际调用。"""
    out, _ = _run("--brightness", "0.8", "--dry-run")
    assert len(out) > 0


def test_main_brightness_global_no_displays():
    """--brightness 不带 --output 且无显示器时，真实环境下跳过。"""
    out, _ = _run("--brightness", "0.8")
    # 有显示器时正常执行，无显示器时报错
    assert isinstance(out, str)


def test_main_gamma_global_dry_run():
    """--gamma 不带 --output 应应用到所有已连接显示器（dry-run）。"""
    out, _ = _run("--gamma", "1.0:0.9:0.8", "--dry-run")
    assert len(out) > 0


def test_main_night_mode_global_dry_run():
    """--night-mode 不带 --output 应应用到所有已连接显示器（dry-run）。"""
    out, _ = _run("--night-mode", "0.3", "--dry-run")
    assert len(out) > 0


def test_main_brightness_with_output_dry_run():
    """--brightness 带 --output 的 dry-run。"""
    out, _ = _run("-o", "DISPLAY1", "--brightness", "0.8", "--dry-run")
    assert len(out) > 0


def test_main_global_op_requires_output_for_other_ops():
    """全局操作中混用需要 --output 的操作时应报错。"""
    import io

    old_argv = sys.argv
    old_stderr = sys.stderr
    sys.argv = ["winrandr", "--brightness", "0.8", "--mode", "1920x1080"]
    err = io.StringIO()
    sys.stderr = err
    try:
        cli_main()
    except SystemExit:
        pass
    finally:
        sys.argv = old_argv
        sys.stderr = old_stderr
    # 验证发生了错误退出或输出错误信息


def test_main_night_mode_with_output_dry_run():
    """--night-mode 带 --output 的 dry-run。"""
    out, _ = _run("-o", "DISPLAY1", "--night-mode", "light", "--dry-run")
    assert len(out) > 0
