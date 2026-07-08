"""分辨率和刷新率管理。"""

import logging
from ctypes import sizeof, byref

from winrandr.models import DisplayMode
from winrandr.win32.structures import DEVMODE
from winrandr.win32.bindings import (
    _ChangeDisplaySettingsEx, _EnumDisplaySettings,
)
from winrandr.win32.constants import (
    ENUM_REGISTRY_SETTINGS, ENUM_CURRENT_SETTINGS,
    CDS_UPDATEREGISTRY, DISP_CHANGE_SUCCESSFUL, DISP_CHANGE_MESSAGES,
)

logger = logging.getLogger(__name__)


def _enumerate_modes(gdi_name: str, cur_width: int, cur_height: int, cur_refresh: float) -> list[DisplayMode]:
    """枚举指定显示器的所有可用模式，标记当前和首选。"""
    modes = []
    reg_dm = DEVMODE()
    reg_dm.dmSize = sizeof(DEVMODE)
    has_reg = _EnumDisplaySettings(gdi_name, ENUM_REGISTRY_SETTINGS, byref(reg_dm))

    i = 0
    while True:
        dm = DEVMODE()
        dm.dmSize = sizeof(DEVMODE)
        if not _EnumDisplaySettings(gdi_name, i, byref(dm)):
            break
        if dm.dmPelsWidth > 0 and dm.dmPelsHeight > 0 and dm.dmDisplayFrequency > 0:
            rr = float(dm.dmDisplayFrequency)
            is_cur = (dm.dmPelsWidth == cur_width and dm.dmPelsHeight == cur_height
                      and abs(rr - cur_refresh) < 0.01)
            is_pref = bool(has_reg
                           and dm.dmPelsWidth == reg_dm.dmPelsWidth
                           and dm.dmPelsHeight == reg_dm.dmPelsHeight)
            modes.append(DisplayMode(
                width=dm.dmPelsWidth, height=dm.dmPelsHeight, refresh_rate=rr,
                is_current=is_cur, is_preferred=is_pref,
            ))
        i += 1
    return modes


def set_resolution(device_name: str, width: int, height: int, refresh_rate: float = 0) -> bool:
    """设置显示器的分辨率和刷新率。"""
    dm = DEVMODE()
    dm.dmSize = sizeof(DEVMODE)

    ret = _EnumDisplaySettings(device_name, ENUM_CURRENT_SETTINGS, byref(dm))
    if not ret:
        logger.error("无法获取 %s 的当前显示设置（显示器可能已断开或驱动异常）", device_name)
        return False

    dm.dmFields = 0
    dm.dmPelsWidth = width
    dm.dmPelsHeight = height
    dm.dmBitsPerPel = 32
    dm.dmFields |= 0x00080000 | 0x00100000 | 0x00040000

    if refresh_rate > 0:
        dm.dmDisplayFrequency = int(refresh_rate)
        dm.dmFields |= 0x00400000

    ret = _ChangeDisplaySettingsEx(device_name, byref(dm), None, CDS_UPDATEREGISTRY, None)
    if ret != DISP_CHANGE_SUCCESSFUL:
        msg = DISP_CHANGE_MESSAGES.get(ret, f"未知错误码 {ret}")
        logger.error("应用分辨率 %dx%d 到 %s 失败: %s", width, height, device_name, msg)
        return False
    return True


def set_preferred_resolution(device_name: str) -> bool:
    """设置为注册表中保存的首选分辨率。"""
    dm = DEVMODE()
    dm.dmSize = sizeof(DEVMODE)
    if not _EnumDisplaySettings(device_name, ENUM_REGISTRY_SETTINGS, byref(dm)):
        logger.error("无法获取 %s 的注册表设置（可能从未保存过首选分辨率）", device_name)
        return False
    return set_resolution(
        device_name,
        dm.dmPelsWidth,
        dm.dmPelsHeight,
        float(dm.dmDisplayFrequency) if dm.dmDisplayFrequency > 0 else 0,
    )


def set_auto(device_name: str) -> bool:
    """启用显示器并使用首选分辨率（等效于 xrandr --auto）。"""
    return set_preferred_resolution(device_name)
