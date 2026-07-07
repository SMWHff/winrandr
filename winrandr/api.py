"""公开 API：显示器信息查询和配置修改。"""

import logging
from ctypes import sizeof, byref

from winrandr.models import DisplayMode, DisplayInfo
from winrandr.constants import (
    DISPLAYCONFIG_PATH_MODE_IDX_INVALID,
    DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE,
    DISPLAYCONFIG_MODE_INFO_TYPE_TARGET,
    ROTATION_DEGREES,
    CDS_UPDATEREGISTRY, DISP_CHANGE_SUCCESSFUL, ENUM_CURRENT_SETTINGS,
    DISPLAY_DEVICE_ATTACHED_TO_DESKTOP, DISPLAY_DEVICE_PRIMARY_DEVICE,
    DISPLAY_DEVICE_MIRRORING_DRIVER, DISPLAY_DEVICE_VGA_COMPATIBLE,
    DISPLAY_DEVICE_REMOVABLE, DISPLAY_DEVICE_DISCONNECTED,
    DISPLAY_DEVICE_REMOTE, DISPLAY_DEVICE_MODESPRUNED,
)
from winrandr.structures import DEVMODE, DISPLAY_DEVICE
from winrandr.bindings import (
    query_active_config, query_all_config, get_gdi_name,
    get_friendly_name_via_enum, get_screen_size_mm,
    get_resolution_refresh_via_enum,
    get_adapter_name, get_monitor_device_path,
    _ChangeDisplaySettingsEx, _EnumDisplaySettings, _EnumDisplayDevices,
)

from winrandr.features.gamma import set_brightness, set_gamma  # noqa: F401
from winrandr.features.layout import (  # noqa: F401
    set_position, set_position_relative, set_rotation,
    set_primary, set_off, set_reflect,
)

logger = logging.getLogger(__name__)


ENUM_REGISTRY_SETTINGS = 0xFFFFFFFE


def _enumerate_modes(gdi_name: str, cur_width: int, cur_height: int, cur_refresh: float) -> list[DisplayMode]:
    """枚举指定显示器的所有可用模式。"""
    modes = []
    i = 0

    # 通过 ENUM_REGISTRY_SETTINGS 获取默认模式，标记为首选
    reg_dm = DEVMODE()
    reg_dm.dmSize = sizeof(DEVMODE)
    has_reg = _EnumDisplaySettings(gdi_name, 0xFFFFFFFE, byref(reg_dm))

    while True:
        dm = DEVMODE()
        dm.dmSize = sizeof(DEVMODE)
        ret = _EnumDisplaySettings(gdi_name, i, byref(dm))
        if not ret:
            break
        if dm.dmPelsWidth > 0 and dm.dmPelsHeight > 0 and dm.dmDisplayFrequency > 0:
            rr = float(dm.dmDisplayFrequency)
            is_cur = (dm.dmPelsWidth == cur_width and dm.dmPelsHeight == cur_height
                      and abs(rr - cur_refresh) < 0.01)
            is_pref = bool(has_reg
                           and dm.dmPelsWidth == reg_dm.dmPelsWidth
                           and dm.dmPelsHeight == reg_dm.dmPelsHeight)
            modes.append(DisplayMode(
                width=dm.dmPelsWidth,
                height=dm.dmPelsHeight,
                refresh_rate=rr,
                is_current=is_cur,
                is_preferred=is_pref,
            ))
        i += 1
    return modes


def list_displays() -> list[DisplayInfo]:
    """列出活动显示器及其当前配置。"""
    config = query_active_config()
    if config is None:
        return []
    paths, modes, path_count, mode_count = config

    seen = set()
    displays = []

    for i in range(path_count):
        path = paths[i]
        gdi_name = get_gdi_name(path)
        if not gdi_name or gdi_name in seen:
            continue
        seen.add(gdi_name)

        is_primary = bool(path.sourceInfo.statusFlags & 0x01)
        rotation = ROTATION_DEGREES.get(path.targetInfo.rotation, 0)

        width = height = pos_x = pos_y = 0
        mode_idx = path.sourceInfo.modeInfoIdx
        if (mode_idx != DISPLAYCONFIG_PATH_MODE_IDX_INVALID
                and mode_idx < mode_count
                and modes[mode_idx].infoType == DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE):
            sm = modes[mode_idx]._union.sourceMode
            width, height = sm.width, sm.height
            pos_x, pos_y = sm.position.x, sm.position.y
        else:
            w, h, _, _ = get_resolution_refresh_via_enum(gdi_name)
            width, height = w, h

        refresh = 0.0
        tmi = path.targetInfo.modeInfoIdx
        if (tmi != DISPLAYCONFIG_PATH_MODE_IDX_INVALID
                and tmi < mode_count
                and modes[tmi].infoType == DISPLAYCONFIG_MODE_INFO_TYPE_TARGET):
            vs = modes[tmi]._union.targetMode.targetVideoSignalInfo.vSyncFreq
            if vs.Denominator:
                refresh = vs.Numerator / vs.Denominator

        if refresh == 0.0:
            _, _, rr, _ = get_resolution_refresh_via_enum(gdi_name)
            refresh = rr

        active = width > 0 and height > 0
        friendly = get_friendly_name_via_enum(gdi_name)
        w_mm, h_mm = get_screen_size_mm(gdi_name) if active else (0, 0)

        all_modes = _enumerate_modes(gdi_name, width, height, refresh) if active else []

        displays.append(DisplayInfo(
            name=gdi_name,
            friendly_name=friendly,
            connected=active,
            width=width,
            height=height,
            refresh_rate=round(refresh, 2),
            position_x=pos_x,
            position_y=pos_y,
            is_primary=is_primary,
            rotation=rotation,
            width_mm=w_mm,
            height_mm=h_mm,
            modes=all_modes,
        ))

    return displays


def set_resolution(device_name: str, width: int, height: int, refresh_rate: float = 0) -> bool:
    """设置显示器的分辨率和刷新率。"""
    dm = DEVMODE()
    dm.dmSize = sizeof(DEVMODE)

    ret = _EnumDisplaySettings(device_name, ENUM_CURRENT_SETTINGS, byref(dm))
    if not ret:
        logger.error("无法获取 %s 的当前显示设置", device_name)
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
        logger.error("应用分辨率失败，错误码: %d", ret)
        return False
    return True


def set_preferred_resolution(device_name: str) -> bool:
    """设置为注册表中保存的首选分辨率。"""
    dm = DEVMODE()
    dm.dmSize = sizeof(DEVMODE)
    if not _EnumDisplaySettings(device_name, ENUM_REGISTRY_SETTINGS, byref(dm)):
        logger.error("无法获取 %s 的注册表设置", device_name)
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


def get_display_props(device_name: str) -> dict:
    """获取指定显示器的扩展属性（用于 --prop）。"""
    props = {}

    # 通过 EnumDisplayDevices 获取 DeviceID 和状态标志
    dd = DISPLAY_DEVICE()
    dd.cb = sizeof(DISPLAY_DEVICE)
    if _EnumDisplayDevices(device_name, 0, byref(dd), 0):
        if dd.DeviceID:
            props["device_id"] = dd.DeviceID
        # 解码 StateFlags
        flags = []
        if dd.StateFlags & DISPLAY_DEVICE_ATTACHED_TO_DESKTOP:
            flags.append("attached")
        if dd.StateFlags & DISPLAY_DEVICE_PRIMARY_DEVICE:
            flags.append("primary")
        if dd.StateFlags & DISPLAY_DEVICE_MIRRORING_DRIVER:
            flags.append("mirroring")
        if dd.StateFlags & DISPLAY_DEVICE_REMOVABLE:
            flags.append("removable")
        if dd.StateFlags & DISPLAY_DEVICE_DISCONNECTED:
            flags.append("disconnected")
        if dd.StateFlags & DISPLAY_DEVICE_REMOTE:
            flags.append("remote")
        if dd.StateFlags & DISPLAY_DEVICE_VGA_COMPATIBLE:
            flags.append("vga")
        if dd.StateFlags & DISPLAY_DEVICE_MODESPRUNED:
            flags.append("modes_pruned")
        if flags:
            props["state_flags"] = ", ".join(flags)

    # 通过 QDC 获取适配器名称和显示器设备路径
    config = query_all_config()
    if config:
        paths, modes, path_count, mode_count = config
        for i in range(path_count):
            gdi_name = get_gdi_name(paths[i])
            if gdi_name == device_name:
                adapter = get_adapter_name(paths[i])
                if adapter:
                    props["adapter"] = adapter
                mon_path = get_monitor_device_path(paths[i])
                if mon_path:
                    props["monitor_path"] = mon_path
                break

    return props


def list_providers() -> list[dict]:
    """列举 GPU 适配器。"""
    providers = []
    dd = DISPLAY_DEVICE()
    dd.cb = sizeof(DISPLAY_DEVICE)
    i = 0
    while _EnumDisplayDevices(None, i, byref(dd), 0):
        providers.append({
            "name": dd.DeviceName,
            "string": dd.DeviceString,
            "flags": dd.StateFlags,
        })
        dd = DISPLAY_DEVICE()
        dd.cb = sizeof(DISPLAY_DEVICE)
        i += 1
    return providers
