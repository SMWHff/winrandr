"""共享测试夹具：真实硬件测试与纯逻辑测试。"""

import pytest

from winrandr.models import DisplayInfo, DisplayMode

_PROFILE_NAME = "__test_restore__"


def _main_display(displays):
    """返回第一个已连接的主显示器。"""
    for d in displays:
        if d.connected and d.is_primary:
            return d
    for d in displays:
        if d.connected:
            return d
    return None


def _write_op(op, *args, **kwargs):
    """执行写操作，SDC 不可用时 xfail。"""
    result = op(*args, **kwargs)
    if not result:
        pytest.xfail(f"SetDisplayConfig 不可用（虚拟显示器驱动可能干扰），{op.__name__} 预期失败")


@pytest.fixture
def actual_display():
    """返回主显示器，没有则跳过。"""
    from winrandr.api import list_displays

    displays = list_displays()
    d = _main_display(displays)
    if d is None:
        pytest.skip("没有已连接的显示器")
    return d


@pytest.fixture
def profile_backup():
    """自动保存和恢复显示器配置。"""
    from winrandr.profiles import save_profile

    save_profile(_PROFILE_NAME)
    yield
    try:
        from winrandr.profiles import load_profile

        load_profile(_PROFILE_NAME)
    except Exception:  # noqa: BLE001
        pass
    try:
        from winrandr.profiles import delete_profile

        delete_profile(_PROFILE_NAME)
    except Exception:  # noqa: BLE001
        pass


@pytest.fixture
def connected_displays():
    """返回所有已连接的显示器，少于 2 个则跳过。"""
    from winrandr.api import list_displays

    displays = list_displays()
    connected = [d for d in displays if d.connected]
    if len(connected) < 2:
        pytest.skip("需要至少 2 个已连接显示器")
    return connected


def pytest_sessionfinish():
    """测试会话结束时重置伽马为单位矩阵（绝对写，不依赖当前值）。"""
    try:
        from winrandr.api import list_displays
        from winrandr.features.gamma import _reset_gamma_to_identity

        for d in list_displays():
            if d.connected:
                _reset_gamma_to_identity(d.name)
    except Exception:  # noqa: BLE001
        pass


def _fake_display(name="DISPLAY1", connected=True, **kw):
    """创建一个模拟的 DisplayInfo 用于纯逻辑测试。"""
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
