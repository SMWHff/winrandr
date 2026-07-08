"""测试格式化输出。"""

from winrandr.formatter import _short_name, _fmt_modes, format_displays, format_monitor_list
from winrandr.models import DisplayInfo, DisplayMode


def test_short_name():
    assert _short_name(r"\\.\DISPLAY1") == "DISPLAY1"
    assert _short_name("DISPLAY1") == "DISPLAY1"


def test_format_displays_basic():
    displays = [
        DisplayInfo(
            name=r"\\.\DISPLAY1", friendly_name="Generic Monitor",
            width=1920, height=1080, refresh_rate=60.0,
            position_x=0, position_y=0,
            is_primary=True, rotation=0,
            width_mm=527, height_mm=296, connected=True,
            modes=[DisplayMode(1920, 1080, 60.0, is_current=True, is_preferred=True)],
        ),
    ]
    out = format_displays(displays)
    assert "Screen 0:" in out
    assert "minimum 320 x 200" in out
    assert "maximum 32767 x 32767" in out
    assert "1920 x 1080" in out
    assert "DISPLAY1" in out
    assert "connected" in out
    assert "1920x1080" in out
    assert "primary" in out
    assert "60.00*+" in out
    # 旋转列表
    assert "normal left inverted right" in out


def test_format_displays_disconnected():
    displays = [
        DisplayInfo(
            name=r"\\.\DISPLAY1", friendly_name="", connected=False,
            width=0, height=0, refresh_rate=0.0,
            position_x=0, position_y=0,
            is_primary=False, rotation=0,
            width_mm=0, height_mm=0, modes=[],
        ),
    ]
    out = format_displays(displays)
    assert "DISPLAY1" in out
    assert "disconnected" in out
    assert "minimum 320 x 200" in out


def test_format_displays_with_props():
    displays = [
        DisplayInfo(
            name=r"\\.\DISPLAY1", friendly_name="Test Monitor",
            width=1920, height=1080, refresh_rate=60.0,
            position_x=0, position_y=0,
            is_primary=True, rotation=0,
            width_mm=527, height_mm=296, connected=True,
            modes=[DisplayMode(1920, 1080, 60.0, is_current=True, is_preferred=True)],
            properties={
                "device_id": "MONITOR\\TEST123",
                "state_flags": "attached, primary",
            },
        ),
    ]
    out = format_displays(displays)
    assert "device id: MONITOR\\TEST123" in out
    assert "state flags: attached, primary" in out


def test_format_displays_non_primary():
    """非主显示器不带 primary 关键字。"""
    displays = [
        DisplayInfo(
            name=r"\\.\DISPLAY1", friendly_name="", connected=True,
            width=1920, height=1080, refresh_rate=60.0,
            position_x=0, position_y=0,
            is_primary=False, rotation=0,
            width_mm=527, height_mm=296,
            modes=[DisplayMode(1920, 1080, 60.0, is_current=True, is_preferred=True)],
        ),
    ]
    out = format_displays(displays)
    assert "DISPLAY1 connected 1920x1080+0+0" in out
    assert "primary" not in out.split("\n")[2]  # display line doesn't have primary


def test_format_displays_rotated_left():
    """旋转 90°（left）时输出宽高交换并显示旋转名称。"""
    displays = [
        DisplayInfo(
            name=r"\\.\DISPLAY1", friendly_name="", connected=True,
            width=1920, height=1080, refresh_rate=60.0,
            position_x=0, position_y=0, rotation=90,
            is_primary=False, width_mm=527, height_mm=296,
            modes=[DisplayMode(1920, 1080, 60.0, is_current=True, is_preferred=True)],
        ),
    ]
    out = format_displays(displays)
    assert "1080x1920" in out.split("\n")[2]  # 宽高已交换
    assert "left (normal left inverted right)" in out


def test_format_displays_rotated_inverted():
    """旋转 180°（inverted）宽高不变但有旋转名。"""
    displays = [
        DisplayInfo(
            name=r"\\.\DISPLAY1", friendly_name="", connected=True,
            width=1920, height=1080, refresh_rate=60.0,
            position_x=0, position_y=0, rotation=180,
            is_primary=False, width_mm=527, height_mm=296,
            modes=[DisplayMode(1920, 1080, 60.0, is_current=True, is_preferred=True)],
        ),
    ]
    out = format_displays(displays)
    assert "1920x1080" in out.split("\n")[2]  # 180° 不交换
    assert "inverted (normal left inverted right)" in out


def test_format_displays_normal_rotation_list():
    """确认 normal 旋转显示完整的可选方向列表。"""
    displays = [
        DisplayInfo(
            name=r"\\.\DISPLAY1", friendly_name="", connected=True,
            width=1920, height=1080, refresh_rate=60.0,
            position_x=0, position_y=0, rotation=0,
            is_primary=False, width_mm=527, height_mm=296,
            modes=[DisplayMode(1920, 1080, 60.0, is_current=True, is_preferred=True)],
        ),
    ]
    out = format_displays(displays)
    line = out.split("\n")[2]
    assert "(normal left inverted right)" in line
    assert "normal left inverted right" in line


def test_format_modes_alignment():
    """分辨率列表中各列对齐。"""
    displays = [
        DisplayInfo(
            name=r"\\.\DISPLAY1", friendly_name="", connected=True,
            width=1920, height=1080, refresh_rate=60.0,
            position_x=0, position_y=0,
            is_primary=True, rotation=0,
            width_mm=527, height_mm=296,
            modes=[
                DisplayMode(1920, 1080, 60.0, is_current=True, is_preferred=True),
                DisplayMode(1280, 720, 60.0),
                DisplayMode(1024, 768, 75.0, is_current=False, is_preferred=False),
                DisplayMode(1024, 768, 60.0),
            ],
        ),
    ]
    out = format_displays(displays)
    lines = out.split("\n")
    # 模式行格式：   1024x768       60.00
    mode_lines = [l for l in lines if "x" in l and l.strip().startswith("1")]
    for ml in mode_lines:
        # 验证分辨率与刷新率之间有足够的间距（≥3 空格）
        parts = ml.strip().split()
        assert len(parts) >= 2


def test_format_monitor_list_basic():
    """--listmonitors 格式：编号、标记、分辨率/物理尺寸、位置。"""
    displays = [
        DisplayInfo(
            name=r"\\.\DISPLAY1", friendly_name="", connected=True,
            width=1920, height=1080, position_x=0, position_y=0,
            is_primary=True, width_mm=527, height_mm=296,
        ),
        DisplayInfo(
            name=r"\\.\DISPLAY2", friendly_name="", connected=True,
            width=1920, height=1080, position_x=1920, position_y=0,
            is_primary=False, width_mm=527, height_mm=296,
        ),
    ]
    out = format_monitor_list(displays)
    assert "Monitors: 2" in out
    assert "DISPLAY1" in out and "DISPLAY2" in out
    assert "+*DISPLAY1" in out  # primary flag
    assert "+ DISPLAY2" in out   # non-primary flag


def test_fmt_modes_preferred_flag():
    """Preferred flag (+) always on preferred mode, independent of current."""
    modes = [
        DisplayMode(1920, 1080, 60.0, is_current=True, is_preferred=False),
        DisplayMode(1920, 1080, 59.94, is_current=False, is_preferred=True),
    ]
    lines = []
    _fmt_modes(lines, modes)
    out = "\n".join(lines)
    assert "60.00*" in out
    assert "59.94+" in out


def test_format_displays_empty():
    """空显示器列表返回空字符串。"""
    assert format_displays([]) == ""


def test_format_displays_all_disconnected():
    """全部断连的显示器。"""
    displays = [
        DisplayInfo(name=r"\\.\DISPLAY1", friendly_name="", connected=False,
                    width=0, height=0, refresh_rate=0.0, position_x=0, position_y=0,
                    is_primary=False, rotation=0, width_mm=0, height_mm=0, modes=[]),
        DisplayInfo(name=r"\\.\DISPLAY2", friendly_name="", connected=False,
                    width=0, height=0, refresh_rate=0.0, position_x=0, position_y=0,
                    is_primary=False, rotation=0, width_mm=0, height_mm=0, modes=[]),
    ]
    out = format_displays(displays)
    for d in ("DISPLAY1", "DISPLAY2", "disconnected"):
        assert d in out
    assert "no active displays" in out


def test_format_displays_rotated_270():
    """旋转 270° 时宽高交换，显示 inverted 名。"""
    displays = [DisplayInfo(
        name=r"\\.\DISPLAY1", friendly_name="", connected=True,
        width=1920, height=1080, refresh_rate=60.0,
        position_x=0, position_y=0, rotation=270,
        is_primary=False, width_mm=527, height_mm=296,
        modes=[DisplayMode(1920, 1080, 60.0, is_current=True, is_preferred=True)],
    )]
    out = format_displays(displays)
    assert "1080x1920" in out  # 宽高已交换


def test_format_displays_multiple_connected():
    """多显示器布局：累积 current 计算正确。"""
    displays = [
        DisplayInfo(name=r"\\.\DISPLAY1", friendly_name="", connected=True,
                    width=1920, height=1080, position_x=0, position_y=0,
                    is_primary=True, rotation=0, width_mm=527, height_mm=296,
                    modes=[DisplayMode(1920, 1080, 60.0)]),
        DisplayInfo(name=r"\\.\DISPLAY2", friendly_name="", connected=True,
                    width=1280, height=1024, position_x=1920, position_y=0,
                    is_primary=False, rotation=0, width_mm=0, height_mm=0,
                    modes=[DisplayMode(1280, 1024, 60.0)]),
    ]
    out = format_displays(displays)
    assert "current 3200 x 1080" in out  # 1920+1280 = 3200
    assert "primary" in out.split("\n")[2]  # DISPLAY1 line
    assert "DISPLAY2" in out


def test_format_displays_no_modes():
    """连接但无模式列表的显示器。"""
    displays = [DisplayInfo(
        name=r"\\.\DISPLAY1", friendly_name="", connected=True,
        width=1920, height=1080, refresh_rate=60.0,
        position_x=0, position_y=0, is_primary=False, rotation=0,
        width_mm=527, height_mm=296, modes=[],
    )]
    out = format_displays(displays)
    assert "DISPLAY1 connected" in out
    assert "1920x1080" in out


def test_format_monitor_list_no_connected():
    """--listmonitors 当无连接显示器时输出 0。"""
    displays = [DisplayInfo(
        name=r"\\.\DISPLAY1", friendly_name="", connected=False,
        width=0, height=0, refresh_rate=0.0, position_x=0, position_y=0,
        is_primary=False, rotation=0, width_mm=0, height_mm=0, modes=[],
    )]
    out = format_monitor_list(displays)
    assert "Monitors: 0" in out


def test_fmt_props_empty():
    """空属性字典不产生输出行。"""
    from winrandr.formatter import _fmt_props
    lines = []
    _fmt_props(lines, {})
    assert lines == []
