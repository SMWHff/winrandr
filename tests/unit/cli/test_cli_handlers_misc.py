"""Tests for CLI handler functions — listmodes and identify."""

from argparse import Namespace
from unittest.mock import patch
import pytest
from winrandr.cli.handlers import _handle_listmodes, _handle_identify

DN = r"\\.\DISPLAY1"


def _ns(**kwargs) -> Namespace:
    defaults = dict(dry_run=True, output="DISPLAY1",
                    mode=None, pos=None, rate=None, rotate=None,
                    primary=None, preferred=None, off=None,
                    brightness=None, reflect=None, gamma=None,
                    identify=False,
                    left_of=None, right_of=None, above=None, below=None, same_as=None)
    defaults.update(kwargs)
    return Namespace(**defaults)


# --- _handle_listmodes ---

def test_handle_listmodes_basic():
    """基本 listmodes 输出。"""
    from winrandr.models import DisplayMode, DisplayInfo
    dm = DisplayMode(1920, 1080, 60.0, True, True)
    disp = DisplayInfo(name=r"\\.\DISPLAY1", friendly_name="Fake",
                       connected=True, width=1920, height=1080,
                       refresh_rate=60.0, position_x=0, position_y=0,
                       is_primary=True, rotation=0, width_mm=527, height_mm=296,
                       modes=[dm])
    with patch("winrandr.cli.handlers.list_displays", return_value=[disp]):
        _handle_listmodes(_ns(), as_json=False)


def test_handle_listmodes_json():
    """listmodes --json 输出。"""
    from winrandr.models import DisplayMode, DisplayInfo
    dm = DisplayMode(1920, 1080, 60.0, True, True)
    disp = DisplayInfo(name=r"\\.\DISPLAY1", friendly_name="Fake",
                       connected=True, width=1920, height=1080,
                       refresh_rate=60.0, position_x=0, position_y=0,
                       is_primary=True, rotation=0, width_mm=527, height_mm=296,
                       modes=[dm])
    with patch("winrandr.cli.handlers.list_displays", return_value=[disp]):
        _handle_listmodes(_ns(), as_json=True)


def test_handle_listmodes_no_displays():
    """无显示器时返回提示不报错。"""
    with patch("winrandr.cli.handlers.list_displays", return_value=[]):
        _handle_listmodes(_ns(), as_json=False)


# --- _handle_identify ---

def test_identify_dry_run():
    """dry-run 下只输出消息，不调用 API。"""
    with patch("winrandr.cli.handlers.identify_display", return_value=True) as mock_fn:
        _handle_identify(_ns(identify=True, dry_run=True), DN)
        assert mock_fn.called is False


def test_identify_non_dry_run():
    """非 dry-run 模式调用 identify_display API。"""
    with patch("winrandr.cli.handlers.identify_display", return_value=True) as mock_fn:
        _handle_identify(_ns(identify=True, dry_run=False), DN)
        assert mock_fn.called is True


def test_identify_api_failure():
    """API 失败时退出。"""
    with patch("winrandr.cli.handlers.identify_display", return_value=False):
        with pytest.raises(SystemExit):
            _handle_identify(_ns(identify=True, dry_run=False), DN)
