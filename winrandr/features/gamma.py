"""伽马校正与亮度控制。"""

import logging
from ctypes import c_uint16

from winrandr.win32.bindings import _CreateDCW, _DeleteDC, _GetDeviceGammaRamp, _SetDeviceGammaRamp

logger = logging.getLogger(__name__)


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
            logger.error("无法为 %s 创建设备上下文（远程桌面或驱动限制）", device_name)
            return False
        try:
            ramp = (c_uint16 * (3 * 256))()
            if not _GetDeviceGammaRamp(dc, ramp):
                logger.error("无法获取 %s 的伽马校正表（驱动可能不支持）", device_name)
                return False
            for i in range(3 * 256):
                val = int(ramp[i] * brightness)
                ramp[i] = max(0, min(65535, val))
            if not _SetDeviceGammaRamp(dc, ramp):
                logger.error("无法设置 %s 的伽马校正表（驱动拒绝写入）", device_name)
                return False
            logger.debug("设置 %s 亮度为 %.2f", device_name, brightness)
            return True
        finally:
            _DeleteDC(dc)
    except Exception as e:
        logger.error("设置亮度失败（%.2f）: %s", brightness, e)
        return False


def set_gamma(device_name: str, red: float, green: float, blue: float) -> bool:
    """设置伽马校正（三通道独立，与 xrandr --gamma 一致）。"""
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
            for i in range(256):
                ramp[i] = max(0, min(65535, int(ramp[i] * red)))
            for i in range(256, 512):
                ramp[i] = max(0, min(65535, int(ramp[i] * green)))
            for i in range(512, 768):
                ramp[i] = max(0, min(65535, int(ramp[i] * blue)))
            if not _SetDeviceGammaRamp(dc, ramp):
                logger.error("无法设置 %s 的伽马校正表（驱动拒绝写入）", device_name)
                return False
            logger.debug("设置 %s 伽马为 R=%.2f G=%.2f B=%.2f", device_name, red, green, blue)
            return True
        finally:
            _DeleteDC(dc)
    except Exception as e:
        logger.error("设置伽马校正失败（R=%.2f G=%.2f B=%.2f）: %s", red, green, blue, e)
        return False
