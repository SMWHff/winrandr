"""EDID 读取与解析：从注册表读取显示器 EDID 并解析为可读字段。"""

import logging
import winreg
from ctypes import sizeof, byref
from datetime import datetime

from winrandr.win32.structures import DISPLAY_DEVICE
from winrandr.win32.bindings import _EnumDisplayDevices

logger = logging.getLogger(__name__)

_EDID_MFG_CODES = {
    0x05E: "AOC", 0x06E: "AMI", 0x08D: "CAN", 0x09D: "CIN", 0x0AC: "DBL",
    0x10D: "CPL", 0x1B0: "GLM", 0x20C: "CIT", 0x22D: "LEN", 0x223: "LPL",
    0x224: "LPK", 0x258: "MAG", 0x259: "MAX", 0x25E: "MEL", 0x264: "MIR",
    0x26D: "NEC", 0x2A3: "OPT", 0x2A9: "ORN", 0x2B8: "PNA", 0x2D2: "FUS",
    0x2D3: "PTR", 0x2E5: "QDS", 0x30E: "SAM", 0x33C: "SMI", 0x34A: "SNY",
    0x366: "STD", 0x369: "STN", 0x38B: "TRL", 0x3A2: "UNE", 0x3A3: "UNY",
    0x3AA: "VSC", 0x3B0: "WTC", 0x3C7: "XMI", 0x3CE: "YOK", 0x400: "ZCM",
}


def _find_edid_desc(data: bytes, tag: int) -> str | None:
    """从 EDID 描述符块（54-126，步长 18）查找指定 tag 的字符串。"""
    for offset in range(54, 126, 18):
        if data[offset] == 0x00 and data[offset + 1] == 0x00 and data[offset + 3] == tag:
            raw = data[offset + 5:offset + 18]
            try:
                return raw.split(b'\x0a')[0].decode('ascii').strip()
            except ValueError:
                return None
    return None


def _find_edid_name(data: bytes) -> str | None:
    return _find_edid_desc(data, 0xFC)


def _find_edid_serial(data: bytes) -> str | None:
    return _find_edid_desc(data, 0xFF)


def _parse_edid(data: bytes) -> dict[str, str]:
    """解析 EDID 二进制数据，返回可读的显示器信息。"""
    if len(data) < 128 or data[0:8] != b'\x00\xff\xff\xff\xff\xff\xff\x00':
        return {"edid_raw": data[:128].hex().upper()[:64] + "..." if data else "unavailable"}

    info = {}
    mfg_id = (data[8] << 8) | data[9]
    mfg = "".join(chr(ord('A') + ((mfg_id >> (10 - i * 5)) & 0x1F) - 1) for i in range(3))
    info["edid_mfg"] = _EDID_MFG_CODES.get(mfg_id, mfg)
    name = _find_edid_name(data)
    info["edid_product"] = f"{(data[10] | (data[11] << 8)):04X}"
    if name:
        info["edid_name"] = name
    serial = _find_edid_serial(data)
    if serial:
        info["edid_serial"] = serial
    week, year_n = data[16], data[17] + 1990
    if 1 <= week <= 52:
        info["edid_date"] = datetime.fromisocalendar(year_n, week, 5).strftime("%Y-%m-%d")
    else:
        info["edid_date"] = str(year_n)

    info["edid_version"] = f"{data[18]}.{data[19]}"
    if data[21] or data[22]:
        info["edid_size"] = f"{data[21]}x{data[22]} cm"
    info["edid_desc"] = f"{info['edid_mfg']} {name or info['edid_product']} ({info['edid_version']})"
    return info


def get_edid(gdi_name: str) -> dict[str, str]:
    """从注册表读取指定显示器的 EDID 并解析。"""
    dd = DISPLAY_DEVICE()
    dd.cb = sizeof(DISPLAY_DEVICE)
    if not _EnumDisplayDevices(gdi_name, 0, byref(dd), 0):
        return {}
    if not dd.DeviceID:
        return {}
    parts = dd.DeviceID.split("\\")
    if len(parts) < 2:
        return {}
    base = f"SYSTEM\\CurrentControlSet\\Enum\\DISPLAY\\{parts[1]}"
    try:
        parent = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base)
    except OSError:
        return {}
    i = 0
    try:
        while True:
            inst = winreg.EnumKey(parent, i)
            i += 1
            try:
                key = winreg.OpenKey(parent, f"{inst}\\Device Parameters")
                edid_data, _ = winreg.QueryValueEx(key, "EDID")
                winreg.CloseKey(key)
                winreg.CloseKey(parent)
                return _parse_edid(edid_data)
            except OSError:
                continue
    except OSError:
        pass
    winreg.CloseKey(parent)
    return {}
