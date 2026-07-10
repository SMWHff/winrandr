"""缺失 mode 条目的检测与修复（虚拟驱动可能导致 QDC 返回不完整数据）。"""

import logging
from ctypes import byref, sizeof

from winrandr.win32.bindings import (
    _CreateDCW,
    _DeleteDC,
    _EnumDisplaySettings,
    _GetDeviceCaps,
)
from winrandr.win32.constants import (
    DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE,
    DISPLAYCONFIG_MODE_INFO_TYPE_TARGET,
    DISPLAYCONFIG_PATH_MODE_IDX_INVALID,
    ENUM_CURRENT_SETTINGS,
)
from winrandr.win32.structures import DEVMODE, DISPLAYCONFIG_MODE_INFO, DISPLAYCONFIG_PATH_INFO

logger = logging.getLogger(__name__)


def _fill_source_mode(
    mode: DISPLAYCONFIG_MODE_INFO,
    p: DISPLAYCONFIG_PATH_INFO,
    gdi: str,
) -> None:
    """用 EnumDisplaySettings 或 CreateDCW 填充缺失的 SOURCE mode 条目。"""
    dm = DEVMODE()
    dm.dmSize = sizeof(DEVMODE)
    if _EnumDisplaySettings(gdi, ENUM_CURRENT_SETTINGS, byref(dm)):
        w, h = dm.dmPelsWidth, dm.dmPelsHeight
    else:
        dc = _CreateDCW("DISPLAY", gdi, None, None)
        if not dc:
            return
        w = _GetDeviceCaps(dc, 8)
        h = _GetDeviceCaps(dc, 10)
        _DeleteDC(dc)
    mode.infoType = DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE
    mode.adapterId = p.sourceInfo.adapterId
    mode.id = p.sourceInfo.id
    mode._union.sourceMode.width = w
    mode._union.sourceMode.height = h


def _fill_target_mode(
    mode: DISPLAYCONFIG_MODE_INFO,
    p: DISPLAYCONFIG_PATH_INFO,
    gdi: str,
) -> None:
    """用 EnumDisplaySettings 或 CreateDCW 填充缺失的 TARGET mode 条目。"""
    dm = DEVMODE()
    dm.dmSize = sizeof(DEVMODE)
    if _EnumDisplaySettings(gdi, ENUM_CURRENT_SETTINGS, byref(dm)):
        w, h, rr = dm.dmPelsWidth, dm.dmPelsHeight, dm.dmDisplayFrequency
    else:
        dc = _CreateDCW("DISPLAY", gdi, None, None)
        if not dc:
            return
        w = _GetDeviceCaps(dc, 8)
        h = _GetDeviceCaps(dc, 10)
        rr = _GetDeviceCaps(dc, 116)
        _DeleteDC(dc)
    mode.infoType = DISPLAYCONFIG_MODE_INFO_TYPE_TARGET
    mode.adapterId = p.targetInfo.adapterId
    mode.id = p.targetInfo.id
    sig = mode._union.targetMode.targetVideoSignalInfo
    sig.activeSize.cx = w
    sig.activeSize.cy = h
    sig.vSyncFreq.Numerator = rr
    sig.vSyncFreq.Denominator = 1
    sig.pixelRate = w * h * rr
    sig.totalSize.cx = w
    sig.totalSize.cy = h
    sig.hSyncFreq.Numerator = w * rr
    sig.hSyncFreq.Denominator = 1
    sig.scanLineOrdering = 0


def _fill_missing_modes(
    new_modes: DISPLAYCONFIG_MODE_INFO,
    p: DISPLAYCONFIG_PATH_INFO,
    gdi: str,
    mode_count: int,
    new_count: int,
) -> None:
    """为单个路径填充缺失的 SOURCE/TARGET mode 条目。"""
    smi = p.sourceInfo.modeInfoIdx
    tmi = p.targetInfo.modeInfoIdx
    if smi != DISPLAYCONFIG_PATH_MODE_IDX_INVALID and smi >= mode_count and smi < new_count:
        if new_modes[smi].infoType == 0:
            _fill_source_mode(new_modes[smi], p, gdi)
    if tmi != DISPLAYCONFIG_PATH_MODE_IDX_INVALID and tmi >= mode_count and tmi < new_count:
        if new_modes[tmi].infoType == 0:
            _fill_target_mode(new_modes[tmi], p, gdi)


def repair_mode_array(
    paths: DISPLAYCONFIG_PATH_INFO,
    path_count: int,
    modes: DISPLAYCONFIG_MODE_INFO,
    mode_count: int,
    get_gdi_name_fn,  # noqa: ANN001
) -> tuple[DISPLAYCONFIG_MODE_INFO, int]:
    """检测越界的 modeInfoIdx，用 EnumDisplaySettings/CreateDCW 补充缺失的 mode 条目。"""
    new_count = mode_count
    for i in range(path_count):
        for idx in (paths[i].sourceInfo.modeInfoIdx, paths[i].targetInfo.modeInfoIdx):
            if idx != DISPLAYCONFIG_PATH_MODE_IDX_INVALID and idx >= new_count:
                new_count = idx + 1

    if new_count == mode_count:
        return modes, mode_count

    new_modes = (DISPLAYCONFIG_MODE_INFO * new_count)()
    for j in range(mode_count):
        new_modes[j] = modes[j]

    for i in range(path_count):
        gdi = get_gdi_name_fn(paths[i])
        if gdi:
            _fill_missing_modes(new_modes, paths[i], gdi, mode_count, new_count)

    logger.warning("mode 数组从 %d 扩展至 %d（虚拟驱动导致 QDC 返回不完整数据）", mode_count, new_count)
    return new_modes, new_count
