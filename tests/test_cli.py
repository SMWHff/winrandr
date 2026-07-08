"""Tests for CLI utility functions (_fail, _normalize_name, _apply_aliases, _is_mod_op)."""

import argparse
import pytest
from winrandr.cli import _normalize_name, _fail, _apply_aliases, _is_mod_op, _check_relative_mutex, _MOD_OP_ATTRS


def test_normalize_name():
    assert _normalize_name("DISPLAY1") == r"\\.\DISPLAY1"
    assert _normalize_name(r"\\.\DISPLAY1") == r"\\.\DISPLAY1"
    assert _normalize_name("1") == r"\\.\DISPLAY1"
    assert _normalize_name("display1") == r"\\.\DISPLAY1"


def test_normalize_name_edge_cases():
    assert _normalize_name("DISPLAY1") == r"\\.\DISPLAY1"
    assert _normalize_name(r"\\.\DISPLAY1") == r"\\.\DISPLAY1"
    assert _normalize_name("WinDisc") == "WinDisc"


def test_normalize_name_various():
    assert _normalize_name("\\\\.\\DISPLAY1") == r"\\.\DISPLAY1"
    assert _normalize_name("display1") == r"\\.\DISPLAY1"
    assert _normalize_name("1") == r"\\.\DISPLAY1"
    assert _normalize_name("2") == r"\\.\DISPLAY2"
    assert _normalize_name("WinDisc") == "WinDisc"


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
    defaults = dict(mode=None, size=None, rotate=None, orientation=None,
                    primary=False, preferred=False, off=False, auto=False,
                    brightness=None, reflect=None, gamma=None, noprimary=False,
                    pos=None, left_of=None, right_of=None, above=None,
                    below=None, same_as=None,
                    listmodes=False, listproviders=False, listmonitors=False,
                    listactivemonitors=False, x=False, y=False,
                    query=False, current=False, prop=False, dry_run=False,
                    verbose=False, json=False, screen=None, nograb=False,
                    output=None, rate=None)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_apply_aliases_size_to_mode():
    """--size 应转换为 --mode。"""
    ns = _ns(size="1920x1080")
    _apply_aliases(ns)
    assert ns.mode == "1920x1080"


def test_apply_aliases_orientation_to_rotate():
    """--orientation 应转换为 --rotate。"""
    cases = {"0": "normal", "normal": "normal", "2": "inverted",
             "inverted": "inverted", "3": "left", "left": "left",
             "right": "right"}
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


@pytest.mark.parametrize("attr,val", [
    ("left_of", "DISPLAY2"), ("right_of", "DISPLAY2"),
    ("above", "DISPLAY2"), ("below", "DISPLAY2"), ("same_as", "DISPLAY2"),
])
def test_check_relative_mutex_each(attr, val):
    """每个单相对定位参数单独使用不报错。"""
    _check_relative_mutex(_ns(**{attr: val}))


def test_mod_op_attrs_consistency():
    """_MOD_OP_ATTRS 中每个属性在默认 Namespace 中为 None/False。"""
    ns = _ns()
    for attr in _MOD_OP_ATTRS:
        assert not getattr(ns, attr, None), f"{attr} 应默认为空"


# --- main() 集成测试（mock Win32 API）---

from unittest.mock import patch
from winrandr.models import DisplayInfo, DisplayMode
from winrandr.cli import main as cli_main


def _fake_display(name="DISPLAY1", connected=True, **kw):
    """创建假 DisplayInfo 用于测试。"""
    defaults = dict(name=rf"\\.\{name}", friendly_name="Fake Monitor",
                    connected=connected, width=1920, height=1080,
                    refresh_rate=60.0, position_x=0, position_y=0,
                    is_primary=True, rotation=0, width_mm=527, height_mm=296,
                    modes=[DisplayMode(1920, 1080, 60.0, True, True)])
    defaults.update(kw)
    return DisplayInfo(**defaults)


def test_main_query_show_displays():
    """main() 查询模式应打印显示器信息。"""
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("sys.argv", ["winrandr"]):
            cli_main()  # 不应抛出异常


def test_main_dry_run_set_resolution():
    """dry-run 模式不实际修改 set_resolution 不被调用。"""
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.set_resolution", return_value=True) as mock_set:
            with patch("sys.argv", ["winrandr", "--output", "DISPLAY1", "--mode", "1920x1080", "--dry-run"]):
                cli_main()
            assert mock_set.called is False


def test_main_dry_run_set_position():
    """dry-run 模式设置位置不应调用 set_position。"""
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.set_position", return_value=True) as mock_set:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "-p", "1920x0", "--dry-run"]):
                cli_main()
            assert mock_set.called is False


def test_main_invalid_output():
    """无效 --output 应报错退出。"""
    with patch("winrandr.cli.list_displays", return_value=[_fake_display("DISPLAY1")]):
        with patch("winrandr.cli.list_providers", return_value=[]):
            with pytest.raises(SystemExit):
                with patch("sys.argv", ["winrandr", "--output", "DISPLAY99", "--mode", "1920x1080"]):
                    cli_main()


def test_main_noprimary_standalone():
    """--noprimary 单独使用 dry-run 不调用 set_noprimary。"""
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.set_noprimary", return_value=True) as mock_set:
            with patch("sys.argv", ["winrandr", "--noprimary", "--dry-run"]):
                cli_main()
            assert mock_set.called is False


def test_main_noprimary_with_mode():
    """--noprimary 与 --mode 一起使用时继续执行 mode 操作。"""
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.set_noprimary", return_value=True):
            with patch("winrandr.cli.set_resolution", return_value=True) as mock_set:
                with patch("sys.argv", ["winrandr", "--noprimary", "-o", "DISPLAY1", "-m", "1920x1080", "--dry-run"]):
                    cli_main()
                assert mock_set.called is False
