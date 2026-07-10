"""Tests for win32/utils.py get_connector_type function — 真实硬件测试。"""

from winrandr.win32.structures import DISPLAYCONFIG_PATH_INFO
from winrandr.win32.utils import get_connector_type, query_active_config

VALID_TYPES = {"HDMI", "DisplayPort", "USB-C", "VGA", "DVI", ""}


def _real_paths():
    """获取真实活动路径列表，跳过无配置的机器。"""
    config = query_active_config()
    if config is None:
        return []
    return config[0], config[2]


def test_connector_type_all_paths():
    """所有活动路径的连接器类型应为已知类型或空字符串。"""
    paths, count = _real_paths()
    if count == 0:
        return
    for i in range(count):
        ct = get_connector_type(paths[i])
        assert ct in VALID_TYPES, f"未知连接器类型: {ct}"


def test_connector_type_api_failure():
    """不存在的路径（adapterId=0）调用真实 API 应返回空字符串。"""
    path = (DISPLAYCONFIG_PATH_INFO * 1)()[0]
    result = get_connector_type(path)
    assert result == ""
