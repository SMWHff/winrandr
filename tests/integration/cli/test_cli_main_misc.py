"""Tests for main() CLI entry point (真实硬件)。"""

import subprocess
import sys as _sys

from winrandr.cli import main as cli_main


def _run(*args):
    import io

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


def test_main_listproviders():
    """--listproviders 应输出 GPU 信息。"""
    out, _ = _run("--listproviders")
    assert len(out) > 0


def test_main_listproviders_json():
    """--listproviders --json 应输出 JSON。"""
    import json

    out, _ = _run("--listproviders", "--json")
    data = json.loads(out)
    assert isinstance(data, list)


def test_main_listmonitors():
    """--listmonitors 应输出显示器列表。"""
    out, _ = _run("--listmonitors")
    assert len(out) > 0


def test_entry_point_version():
    """python -m winrandr --version 应正常退出。"""
    result = subprocess.run(
        [_sys.executable, "-m", "winrandr", "--version"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert "winrandr" in result.stdout


def test_entry_point_version_v():
    """python -m winrandr -v 应显示版本。"""
    result = subprocess.run(
        [_sys.executable, "-m", "winrandr", "-v"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert "winrandr" in result.stdout


def test_main_verbose():
    """--verbose 应不崩溃。"""
    out, _ = _run("--verbose")
    assert isinstance(out, str)


def test_main_listproviders_empty():
    """--listproviders 正常执行。"""
    out, _ = _run("--listproviders")
    assert isinstance(out, str)


def test_main_listmonitors_empty():
    """--listmonitors 正常执行。"""
    out, _ = _run("--listmonitors")
    assert isinstance(out, str)
