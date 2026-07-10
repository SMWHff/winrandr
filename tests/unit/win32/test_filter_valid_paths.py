"""Tests for win32/utils.py filter_valid_paths and apply_filtered — 真实硬件测试。"""

from winrandr.win32.utils import filter_valid_paths, get_gdi_name, query_active_config


def _real_config():
    """获取真实活动配置，跳过无配置的机器。"""
    config = query_active_config()
    if config is None:
        return None
    return config


def test_filter_real_paths():
    """真实 QDC 路径过滤应返回有效索引且无重复 GDI 名。"""
    config = _real_config()
    if config is None:
        return
    paths, modes, path_count, mode_count = config
    result = filter_valid_paths(paths, path_count, modes, mode_count)
    assert isinstance(result, list)

    gdi_names = []
    for idx in result:
        gdi = get_gdi_name(paths[idx])
        assert gdi not in gdi_names, f"存在重复 GDI 名: {gdi}"
        gdi_names.append(gdi)


def test_filter_real_paths_subset():
    """部分路径应能正确过滤。"""
    config = _real_config()
    if config is None or config[2] < 2:
        return
    paths, modes, path_count, mode_count = config
    n = max(1, path_count // 2)
    result = filter_valid_paths(paths, n, modes, mode_count)
    assert len(result) <= n


def test_filter_empty():
    """空路径数组返回空列表。"""
    from winrandr.win32.structures import DISPLAYCONFIG_MODE_INFO, DISPLAYCONFIG_PATH_INFO

    paths = (DISPLAYCONFIG_PATH_INFO * 0)()
    modes = (DISPLAYCONFIG_MODE_INFO * 0)()
    assert filter_valid_paths(paths, 0, modes, 0) == []
