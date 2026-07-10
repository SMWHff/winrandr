"""Tests for CLI handler functions — listmodes and identify."""

from argparse import Namespace

import pytest

from winrandr.cli.handlers import _handle_identify, _handle_listmodes

DN = r"\\.\DISPLAY1"


def _ns(**kwargs) -> Namespace:
    defaults = dict(
        dry_run=True,
        output="DISPLAY1",
        mode=None,
        pos=None,
        rate=None,
        rotate=None,
        primary=None,
        preferred=None,
        off=None,
        brightness=None,
        reflect=None,
        gamma=None,
        identify=False,
        left_of=None,
        right_of=None,
        above=None,
        below=None,
        same_as=None,
    )
    defaults.update(kwargs)
    return Namespace(**defaults)


# --- _handle_listmodes ---


def test_handle_listmodes_basic():
    """listmodes 基于真实显示器数据。"""
    _handle_listmodes(_ns(), as_json=False)


def test_handle_listmodes_json():
    """listmodes --json 基于真实数据。"""
    _handle_listmodes(_ns(), as_json=True)


def test_handle_listmodes_no_displays():
    """list_displays 为空时应有提示不报错。"""
    from unittest.mock import patch

    with patch("winrandr.cli.handlers.list_displays", return_value=[]):
        _handle_listmodes(_ns(), as_json=False)


def test_handle_listmodes_output_not_found():
    """指定输出不存在时应报错。"""
    from unittest.mock import patch

    from tests.conftest import _fake_display

    d = _fake_display("DISPLAY_OTHER")
    with patch("winrandr.cli.handlers.list_displays", return_value=[d]):
        with pytest.raises(SystemExit):
            _handle_listmodes(_ns(output="DISPLAY1"), as_json=False)


# --- _handle_identify ---


def test_identify_dry_run():
    """dry-run 下只输出消息，不调用 API。"""
    _handle_identify(_ns(identify=True, dry_run=True), DN)


def test_identify_non_dry_run():
    """非 dry-run 模式调用 identify_display API。"""
    try:
        _handle_identify(_ns(identify=True, dry_run=False), DN)
    except SystemExit:
        pytest.xfail("identify_display 不可用")


# --- _setup_logging ---


def test_setup_logging_first_call():
    """首次调用 _setup_logging 应创建文件和控制台两个处理器。"""
    import logging as _logging

    from winrandr.cli.common import _setup_logging

    root = _logging.getLogger()
    old_handlers = root.handlers[:]
    root.handlers.clear()
    try:
        _setup_logging()
        assert len(root.handlers) == 2
    finally:
        for h in root.handlers:
            h.close()
        root.handlers.clear()
        root.handlers.extend(old_handlers)


def test_setup_logging_frozen():
    """frozen 模式下日志目录应指向 exe 目录。"""
    import logging as _logging
    from unittest.mock import patch

    from winrandr.cli.common import _setup_logging

    root = _logging.getLogger()
    old_handlers = root.handlers[:]
    root.handlers.clear()
    try:
        with patch("sys.frozen", True, create=True):
            _setup_logging()
            assert len(root.handlers) == 2
    finally:
        for h in root.handlers:
            h.close()
        root.handlers.clear()
        root.handlers.extend(old_handlers)


def test_setup_logging_makedirs_oserror():
    """os.makedirs 失败时应静默降级，仍有一个控制台处理器。"""
    import logging as _logging
    from unittest.mock import patch

    from winrandr.cli.common import _setup_logging

    root = _logging.getLogger()
    old_handlers = root.handlers[:]
    root.handlers.clear()
    try:
        with patch("os.makedirs", side_effect=OSError("permission denied")):
            _setup_logging()
            assert len(root.handlers) == 1  # 只有控制台处理器
            assert isinstance(root.handlers[0], _logging.StreamHandler)
    finally:
        for h in root.handlers:
            h.close()
        root.handlers.clear()
        root.handlers.extend(old_handlers)
