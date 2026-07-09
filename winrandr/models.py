"""显示器和显示模式的数据模型。"""

from dataclasses import dataclass, field
from typing import NamedTuple

from winrandr.win32.structures import DISPLAYCONFIG_MODE_INFO, DISPLAYCONFIG_PATH_INFO

__all__ = ["DisplayInfo", "DisplayMode", "QdcConfig"]


class QdcConfig(NamedTuple):
    """QueryDisplayConfig 返回的四元组封装。"""

    paths: DISPLAYCONFIG_PATH_INFO
    modes: DISPLAYCONFIG_MODE_INFO
    path_count: int
    mode_count: int


@dataclass
class DisplayMode:
    """单个显示模式（分辨率 + 刷新率 + 标记）。"""

    width: int
    height: int
    refresh_rate: float
    is_current: bool = False
    is_preferred: bool = False


@dataclass
class DisplayInfo:
    """显示器信息。"""

    name: str
    friendly_name: str
    connected: bool = True
    width: int = 0
    height: int = 0
    refresh_rate: float = 0.0
    position_x: int = 0
    position_y: int = 0
    is_primary: bool = False
    rotation: int = 0
    width_mm: int = 0
    height_mm: int = 0
    modes: list[DisplayMode] = field(default_factory=list)
    properties: dict[str, str] | None = None
