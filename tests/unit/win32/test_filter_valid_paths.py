"""Tests for win32/utils.py filter_valid_paths and apply_filtered."""

from winrandr.win32.constants import (
    DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE,
    DISPLAYCONFIG_MODE_INFO_TYPE_TARGET,
    DISPLAYCONFIG_PATH_MODE_IDX_INVALID,
)
from winrandr.win32.structures import DISPLAYCONFIG_MODE_INFO, DISPLAYCONFIG_PATH_INFO
from winrandr.win32.utils import filter_valid_paths


def test_filter_valid_paths_all_valid():
    """两条路径都有效时全部返回。"""
    paths = (DISPLAYCONFIG_PATH_INFO * 2)()
    modes = (DISPLAYCONFIG_MODE_INFO * 4)()
    paths[0].sourceInfo.modeInfoIdx = 0
    paths[0].targetInfo.modeInfoIdx = 1
    paths[1].sourceInfo.modeInfoIdx = 2
    paths[1].targetInfo.modeInfoIdx = 3
    modes[0].infoType = DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE
    modes[1].infoType = DISPLAYCONFIG_MODE_INFO_TYPE_TARGET
    modes[2].infoType = DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE
    modes[3].infoType = DISPLAYCONFIG_MODE_INFO_TYPE_TARGET
    assert filter_valid_paths(paths, 2, modes, 4) == [0, 1]


def test_filter_valid_paths_invalid_source():
    """source mode 索引无效时过滤掉该路径。"""
    paths = (DISPLAYCONFIG_PATH_INFO * 1)()
    modes = (DISPLAYCONFIG_MODE_INFO * 1)()
    paths[0].sourceInfo.modeInfoIdx = DISPLAYCONFIG_PATH_MODE_IDX_INVALID
    paths[0].targetInfo.modeInfoIdx = 0
    modes[0].infoType = DISPLAYCONFIG_MODE_INFO_TYPE_TARGET
    assert filter_valid_paths(paths, 1, modes, 1) == []


def test_filter_valid_paths_invalid_target():
    """target mode 索引无效时过滤掉该路径。"""
    paths = (DISPLAYCONFIG_PATH_INFO * 1)()
    modes = (DISPLAYCONFIG_MODE_INFO * 1)()
    paths[0].sourceInfo.modeInfoIdx = 0
    paths[0].targetInfo.modeInfoIdx = DISPLAYCONFIG_PATH_MODE_IDX_INVALID
    modes[0].infoType = DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE
    assert filter_valid_paths(paths, 1, modes, 1) == []


def test_filter_valid_paths_out_of_range():
    """mode 索引超出 mode_count 时过滤掉该路径。"""
    paths = (DISPLAYCONFIG_PATH_INFO * 1)()
    modes = (DISPLAYCONFIG_MODE_INFO * 1)()
    paths[0].sourceInfo.modeInfoIdx = 5
    paths[0].targetInfo.modeInfoIdx = 0
    modes[0].infoType = DISPLAYCONFIG_MODE_INFO_TYPE_TARGET
    assert filter_valid_paths(paths, 1, modes, 1) == []


def test_filter_valid_paths_wrong_type():
    """mode 类型不匹配时过滤掉该路径。"""
    paths = (DISPLAYCONFIG_PATH_INFO * 1)()
    modes = (DISPLAYCONFIG_MODE_INFO * 2)()
    paths[0].sourceInfo.modeInfoIdx = 0
    paths[0].targetInfo.modeInfoIdx = 1
    modes[0].infoType = DISPLAYCONFIG_MODE_INFO_TYPE_TARGET
    modes[1].infoType = DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE
    assert filter_valid_paths(paths, 1, modes, 2) == []


def test_filter_valid_paths_mixed():
    """混合场景：有效路径保留、无效路径过滤。"""
    paths = (DISPLAYCONFIG_PATH_INFO * 3)()
    modes = (DISPLAYCONFIG_MODE_INFO * 4)()
    paths[0].sourceInfo.modeInfoIdx = 0
    paths[0].targetInfo.modeInfoIdx = 1
    paths[1].sourceInfo.modeInfoIdx = DISPLAYCONFIG_PATH_MODE_IDX_INVALID
    paths[1].targetInfo.modeInfoIdx = 2
    paths[2].sourceInfo.modeInfoIdx = 2
    paths[2].targetInfo.modeInfoIdx = 3
    modes[0].infoType = DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE
    modes[1].infoType = DISPLAYCONFIG_MODE_INFO_TYPE_TARGET
    modes[2].infoType = DISPLAYCONFIG_MODE_INFO_TYPE_TARGET
    modes[3].infoType = DISPLAYCONFIG_MODE_INFO_TYPE_TARGET
    assert filter_valid_paths(paths, 3, modes, 4) == [0]


def test_filter_valid_paths_empty():
    """空路径数组返回空列表。"""
    paths = (DISPLAYCONFIG_PATH_INFO * 0)()
    modes = (DISPLAYCONFIG_MODE_INFO * 0)()
    assert filter_valid_paths(paths, 0, modes, 0) == []
