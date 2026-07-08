"""Tests for EDID parsing functions (pure logic, no hardware dependency)."""

from winrandr.edid import _parse_edid, _find_edid_name, _find_edid_serial


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
    """Build a minimal 128-byte EDID block. Non-relevant bytes are zeroed."""
    data = bytearray(128)

    # Header
    data[0:8] = b'\x00\xff\xff\xff\xff\xff\xff\x00'
    # Manufacturer ID (packed 5-bit)
    data[8] = (mfg_id >> 8) & 0xFF
    data[9] = mfg_id & 0xFF
    # Product code (little-endian)
    data[10] = product & 0xFF
    data[11] = (product >> 8) & 0xFF
    # Serial number
    data[12] = serial & 0xFF
    data[13] = (serial >> 8) & 0xFF
    data[14] = (serial >> 16) & 0xFF
    data[15] = (serial >> 24) & 0xFF
    # Week / year
    data[16] = week
    data[17] = year_offset
    # EDID version
    major, minor = divmod(int(version * 10), 10)
    data[18] = major
    data[19] = minor
    # Physical size
    data[21] = width_cm
    data[22] = height_cm

    # Monitor name descriptor block at offset 54
    if name:
        data[54] = 0x00
        data[55] = 0x00
        data[56] = 0x00
        data[57] = 0xFC  # Monitor name tag
        data[58] = 0x00  # reserved
        raw_name = name.encode('ascii')
        data[59:59 + len(raw_name)] = raw_name
        data[59 + len(raw_name)] = 0x0A  # newline terminator

    # Serial descriptor block at offset 72
    if serial_str:
        data[72] = 0x00
        data[73] = 0x00
        data[74] = 0x00
        data[75] = 0xFF  # Serial tag
        data[76] = 0x00  # reserved
        raw = serial_str.encode('ascii')[:13]  # max 13 bytes for descriptor data
        data[77:77 + len(raw)] = raw
        if len(raw) < 13:
            data[77 + len(raw)] = 0x0A  # newline terminator (if room)

    return bytes(data)


def test_parse_edid_valid():
    """Parse a well-formed EDID block."""
    edid = _build_edid(name="TestMonitor")
    result = _parse_edid(edid)
    assert result["edid_mfg"] == "AOC"
    assert result["edid_name"] == "TestMonitor"
    assert result["edid_product"] == "2411"  # raw product code
    assert "edid_serial" not in result  # no descriptor serial in test data
    assert result["edid_date"] == "2023-02-24"  # ISO week 8, Friday
    assert result["edid_version"] == "1.4"
    assert result["edid_size"] == "53x30 cm"
    assert result["edid_name"] == "TestMonitor"
    assert result["edid_desc"] == "AOC TestMonitor (1.4)"


def test_parse_edid_unknown_mfg():
    """Manufacturer not in lookup dict uses decoded PNP ID."""
    edid = _build_edid(mfg_id=0x1234, name="UnknownCo")
    result = _parse_edid(edid)
    assert result["edid_mfg"] == "DQT"


def test_parse_edid_no_serial():
    """Serial number 0 should be omitted."""
    edid = _build_edid(serial=0)
    result = _parse_edid(edid)
    assert "edid_serial" not in result


def test_parse_edid_no_size():
    """Zero physical size should be omitted."""
    edid = _build_edid(width_cm=0, height_cm=0)
    result = _parse_edid(edid)
    assert "edid_size" not in result


def test_parse_edid_no_name():
    """No monitor name descriptor → edid_name absent."""
    edid = _build_edid(name=None)
    result = _parse_edid(edid)
    assert "edid_name" not in result
    assert result["edid_desc"] == "AOC 2411 (1.4)"  # fallback to product code


def test_parse_edid_too_short():
    """Data shorter than 128 bytes returns fallback."""
    result = _parse_edid(b'\x00' * 64)
    assert "edid_raw" in result
    assert result["edid_raw"].startswith("00")


def test_parse_edid_invalid_header():
    """Missing EDID header returns fallback."""
    data = b'\xff' * 128
    result = _parse_edid(data)
    assert "edid_raw" in result


def test_parse_edid_empty():
    """Empty data returns fallback."""
    result = _parse_edid(b'')
    assert result["edid_raw"] == "unavailable"


def test_parse_edid_no_week():
    """Week 0 should show only the year."""
    edid = _build_edid(week=0)
    result = _parse_edid(edid)
    assert result["edid_date"] == "2023"


def test_find_edid_name_present():
    """Extract monitor name from descriptor block."""
    data = _build_edid(name="My Monitor")
    assert _find_edid_name(data) == "My Monitor"


def test_find_edid_name_no_tag():
    """No 0xFC descriptor block → None."""
    data = _build_edid(name=None)
    assert _find_edid_name(data) is None


def test_find_edid_name_empty():
    """No name written when name is empty → returns None."""
    data = _build_edid(name="")
    assert _find_edid_name(data) is None


def test_parse_edid_with_serial_str():
    """EDID with both name and serial descriptors."""
    edid = _build_edid(name="MyMonitor", serial_str="AP11308Z00136")
    result = _parse_edid(edid)
    assert result["edid_name"] == "MyMonitor"
    assert result["edid_product"] == "2411"
    assert result["edid_serial"] == "AP11308Z00136"
    assert result["edid_date"] == "2023-02-24"
    assert result["edid_desc"] == "AOC MyMonitor (1.4)"


def test_find_edid_serial_present():
    """Extract serial from descriptor block."""
    data = _build_edid(serial_str="SN9876543210")
    assert _find_edid_serial(data) == "SN9876543210"


def test_find_edid_serial_missing():
    """No 0xFF descriptor block → None."""
    data = _build_edid(serial_str=None)
    assert _find_edid_serial(data) is None
