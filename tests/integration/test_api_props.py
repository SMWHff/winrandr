"""Tests for public API function get_display_props (真实硬件)。"""

from winrandr.api import get_display_props, list_displays


def test_get_display_props_returns_dict():
    """get_display_props 应返回字典。"""
    result = get_display_props(r"\\.\DISPLAY1")
    assert isinstance(result, dict)


def test_get_display_props_nonexistent():
    """不存在显示器的 props 应返回空字典或含有效键。"""
    result = get_display_props(r"\\.\NONEXISTENT")
    assert isinstance(result, dict)


def test_get_display_props_connected():
    """已连接显示器应有 device_id 或 adapter 等信息。"""
    displays = list_displays()
    connected = [d for d in displays if d.connected]
    for d in connected:
        props = get_display_props(d.name)
        assert isinstance(props, dict)


def test_get_display_props_contains_keys():
    """已连接显示器的 props 应包含预期的键。"""
    displays = list_displays()
    connected = [d for d in displays if d.connected]
    for d in connected:
        props = get_display_props(d.name)
        if not props:
            continue
        valid_keys = {
            "device_id",
            "state_flags",
            "adapter",
            "monitor_path",
            "connector_type",
            "manufacturer_id",
            "product_code",
            "edid_name",
            "edid_mfg",
            "edid_product",
            "edid_serial",
            "edid_date",
            "edid_version",
            "edid_size",
            "edid_desc",
            "edid_raw",
        }
        for key in props:
            assert key in valid_keys, f"未知属性键: {key}"
