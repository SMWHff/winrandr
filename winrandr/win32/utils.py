"""内部工具函数：显示配置查询、设备信息获取、配置应用。"""

import logging
from ctypes import sizeof, byref, c_uint32

from winrandr.win32.constants import (
    QDC_ONLY_ACTIVE_PATHS, QDC_ALL_PATHS,
    SDC_APPLY, SDC_USE_SUPPLIED_DISPLAY_CONFIG,
    SDC_SAVE_TO_DATABASE, SDC_ALLOW_CHANGES,
    DISPLAYCONFIG_DEVICE_INFO_GET_SOURCE_NAME,
    DISPLAYCONFIG_DEVICE_INFO_GET_TARGET_NAME,
    DISPLAYCONFIG_DEVICE_INFO_GET_ADAPTER_NAME,
    DISPLAYCONFIG_PATH_MODE_IDX_INVALID,
    DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE,
    DISPLAYCONFIG_MODE_INFO_TYPE_TARGET,
    ENUM_CURRENT_SETTINGS,
)
from winrandr.win32.structures import (
    DISPLAYCONFIG_PATH_INFO, DISPLAYCONFIG_MODE_INFO,
    DISPLAYCONFIG_SOURCE_DEVICE_NAME, DISPLAYCONFIG_TARGET_DEVICE_NAME,
    DISPLAYCONFIG_ADAPTER_NAME, DISPLAY_DEVICE, DEVMODE,
)
from winrandr.win32.bindings import (
    _GetDisplayConfigBufferSizes, _QueryDisplayConfig, _SetDisplayConfig,
    _DisplayConfigGetDeviceInfo, _EnumDisplaySettings,
    _EnumDisplayDevices, _CreateDCW, _DeleteDC, _GetDeviceCaps,
)

logger = logging.getLogger(__name__)

_SDC_AVAILABLE = None
_QDC_CACHE = None
_QDC_ALL_CACHE = None


def _invalidate_qdc_cache() -> None:
    global _QDC_CACHE, _QDC_ALL_CACHE
    _QDC_CACHE = None
    _QDC_ALL_CACHE = None


def get_gdi_name(path) -> str:
    """获取路径对应的 GDI 设备名。"""
    name = DISPLAYCONFIG_SOURCE_DEVICE_NAME()
    name.header.type = DISPLAYCONFIG_DEVICE_INFO_GET_SOURCE_NAME
    name.header.size = sizeof(DISPLAYCONFIG_SOURCE_DEVICE_NAME)
    name.header.adapterId = path.sourceInfo.adapterId
    name.header.id = path.sourceInfo.id
    ret = _DisplayConfigGetDeviceInfo(byref(name.header))
    return name.viewGdiDeviceName if ret == 0 else ""


def get_adapter_name(path) -> str:
    """获取路径对应的 GPU 适配器名称。"""
    name = DISPLAYCONFIG_ADAPTER_NAME()
    name.header.type = DISPLAYCONFIG_DEVICE_INFO_GET_ADAPTER_NAME
    name.header.size = sizeof(DISPLAYCONFIG_ADAPTER_NAME)
    name.header.adapterId = path.sourceInfo.adapterId
    name.header.id = path.sourceInfo.id
    ret = _DisplayConfigGetDeviceInfo(byref(name.header))
    return name.adapterDevicePath if ret == 0 else ""


def get_monitor_device_path(path) -> str:
    """获取路径对应的显示器设备路径。"""
    tname = DISPLAYCONFIG_TARGET_DEVICE_NAME()
    tname.header.type = DISPLAYCONFIG_DEVICE_INFO_GET_TARGET_NAME
    tname.header.size = sizeof(DISPLAYCONFIG_TARGET_DEVICE_NAME)
    tname.header.adapterId = path.targetInfo.adapterId
    tname.header.id = path.targetInfo.id
    ret = _DisplayConfigGetDeviceInfo(byref(tname.header))
    return tname.monitorDevicePath if ret == 0 else ""


def query_active_config() -> tuple | None:
    """查询当前活动显示配置（内部缓存，apply_config 成功后自动失效）。"""
    global _QDC_CACHE
    if _QDC_CACHE is not None:
        return _QDC_CACHE

    path_count = c_uint32(0)
    mode_count = c_uint32(0)

    ret = _GetDisplayConfigBufferSizes(QDC_ONLY_ACTIVE_PATHS, byref(path_count), byref(mode_count))
    if ret != 0:
        logger.error("GetDisplayConfigBufferSizes (active) 失败, 错误码=%d", ret)
        return None

    paths = (DISPLAYCONFIG_PATH_INFO * path_count.value)()
    modes = (DISPLAYCONFIG_MODE_INFO * mode_count.value)()

    ret = _QueryDisplayConfig(
        QDC_ONLY_ACTIVE_PATHS, byref(path_count), paths,
        byref(mode_count), modes, None,
    )
    if ret != 0:
        logger.error("QueryDisplayConfig (active) 失败, 错误码=%d", ret)
        return None

    _QDC_CACHE = (paths, modes, path_count.value, mode_count.value)
    return _QDC_CACHE


def query_all_config() -> tuple | None:
    """查询所有显示配置（含已断开的），同上返回格式（内部缓存，apply_config 成功后自动失效）。"""
    global _QDC_ALL_CACHE
    if _QDC_ALL_CACHE is not None:
        return _QDC_ALL_CACHE
    path_count = c_uint32(0)
    mode_count = c_uint32(0)

    ret = _GetDisplayConfigBufferSizes(QDC_ALL_PATHS, byref(path_count), byref(mode_count))
    if ret != 0:
        logger.error("GetDisplayConfigBufferSizes (all) 失败, 错误码=%d", ret)
        return None

    paths = (DISPLAYCONFIG_PATH_INFO * path_count.value)()
    modes = (DISPLAYCONFIG_MODE_INFO * mode_count.value)()

    ret = _QueryDisplayConfig(
        QDC_ALL_PATHS, byref(path_count), paths,
        byref(mode_count), modes, None,
    )
    if ret != 0:
        logger.error("QueryDisplayConfig (all) 失败, 错误码=%d", ret)
        return None

    _QDC_ALL_CACHE = (paths, modes, path_count.value, mode_count.value)
    return _QDC_ALL_CACHE


def get_screen_size_mm(gdi_name: str) -> tuple[int, int]:
    """获取显示器物理尺寸（mm），通过 GDI CreateDCW + GetDeviceCaps。"""
    if not gdi_name:
        return 0, 0
    HORZSIZE = 4
    VERTSIZE = 6
    dc = None
    try:
        dc = _CreateDCW("DISPLAY", gdi_name, None, None)
        if not dc:
            return 0, 0
        return _GetDeviceCaps(dc, HORZSIZE), _GetDeviceCaps(dc, VERTSIZE)
    except OSError:
        return 0, 0
    finally:
        if dc:
            _DeleteDC(dc)


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


def get_resolution_refresh_via_enum(gdi_name: str) -> tuple[int, int, float, int]:
    """使用 EnumDisplaySettings 获取分辨率、刷新率、色深。"""
    dm = DEVMODE()
    dm.dmSize = sizeof(DEVMODE)
    ret = _EnumDisplaySettings(gdi_name, ENUM_CURRENT_SETTINGS, byref(dm))
    if not ret:
        return 0, 0, 0.0, 32
    return dm.dmPelsWidth, dm.dmPelsHeight, float(dm.dmDisplayFrequency), dm.dmBitsPerPel


SDC_ERROR_MESSAGES = {
    5: "拒绝访问（请以管理员身份运行）",
    31: "一般性故障（驱动可能不支持操作）",
    50: "操作不受支持",
    87: "参数无效",
    1610: "显示配置无效（虚拟显示器驱动可能干扰）",
}

def apply_config(paths, path_count: int, modes, mode_count: int, flags: int | None = None) -> bool:
    """应用显示配置，成功后自动失效 QDC 缓存。"""
    if flags is None:
        flags = (
            SDC_APPLY | SDC_USE_SUPPLIED_DISPLAY_CONFIG
            | SDC_ALLOW_CHANGES | SDC_SAVE_TO_DATABASE
        )
    ret = _SetDisplayConfig(path_count, paths, mode_count, modes, flags)
    if ret == 0:
        _invalidate_qdc_cache()
        return True
    msg = SDC_ERROR_MESSAGES.get(ret, f"未知错误码 {ret}")
    logger.error("SetDisplayConfig 失败: %s", msg)
    return False


def set_display_config_available() -> bool:
    """检测 SetDisplayConfig 是否可用（OrayIddDriver 可能破坏 SDC）。"""
    global _SDC_AVAILABLE
    if _SDC_AVAILABLE is not None:
        return _SDC_AVAILABLE
    pc = c_uint32(0)
    mc = c_uint32(0)
    try:
        ret = _GetDisplayConfigBufferSizes(QDC_ONLY_ACTIVE_PATHS, pc, mc)
        _SDC_AVAILABLE = (ret == 0)
    except OSError:
        _SDC_AVAILABLE = False
    if not _SDC_AVAILABLE:
        logger.warning("SetDisplayConfig 不可用（可能虚拟显示器驱动干扰），部分功能将受限。")
    return _SDC_AVAILABLE


def find_path_idx(paths, count: int, device_name: str) -> int | None:
    """通过 GDI 设备名查找路径在数组中的索引。"""
    for i in range(count):
        gdi_name = get_gdi_name(paths[i])
        if gdi_name == device_name:
            return i
    return None


def filter_valid_paths(paths, path_count: int, modes, mode_count: int) -> list[int]:
    """过滤出有效路径：mode 索引需指向对应类型的 mode 条目。"""
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


def apply_filtered(paths, path_count: int, modes, mode_count: int, flags: int | None = None) -> bool:
    """过滤出有效路径后应用配置（避免虚拟显示器幽灵路径导致 SDC 失败）。"""
    valid_idxs = filter_valid_paths(paths, path_count, modes, mode_count)
    if not valid_idxs:
        logger.warning("所有 %d 个路径均被过滤（无效 mode 索引），跳过 SetDisplayConfig", path_count)
        return False
    valid = (DISPLAYCONFIG_PATH_INFO * len(valid_idxs))()
    for dest, src_idx in enumerate(valid_idxs):
        valid[dest] = paths[src_idx]
    return apply_config(valid, len(valid_idxs), modes, mode_count, flags)
