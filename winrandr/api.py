"""公开 API：显示器信息查询和配置修改。"""

from typing import Optional
import logging

from winrandr.models import DisplayMode, DisplayInfo
from winrandr.constants import (
    DISPLAYCONFIG_PATH_MODE_IDX_INVALID,
    DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE,
    DISPLAYCONFIG_MODE_INFO_TYPE_TARGET,
    ROTATION_DEGREES, ROTATION_MAP,
    CDS_UPDATEREGISTRY, DISP_CHANGE_SUCCESSFUL, ENUM_CURRENT_SETTINGS,
)
from ctypes import sizeof, byref, c_uint16

from winrandr.structures import DEVMODE, DISPLAYCONFIG_PATH_INFO
from winrandr.bindings import (
    query_active_config, query_all_config, get_gdi_name,
    get_friendly_name_via_enum, get_screen_size_mm,
    get_resolution_refresh_via_enum, apply_config, apply_filtered,
    find_path_idx, set_display_config_available,
    _ChangeDisplaySettingsEx, _EnumDisplaySettings,
    _CreateDCW, _DeleteDC, _GetDeviceGammaRamp, _SetDeviceGammaRamp,
)

logger = logging.getLogger(__name__)


def _enumerate_modes(gdi_name: str, cur_width: int, cur_height: int, cur_refresh: float) -> list[DisplayMode]:
    """枚举指定显示器的所有可用模式。"""
    modes = []
    i = 0
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
            is_pref = (dm.dmPelsWidth == 1920 and dm.dmPelsHeight == 1080) if i == 0 else False
            modes.append(DisplayMode(
                width=dm.dmPelsWidth,
                height=dm.dmPelsHeight,
                refresh_rate=rr,
                is_current=is_cur,
                is_preferred=is_pref,
            ))
        i += 1
    return modes


def list_displays(include_disconnected: bool = True) -> list[DisplayInfo]:
    """列出显示器及其当前配置。

    Args:
        include_disconnected: 是否包含已断开的（虚拟）显示器。
    """
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


def set_position(device_name: str, x: int, y: int) -> bool:
    """设置显示器的桌面位置。"""
    if not set_display_config_available():
        return False
    config = query_active_config()
    if config is None:
        return False
    paths, modes, path_count, mode_count = config

    idx = find_path_idx(paths, path_count, device_name)
    if idx is None:
        logger.error("未找到显示器: %s", device_name)
        return False

    mode_idx = paths[idx].sourceInfo.modeInfoIdx
    if mode_idx == DISPLAYCONFIG_PATH_MODE_IDX_INVALID or mode_idx >= mode_count:
        logger.error("显示器 %s 模式索引无效", device_name)
        return False

    modes[mode_idx]._union.sourceMode.position.x = x
    modes[mode_idx]._union.sourceMode.position.y = y
    return apply_filtered(paths, path_count, modes, mode_count)


def set_rotation(device_name: str, degrees: int) -> bool:
    """设置显示器旋转角度（0、90、180、270）。"""
    rot = ROTATION_MAP.get(degrees)
    if rot is None:
        logger.error("无效旋转角度: %d（必须为 0、90、180 或 270）", degrees)
        return False

    if not set_display_config_available():
        return False
    config = query_active_config()
    if config is None:
        return False
    paths, modes, path_count, mode_count = config

    idx = find_path_idx(paths, path_count, device_name)
    if idx is None:
        logger.error("未找到显示器: %s", device_name)
        return False

    paths[idx].targetInfo.rotation = rot
    return apply_filtered(paths, path_count, modes, mode_count)


def set_primary(device_name: str) -> bool:
    """将指定显示器设为主显示器。"""
    if not set_display_config_available():
        return False
    config = query_active_config()
    if config is None:
        return False
    paths, modes, path_count, mode_count = config

    found = False
    for i in range(path_count):
        gdi = get_gdi_name(paths[i])
        if gdi == device_name:
            paths[i].sourceInfo.statusFlags |= 0x01
            found = True
        else:
            paths[i].sourceInfo.statusFlags &= ~0x01

    if not found:
        logger.error("未找到显示器: %s", device_name)
        return False
    return apply_filtered(paths, path_count, modes, mode_count)


def set_off(device_name: str) -> bool:
    """关闭（禁用）指定显示器。"""
    if not set_display_config_available():
        return False
    config = query_active_config()
    if config is None:
        return False
    paths, modes, path_count, mode_count = config

    kept = []
    for i in range(path_count):
        gdi = get_gdi_name(paths[i])
        if gdi != device_name:
            kept.append(i)

    if len(kept) == path_count:
        logger.error("未找到显示器: %s", device_name)
        return False

    new_paths = (DISPLAYCONFIG_PATH_INFO * len(kept))()
    for dest, src_idx in enumerate(kept):
        new_paths[dest] = paths[src_idx]

    return apply_config(new_paths, len(kept), modes, mode_count)


def set_brightness(device_name: str, brightness: float) -> bool:
    """通过伽马校正设置显示器亮度。

    brightness: 0.1-2.0 范围，1.0 为正常。方式同 xrandr --brightness。
    """
    if brightness < 0:
        logger.error("亮度值不能为负数: %g", brightness)
        return False
    try:
        dc = _CreateDCW("DISPLAY", device_name, None, None)
        if not dc:
            logger.error("无法为 %s 创建设备上下文", device_name)
            return False
        try:
            ramp = (c_uint16 * (3 * 256))()
            if not _GetDeviceGammaRamp(dc, ramp):
                logger.error("无法获取 %s 的伽马校正表", device_name)
                return False
            for i in range(3 * 256):
                val = int(ramp[i] * brightness)
                ramp[i] = max(0, min(65535, val))
            if not _SetDeviceGammaRamp(dc, ramp):
                logger.error("无法设置 %s 的伽马校正表", device_name)
                return False
            return True
        finally:
            _DeleteDC(dc)
    except Exception as e:
        logger.error("设置亮度失败: %s", e)
        return False


def set_reflect(device_name: str, axis: str) -> bool:
    """设置显示器镜像翻转。

    在 Windows 上仅支持 xy（等同于 180° 旋转）。
    """
    if axis == "xy":
        return set_rotation(device_name, 180)
    logger.error("不支持 --reflect %s（Windows 仅支持 xy = 旋转 180°）", axis)
    return False
