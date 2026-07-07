"""测试 CLI 参数解析和工具函数。"""

import pytest

from winrandr.cli import _build_parser, _normalize_name
from winrandr.formatter import _short_name, _fmt_modes


def test_short_name():
    assert _short_name(r"\\.\DISPLAY1") == "DISPLAY1"
    assert _short_name("DISPLAY1") == "DISPLAY1"
    assert _short_name(r"\\.\DISPLAY2") == "DISPLAY2"


def test_normalize_name():
    assert _normalize_name("DISPLAY1") == r"\\.\DISPLAY1"
    assert _normalize_name(r"\\.\DISPLAY1") == r"\\.\DISPLAY1"
    assert _normalize_name("1") == r"\\.\DISPLAY1"
    assert _normalize_name("display1") == r"\\.\DISPLAY1"


def test_parser_basic():
    p = _build_parser()
    args = p.parse_args([])
    assert args.listmodes is False
    assert args.output is None
    assert args.mode is None
    assert args.rate is None
    assert args.json is False
    assert args.verbose is False


def test_parser_output_mode():
    p = _build_parser()
    args = p.parse_args(["--output", "DISPLAY1", "--mode", "1920x1080"])
    assert args.output == "DISPLAY1"
    assert args.mode == "1920x1080"


def test_parser_mode_with_rate():
    p = _build_parser()
    args = p.parse_args(["-o", "DISPLAY1", "-m", "1920x1080", "-r", "60"])
    assert args.output == "DISPLAY1"
    assert args.mode == "1920x1080"
    assert args.rate == 60.0


def test_parser_position():
    p = _build_parser()
    args = p.parse_args(["--output", "DISPLAY1", "--pos", "1920x0"])
    assert args.pos == "1920x0"


def test_parser_position_plus():
    p = _build_parser()
    args = p.parse_args(["-o", "DISPLAY1", "-p", "+1920+0"])
    assert args.pos == "+1920+0"


def test_parser_rotate():
    p = _build_parser()
    for rot in ["normal", "left", "right", "inverted"]:
        args = p.parse_args(["-o", "DISPLAY1", "--rotate", rot])
        assert args.rotate == rot


def test_parser_primary():
    p = _build_parser()
    args = p.parse_args(["-o", "DISPLAY1", "--primary"])
    assert args.primary is True


def test_parser_preferred():
    p = _build_parser()
    args = p.parse_args(["-o", "DISPLAY1", "--preferred"])
    assert args.preferred is True


def test_parser_off():
    p = _build_parser()
    args = p.parse_args(["-o", "DISPLAY1", "--off"])
    assert args.off is True


def test_parser_json():
    p = _build_parser()
    args = p.parse_args(["--json"])
    assert args.json is True


def test_parser_brightness():
    p = _build_parser()
    args = p.parse_args(["-o", "DISPLAY1", "--brightness", "0.8"])
    assert args.brightness == 0.8


def test_parser_reflect():
    p = _build_parser()
    for axis in ["x", "y", "xy"]:
        args = p.parse_args(["-o", "DISPLAY1", "--reflect", axis])
        assert args.reflect == axis


def test_parser_gamma():
    p = _build_parser()
    args = p.parse_args(["-o", "DISPLAY1", "--gamma", "1.0:0.9:0.8"])
    assert args.gamma == "1.0:0.9:0.8"


def test_parser_relative_mutual_exclusion():
    """验证相对定位参数互斥。"""
    p = _build_parser()
    with pytest.raises(SystemExit):
        p.parse_args(["-o", "DISPLAY1", "--left-of", "DISPLAY2", "--right-of", "DISPLAY3"])


def test_parser_verbose():
    p = _build_parser()
    args = p.parse_args(["-v"])
    assert args.verbose is True


def test_parser_listmodes():
    p = _build_parser()
    args = p.parse_args(["--listmodes"])
    assert args.listmodes is True


def test_parser_version():
    p = _build_parser()
    with pytest.raises(SystemExit):
        p.parse_args(["--version"])


def test_parser_short_opts():
    p = _build_parser()
    args = p.parse_args(["-o", "DISPLAY1", "-m", "1920x1080", "-r", "144", "-p", "0x0"])
    assert args.output == "DISPLAY1"
    assert args.mode == "1920x1080"
    assert args.rate == 144.0
    assert args.pos == "0x0"


def test_parser_position_negative():
    """负坐标使用 = 语法（argparse 将 -1920x0 视为参数名）。"""
    p = _build_parser()
    args = p.parse_args(["-o", "DISPLAY1", "--pos=-1920x0"])
    assert args.pos == "-1920x0"


def test_parser_position_negative_y():
    """Y 为负 +1920x-1080。"""
    p = _build_parser()
    args = p.parse_args(["-o", "DISPLAY1", "-p", "+1920x-1080"])
    assert args.pos == "+1920x-1080"


def test_fmt_modes_preferred_flag():
    """验证 + 标记始终在首选模式上，不受 has_cur 影响。"""
    from winrandr.models import DisplayMode
    from winrandr.formatter import _fmt_modes
    modes = [
        DisplayMode(1920, 1080, 60.0, is_current=True, is_preferred=False),
        DisplayMode(1920, 1080, 59.94, is_current=False, is_preferred=True),
    ]
    lines = []
    _fmt_modes(lines, modes)
    out = "\n".join(lines)
    assert "60.00*" in out, "当前模式应有 *"
    assert "59.94+" in out, "首选模式应有 +（即使非当前）"


def test_normalize_name_edge_cases():
    assert _normalize_name("DISPLAY1") == r"\\.\DISPLAY1"
    assert _normalize_name(r"\\.\DISPLAY1") == r"\\.\DISPLAY1"
    # 非标准名保持原样
    assert _normalize_name("WinDisc") == "WinDisc"


def test_parser_auto():
    p = _build_parser()
    args = p.parse_args(["-o", "DISPLAY1", "--auto"])
    assert args.auto is True


def test_parser_dry_run():
    p = _build_parser()
    args = p.parse_args(["-o", "DISPLAY1", "--mode", "1920x1080", "--dry-run"])
    assert args.dry_run is True
    assert args.mode == "1920x1080"
    assert args.output == "DISPLAY1"


def test_parser_listproviders():
    p = _build_parser()
    args = p.parse_args(["--listproviders"])
    assert args.listproviders is True


def test_parser_auto_dry_run():
    """--auto 与 --dry-run 同时使用。"""
    p = _build_parser()
    args = p.parse_args(["-o", "DISPLAY1", "--auto", "--dry-run"])
    assert args.auto is True
    assert args.dry_run is True


def test_parser_prop():
    p = _build_parser()
    args = p.parse_args(["--prop"])
    assert args.prop is True


def test_parser_prop_with_output():
    p = _build_parser()
    args = p.parse_args(["-o", "DISPLAY1", "--prop"])
    assert args.prop is True
    assert args.output == "DISPLAY1"
