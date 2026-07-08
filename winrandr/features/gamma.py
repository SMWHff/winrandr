"""伽马校正、亮度控制与显示器识别。"""

import logging
import time
from collections.abc import Callable
from ctypes import c_uint16

from winrandr.win32.bindings import (
    _CreateDCW,
    _DeleteDC,
    _GetDeviceGammaRamp,
    _SetDeviceGammaRamp,
)

logger = logging.getLogger(__name__)


def _apply_gamma(device_name: str, modifier: Callable) -> bool:
    """伽马校正表通用操作：创建 DC、获取、修改、写回、清理。"""
    try:
        dc = _CreateDCW("DISPLAY", device_name, None, None)
        if not dc:
            logger.error("无法为 %s 创建设备上下文（远程桌面或驱动限制）", device_name)
            return False
        try:
            ramp = (c_uint16 * (3 * 256))()
            if not _GetDeviceGammaRamp(dc, ramp):
                logger.error("无法获取 %s 的伽马校正表（驱动可能不支持）", device_name)
                return False
            modifier(ramp)
            if not _SetDeviceGammaRamp(dc, ramp):
                logger.error("无法设置 %s 的伽马校正表（驱动拒绝写入）", device_name)
                return False
            return True
        finally:
            _DeleteDC(dc)
    except OSError:
        logger.exception("伽马校正操作异常")
        return False


def set_brightness(device_name: str, brightness: float) -> bool:
    """通过伽马校正设置显示器亮度。

    brightness: 0.1-2.0 范围，1.0 为正常。方式同 xrandr --brightness。
    """
    if brightness < 0:
        logger.error("亮度值不能为负数: %g", brightness)
        return False

    def _modify(ramp):
        for i in range(3 * 256):
            ramp[i] = max(0, min(65535, int(ramp[i] * brightness)))

    ok = _apply_gamma(device_name, _modify)
    if ok:
        logger.debug("设置 %s 亮度为 %.2f", device_name, brightness)
    return ok


def set_gamma(device_name: str, red: float, green: float, blue: float) -> bool:
    """设置伽马校正（三通道独立，与 xrandr --gamma 一致）。"""
    def _modify(ramp):
        for i in range(256):
            ramp[i] = max(0, min(65535, int(ramp[i] * red)))
        for i in range(256, 512):
            ramp[i] = max(0, min(65535, int(ramp[i] * green)))
        for i in range(512, 768):
            ramp[i] = max(0, min(65535, int(ramp[i] * blue)))

    ok = _apply_gamma(device_name, _modify)
    if ok:
        logger.debug("设置 %s 伽马为 R=%.2f G=%.2f B=%.2f", device_name, red, green, blue)
    return ok


def identify_display(device_name: str, duration: float = 2.0) -> bool:
    """通过闪烁屏幕帮助识别指定显示器（闪 3 次后恢复原状）。"""
    try:
        dc = _CreateDCW("DISPLAY", device_name, None, None)
    except OSError:
        logger.exception("识别显示器操作异常")
        return False
    if not dc:
        logger.error("无法为 %s 创建设备上下文", device_name)
        return False

    saved = (c_uint16 * (3 * 256))()
    try:
        ramp = (c_uint16 * (3 * 256))()
        if not _GetDeviceGammaRamp(dc, ramp):
            logger.error("无法获取 %s 的伽马校正表", device_name)
            return False
        for i in range(3 * 256):
            saved[i] = ramp[i]

        flash = (c_uint16 * (3 * 256))()
        for i in range(3 * 256):
            flash[i] = 65535
        blank = (c_uint16 * (3 * 256))()

        interval = duration / 6
        for _ in range(3):
            _SetDeviceGammaRamp(dc, flash)
            time.sleep(interval)
            _SetDeviceGammaRamp(dc, blank)
            time.sleep(interval)
    finally:
        _SetDeviceGammaRamp(dc, saved)
        _DeleteDC(dc)
    return True
