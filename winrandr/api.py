"""公开 API：显示器信息查询和配置修改。"""

__all__ = [
    "list_displays", "set_position_relative", "get_display_props",
    "list_providers",
]

import logging
from ctypes import sizeof, byref

from winrandr.models import DisplayInfo
from winrandr.formatter import short_name
from winrandr.win32.constants import (
    DISPLAYCONFIG_PATH_MODE_IDX_INVALID,
    DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE,
    DISPLAYCONFIG_MODE_INFO_TYPE_TARGET,
    ROTATION_DEGREES,
    DISPLAY_DEVICE_ATTACHED_TO_DESKTOP, DISPLAY_DEVICE_PRIMARY_DEVICE,
    DISPLAY_DEVICE_MIRRORING_DRIVER, DISPLAY_DEVICE_VGA_COMPATIBLE,
    DISPLAY_DEVICE_REMOVABLE, DISPLAY_DEVICE_DISCONNECTED,
    DISPLAY_DEVICE_REMOTE, DISPLAY_DEVICE_MODESPRUNED,
)
from winrandr.win32.structures import DISPLAY_DEVICE
from winrandr.win32.utils import (
    query_active_config, query_all_config, get_gdi_name,
    get_friendly_name_via_enum, get_screen_size_mm,
    get_resolution_refresh_via_enum,
    get_adapter_name, get_monitor_device_path,
)
from winrandr.win32.bindings import _EnumDisplayDevices
from winrandr.edid import get_edid
from winrandr.features.gamma import set_brightness, set_gamma, identify_display  # noqa: F401
from winrandr.features.layout import (  # noqa: F401
    set_position, set_rotation, set_primary, set_off, set_reflect,
    set_noprimary,
)
from winrandr.features.resolution import (  # noqa: F401
    set_resolution, set_preferred_resolution, set_auto,
    enumerate_modes,
)

logger = logging.getLogger(__name__)


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

        all_modes = enumerate_modes(gdi_name, width, height, refresh) if active else []

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


def set_position_relative(device_name: str, reference_name: str, relation: str) -> bool:
    """相对定位，类似 xrandr --left-of / --right-of / --above / --below / --same-as。"""
    displays = list_displays()

    target = ref = None
    for d in displays:
        if not d.connected:
            continue
        sn = short_name(d.name)
        if sn == short_name(device_name) or d.name == device_name:
            target = d
        if sn == short_name(reference_name) or d.name == reference_name:
            ref = d

    if not target:
        logger.error("未找到显示器: %s", device_name)
        return False
    if not ref:
        logger.error("未找到参考显示器: %s", reference_name)
        return False

    pos_map = {
        "right-of": (ref.position_x + ref.width, ref.position_y),
        "left-of": (ref.position_x - target.width, ref.position_y),
        "below": (ref.position_x, ref.position_y + ref.height),
        "above": (ref.position_x, ref.position_y - target.height),
        "same-as": (ref.position_x, ref.position_y),
    }
    pos = pos_map.get(relation)
    if pos is None:
        logger.error("无效相对位置关系: %s", relation)
        return False
    x, y = pos
    return set_position(device_name, x, y)


def get_display_props(device_name: str) -> dict[str, str]:
    """获取指定显示器的扩展属性（用于 --prop）。"""
    props = {}

    dd = DISPLAY_DEVICE()
    dd.cb = sizeof(DISPLAY_DEVICE)
    if _EnumDisplayDevices(device_name, 0, byref(dd), 0):
        if dd.DeviceID:
            props["device_id"] = dd.DeviceID
        flag_names = {
            DISPLAY_DEVICE_ATTACHED_TO_DESKTOP: "attached",
            DISPLAY_DEVICE_PRIMARY_DEVICE: "primary",
            DISPLAY_DEVICE_MIRRORING_DRIVER: "mirroring",
            DISPLAY_DEVICE_REMOVABLE: "removable",
            DISPLAY_DEVICE_DISCONNECTED: "disconnected",
            DISPLAY_DEVICE_REMOTE: "remote",
            DISPLAY_DEVICE_VGA_COMPATIBLE: "vga",
            DISPLAY_DEVICE_MODESPRUNED: "modes_pruned",
        }
        flags = [n for f, n in flag_names.items() if dd.StateFlags & f]
        if flags:
            props["state_flags"] = ", ".join(flags)

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

    edid = get_edid(device_name)
    if edid:
        props.update(edid)

    return props


def list_providers() -> list[dict[str, str | int]]:
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
