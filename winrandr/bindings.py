"""Win32 API 函数绑定和内部工具函数。"""

import logging
import ctypes
from ctypes import wintypes, byref, sizeof, POINTER

logger = logging.getLogger(__name__)

from winrandr.constants import (
    QDC_ONLY_ACTIVE_PATHS, QDC_ALL_PATHS,
    SDC_APPLY, SDC_USE_SUPPLIED_DISPLAY_CONFIG,
    SDC_SAVE_TO_DATABASE, SDC_ALLOW_CHANGES,
    DISPLAYCONFIG_DEVICE_INFO_GET_SOURCE_NAME,
    DISPLAYCONFIG_PATH_MODE_IDX_INVALID,
    ENUM_CURRENT_SETTINGS,
)
from winrandr.structures import (
    DISPLAYCONFIG_PATH_INFO, DISPLAYCONFIG_MODE_INFO,
    DISPLAYCONFIG_SOURCE_DEVICE_NAME, DISPLAYCONFIG_TARGET_DEVICE_NAME,
    DISPLAYCONFIG_DEVICE_INFO_HEADER,
    DISPLAY_DEVICE, DEVMODE, LUID, c_uint32,
)

_user32 = ctypes.windll.user32
_gdi32 = ctypes.windll.gdi32

# ── API 函数绑定 ─────────────────────────────────────────────────────────────

_GetDisplayConfigBufferSizes = _user32.GetDisplayConfigBufferSizes
_GetDisplayConfigBufferSizes.argtypes = [
    c_uint32, POINTER(c_uint32), POINTER(c_uint32),
]
_GetDisplayConfigBufferSizes.restype = wintypes.LONG

_QueryDisplayConfig = _user32.QueryDisplayConfig
_QueryDisplayConfig.argtypes = [
    c_uint32, POINTER(c_uint32), POINTER(DISPLAYCONFIG_PATH_INFO),
    POINTER(c_uint32), POINTER(DISPLAYCONFIG_MODE_INFO), wintypes.LPVOID,
]
_QueryDisplayConfig.restype = wintypes.LONG

_SetDisplayConfig = _user32.SetDisplayConfig
_SetDisplayConfig.argtypes = [
    c_uint32, POINTER(DISPLAYCONFIG_PATH_INFO),
    c_uint32, POINTER(DISPLAYCONFIG_MODE_INFO), c_uint32,
]
_SetDisplayConfig.restype = wintypes.LONG

_DisplayConfigGetDeviceInfo = _user32.DisplayConfigGetDeviceInfo
_DisplayConfigGetDeviceInfo.argtypes = [POINTER(DISPLAYCONFIG_DEVICE_INFO_HEADER)]
_DisplayConfigGetDeviceInfo.restype = wintypes.LONG

_ChangeDisplaySettingsEx = _user32.ChangeDisplaySettingsExW
_ChangeDisplaySettingsEx.argtypes = [
    wintypes.LPCWSTR, POINTER(DEVMODE), wintypes.HWND, wintypes.DWORD, wintypes.LPVOID,
]
_ChangeDisplaySettingsEx.restype = wintypes.LONG

_EnumDisplaySettings = _user32.EnumDisplaySettingsW
_EnumDisplaySettings.argtypes = [
    wintypes.LPCWSTR, wintypes.DWORD, POINTER(DEVMODE),
]
_EnumDisplaySettings.restype = wintypes.BOOL

_EnumDisplayDevices = _user32.EnumDisplayDevicesW
_EnumDisplayDevices.argtypes = [
    wintypes.LPCWSTR, wintypes.DWORD, POINTER(DISPLAY_DEVICE), wintypes.DWORD,
]
_EnumDisplayDevices.restype = wintypes.BOOL

# ── GDI 函数绑定 ─────────────────────────────────────────────────────────────

_CreateDCW = _gdi32.CreateDCW
_CreateDCW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPVOID]
_CreateDCW.restype = wintypes.HDC

_DeleteDC = _gdi32.DeleteDC
_DeleteDC.argtypes = [wintypes.HDC]
_DeleteDC.restype = wintypes.BOOL

_GetDeviceCaps = _gdi32.GetDeviceCaps
_GetDeviceCaps.argtypes = [wintypes.HDC, ctypes.c_int]
_GetDeviceCaps.restype = ctypes.c_int

_GetDeviceGammaRamp = _gdi32.GetDeviceGammaRamp
_GetDeviceGammaRamp.argtypes = [wintypes.HDC, wintypes.LPVOID]
_GetDeviceGammaRamp.restype = wintypes.BOOL

_SetDeviceGammaRamp = _gdi32.SetDeviceGammaRamp
_SetDeviceGammaRamp.argtypes = [wintypes.HDC, wintypes.LPVOID]
_SetDeviceGammaRamp.restype = wintypes.BOOL


# ── 内部工具函数 ─────────────────────────────────────────────────────────────

def get_gdi_name(path) -> str:
    """获取路径对应的 GDI 设备名。"""
    name = DISPLAYCONFIG_SOURCE_DEVICE_NAME()
    name.header.type = DISPLAYCONFIG_DEVICE_INFO_GET_SOURCE_NAME
    name.header.size = sizeof(DISPLAYCONFIG_SOURCE_DEVICE_NAME)
    name.header.adapterId = path.sourceInfo.adapterId
    name.header.id = path.sourceInfo.id
    ret = _DisplayConfigGetDeviceInfo(byref(name.header))
    return name.viewGdiDeviceName if ret == 0 else ""


def query_active_config():
    """查询当前活动显示配置，返回 (paths, modes, path_count, mode_count)。"""
    path_count = c_uint32(0)
    mode_count = c_uint32(0)

    ret = _GetDisplayConfigBufferSizes(QDC_ONLY_ACTIVE_PATHS, byref(path_count), byref(mode_count))
    if ret != 0:
        return None

    paths = (DISPLAYCONFIG_PATH_INFO * path_count.value)()
    modes = (DISPLAYCONFIG_MODE_INFO * mode_count.value)()

    ret = _QueryDisplayConfig(
        QDC_ONLY_ACTIVE_PATHS, byref(path_count), paths,
        byref(mode_count), modes, None,
    )
    if ret != 0:
        return None

    return paths, modes, path_count.value, mode_count.value


def query_all_config():
    """查询所有显示配置（含已断开的），同上返回格式。"""
    path_count = c_uint32(0)
    mode_count = c_uint32(0)

    ret = _GetDisplayConfigBufferSizes(QDC_ALL_PATHS, byref(path_count), byref(mode_count))
    if ret != 0:
        return None

    paths = (DISPLAYCONFIG_PATH_INFO * path_count.value)()
    modes = (DISPLAYCONFIG_MODE_INFO * mode_count.value)()

    ret = _QueryDisplayConfig(
        QDC_ALL_PATHS, byref(path_count), paths,
        byref(mode_count), modes, None,
    )
    if ret != 0:
        return None

    return paths, modes, path_count.value, mode_count.value


def get_screen_size_mm(gdi_name: str):
    """获取显示器物理尺寸（mm），通过 GDI CreateDCW + GetDeviceCaps。"""
    if not gdi_name:
        return 0, 0
    try:
        dc = _CreateDCW("DISPLAY", gdi_name, None, None)
        if not dc:
            return 0, 0
        HORZSIZE = 4
        VERTSIZE = 6
        w = _GetDeviceCaps(dc, HORZSIZE)
        h = _GetDeviceCaps(dc, VERTSIZE)
        _DeleteDC(dc)
        return w, h
    except Exception:
        return 0, 0


def get_friendly_name_via_enum(gdi_name: str) -> str:
    """使用 EnumDisplayDevices 获取显示器友好名称。"""
    dd = DISPLAY_DEVICE()
    dd.cb = sizeof(DISPLAY_DEVICE)
    if _EnumDisplayDevices(gdi_name, 0, byref(dd), 0):
        dm = DISPLAY_DEVICE()
        dm.cb = sizeof(DISPLAY_DEVICE)
        if _EnumDisplayDevices(gdi_name, 1, byref(dm), 0):
            return dm.DeviceString
        return dd.DeviceString
    return ""


def get_resolution_refresh_via_enum(gdi_name: str):
    """使用 EnumDisplaySettings 获取分辨率、刷新率、色深。"""
    dm = DEVMODE()
    dm.dmSize = sizeof(DEVMODE)
    ret = _EnumDisplaySettings(gdi_name, ENUM_CURRENT_SETTINGS, byref(dm))
    if not ret:
        return 0, 0, 0.0, 32
    return dm.dmPelsWidth, dm.dmPelsHeight, float(dm.dmDisplayFrequency), dm.dmBitsPerPel


def apply_config(paths, path_count, modes, mode_count, flags=None):
    """应用显示配置。"""
    if flags is None:
        flags = (
            SDC_APPLY | SDC_USE_SUPPLIED_DISPLAY_CONFIG
            | SDC_ALLOW_CHANGES | SDC_SAVE_TO_DATABASE
        )
    return _SetDisplayConfig(path_count, paths, mode_count, modes, flags) == 0


_SDC_AVAILABLE = None


def set_display_config_available() -> bool:
    """检测 SetDisplayConfig 是否可用（OrayIddDriver 可能破坏 SDC）。"""
    global _SDC_AVAILABLE
    if _SDC_AVAILABLE is not None:
        return _SDC_AVAILABLE
    try:
        r = _SetDisplayConfig(0, None, 0, None, SDC_APPLY)
        _SDC_AVAILABLE = (r == 0)
    except Exception:
        _SDC_AVAILABLE = False
    if not _SDC_AVAILABLE:
        logger.warning(
            "SetDisplayConfig 不可用，可能是 OrayIddDriver 等虚拟显示器驱动干扰所致。"
            " set_position / set_rotation / set_primary / set_off 等功能将不可用。",
        )
    return _SDC_AVAILABLE


def find_path_idx(paths, count, device_name):
    """通过 GDI 设备名查找路径在数组中的索引。"""
    for i in range(count):
        gdi_name = get_gdi_name(paths[i])
        if gdi_name == device_name:
            return i
    return None


def filter_valid_paths(paths, path_count, modes, mode_count):
    """过滤出有效路径：mode 索引需指向对应类型的 mode 条目。"""
    from winrandr.constants import (
        DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE,
        DISPLAYCONFIG_MODE_INFO_TYPE_TARGET,
    )
    valid = []
    for i in range(path_count):
        p = paths[i]
        smi = p.sourceInfo.modeInfoIdx
        tmi = p.targetInfo.modeInfoIdx
        smi_ok = (
            smi != DISPLAYCONFIG_PATH_MODE_IDX_INVALID
            and smi < mode_count
            and modes[smi].infoType == DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE
        )
        tmi_ok = (
            tmi != DISPLAYCONFIG_PATH_MODE_IDX_INVALID
            and tmi < mode_count
            and modes[tmi].infoType == DISPLAYCONFIG_MODE_INFO_TYPE_TARGET
        )
        if smi_ok and tmi_ok:
            valid.append(i)
    return valid


def apply_filtered(paths, path_count, modes, mode_count, flags=None):
    """过滤出有效路径后应用配置（避免虚拟显示器幽灵路径导致 SDC 失败）。"""
    valid_idxs = filter_valid_paths(paths, path_count, modes, mode_count)
    if not valid_idxs:
        return False
    valid = (DISPLAYCONFIG_PATH_INFO * len(valid_idxs))()
    for dest, src_idx in enumerate(valid_idxs):
        valid[dest] = paths[src_idx]
    return apply_config(valid, len(valid_idxs), modes, mode_count, flags)
