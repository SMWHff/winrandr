"""Tests for features/layout.py with mocked Win32 API."""

from unittest.mock import patch, MagicMock


# --- failure paths ---

def test_set_position_sdc_unavailable():
    from winrandr.features.layout import set_position
    with patch("winrandr.features.layout.set_display_config_available", return_value=False):
        assert set_position(r"\\.\DISPLAY1", 0, 0) is False


def test_set_position_config_none():
    from winrandr.features.layout import set_position
    with patch("winrandr.features.layout.set_display_config_available", return_value=True):
        with patch("winrandr.features.layout.query_active_config", return_value=None):
            assert set_position(r"\\.\DISPLAY1", 0, 0) is False


def test_set_position_device_not_found():
    from winrandr.features.layout import set_position
    with patch("winrandr.features.layout.set_display_config_available", return_value=True):
        with patch("winrandr.features.layout.query_active_config", return_value=(MagicMock(), MagicMock(), 1, 1)):
            with patch("winrandr.features.layout.find_path_idx", return_value=None):
                assert set_position(r"\\.\DISPLAY99", 0, 0) is False


def test_set_rotation_invalid_degrees():
    from winrandr.features.layout import set_rotation
    assert set_rotation(r"\\.\DISPLAY1", 45) is False


def test_set_rotation_sdc_unavailable():
    from winrandr.features.layout import set_rotation
    with patch("winrandr.features.layout.set_display_config_available", return_value=False):
        assert set_rotation(r"\\.\DISPLAY1", 90) is False


def test_set_rotation_config_none():
    from winrandr.features.layout import set_rotation
    with patch("winrandr.features.layout.set_display_config_available", return_value=True):
        with patch("winrandr.features.layout.query_active_config", return_value=None):
            assert set_rotation(r"\\.\DISPLAY1", 90) is False


def test_set_rotation_device_not_found():
    from winrandr.features.layout import set_rotation
    with patch("winrandr.features.layout.set_display_config_available", return_value=True):
        with patch("winrandr.features.layout.query_active_config", return_value=(MagicMock(), MagicMock(), 1, 1)):
            with patch("winrandr.features.layout.find_path_idx", return_value=None):
                assert set_rotation(r"\\.\DISPLAY99", 90) is False


def test_set_position_invalid_mode_idx():
    from winrandr.features.layout import set_position
    from winrandr.win32.constants import DISPLAYCONFIG_PATH_MODE_IDX_INVALID
    mock_paths = MagicMock()
    mock_paths.__getitem__.return_value.sourceInfo.modeInfoIdx = DISPLAYCONFIG_PATH_MODE_IDX_INVALID
    with patch("winrandr.features.layout.set_display_config_available", return_value=True):
        with patch("winrandr.features.layout.query_active_config", return_value=(mock_paths, MagicMock(), 1, 1)):
            with patch("winrandr.features.layout.find_path_idx", return_value=0):
                assert set_position(r"\\.\DISPLAY1", 0, 0) is False


def test_set_primary_sdc_unavailable():
    from winrandr.features.layout import set_primary
    with patch("winrandr.features.layout.set_display_config_available", return_value=False):
        assert set_primary(r"\\.\DISPLAY1") is False


def test_set_primary_config_none():
    from winrandr.features.layout import set_primary
    with patch("winrandr.features.layout.set_display_config_available", return_value=True):
        with patch("winrandr.features.layout.query_active_config", return_value=None):
            assert set_primary(r"\\.\DISPLAY1") is False


def test_set_primary_device_not_found():
    from winrandr.features.layout import set_primary
    with patch("winrandr.features.layout.set_display_config_available", return_value=True):
        with patch("winrandr.features.layout.query_active_config", return_value=(MagicMock(), MagicMock(), 1, 1)):
            with patch("winrandr.features.layout.get_gdi_name", return_value="OTHER"):
                assert set_primary(r"\\.\DISPLAY99") is False


def test_set_off_sdc_unavailable():
    from winrandr.features.layout import set_off
    with patch("winrandr.features.layout.set_display_config_available", return_value=False):
        assert set_off(r"\\.\DISPLAY1") is False


def test_set_off_config_none():
    from winrandr.features.layout import set_off
    with patch("winrandr.features.layout.set_display_config_available", return_value=True):
        with patch("winrandr.features.layout.query_active_config", return_value=None):
            assert set_off(r"\\.\DISPLAY1") is False


def test_set_off_device_not_found():
    from winrandr.features.layout import set_off
    with patch("winrandr.features.layout.set_display_config_available", return_value=True):
        with patch("winrandr.features.layout.query_active_config", return_value=(MagicMock(), MagicMock(), 1, 1)):
            with patch("winrandr.features.layout.get_gdi_name", return_value="OTHER"):
                assert set_off(r"\\.\DISPLAY99") is False


def test_set_noprimary_sdc_unavailable():
    from winrandr.features.layout import set_noprimary
    with patch("winrandr.features.layout.set_display_config_available", return_value=False):
        assert set_noprimary() is False


def test_set_noprimary_config_none():
    from winrandr.features.layout import set_noprimary
    with patch("winrandr.features.layout.set_display_config_available", return_value=True):
        with patch("winrandr.features.layout.query_active_config", return_value=None):
            assert set_noprimary() is False


def test_set_reflect_unsupported():
    from winrandr.features.layout import set_reflect
    assert set_reflect(r"\\.\DISPLAY1", "x") is False
    assert set_reflect(r"\\.\DISPLAY1", "y") is False


def test_set_reflect_xy_delegates():
    from winrandr.features.layout import set_reflect
    with patch("winrandr.features.layout.set_rotation", return_value=True) as mock_fn:
        assert set_reflect(r"\\.\DISPLAY1", "xy") is True
        mock_fn.assert_called_once_with(r"\\.\DISPLAY1", 180)


# --- success paths (need real ctypes arrays) ---

def _make_valid_qdc(path_count=1, mode_count=2):
    """创建有效的 QDC 配置用于成功路径测试。"""
    from winrandr.win32.structures import DISPLAYCONFIG_PATH_INFO, DISPLAYCONFIG_MODE_INFO
    from winrandr.win32.constants import DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE, DISPLAYCONFIG_MODE_INFO_TYPE_TARGET
    paths = (DISPLAYCONFIG_PATH_INFO * path_count)()
    modes = (DISPLAYCONFIG_MODE_INFO * mode_count)()
    for i in range(path_count):
        paths[i].sourceInfo.modeInfoIdx = 0
        paths[i].targetInfo.modeInfoIdx = 1
    modes[0].infoType = DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE
    modes[1].infoType = DISPLAYCONFIG_MODE_INFO_TYPE_TARGET
    return paths, modes


def test_set_position_success():
    from winrandr.features.layout import set_position
    paths, modes = _make_valid_qdc()
    with patch("winrandr.features.layout.set_display_config_available", return_value=True):
        with patch("winrandr.features.layout.query_active_config",
                   return_value=(paths, modes, 1, 2)):
            with patch("winrandr.features.layout.find_path_idx", return_value=0):
                with patch("winrandr.features.layout.apply_filtered", return_value=True):
                    assert set_position(r"\\.\DISPLAY1", 100, 200) is True
                    assert modes[0]._union.sourceMode.position.x == 100
                    assert modes[0]._union.sourceMode.position.y == 200


def test_set_rotation_success():
    from winrandr.features.layout import set_rotation
    paths, modes = _make_valid_qdc()
    with patch("winrandr.features.layout.set_display_config_available", return_value=True):
        with patch("winrandr.features.layout.query_active_config",
                   return_value=(paths, modes, 1, 2)):
            with patch("winrandr.features.layout.find_path_idx", return_value=0):
                with patch("winrandr.features.layout.apply_filtered", return_value=True):
                    assert set_rotation(r"\\.\DISPLAY1", 90) is True


def test_set_primary_success():
    from winrandr.features.layout import set_primary
    paths, modes = _make_valid_qdc(path_count=2)
    call_count = 0

    def fake_gdi(_path):
        nonlocal call_count
        result = r"\\.\DISPLAY1" if call_count == 0 else r"\\.\DISPLAY2"
        call_count += 1
        return result

    with patch("winrandr.features.layout.set_display_config_available", return_value=True):
        with patch("winrandr.features.layout.query_active_config",
                   return_value=(paths, modes, 2, 2)):
            with patch("winrandr.features.layout.get_gdi_name", side_effect=fake_gdi):
                with patch("winrandr.features.layout.apply_filtered", return_value=True):
                    assert set_primary(r"\\.\DISPLAY1") is True
                    assert paths[0].sourceInfo.statusFlags & 0x01
                    assert not (paths[1].sourceInfo.statusFlags & 0x01)


def test_set_off_success():
    from winrandr.features.layout import set_off
    paths, modes = _make_valid_qdc(path_count=2)
    call_count = 0

    def fake_gdi(_path):
        nonlocal call_count
        result = r"\\.\DISPLAY1" if call_count == 0 else r"\\.\DISPLAY2"
        call_count += 1
        return result

    with patch("winrandr.features.layout.set_display_config_available", return_value=True):
        with patch("winrandr.features.layout.query_active_config",
                   return_value=(paths, modes, 2, 2)):
            with patch("winrandr.features.layout.get_gdi_name", side_effect=fake_gdi):
                with patch("winrandr.features.layout.apply_config", return_value=True) as mock_ac:
                    assert set_off(r"\\.\DISPLAY1") is True
                    mock_ac.assert_called_once()
                    assert len(mock_ac.call_args[0][0]) == 1


def test_set_noprimary_success():
    from winrandr.features.layout import set_noprimary
    paths, modes = _make_valid_qdc(path_count=2)
    paths[0].sourceInfo.statusFlags = 0x01
    paths[1].sourceInfo.statusFlags = 0x01
    with patch("winrandr.features.layout.set_display_config_available", return_value=True):
        with patch("winrandr.features.layout.query_active_config",
                   return_value=(paths, modes, 2, 2)):
            with patch("winrandr.features.layout.apply_filtered", return_value=True):
                assert set_noprimary() is True
                assert not (paths[0].sourceInfo.statusFlags & 0x01)
                assert not (paths[1].sourceInfo.statusFlags & 0x01)
