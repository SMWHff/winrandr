"""显示器配置存档管理（Profile）。"""

import json
import logging
import os
import sys
from datetime import datetime

from winrandr import __version__
from winrandr.api import list_displays

logger = logging.getLogger(__name__)

_CONFIG_DIR = os.path.join(
    os.environ.get("APPDATA", os.path.join(os.path.expanduser("~"), ".config")),
    "winrandr",
)
_PROFILES_FILE = os.path.join(_CONFIG_DIR, "profiles.json")


def _load_all() -> dict:
    if not os.path.exists(_PROFILES_FILE):
        return {}
    try:
        with open(_PROFILES_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        logger.exception("读取配置文件失败")
        return {}


def _save_all(data: dict) -> bool:
    os.makedirs(_CONFIG_DIR, exist_ok=True)
    try:
        with open(_PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError:
        logger.exception("写入配置文件失败")
        return False
    else:
        return True


def preview_save() -> list[str]:
    """预览存档将要保存的显示器配置，返回可读行列表。"""
    displays = list_displays()
    if not displays:
        return ["未检测到活动显示器"]
    lines = [f"将保存以下 {len(displays)} 台显示器的配置："]
    for d in displays:
        sn = d.name.replace("\\\\.\\", "")
        primary = " (主)" if d.is_primary else ""
        rot = f" {d.rotation}°" if d.rotation else ""
        lines.append(
            f"  {sn}: {d.width}x{d.height} @ {d.refresh_rate}Hz 位置({d.position_x},{d.position_y}){rot}{primary}",
        )
    return lines


def save_profile(name: str) -> bool:
    """保存当前显示器配置为指定名称的存档。"""
    displays = list_displays()
    if not displays:
        logger.warning("未检测到活动显示器，无法存档")
        print("错误: 未检测到活动显示器，无法存档", file=sys.stderr)
        return False

    configs = []
    for d in displays:
        configs.append(
            {
                "name": d.name,
                "x": d.position_x,
                "y": d.position_y,
                "width": d.width,
                "height": d.height,
                "refresh_rate": d.refresh_rate,
                "rotation": d.rotation,
                "is_primary": d.is_primary,
            }
        )

    data = _load_all()
    data[name] = {
        "displays": configs,
        "created": datetime.now().isoformat(),
        "version": __version__,
    }
    if not _save_all(data):
        return False
    logger.info("已保存存档: %s (%d 个显示器)", name, len(configs))
    return True


def diff_profile(name: str) -> list[str]:
    """比较当前配置与存档的差异，返回人类可读的变更列表。"""
    data = _load_all()
    profile = data.get(name)
    if not profile:
        return ["未找到存档"]

    current = {d.name: d for d in list_displays()}
    lines = [f"存档「{name}」将要执行的变更："]
    configs = profile["displays"]
    found = False

    for dc in configs:
        dn = dc["name"]
        cur = current.get(dn)
        if not cur:
            lines.append(f"  ⚠ {dn}: 当前未连接，跳过")
            continue
        found = True
        changes = []
        sn = dn.replace("\\\\.\\", "")
        if (cur.position_x, cur.position_y) != (dc["x"], dc["y"]):
            changes.append(f"位置 ({cur.position_x},{cur.position_y})→({dc['x']},{dc['y']})")
        if cur.rotation != dc["rotation"]:
            changes.append(f"旋转 {cur.rotation}°→{dc['rotation']}°")
        if (cur.width, cur.height, cur.refresh_rate) != (dc["width"], dc["height"], dc["refresh_rate"]):
            changes.append(f"分辨率 {cur.width}x{cur.height}→{dc['width']}x{dc['height']}")
        if dc["is_primary"] and not cur.is_primary:
            changes.append("设为主显示器")
        if changes:
            lines.append(f"  {sn}: {', '.join(changes)}")
        else:
            lines.append(f"  {sn}: 无变更")

    if not found:
        lines.append("  所有显示器均未连接，无法恢复")
    return lines


def load_profile(name: str) -> bool:  # noqa: C901  # 循环中含多条 API 调用，分支多但线性
    """恢复指定名称的显示器配置存档。"""
    data = _load_all()
    profile = data.get(name)
    if not profile:
        logger.error("未找到存档: %s", name)
        print(f"错误: 未找到存档「{name}」", file=sys.stderr)
        return False

    from winrandr.api import (
        set_auto,
        set_position,
        set_primary,
        set_resolution,
        set_rotation,
    )

    configs = profile["displays"]
    current = {d.name for d in list_displays()}
    success = True

    for dc in configs:
        dn = dc["name"]
        if dn not in current:
            msg = f"显示器 {dn} 不在当前连接中，跳过"
            logger.warning(msg)
            print(f"警告: {msg}", file=sys.stderr)
            continue
        if not set_auto(dn):
            msg = f"启用显示器 {dn} 失败"
            logger.warning(msg)
            print(f"警告: {msg}", file=sys.stderr)
            success = False
            continue
        if not set_position(dn, dc["x"], dc["y"]):
            msg = f"设置 {dn} 位置失败"
            logger.warning(msg)
            print(f"警告: {msg}", file=sys.stderr)
            success = False
        if not set_rotation(dn, dc["rotation"]):
            msg = f"设置 {dn} 旋转失败"
            logger.warning(msg)
            print(f"警告: {msg}", file=sys.stderr)
            success = False
        if not set_resolution(dn, dc["width"], dc["height"], dc["refresh_rate"]):
            msg = f"设置 {dn} 分辨率失败"
            logger.warning(msg)
            print(f"警告: {msg}", file=sys.stderr)
            success = False

    # 最后设置主显示器
    for dc in configs:
        dn = dc["name"]
        if dn in current and dc["is_primary"]:
            if not set_primary(dn):
                msg = f"设置 {dn} 为主显示器失败"
                logger.warning(msg)
                print(f"警告: {msg}", file=sys.stderr)
                success = False
            break

    logger.info("已加载存档: %s", name)
    return success


def list_profiles() -> list[dict[str, str | int | list[str]]]:
    """列出所有存档及其基本信息。"""
    data = _load_all()
    result = []
    for name, info in data.items():
        displays_raw = info.get("displays", [])
        display_summary = []
        for d in displays_raw:
            sn = d.get("name", "?").replace("\\\\.\\", "")
            if "width" in d and "height" in d:
                display_summary.append(f"{sn}({d['width']}x{d['height']})")
            else:
                display_summary.append(sn)
        result.append(
            {
                "name": name,
                "display_count": len(displays_raw),
                "displays": display_summary,
                "created": info.get("created", ""),
                "version": info.get("version", ""),
            }
        )
    return sorted(result, key=lambda x: x["name"])


def delete_profile(name: str) -> bool:
    """删除指定名称的存档。"""
    data = _load_all()
    if name not in data:
        logger.error("未找到存档: %s", name)
        return False
    del data[name]
    if not _save_all(data):
        return False
    logger.info("已删除存档: %s", name)
    return True


def get_profile_names() -> list[str]:
    """返回所有存档名称的列表。"""
    return sorted(_load_all().keys())
