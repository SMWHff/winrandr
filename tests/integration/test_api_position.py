"""Tests for public API function set_position_relative."""

from unittest.mock import patch

from winrandr.api import set_position_relative
from winrandr.models import DisplayInfo


def _disp(name="DISPLAY1", x=0, y=0, w=1920, h=1080):
    return DisplayInfo(
        name=rf"\\.\{name}",
        friendly_name="",
        connected=True,
        width=w,
        height=h,
        refresh_rate=60.0,
        position_x=x,
        position_y=y,
        is_primary=False,
        rotation=0,
        width_mm=0,
        height_mm=0,
        modes=[],
    )


def test_rel_position_target_not_found():
    with patch("winrandr.api.list_displays", return_value=[]):
        assert set_position_relative(r"\\.\DISPLAY1", r"\\.\DISPLAY2", "right-of") is False


def test_rel_position_ref_not_found():
    with patch("winrandr.api.list_displays", return_value=[_disp("DISPLAY1")]):
        assert set_position_relative(r"\\.\DISPLAY1", r"\\.\DISPLAY2", "right-of") is False


def test_rel_position_right_of():
    with patch("winrandr.api.set_position", return_value=True) as mock_sp:
        with patch("winrandr.api.list_displays", return_value=[_disp("DISPLAY1"), _disp("DISPLAY2", x=1920)]):
            assert set_position_relative(r"\\.\DISPLAY1", r"\\.\DISPLAY2", "right-of") is True
            mock_sp.assert_called_once_with(r"\\.\DISPLAY1", 1920 + 1920, 0)


def test_rel_position_left_of():
    with patch("winrandr.api.set_position", return_value=True) as mock_sp:
        with patch("winrandr.api.list_displays", return_value=[_disp("DISPLAY1", w=1920), _disp("DISPLAY2", x=1920)]):
            assert set_position_relative(r"\\.\DISPLAY1", r"\\.\DISPLAY2", "left-of") is True
            mock_sp.assert_called_once_with(r"\\.\DISPLAY1", 1920 - 1920, 0)


def test_rel_position_below():
    with patch("winrandr.api.set_position", return_value=True) as mock_sp:
        with patch("winrandr.api.list_displays", return_value=[_disp("DISPLAY1"), _disp("DISPLAY2", x=0, y=1080)]):
            assert set_position_relative(r"\\.\DISPLAY1", r"\\.\DISPLAY2", "below") is True
            mock_sp.assert_called_once_with(r"\\.\DISPLAY1", 0, 1080 + 1080)


def test_rel_position_above():
    with patch("winrandr.api.set_position", return_value=True) as mock_sp:
        displays = [_disp("DISPLAY1", h=1080), _disp("DISPLAY2", x=0, y=1080)]
        with patch("winrandr.api.list_displays", return_value=displays):
            assert set_position_relative(r"\\.\DISPLAY1", r"\\.\DISPLAY2", "above") is True
            mock_sp.assert_called_once_with(r"\\.\DISPLAY1", 0, 1080 - 1080)


def test_rel_position_same_as():
    with patch("winrandr.api.set_position", return_value=True) as mock_sp:
        with patch("winrandr.api.list_displays", return_value=[_disp("DISPLAY1"), _disp("DISPLAY2", x=1920, y=100)]):
            assert set_position_relative(r"\\.\DISPLAY1", r"\\.\DISPLAY2", "same-as") is True
            mock_sp.assert_called_once_with(r"\\.\DISPLAY1", 1920, 100)


def test_rel_position_disconnected_ref_skipped():
    """断开连接的参考显示器应忽略，导致未找到。"""
    d_conn = _disp("DISPLAY1")
    d_disc = _disp("DISPLAY2", x=1920)
    d_disc.connected = False
    with patch("winrandr.api.set_position", return_value=True) as mock_sp:
        with patch("winrandr.api.list_displays", return_value=[d_conn, d_disc]):
            assert set_position_relative(r"\\.\DISPLAY1", r"\\.\DISPLAY2", "right-of") is False
            assert mock_sp.called is False


def test_rel_position_short_name():
    """不带 \\\\.\\ 前缀的短名也应匹配。"""
    with patch("winrandr.api.set_position", return_value=True) as mock_sp:
        with patch("winrandr.api.list_displays", return_value=[_disp("DISPLAY1"), _disp("DISPLAY2", x=1920)]):
            assert set_position_relative("DISPLAY1", "DISPLAY2", "right-of") is True
            mock_sp.assert_called_once()
            args = mock_sp.call_args[0]
            assert "DISPLAY1" in args[0]
            assert "DISPLAY2" not in args[0]


def test_rel_position_invalid_relation():
    """无效的相对位置关系应返回 False。"""
    with patch("winrandr.api.list_displays", return_value=[_disp("DISPLAY1"), _disp("DISPLAY2", x=1920)]):
        assert set_position_relative(r"\\.\DISPLAY1", r"\\.\DISPLAY2", "invalid") is False
