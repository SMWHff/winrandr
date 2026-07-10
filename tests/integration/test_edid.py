"""EDID parsing tests — pure logic + 真实硬件。"""

from winrandr.edid import _find_edid_name, _find_edid_serial, _parse_edid, get_edid


def _build_edid(
    mfg_id: int = 0x05E3,
    product: int = 0x2411,
    serial: int = 0x88,
    week: int = 8,
    year_offset: int = 33,
    version: float = 1.4,
    width_cm: int = 53,
    height_cm: int = 30,
    name: str | None = "24E11W1",
    serial_str: str | None = None,
) -> bytes:
    data = bytearray(128)
    data[0:8] = b"\x00\xff\xff\xff\xff\xff\xff\x00"
    data[8] = (mfg_id >> 8) & 0xFF
    data[9] = mfg_id & 0xFF
    data[10] = product & 0xFF
    data[11] = (product >> 8) & 0xFF
    data[12] = serial & 0xFF
    data[13] = (serial >> 8) & 0xFF
    data[14] = (serial >> 16) & 0xFF
    data[15] = (serial >> 24) & 0xFF
    data[16] = week
    data[17] = year_offset
    major, minor = divmod(int(version * 10), 10)
    data[18] = major
    data[19] = minor
    data[21] = width_cm
    data[22] = height_cm
    if name:
        data[54:59] = b"\x00\x00\x00\xfc\x00"
        raw_name = name.encode("ascii")
        data[59 : 59 + len(raw_name)] = raw_name
        data[59 + len(raw_name)] = 0x0A
    if serial_str:
        data[72:76] = b"\x00\x00\x00\xff\x00"
        raw = serial_str.encode("ascii")[:13]
        data[77 : 77 + len(raw)] = raw
        if len(raw) < 13:
            data[77 + len(raw)] = 0x0A
    return bytes(data)


# --- 纯逻辑解析测试（构造 EDID 字节，不调 Win32） ---


def test_parse_edid_valid():
    edid = _build_edid(name="TestMonitor")
    result = _parse_edid(edid)
    assert result["edid_mfg"] == "AOC"
    assert result["edid_name"] == "TestMonitor"
    assert result["edid_product"] == "2411"
    assert "edid_serial" not in result
    assert result["edid_date"] == "2023-02-24"
    assert result["edid_version"] == "1.4"
    assert result["edid_size"] == "53x30 cm"
    assert result["edid_desc"] == "AOC TestMonitor (1.4)"


def test_parse_edid_unknown_mfg():
    edid = _build_edid(mfg_id=0x1234, name="UnknownCo")
    result = _parse_edid(edid)
    assert result["edid_mfg"] == "DQT"


def test_parse_edid_no_serial():
    edid = _build_edid(serial=0)
    result = _parse_edid(edid)
    assert "edid_serial" not in result


def test_parse_edid_no_size():
    edid = _build_edid(width_cm=0, height_cm=0)
    result = _parse_edid(edid)
    assert "edid_size" not in result


def test_parse_edid_no_name():
    edid = _build_edid(name=None)
    result = _parse_edid(edid)
    assert "edid_name" not in result
    assert result["edid_desc"] == "AOC 2411 (1.4)"


def test_parse_edid_too_short():
    result = _parse_edid(b"\x00" * 64)
    assert "edid_raw" in result
    assert result["edid_raw"].startswith("00")


def test_parse_edid_invalid_header():
    result = _parse_edid(b"\xff" * 128)
    assert "edid_raw" in result


def test_parse_edid_empty():
    result = _parse_edid(b"")
    assert result["edid_raw"] == "unavailable"


def test_parse_edid_with_serial_str():
    edid = _build_edid(serial=0, serial_str="SN12345678")
    result = _parse_edid(edid)
    assert result["edid_serial"] == "SN12345678"


def test_parse_edid_date_no_week():
    edid = _build_edid(week=0, year_offset=30)
    result = _parse_edid(edid)
    assert result["edid_date"] == "2020"


def test_parse_edid_date_overflow_week():
    edid = _build_edid(week=99, year_offset=30)
    result = _parse_edid(edid)
    assert result["edid_date"] == "2020"


def test_parse_edid_no_week():
    edid = _build_edid(week=0)
    result = _parse_edid(edid)
    assert result["edid_date"] == "2023"


def test_find_edid_name_present():
    data = _build_edid(name="My Monitor")
    assert _find_edid_name(data) == "My Monitor"


def test_find_edid_name_no_tag():
    data = _build_edid(name=None)
    assert _find_edid_name(data) is None


def test_find_edid_name_empty():
    data = _build_edid(name="")
    assert _find_edid_name(data) is None


def test_parse_edid_with_serial_full():
    edid = _build_edid(name="MyMonitor", serial_str="AP11308Z00136")
    result = _parse_edid(edid)
    assert result["edid_name"] == "MyMonitor"
    assert result["edid_product"] == "2411"
    assert result["edid_serial"] == "AP11308Z00136"
    assert result["edid_date"] == "2023-02-24"
    assert result["edid_desc"] == "AOC MyMonitor (1.4)"


def test_find_edid_serial_present():
    data = _build_edid(serial_str="SN9876543210")
    assert _find_edid_serial(data) == "SN9876543210"


def test_find_edid_serial_missing():
    data = _build_edid(serial_str=None)
    assert _find_edid_serial(data) is None


def test_find_edid_name_decode_error():
    from winrandr.edid import _find_edid_desc

    data = bytearray(128)
    data[0:8] = b"\x00\xff\xff\xff\xff\xff\xff\x00"
    data[8] = 0x05
    data[9] = 0xE3
    data[54:59] = b"\x00\x00\x00\xfc\x00"
    data[59:72] = b"\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x0a"
    result = _find_edid_desc(bytes(data), 0xFC)
    assert result is None


def _make_edid_bytes(name: str = "TestMon") -> bytes:
    return _build_edid(name=name)


# --- 真实硬件测试：get_edid ---


def test_get_edid_nonexistent():
    """不存在显示器的 get_edid 应返回空 dict。"""
    result = get_edid(r"\\.\NONEXISTENT")
    assert result == {}


def test_get_edid_real():
    """真实显示器应返回 EDID 或空 dict。"""
    from winrandr.api import list_displays

    displays = list_displays()
    connected = [d for d in displays if d.connected]
    if not connected:
        return
    result = get_edid(connected[0].name)
    assert isinstance(result, dict)
    if result:
        assert "edid_mfg" in result or "manufacturer_id" in result


def test_target_device_name_friendly_name():
    """DISPLAYCONFIG_TARGET_DEVICE_NAME.friendly_name 返回 monitorFriendlyDeviceName。"""
    from winrandr.win32.structures import DISPLAYCONFIG_TARGET_DEVICE_NAME

    sdn = DISPLAYCONFIG_TARGET_DEVICE_NAME()
    sdn.monitorFriendlyDeviceName = "Test Monitor"
    assert sdn.friendly_name == "Test Monitor"


# --- Mock 错误分支测试：get_edid ---


def test_get_edid_no_device_id():
    """_EnumDisplayDevices 成功但无 DeviceID 时应返回空 dict（默认初始化已为空）。"""
    from unittest.mock import patch

    from winrandr.edid import get_edid

    with patch("winrandr.edid._EnumDisplayDevices", return_value=1):
        assert get_edid(r"\\.\DISPLAY1") == {}


def _patch_device_id(val: str):
    """让 DISPLAY_DEVICE 实例化后 DeviceID 指向给定值。"""
    from unittest.mock import patch

    from winrandr.win32.structures import DISPLAY_DEVICE

    orig_init = DISPLAY_DEVICE.__init__

    def _new_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        self.DeviceID = val

    return patch.object(DISPLAY_DEVICE, "__init__", _new_init)


def test_get_edid_open_key_fails():
    """winreg.OpenKey 失败时应返回空 dict。"""
    from unittest.mock import patch

    from winrandr.edid import get_edid

    with _patch_device_id(r"DISPLAY\DEL506E\5&36a3c1f3&0&UID16777488"):
        with patch("winrandr.edid._EnumDisplayDevices", return_value=1):
            with patch("winrandr.edid.winreg.OpenKey", side_effect=OSError("access denied")):
                assert get_edid(r"\\.\DISPLAY1") == {}


def test_get_edid_enum_key_fails():
    """winreg.EnumKey 失败时应返回空 dict。"""
    from unittest.mock import MagicMock, patch

    from winrandr.edid import get_edid

    with _patch_device_id(r"DISPLAY\DEL506E\5&36a3c1f3&0&UID16777488"):
        with patch("winrandr.edid._EnumDisplayDevices", return_value=1):
            with patch("winrandr.edid.winreg.OpenKey", return_value=MagicMock()):
                with patch("winrandr.edid.winreg.EnumKey", side_effect=OSError("no more keys")):
                    with patch("winrandr.edid.winreg.CloseKey"):
                        assert get_edid(r"\\.\DISPLAY1") == {}


def test_get_edid_bad_device_id_no_backslash():
    """DeviceID 无反斜杠时应返回空 dict。"""
    from unittest.mock import patch

    from winrandr.edid import get_edid

    with _patch_device_id("MONITOR123"):
        with patch("winrandr.edid._EnumDisplayDevices", return_value=1):
            assert get_edid(r"\\.\DISPLAY1") == {}


def test_get_edid_open_key_continue_on_error():
    """OpenKey 对第一个子项失败时继续枚举下一个。"""
    from unittest.mock import MagicMock, patch

    from winrandr.edid import get_edid

    open_key_effects = [MagicMock(), OSError("access denied"), MagicMock()]
    enum_key_effects = ["subkey1", "subkey2", OSError("no more")]
    edid_data = b"\x00\xff\xff\xff\xff\xff\xff\x00" + b"\x00" * 120

    with _patch_device_id(r"DISPLAY\DEL506E\5&36a3c1f3&0&UID16777488"):
        with patch("winrandr.edid._EnumDisplayDevices", return_value=1):
            with patch("winrandr.edid.winreg.OpenKey", side_effect=open_key_effects):
                with patch("winrandr.edid.winreg.EnumKey", side_effect=enum_key_effects):
                    with patch("winrandr.edid.winreg.QueryValueEx", return_value=(edid_data, 1)):
                        with patch("winrandr.edid.winreg.CloseKey"):
                            result = get_edid(r"\\.\DISPLAY1")
    assert "edid_mfg" in result
