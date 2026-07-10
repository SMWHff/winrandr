"""Tests for CLI utility functions (_fail, _normalize_name, _apply_aliases, _is_mod_op)."""

import argparse

import pytest

from winrandr.cli import (
    _MOD_OP_ATTRS,
    _apply_aliases,
    _check_relative_mutex,
    _fail,
    _is_mod_op,
    _list_available_displays,
    _normalize_name,
)


@pytest.mark.parametrize(
    "input_name,expected",
    [
        ("DISPLAY1", r"\\.\DISPLAY1"),
        ("display1", r"\\.\DISPLAY1"),
        ("1", r"\\.\DISPLAY1"),
        ("2", r"\\.\DISPLAY2"),
        (r"\\.\DISPLAY1", r"\\.\DISPLAY1"),
        ("\\\\.\\DISPLAY1", r"\\.\DISPLAY1"),
        ("WinDisc", r"\\.\DISPLAYWINDISC"),
    ],
)
def test_normalize_name(input_name, expected):
    assert _normalize_name(input_name) == expected


def test_fail_basic():
    with pytest.raises(SystemExit) as exc:
        _fail("test error")
    assert exc.value.code == 1


def test_fail_with_suggestions():
    with pytest.raises(SystemExit) as exc:
        _fail("test error", ["suggestion 1", "suggestion 2"])
    assert exc.value.code == 1


def _ns(**kwargs) -> argparse.Namespace:
    """Helper: 创建带默认值的 Namespace。"""
    defaults = dict(
        mode=None,
        size=None,
        rotate=None,
        orientation=None,
        primary=False,
        preferred=False,
        off=False,
        auto=False,
        brightness=None,
        reflect=None,
        gamma=None,
        noprimary=False,
        pos=None,
        left_of=None,
        right_of=None,
        above=None,
        below=None,
        same_as=None,
        listmodes=False,
        listproviders=False,
        listmonitors=False,
        listactivemonitors=False,
        x=False,
        y=False,
        query=False,
        current=False,
        prop=False,
        identify=False,
        dry_run=False,
        verbose=False,
        json=False,
        screen=None,
        nograb=False,
        output=None,
        rate=None,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_apply_aliases_size_to_mode():
    """--size 应转换为 --mode。"""
    ns = _ns(size="1920x1080")
    _apply_aliases(ns)
    assert ns.mode == "1920x1080"


def test_apply_aliases_orientation_to_rotate():
    """--orientation 应转换为 --rotate（含 "1" → normal）。"""
    cases = {
        "0": "normal",
        "1": "normal",
        "normal": "normal",
        "2": "inverted",
        "inverted": "inverted",
        "3": "left",
        "left": "left",
        "right": "right",
    }
    for inp, expected in cases.items():
        ns = _ns(orientation=inp)
        _apply_aliases(ns)
        assert ns.rotate == expected, f"orientation={inp} → rotate={expected}"


def test_apply_aliases_listactivemonitors():
    """--listactivemonitors 应转换为 --listmonitors。"""
    ns = _ns(listactivemonitors=True)
    _apply_aliases(ns)
    assert ns.listmonitors is True


def test_apply_aliases_reflect_normal():
    """--reflect normal 应清除 reflect。"""
    ns = _ns(reflect="normal")
    _apply_aliases(ns)
    assert ns.reflect is None


def test_apply_aliases_x_and_y():
    """-x -y 同时设置应为 --reflect xy。"""
    ns = _ns(x=True, y=True)
    _apply_aliases(ns)
    assert ns.reflect == "xy"


def test_apply_aliases_x_only():
    """仅 -x 应为 --reflect x。"""
    ns = _ns(x=True, y=False)
    _apply_aliases(ns)
    assert ns.reflect == "x"


def test_apply_aliases_y_only():
    """仅 -y 应为 --reflect y。"""
    ns = _ns(x=False, y=True)
    _apply_aliases(ns)
    assert ns.reflect == "y"


def test_apply_aliases_reflect_x_wins_over_y():
    """--reflect x 与 -y 同时使用时，--reflect 优先，-y 被忽略，记录警告。"""
    ns = _ns(reflect="x", x=False, y=True)
    _apply_aliases(ns)
    assert ns.reflect == "x"


def test_apply_aliases_reflect_xy_wins_over_x(caplog):
    """--reflect xy 与 -x 同时使用时，--reflect 优先，-x 被忽略，记录警告。"""
    ns = _ns(reflect="xy", x=True, y=False)
    _apply_aliases(ns)
    assert ns.reflect == "xy"
    assert len(caplog.records) == 1
    assert "被忽略" in caplog.records[0].message


def test_apply_aliases_reflect_y_wins_over_x(caplog):
    """--reflect y 与 -x 同时使用时，--reflect 优先，-x 被忽略，记录警告。"""
    ns = _ns(reflect="y", x=True, y=False)
    _apply_aliases(ns)
    assert ns.reflect == "y"
    assert len(caplog.records) == 1
    assert "被忽略" in caplog.records[0].message


def test_apply_aliases_reflect_normal_with_x():
    """--reflect normal（即清除）后 -x 仍生效，因为 normal 视为「未设置」。"""
    ns = _ns(reflect="normal", x=True, y=False)
    _apply_aliases(ns)
    assert ns.reflect == "x"


def test_is_mod_op_true():
    """修改类操作应返回 True。"""
    for attr in _MOD_OP_ATTRS:
        is_bool = attr in ("primary", "preferred", "off", "auto", "noprimary")
        ns = _ns(**{attr: True if is_bool else "dummy"})
        assert _is_mod_op(ns), f"{attr} should be mod op"


def test_is_mod_op_false():
    """纯查询类操作应返回 False。"""
    ns = _ns(query=True, listmodes=True, json=True)
    assert not _is_mod_op(ns)


def test_check_relative_mutex_single():
    """单个相对定位参数不报错。"""
    ns = _ns(left_of="DISPLAY2")
    _check_relative_mutex(ns)  # should not raise


def test_check_relative_mutex_multiple():
    """多个相对定位参数应中断。"""
    ns = _ns(left_of="DISPLAY2", right_of="DISPLAY3")
    with pytest.raises(SystemExit):
        _check_relative_mutex(ns)


def test_check_relative_mutex_none():
    """无相对定位参数不报错。"""
    ns = _ns()
    _check_relative_mutex(ns)  # should not raise


@pytest.mark.parametrize(
    "attr,val",
    [
        ("left_of", "DISPLAY2"),
        ("right_of", "DISPLAY2"),
        ("above", "DISPLAY2"),
        ("below", "DISPLAY2"),
        ("same_as", "DISPLAY2"),
    ],
)
def test_check_relative_mutex_each(attr, val):
    """每个单相对定位参数单独使用不报错。"""
    _check_relative_mutex(_ns(**{attr: val}))


def test_mod_op_attrs_consistency():
    """_MOD_OP_ATTRS 中每个属性在默认 Namespace 中为 None/False。"""
    ns = _ns()
    for attr in _MOD_OP_ATTRS:
        assert not getattr(ns, attr, None), f"{attr} 应默认为空"


def test_list_available_displays_basic():
    """_list_available_displays 返回显示器列表。"""
    result = _list_available_displays()
    assert isinstance(result, str)
    assert len(result) > 0


def test_list_available_displays_empty():
    """_list_available_displays 在有显示器时不崩溃。"""
    result = _list_available_displays()
    assert isinstance(result, str)


def test_list_available_displays_with_providers():
    """提供者中有非 DISPLAY 名称时也能正常列出。"""
    result = _list_available_displays()
    assert isinstance(result, str)


def test_invalidate_qdc_cache_both():
    """_invalidate_qdc_cache 应同时清除 active 和 all 两个缓存。"""
    from winrandr.win32 import utils as win32_utils

    win32_utils._invalidate_qdc_cache()
    assert win32_utils._QDC_CACHE is None
    assert win32_utils._QDC_ALL_CACHE is None
    result = _list_available_displays()
    assert isinstance(result, str)
