"""Tests for win32/utils.py get_connector_type function."""

import ctypes
from ctypes import byref, sizeof
from unittest.mock import patch

from winrandr.win32.constants import DISPLAYCONFIG_DEVICE_INFO_GET_TARGET_NAME
from winrandr.win32.structures import (
    DISPLAYCONFIG_PATH_INFO,
    DISPLAYCONFIG_TARGET_DEVICE_NAME,
)
from winrandr.win32.utils import get_connector_type


def _make_fake_api(target_flags: int):
    """创建模拟 _DisplayConfigGetDeviceInfo 的工厂函数，返回指定 targetFlags。"""

    def fake(header_ptr):
        tname = DISPLAYCONFIG_TARGET_DEVICE_NAME()
        tname.header.type = DISPLAYCONFIG_DEVICE_INFO_GET_TARGET_NAME
        tname.header.size = sizeof(DISPLAYCONFIG_TARGET_DEVICE_NAME)
        tname.targetFlags = target_flags
        ctypes.memmove(header_ptr, byref(tname), sizeof(DISPLAYCONFIG_TARGET_DEVICE_NAME))
        return 0

    return fake


def _make_path():
    return (DISPLAYCONFIG_PATH_INFO * 1)()[0]


def test_connector_type_hdmi():
    path = _make_path()
    with patch("winrandr.win32.utils._DisplayConfigGetDeviceInfo", side_effect=_make_fake_api(0x08)):
        assert get_connector_type(path) == "HDMI"


def test_connector_type_dp():
    path = _make_path()
    with patch("winrandr.win32.utils._DisplayConfigGetDeviceInfo", side_effect=_make_fake_api(0x10)):
        assert get_connector_type(path) == "DisplayPort"


def test_connector_type_usb_c():
    path = _make_path()
    with patch("winrandr.win32.utils._DisplayConfigGetDeviceInfo", side_effect=_make_fake_api(0x80)):
        assert get_connector_type(path) == "USB-C"


def test_connector_type_vga():
    path = _make_path()
    with patch("winrandr.win32.utils._DisplayConfigGetDeviceInfo", side_effect=_make_fake_api(0x04)):
        assert get_connector_type(path) == "VGA"


def test_connector_type_dvi():
    path = _make_path()
    with patch("winrandr.win32.utils._DisplayConfigGetDeviceInfo", side_effect=_make_fake_api(0x02)):
        assert get_connector_type(path) == "DVI"


def test_connector_type_unknown():
    """未知的标志位应返回空字符串。"""
    path = _make_path()
    with patch("winrandr.win32.utils._DisplayConfigGetDeviceInfo", side_effect=_make_fake_api(0x40)):
        assert get_connector_type(path) == ""


def test_connector_type_api_failure():
    """API 调用失败时返回空字符串。"""
    path = _make_path()
    with patch("winrandr.win32.utils._DisplayConfigGetDeviceInfo", return_value=1):
        assert get_connector_type(path) == ""
