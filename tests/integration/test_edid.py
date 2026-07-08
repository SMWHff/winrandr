"""EDID parsing tests — extracted from test_models.py."""

from unittest.mock import MagicMock, patch

from winrandr.edid import _find_edid_name, _find_edid_serial, _parse_edid


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
    data[0:8] = b'\x00\xff\xff\xff\xff\xff\xff\x00'
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
        data[54:59] = b'\x00\x00\x00\xFC\x00'
        raw_name = name.encode('ascii')
        data[59:59 + len(raw_name)] = raw_name
        data[59 + len(raw_name)] = 0x0A
    if serial_str:
        data[72:76] = b'\x00\x00\x00\xFF\x00'
        raw = serial_str.encode('ascii')[:13]
        data[77:77 + len(raw)] = raw
        if len(raw) < 13:
            data[77 + len(raw)] = 0x0A
    return bytes(data)


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
    result = _parse_edid(b'\x00' * 64)
    assert "edid_raw" in result
    assert result["edid_raw"].startswith("00")


def test_parse_edid_invalid_header():
    result = _parse_edid(b'\xff' * 128)
    assert "edid_raw" in result


def test_parse_edid_empty():
    result = _parse_edid(b'')
    assert result["edid_raw"] == "unavailable"


def test_parse_edid_with_serial_str():
    """EDID with text serial descriptor block."""
    edid = _build_edid(serial=0, serial_str="SN12345678")
    result = _parse_edid(edid)
    assert result["edid_serial"] == "SN12345678"


def test_parse_edid_date_no_week():
    """Week 0 falls back to year-only."""
    edid = _build_edid(week=0, year_offset=30)
    result = _parse_edid(edid)
    assert result["edid_date"] == "2020"


def test_parse_edid_date_overflow_week():
    """Week > 52 falls back to year-only."""
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
    """非 ASCII 字节导致 decode 失败时返回 None。"""
    from winrandr.edid import _find_edid_desc
    data = bytearray(128)
    data[0:8] = b'\x00\xff\xff\xff\xff\xff\xff\x00'
    data[8] = 0x05
    data[9] = 0xE3
    data[54:59] = b'\x00\x00\x00\xFC\x00'
    data[59:72] = b'\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x0a'
    result = _find_edid_desc(bytes(data), 0xFC)
    assert result is None


def _make_edid_bytes(name: str = "TestMon") -> bytes:
    return _build_edid(name=name)


def test_get_edid_enum_fails():
    """_EnumDisplayDevices 失败时返回空 dict。"""
    from winrandr.edid import get_edid
    with patch("winrandr.edid._EnumDisplayDevices", return_value=False):
        assert get_edid(r"\\.\DISPLAY1") == {}


def test_get_edid_no_device_id():
    """DeviceID 为空时返回空 dict。"""
    from winrandr.edid import get_edid
    def fake_enum(_, __, dd_ptr, ___):
        dd_ptr._obj.cb = 1
        return True
    with patch("winrandr.edid._EnumDisplayDevices", side_effect=fake_enum):
        assert get_edid(r"\\.\DISPLAY1") == {}


def test_get_edid_short_device_id():
    """DeviceID 格式异常（段数 < 2）时返回空 dict。"""
    from winrandr.edid import get_edid
    def fake_enum(_, __, dd_ptr, ___):
        dd_ptr._obj.DeviceID = "NODELIMITERS"
        return True
    with patch("winrandr.edid._EnumDisplayDevices", side_effect=fake_enum):
        assert get_edid(r"\\.\DISPLAY1") == {}


def test_get_edid_registry_open_fails():
    """winreg.OpenKey 失败时返回空 dict。"""
    from winrandr.edid import get_edid
    def fake_enum(_, __, dd_ptr, ___):
        dd_ptr._obj.DeviceID = r"MONITOR\ABC123"
        return True
    with patch("winrandr.edid._EnumDisplayDevices", side_effect=fake_enum):
        with patch("winrandr.edid.winreg.OpenKey", side_effect=OSError):
            assert get_edid(r"\\.\DISPLAY1") == {}


def test_get_edid_success():
    """完整成功的 get_edid 路径。"""
    from winrandr.edid import get_edid
    edid_bytes = _make_edid_bytes("ProDisplay")
    def fake_enum(_, __, dd_ptr, ___):
        dd_ptr._obj.DeviceID = r"MONITOR\ABC123"
        return True

    fake_key = MagicMock()
    fake_parent = MagicMock()
    fake_enum_key = MagicMock(side_effect=["inst0", OSError()])

    with patch("winrandr.edid._EnumDisplayDevices", side_effect=fake_enum):
        with patch("winrandr.edid.winreg.OpenKey") as mock_open:
            mock_open.side_effect = lambda key, path: fake_parent if "Enum\\DISPLAY" in path else fake_key
            with patch("winrandr.edid.winreg.EnumKey", side_effect=fake_enum_key):
                with patch("winrandr.edid.winreg.QueryValueEx", return_value=(edid_bytes, 0)):
                    with patch("winrandr.edid.winreg.CloseKey"):
                        result = get_edid(r"\\.\DISPLAY1")
                        assert "edid_name" in result
                        assert result["edid_name"] == "ProDisplay"


def test_get_edid_all_instances_fail():
    """所有实例均失败后返回空 dict（覆盖 inner/outer except 路径）。"""
    from winrandr.edid import get_edid
    def fake_enum(_, __, dd_ptr, ___):
        dd_ptr._obj.DeviceID = r"MONITOR\ABC123"
        return True

    fake_parent = MagicMock()
    fake_enum_key = MagicMock(side_effect=["inst0", OSError()])

    with patch("winrandr.edid._EnumDisplayDevices", side_effect=fake_enum):
        with patch("winrandr.edid.winreg.OpenKey") as mock_open:
            mock_open.side_effect = [fake_parent, OSError()]
            with patch("winrandr.edid.winreg.EnumKey", side_effect=fake_enum_key):
                with patch("winrandr.edid.winreg.CloseKey"):
                    result = get_edid(r"\\.\DISPLAY1")
                    assert result == {}


def test_target_device_name_friendly_name():
    """DISPLAYCONFIG_TARGET_DEVICE_NAME.friendly_name 返回 monitorFriendlyDeviceName。"""
    from winrandr.win32.structures import DISPLAYCONFIG_TARGET_DEVICE_NAME
    sdn = DISPLAYCONFIG_TARGET_DEVICE_NAME()
    sdn.monitorFriendlyDeviceName = "Test Monitor"
    assert sdn.friendly_name == "Test Monitor"
