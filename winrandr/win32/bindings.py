"""Win32 API 函数绑定（ctypes 声明）。"""
import ctypes
from ctypes import wintypes, POINTER

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
    DISPLAYCONFIG_ADAPTER_NAME,
    DISPLAYCONFIG_DEVICE_INFO_HEADER,
    DISPLAY_DEVICE, DEVMODE, LUID, c_uint32,
)

_user32 = ctypes.windll.user32
_gdi32 = ctypes.windll.gdi32

# ── 显示配置 API ──

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

# ── GDI 函数绑定 ──

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
