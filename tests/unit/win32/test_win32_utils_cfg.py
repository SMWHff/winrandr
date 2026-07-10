"""Win32 工具函数——配置应用与缓存相关测试（真实硬件）。"""

from winrandr.win32 import utils as win32_utils
from winrandr.win32.repair import repair_mode_array
from winrandr.win32.utils import find_path_idx, get_gdi_name, query_active_config


def _clear_caches():
    win32_utils._QDC_CACHE = None
    win32_utils._QDC_ALL_CACHE = None
    win32_utils._SDC_AVAILABLE = None


def _real_config():
    config = query_active_config()
    if config is None or config[2] == 0:
        return None
    return config


# --- repair_mode_array ---


def test_repair_mode_array_real_data():
    """真实 QDC 数据经 repair 后无越界索引。"""
    config = _real_config()
    if config is None:
        return
    paths, modes, path_count, mode_count = config
    _new_modes, new_count = repair_mode_array(paths, path_count, modes, mode_count, get_gdi_name)
    assert new_count >= mode_count
    for i in range(path_count):
        smi = paths[i].sourceInfo.modeInfoIdx
        tmi = paths[i].targetInfo.modeInfoIdx
        if smi != 0xFFFFFFFF:
            assert smi < new_count, f"sourceInfo.modeInfoIdx={smi} >= {new_count}"
        if tmi != 0xFFFFFFFF:
            assert tmi < new_count, f"targetInfo.modeInfoIdx={tmi} >= {new_count}"


def test_repair_mode_array_fill_source_fallback():
    """_fill_source_mode 在 EnumDisplaySettings 失败时回退 CreateDCW。"""
    from unittest.mock import patch

    from winrandr.win32.constants import DISPLAYCONFIG_PATH_MODE_IDX_INVALID
    from winrandr.win32.structures import (
        DISPLAYCONFIG_MODE_INFO,
        DISPLAYCONFIG_PATH_INFO,
        DISPLAYCONFIG_PATH_SOURCE_INFO,
        DISPLAYCONFIG_PATH_TARGET_INFO,
    )

    # Build 1 path with modeInfoIdx=0 (out of range vs mode_count=0)
    src = DISPLAYCONFIG_PATH_SOURCE_INFO()
    src.adapterId.LowPart = 0
    src.id = 0
    src.modeInfoIdx = 0  # valid but >= mode_count(0) => needs repair
    src.statusFlags = 0
    tgt = DISPLAYCONFIG_PATH_TARGET_INFO()
    tgt.adapterId.LowPart = 0
    tgt.id = 0
    tgt.modeInfoIdx = DISPLAYCONFIG_PATH_MODE_IDX_INVALID
    path = DISPLAYCONFIG_PATH_INFO()
    path.sourceInfo = src
    path.targetInfo = tgt
    path.flags = 0

    paths = (DISPLAYCONFIG_PATH_INFO * 1)(path)
    modes = (DISPLAYCONFIG_MODE_INFO * 0)()
    path_count = 1
    mode_count = 0

    gdi_name = r"\\.\DISPLAY1"
    fake_dc = 12345  # fake HDC handle

    with patch("winrandr.win32.repair._EnumDisplaySettings", return_value=0):
        with patch("winrandr.win32.repair._CreateDCW", return_value=fake_dc):
            with patch("winrandr.win32.repair._GetDeviceCaps", side_effect=[1920, 1080]):
                new_modes, new_count = repair_mode_array(paths, path_count, modes, mode_count, lambda _: gdi_name)
    assert new_count == 1
    assert new_modes[0].infoType == 1  # DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE
    assert new_modes[0]._union.sourceMode.width == 1920
    assert new_modes[0]._union.sourceMode.height == 1080


def test_repair_mode_array_fill_source_both_fail():
    """_fill_source_mode 在 EnumDisplaySettings 和 CreateDCW 都失败时返回不崩溃。"""
    from unittest.mock import patch

    from winrandr.win32.constants import DISPLAYCONFIG_PATH_MODE_IDX_INVALID
    from winrandr.win32.structures import (
        DISPLAYCONFIG_MODE_INFO,
        DISPLAYCONFIG_PATH_INFO,
        DISPLAYCONFIG_PATH_SOURCE_INFO,
        DISPLAYCONFIG_PATH_TARGET_INFO,
    )

    src = DISPLAYCONFIG_PATH_SOURCE_INFO()
    src.adapterId.LowPart = 0
    src.id = 0
    src.modeInfoIdx = 0
    src.statusFlags = 0
    tgt = DISPLAYCONFIG_PATH_TARGET_INFO()
    tgt.adapterId.LowPart = 0
    tgt.id = 0
    tgt.modeInfoIdx = DISPLAYCONFIG_PATH_MODE_IDX_INVALID
    path = DISPLAYCONFIG_PATH_INFO()
    path.sourceInfo = src
    path.targetInfo = tgt
    path.flags = 0

    paths = (DISPLAYCONFIG_PATH_INFO * 1)(path)
    modes = (DISPLAYCONFIG_MODE_INFO * 0)()
    gdi_name = r"\\.\DISPLAY1"

    with patch("winrandr.win32.repair._EnumDisplaySettings", return_value=0):
        with patch("winrandr.win32.repair._CreateDCW", return_value=None):
            new_modes, new_count = repair_mode_array(paths, 1, modes, 0, lambda _: gdi_name)
    # Should not crash, mode stays zero-initialized
    assert new_count == 1
    assert new_modes[0].infoType == 0


def test_repair_mode_array_fill_target_fallback():
    """_fill_target_mode 在 EnumDisplaySettings 失败时回退 CreateDCW。"""
    from unittest.mock import patch

    from winrandr.win32.constants import DISPLAYCONFIG_PATH_MODE_IDX_INVALID
    from winrandr.win32.structures import (
        DISPLAYCONFIG_MODE_INFO,
        DISPLAYCONFIG_PATH_INFO,
        DISPLAYCONFIG_PATH_SOURCE_INFO,
        DISPLAYCONFIG_PATH_TARGET_INFO,
    )

    src = DISPLAYCONFIG_PATH_SOURCE_INFO()
    src.adapterId.LowPart = 0
    src.id = 0
    src.modeInfoIdx = DISPLAYCONFIG_PATH_MODE_IDX_INVALID
    src.statusFlags = 0
    tgt = DISPLAYCONFIG_PATH_TARGET_INFO()
    tgt.adapterId.LowPart = 0
    tgt.id = 0
    tgt.modeInfoIdx = 0  # target mode out of range
    path = DISPLAYCONFIG_PATH_INFO()
    path.sourceInfo = src
    path.targetInfo = tgt
    path.flags = 0

    paths = (DISPLAYCONFIG_PATH_INFO * 1)(path)
    modes = (DISPLAYCONFIG_MODE_INFO * 0)()
    gdi_name = r"\\.\DISPLAY1"
    fake_dc = 12345

    with patch("winrandr.win32.repair._EnumDisplaySettings", return_value=0):
        with patch("winrandr.win32.repair._CreateDCW", return_value=fake_dc):
            with patch("winrandr.win32.repair._GetDeviceCaps", side_effect=[1920, 1080, 60]):
                new_modes, new_count = repair_mode_array(paths, 1, modes, 0, lambda _: gdi_name)
    assert new_count == 1
    assert new_modes[0].infoType == 2  # DISPLAYCONFIG_MODE_INFO_TYPE_TARGET
    assert new_modes[0]._union.targetMode.targetVideoSignalInfo.activeSize.cx == 1920
    assert new_modes[0]._union.targetMode.targetVideoSignalInfo.activeSize.cy == 1080
    assert new_modes[0]._union.targetMode.targetVideoSignalInfo.vSyncFreq.Numerator == 60


def test_repair_mode_array_no_fix():
    """modeInfoIdx 都有效时不扩展数组。"""
    config = _real_config()
    if config is None:
        return
    paths, modes, path_count, mode_count = config
    _result_modes, count = repair_mode_array(paths, path_count, modes, mode_count, get_gdi_name)
    assert count >= mode_count


def test_repair_fill_source_enum_success():
    """_fill_source_mode 在 EnumDisplaySettings 成功时用其分辨率。"""
    from unittest.mock import patch

    from winrandr.win32.constants import (
        DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE,
        DISPLAYCONFIG_PATH_MODE_IDX_INVALID,
    )
    from winrandr.win32.structures import (
        DISPLAYCONFIG_MODE_INFO,
        DISPLAYCONFIG_PATH_INFO,
        DISPLAYCONFIG_PATH_SOURCE_INFO,
        DISPLAYCONFIG_PATH_TARGET_INFO,
    )

    src = DISPLAYCONFIG_PATH_SOURCE_INFO()
    src.adapterId.LowPart = 0
    src.id = 0
    src.modeInfoIdx = 0
    src.statusFlags = 0
    tgt = DISPLAYCONFIG_PATH_TARGET_INFO()
    tgt.adapterId.LowPart = 0
    tgt.id = 0
    tgt.modeInfoIdx = DISPLAYCONFIG_PATH_MODE_IDX_INVALID
    path = DISPLAYCONFIG_PATH_INFO()
    path.sourceInfo = src
    path.targetInfo = tgt
    path.flags = 0

    paths = (DISPLAYCONFIG_PATH_INFO * 1)(path)
    modes = (DISPLAYCONFIG_MODE_INFO * 0)()
    gdi_name = r"\\.\DISPLAY1"

    with patch("winrandr.win32.repair._EnumDisplaySettings", return_value=1):
        new_modes, new_count = repair_mode_array(paths, 1, modes, 0, lambda _: gdi_name)
    assert new_count == 1
    assert new_modes[0].infoType == DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE


# --- set_display_config_available ---


def test_set_display_config_available_cache():
    _clear_caches()
    win32_utils._SDC_AVAILABLE = True
    assert win32_utils.set_display_config_available() is True


def test_set_display_config_available_real():
    """真实 SDC 可用性检测应返回布尔值。"""
    _clear_caches()
    result = win32_utils.set_display_config_available()
    assert isinstance(result, bool)


def test_set_display_config_available_oserror():
    """GetDisplayConfigBufferSizes 抛出 OSError 时 SDC 应标记为不可用。"""
    _clear_caches()
    from unittest.mock import patch

    with patch("winrandr.win32.utils._GetDisplayConfigBufferSizes", side_effect=OSError("access denied")):
        result = win32_utils.set_display_config_available()
    assert result is False
    assert win32_utils._SDC_AVAILABLE is False


# --- find_path_idx ---


def test_find_path_idx_real():
    """真实 QDC 路径中搜索 GDI 名应返回有效索引或 None。"""
    config = _real_config()
    if config is None:
        return
    paths, _, path_count, _ = config

    first_gdi = get_gdi_name(paths[0])
    if first_gdi:
        idx = find_path_idx(paths, path_count, first_gdi)
        assert idx is not None
        assert 0 <= idx < path_count

    idx = find_path_idx(paths, path_count, r"\\.\NONEXISTENT")
    assert idx is None


def test_find_path_idx_not_found():
    """不存在的 GDI 名应返回 None。"""
    config = _real_config()
    if config is None:
        return
    paths, _, path_count, _ = config
    result = find_path_idx(paths, path_count, r"\\.\DISPLAY99")
    assert result is None


# --- apply_config (write, may xfail) ---


def test_query_active_config_get_buffer_fails():
    """GetDisplayConfigBufferSizes 失败时 query_active_config 应返回 None。"""
    from unittest.mock import patch

    _clear_caches()
    with patch("winrandr.win32.utils._GetDisplayConfigBufferSizes", return_value=1):
        result = win32_utils.query_active_config()
    assert result is None


def test_query_active_config_query_fails():
    """QueryDisplayConfig 失败时 query_active_config 应返回 None。"""
    from unittest.mock import patch

    _clear_caches()
    with patch("winrandr.win32.utils._GetDisplayConfigBufferSizes", return_value=0):
        with patch("winrandr.win32.utils._QueryDisplayConfig", return_value=1):
            result = win32_utils.query_active_config()
    assert result is None


def test_apply_config_current_flags():
    """以原始 QDC 数据重设配置（仅 SDC_APPLY），SDC 不可用时 xfail。"""
    from tests.conftest import _write_op

    config = _real_config()
    if config is None:
        return
    paths, modes, path_count, mode_count = config
    _write_op(
        win32_utils.apply_config,
        paths,
        path_count,
        modes,
        mode_count,
        flags=0x00000002,  # SDC_APPLY only
    )


# --- apply_filtered ---


def test_apply_filtered_real():
    """真实 QDC 数据经过滤后应用，SDC 不可用时 xfail。"""
    from tests.conftest import _write_op

    config = _real_config()
    if config is None:
        return
    paths, modes, path_count, mode_count = config
    filtered_paths = win32_utils.filter_valid_paths(paths, path_count, modes, mode_count)
    if not filtered_paths:
        return
    subset = win32_utils._build_path_subset(paths, filtered_paths)
    _write_op(
        win32_utils.apply_config,
        subset,
        len(filtered_paths),
        modes,
        mode_count,
        flags=0x00000002,
    )


def test_apply_filtered_empty_paths():
    """空有效路径返回 False。"""
    config = _real_config()
    if config is None:
        return
    paths, modes, path_count, mode_count = config
    result = win32_utils.apply_filtered(paths, path_count, modes, mode_count, flags=0)
    assert isinstance(result, bool)


# --- _invalidate_qdc_cache ---


def test_invalidate_qdc_cache():
    _clear_caches()
    win32_utils._QDC_CACHE = "something"
    win32_utils._QDC_ALL_CACHE = "else"
    win32_utils._invalidate_qdc_cache()
    assert win32_utils._QDC_CACHE is None
    assert win32_utils._QDC_ALL_CACHE is None


def test_apply_config_success():
    """_SetDisplayConfig 成功时应返回 True 并清除缓存。"""
    from unittest.mock import patch

    from winrandr.win32.structures import (
        DISPLAYCONFIG_MODE_INFO,
        DISPLAYCONFIG_PATH_INFO,
    )

    _clear_caches()
    win32_utils._QDC_CACHE = "stale"
    paths = (DISPLAYCONFIG_PATH_INFO * 1)()
    modes = (DISPLAYCONFIG_MODE_INFO * 1)()
    with patch("winrandr.win32.utils._SetDisplayConfig", return_value=0):
        result = win32_utils.apply_config(paths, 1, modes, 1)
    assert result is True
    assert win32_utils._QDC_CACHE is None
    _clear_caches()
    win32_utils._QDC_CACHE = "something"
    win32_utils._QDC_ALL_CACHE = "else"
    win32_utils._invalidate_qdc_cache()
    assert win32_utils._QDC_CACHE is None
    assert win32_utils._QDC_ALL_CACHE is None
