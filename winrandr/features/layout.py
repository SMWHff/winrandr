"""显示器布局管理：位置、旋转、主屏、关闭、相对定位。"""

import logging

from winrandr.win32.bindings import (
    set_display_config_available, query_active_config, get_gdi_name,
    find_path_idx, apply_filtered, apply_config,
)
from winrandr.win32.constants import ROTATION_MAP, DISPLAYCONFIG_PATH_MODE_IDX_INVALID
from winrandr.win32.structures import DISPLAYCONFIG_PATH_INFO

logger = logging.getLogger(__name__)


def _short_name(name: str) -> str:
    """提取短名称（去掉 \\\\.\\ 前缀）。"""
    return name.split("\\")[-1]


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


def set_position_relative(device_name: str, reference_name: str, relation: str) -> bool:
    """相对定位，类似 xrandr --left-of / --right-of / --above / --below / --same-as。"""
    from winrandr.api import list_displays

    displays = list_displays()

    target = ref = None
    for d in displays:
        if not d.connected:
            continue
        sn = _short_name(d.name)
        if sn == _short_name(device_name) or d.name == device_name:
            target = d
        if sn == _short_name(reference_name) or d.name == reference_name:
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
    x, y = pos_map.get(relation)
    if x is None:
        logger.error("无效相对位置关系: %s", relation)
        return False
    return set_position(device_name, x, y)


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


def set_reflect(device_name: str, axis: str) -> bool:
    """设置显示器镜像翻转。

    在 Windows 上仅支持 xy（等同于 180° 旋转）。
    """
    if axis == "xy":
        return set_rotation(device_name, 180)
    logger.error("不支持 --reflect %s（Windows 仅支持 xy = 旋转 180°）", axis)
    return False
