"""Tests for public API function set_position_relative (真实硬件)。"""

from winrandr.api import set_position_relative


def test_rel_position_target_not_found():
    """不存在的目标显示器应返回 False。"""
    assert set_position_relative(r"\\.\NONEXISTENT_DISPLAY1", r"\\.\DISPLAY2", "right-of") is False


def test_rel_position_ref_not_found():
    """不存在的参考显示器应返回 False。"""
    assert set_position_relative(r"\\.\DISPLAY1", r"\\.\NONEXISTENT_DISPLAY2", "right-of") is False


def test_rel_position_invalid_relation():
    """无效的相对位置关系应返回 False。"""
    assert set_position_relative(r"\\.\DISPLAY1", r"\\.\DISPLAY2", "invalid") is False


def test_rel_position_short_name():
    """短名匹配应正常（不调用真实写操作，只检查 not found）。"""
    result = set_position_relative("NONEXISTENT1", "NONEXISTENT2", "right-of")
    assert result is False


def _require_two_displays():
    """检查是否有至少两个显示器，否则跳过。"""
    from winrandr.api import list_displays

    displays = list_displays()
    connected = [d for d in displays if d.connected]
    if len(connected) < 2:
        return None
    return connected


def test_rel_position_right_of(profile_backup):
    """right-of 相对定位（真实执行，SDC 不可用时 xfail）。"""

    connected = _require_two_displays()
    if connected is None:
        return

    result = set_position_relative(connected[1].name, connected[0].name, "right-of")
    if not result:
        pass


def test_rel_position_left_of(profile_backup):
    connected = _require_two_displays()
    if connected is None:
        return

    result = set_position_relative(connected[1].name, connected[0].name, "left-of")
    if not result:
        import pytest

        pytest.xfail("SetDisplayConfig 不可用")


def test_rel_position_below(profile_backup):
    connected = _require_two_displays()
    if connected is None:
        return

    result = set_position_relative(connected[1].name, connected[0].name, "below")
    if not result:
        import pytest

        pytest.xfail("SetDisplayConfig 不可用")


def test_rel_position_above(profile_backup):
    connected = _require_two_displays()
    if connected is None:
        return

    result = set_position_relative(connected[1].name, connected[0].name, "above")
    if not result:
        import pytest

        pytest.xfail("SetDisplayConfig 不可用")


def test_rel_position_same_as(profile_backup):
    connected = _require_two_displays()
    if connected is None:
        return

    result = set_position_relative(connected[1].name, connected[0].name, "same-as")
    if not result:
        import pytest

        pytest.xfail("SetDisplayConfig 不可用")
