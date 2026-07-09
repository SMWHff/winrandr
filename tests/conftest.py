"""Shared test fixtures."""

from winrandr.models import DisplayInfo, DisplayMode


def _fake_display(name="DISPLAY1", connected=True, **kw):
    """创建一个模拟的 DisplayInfo 用于测试。"""
    defaults = dict(
        name=rf"\\.\{name}",
        friendly_name="Fake Monitor",
        connected=connected,
        width=1920,
        height=1080,
        refresh_rate=60.0,
        position_x=0,
        position_y=0,
        is_primary=True,
        rotation=0,
        width_mm=527,
        height_mm=296,
        modes=[DisplayMode(1920, 1080, 60.0, True, True)],
    )
    defaults.update(kw)
    return DisplayInfo(**defaults)
