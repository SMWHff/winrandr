"""Parser construction and argument parsing tests."""

import pytest

from winrandr.cli import _check_relative_mutex
from winrandr.cli.parser import build_parser


@pytest.mark.parametrize("args,attr", [
    (["--primary"], "primary"),
    (["--preferred"], "preferred"),
    (["--off"], "off"),
    (["--auto"], "auto"),
    (["--listmodes"], "listmodes"),
    (["--listproviders"], "listproviders"),
    (["--listmonitors"], "listmonitors"),
    (["--noprimary"], "noprimary"),
    (["--query"], "query"),
    (["-q"], "query"),
    (["--current"], "current"),
    (["--dryrun"], "dry_run"),
    (["--verbose"], "verbose"),
    (["--json"], "json"),
    (["--prop"], "prop"),
    (["--properties"], "prop"),
    (["--dry-run"], "dry_run"),
])
def test_parser_bool_flag(args, attr):
    p = build_parser()
    assert getattr(p.parse_args(args), attr) is True


def test_parser_basic():
    p = build_parser()
    args = p.parse_args([])
    for attr in ["listmodes", "output", "mode", "rate", "json", "verbose"]:
        assert getattr(args, attr) is False or getattr(args, attr) is None


def test_parser_version_with_v():
    """-v 应触发 version 并退出（同 --version）。"""
    p = build_parser()
    with pytest.raises(SystemExit, match="0"):
        p.parse_args(["-v"])


def test_parser_output_mode():
    p = build_parser()
    args = p.parse_args(["--output", "DISPLAY1", "--mode", "1920x1080"])
    assert args.output == "DISPLAY1" and args.mode == "1920x1080"


def test_parser_mode_with_rate():
    p = build_parser()
    args = p.parse_args(["-o", "DISPLAY1", "-m", "1920x1080", "-r", "60"])
    assert args.output == "DISPLAY1" and args.mode == "1920x1080" and args.rate == 60.0


def test_parser_short_opts():
    p = build_parser()
    args = p.parse_args(["-o", "DISPLAY1", "-m", "1920x1080", "-r", "144", "-p", "0x0"])
    assert args.output == "DISPLAY1" and args.mode == "1920x1080"
    assert args.rate == 144.0 and args.pos == "0x0"


def test_parser_position():
    p = build_parser()
    args = p.parse_args(["--output", "DISPLAY1", "--pos", "1920x0"])
    assert args.pos == "1920x0"


def test_parser_position_plus():
    p = build_parser()
    args = p.parse_args(["-o", "DISPLAY1", "-p", "+1920+0"])
    assert args.pos == "+1920+0"


def test_parser_position_negative():
    p = build_parser()
    args = p.parse_args(["-o", "DISPLAY1", "--pos=-1920x0"])
    assert args.pos == "-1920x0"


def test_parser_position_negative_y():
    p = build_parser()
    args = p.parse_args(["-o", "DISPLAY1", "-p", "+1920x-1080"])
    assert args.pos == "+1920x-1080"


def test_parser_rotate():
    p = build_parser()
    for rot in ["normal", "left", "right", "inverted"]:
        assert p.parse_args(["-o", "DISPLAY1", "--rotate", rot]).rotate == rot


def test_parser_reflect():
    p = build_parser()
    for axis in ["x", "y", "xy"]:
        assert p.parse_args(["-o", "DISPLAY1", "--reflect", axis]).reflect == axis


def test_parser_brightness():
    p = build_parser()
    assert p.parse_args(["-o", "DISPLAY1", "--brightness", "0.8"]).brightness == 0.8


def test_parser_gamma():
    p = build_parser()
    assert p.parse_args(["-o", "DISPLAY1", "--gamma", "1.0:0.9:0.8"]).gamma == "1.0:0.9:0.8"


def test_parser_relative_mutual_exclusion():
    """相对定位互斥校验由 _check_relative_mutex 在 main() 中执行。"""
    p = build_parser()
    args = p.parse_args(["-o", "DISPLAY1", "--left-of", "DISPLAY2", "--right-of", "DISPLAY3"])
    with pytest.raises(SystemExit):
        _check_relative_mutex(args)


def test_parser_version():
    p = build_parser()
    with pytest.raises(SystemExit):
        p.parse_args(["--version"])


def test_parser_dry_run():
    p = build_parser()
    args = p.parse_args(["-o", "DISPLAY1", "--mode", "1920x1080", "--dry-run"])
    assert args.dry_run and args.mode == "1920x1080" and args.output == "DISPLAY1"


def test_parser_auto_dry_run():
    p = build_parser()
    args = p.parse_args(["-o", "DISPLAY1", "--auto", "--dry-run"])
    assert args.auto and args.dry_run


def test_parser_size():
    p = build_parser()
    assert p.parse_args(["-s", "1920x1080", "-o", "DISPLAY1"]).size == "1920x1080"


def test_parser_size_long():
    p = build_parser()
    assert p.parse_args(["--size", "1920x1080", "-o", "DISPLAY1"]).size == "1920x1080"


def test_parser_orientation():
    p = build_parser()
    args = p.parse_args(["-o", "DISPLAY1", "--orientation", "left"])
    assert args.orientation == "left"


def test_parser_orientation_numeric():
    p = build_parser()
    assert p.parse_args(["-o", "DISPLAY1", "--orientation", "0"]).orientation == "0"


def test_parser_reflect_normal():
    p = build_parser()
    assert p.parse_args(["-o", "DISPLAY1", "--reflect", "normal"]).reflect == "normal"


def test_parser_reflect_x():
    p = build_parser()
    assert p.parse_args(["-x", "-o", "DISPLAY1"]).x is True


def test_parser_reflect_y():
    p = build_parser()
    assert p.parse_args(["-y", "-o", "DISPLAY1"]).y is True


def test_parser_reflect_xy_flags():
    p = build_parser()
    args = p.parse_args(["-x", "-y", "-o", "DISPLAY1"])
    assert args.x and args.y


def test_parser_listmodes_json():
    p = build_parser()
    args = p.parse_args(["--listmodes", "--json"])
    assert args.listmodes and args.json


def test_parser_listmodes_with_output():
    p = build_parser()
    args = p.parse_args(["--listmodes", "-o", "DISPLAY1"])
    assert args.listmodes and args.output == "DISPLAY1"


def test_parser_prop_with_output():
    p = build_parser()
    args = p.parse_args(["-o", "DISPLAY1", "--prop"])
    assert args.prop and args.output == "DISPLAY1"


def test_parser_brightness_warn_low():
    p = build_parser()
    assert p.parse_args(["-o", "DISPLAY1", "--brightness", "0.05"]).brightness == 0.05


def test_parser_refresh_alias():
    p = build_parser()
    assert p.parse_args(["-o", "DISPLAY1", "--refresh", "144"]).rate == 144.0


def test_parser_listactivemonitors_alias():
    p = build_parser()
    args = p.parse_args(["--listactivemonitors"])
    assert args.listactivemonitors and not args.listmonitors


def test_parser_screen_nograb():
    p = build_parser()
    args = p.parse_args(["--screen", "0", "--nograb"])
    assert args.screen == "0" and args.nograb


def test_parser_help_output(capsys):
    """--help 输出应包含关键选项。"""
    p = build_parser()
    with pytest.raises(SystemExit):
        p.parse_args(["--help"])
    out, _ = capsys.readouterr()
    for key in ("--mode", "--output", "--rotate", "--primary", "--off",
                "--brightness", "--gamma", "--reflect", "--json",
                "--listmodes", "--dry-run"):
        assert key in out
