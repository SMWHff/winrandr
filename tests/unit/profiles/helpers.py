"""Profiles 测试辅助函数。"""

from winrandr.models import DisplayInfo, DisplayMode


def _make_display(name="DISPLAY1", x=0, y=0, w=1920, h=1080, rr=60.0, rot=0, primary=True) -> DisplayInfo:
    dm = DisplayMode(w, h, rr, True, True)
    return DisplayInfo(
        name=rf"\\.\{name}",
        friendly_name="Test",
        connected=True,
        width=w,
        height=h,
        refresh_rate=rr,
        position_x=x,
        position_y=y,
        is_primary=primary,
        rotation=rot,
        width_mm=527,
        height_mm=296,
        modes=[dm],
    )
