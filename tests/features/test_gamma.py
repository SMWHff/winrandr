"""Tests for features/gamma.py with mocked Win32 API."""

from unittest.mock import patch


def test_set_brightness_success():
    from winrandr.features.gamma import set_brightness

    with patch("winrandr.features.gamma._CreateDCW", return_value=0x1234):
        with patch("winrandr.features.gamma._GetDeviceGammaRamp", return_value=1):
            with patch("winrandr.features.gamma._SetDeviceGammaRamp", return_value=1):
                with patch("winrandr.features.gamma._DeleteDC"):
                    assert set_brightness(r"\\.\DISPLAY1", 0.8) is True


def test_set_brightness_negative():
    from winrandr.features.gamma import set_brightness

    assert set_brightness(r"\\.\DISPLAY1", -0.5) is False


def test_set_brightness_dc_fails():
    from winrandr.features.gamma import set_brightness

    with patch("winrandr.features.gamma._CreateDCW", return_value=None):
        assert set_brightness(r"\\.\DISPLAY1", 0.8) is False


def test_set_brightness_getramp_fails():
    from winrandr.features.gamma import set_brightness

    with patch("winrandr.features.gamma._CreateDCW", return_value=0x1234):
        with patch("winrandr.features.gamma._GetDeviceGammaRamp", return_value=0):
            with patch("winrandr.features.gamma._DeleteDC"):
                assert set_brightness(r"\\.\DISPLAY1", 0.8) is False


def test_set_brightness_setramp_fails():
    from winrandr.features.gamma import set_brightness

    with patch("winrandr.features.gamma._CreateDCW", return_value=0x1234):
        with patch("winrandr.features.gamma._GetDeviceGammaRamp", return_value=1):
            with patch("winrandr.features.gamma._SetDeviceGammaRamp", return_value=0):
                with patch("winrandr.features.gamma._DeleteDC"):
                    assert set_brightness(r"\\.\DISPLAY1", 0.8) is False


def test_set_gamma_success():
    from winrandr.features.gamma import set_gamma

    with patch("winrandr.features.gamma._CreateDCW", return_value=0x1234):
        with patch("winrandr.features.gamma._GetDeviceGammaRamp", return_value=1):
            with patch("winrandr.features.gamma._SetDeviceGammaRamp", return_value=1):
                with patch("winrandr.features.gamma._DeleteDC"):
                    assert set_gamma(r"\\.\DISPLAY1", 1.0, 0.9, 0.8) is True


def test_set_gamma_dc_fails():
    from winrandr.features.gamma import set_gamma

    with patch("winrandr.features.gamma._CreateDCW", return_value=None):
        assert set_gamma(r"\\.\DISPLAY1", 1.0, 0.9, 0.8) is False


def test_set_gamma_getramp_fails():
    from winrandr.features.gamma import set_gamma

    with patch("winrandr.features.gamma._CreateDCW", return_value=0x1234):
        with patch("winrandr.features.gamma._GetDeviceGammaRamp", return_value=0):
            with patch("winrandr.features.gamma._DeleteDC"):
                assert set_gamma(r"\\.\DISPLAY1", 1.0, 0.9, 0.8) is False


def test_set_gamma_setramp_fails():
    from winrandr.features.gamma import set_gamma

    with patch("winrandr.features.gamma._CreateDCW", return_value=0x1234):
        with patch("winrandr.features.gamma._GetDeviceGammaRamp", return_value=1):
            with patch("winrandr.features.gamma._SetDeviceGammaRamp", return_value=0):
                with patch("winrandr.features.gamma._DeleteDC"):
                    assert set_gamma(r"\\.\DISPLAY1", 1.0, 0.9, 0.8) is False


def test_set_gamma_exception():
    from winrandr.features.gamma import set_gamma

    with patch("winrandr.features.gamma._CreateDCW", side_effect=OSError("mock")):
        assert set_gamma(r"\\.\DISPLAY1", 1.0, 0.9, 0.8) is False


def test_set_brightness_exception():
    from winrandr.features.gamma import set_brightness

    with patch("winrandr.features.gamma._CreateDCW", side_effect=OSError("mock")):
        assert set_brightness(r"\\.\DISPLAY1", 0.8) is False


def test_identify_success():
    from winrandr.features.gamma import identify_display

    with patch("winrandr.features.gamma._CreateDCW", return_value=0x1234):
        with patch("winrandr.features.gamma._GetDeviceGammaRamp", return_value=1):
            with patch("winrandr.features.gamma._SetDeviceGammaRamp", return_value=1):
                with patch("winrandr.features.gamma._DeleteDC"):
                    with patch("winrandr.features.gamma.time.sleep"):
                        assert identify_display(r"\\.\DISPLAY1") is True


def test_identify_dc_fails():
    from winrandr.features.gamma import identify_display

    with patch("winrandr.features.gamma._CreateDCW", return_value=None):
        assert identify_display(r"\\.\DISPLAY1") is False


def test_identify_getramp_fails():
    from winrandr.features.gamma import identify_display

    with patch("winrandr.features.gamma._CreateDCW", return_value=0x1234):
        with patch("winrandr.features.gamma._GetDeviceGammaRamp", return_value=0):
            with patch("winrandr.features.gamma._DeleteDC"):
                assert identify_display(r"\\.\DISPLAY1") is False


def test_identify_flash_fails():
    from winrandr.features.gamma import identify_display

    with patch("winrandr.features.gamma._CreateDCW", return_value=0x1234):
        with patch("winrandr.features.gamma._GetDeviceGammaRamp", return_value=1):
            with patch("winrandr.features.gamma._SetDeviceGammaRamp", side_effect=[0, 1]):
                with patch("winrandr.features.gamma._DeleteDC"):
                    with patch("winrandr.features.gamma.time.sleep"):
                        assert identify_display(r"\\.\DISPLAY1") is False


def test_identify_blank_fails():
    from winrandr.features.gamma import identify_display

    with patch("winrandr.features.gamma._CreateDCW", return_value=0x1234):
        with patch("winrandr.features.gamma._GetDeviceGammaRamp", return_value=1):
            with patch("winrandr.features.gamma._SetDeviceGammaRamp", side_effect=[1, 0, 1]):
                with patch("winrandr.features.gamma._DeleteDC"):
                    with patch("winrandr.features.gamma.time.sleep"):
                        assert identify_display(r"\\.\DISPLAY1") is False


def test_identify_exception():
    from winrandr.features.gamma import identify_display

    with patch("winrandr.features.gamma._CreateDCW", side_effect=OSError("mock")):
        assert identify_display(r"\\.\DISPLAY1") is False


# --- set_night_mode ---


def test_set_night_mode_strength_05():
    """Success path with medium strength (0.5)."""
    from winrandr.features.gamma import set_night_mode

    with patch("winrandr.features.gamma._CreateDCW", return_value=0x1234):
        with patch("winrandr.features.gamma._GetDeviceGammaRamp", return_value=1):
            with patch("winrandr.features.gamma._SetDeviceGammaRamp", return_value=1) as mock_set:
                with patch("winrandr.features.gamma._DeleteDC"):
                    assert set_night_mode(r"\\.\DISPLAY1", 0.5) is True
                    assert mock_set.call_count == 1


def test_set_night_mode_strength_00():
    """Success path with strength=0.0 (no change to blue channel)."""
    from winrandr.features.gamma import set_night_mode

    with patch("winrandr.features.gamma._CreateDCW", return_value=0x1234):
        with patch("winrandr.features.gamma._GetDeviceGammaRamp", return_value=1):
            with patch("winrandr.features.gamma._SetDeviceGammaRamp", return_value=1):
                with patch("winrandr.features.gamma._DeleteDC"):
                    assert set_night_mode(r"\\.\DISPLAY1", 0.0) is True


def test_set_night_mode_strength_10():
    """Success path with maximum strength (1.0) — blue channel should be zeroed."""
    from winrandr.features.gamma import set_night_mode

    def _mock_get_ramp(_dc, ramp):
        for i in range(768):
            ramp[i] = 65535
        return 1

    captured = []

    def _mock_set_ramp(_dc, ramp):
        captured.clear()
        captured.extend(ramp[i] for i in range(768))
        return 1

    with patch("winrandr.features.gamma._CreateDCW", return_value=0x1234):
        with patch("winrandr.features.gamma._GetDeviceGammaRamp", side_effect=_mock_get_ramp):
            with patch("winrandr.features.gamma._SetDeviceGammaRamp", side_effect=_mock_set_ramp):
                with patch("winrandr.features.gamma._DeleteDC"):
                    assert set_night_mode(r"\\.\DISPLAY1", 1.0) is True

    for i in range(512):
        assert captured[i] == 65535, f"R/G channel at index {i} should be 65535"
    for i in range(512, 768):
        assert captured[i] == 0, f"Blue channel at index {i} should be 0, got {captured[i]}"


def test_set_night_mode_blue_channel_only():
    """Verify only blue channel is modified after calling set_night_mode."""
    from winrandr.features.gamma import set_night_mode

    def _mock_get_ramp(_dc, ramp):
        for i in range(768):
            ramp[i] = 65535
        return 1

    captured = []

    def _mock_set_ramp(_dc, ramp):
        captured.clear()
        captured.extend(ramp[i] for i in range(768))
        return 1

    with patch("winrandr.features.gamma._CreateDCW", return_value=0x1234):
        with patch("winrandr.features.gamma._GetDeviceGammaRamp", side_effect=_mock_get_ramp):
            with patch("winrandr.features.gamma._SetDeviceGammaRamp", side_effect=_mock_set_ramp):
                with patch("winrandr.features.gamma._DeleteDC"):
                    assert set_night_mode(r"\\.\DISPLAY1", 0.5) is True

    for i in range(512):
        assert captured[i] == 65535, f"R/G channel at index {i} should be 65535"
    for i in range(512, 768):
        assert captured[i] <= 65535
        assert captured[i] == 32767, f"Blue channel at index {i} should be 32767, got {captured[i]}"


def test_set_night_mode_strength_negative():
    """strength=-0.1 should return False."""
    from winrandr.features.gamma import set_night_mode

    assert set_night_mode(r"\\.\DISPLAY1", -0.1) is False


def test_set_night_mode_strength_too_high():
    """strength=1.5 should return False."""
    from winrandr.features.gamma import set_night_mode

    assert set_night_mode(r"\\.\DISPLAY1", 1.5) is False


def test_set_night_mode_dc_fails():
    """_CreateDCW returns None."""
    from winrandr.features.gamma import set_night_mode

    with patch("winrandr.features.gamma._CreateDCW", return_value=None):
        assert set_night_mode(r"\\.\DISPLAY1", 0.5) is False


def test_set_night_mode_getramp_fails():
    """_GetDeviceGammaRamp returns 0 (failure)."""
    from winrandr.features.gamma import set_night_mode

    with patch("winrandr.features.gamma._CreateDCW", return_value=0x1234):
        with patch("winrandr.features.gamma._GetDeviceGammaRamp", return_value=0):
            with patch("winrandr.features.gamma._DeleteDC"):
                assert set_night_mode(r"\\.\DISPLAY1", 0.5) is False


def test_set_night_mode_setramp_fails():
    """_SetDeviceGammaRamp returns 0 (failure) — verify returns False."""
    from winrandr.features.gamma import set_night_mode

    with patch("winrandr.features.gamma._CreateDCW", return_value=0x1234):
        with patch("winrandr.features.gamma._GetDeviceGammaRamp", return_value=1):
            with patch("winrandr.features.gamma._SetDeviceGammaRamp", return_value=0):
                with patch("winrandr.features.gamma._DeleteDC"):
                    assert set_night_mode(r"\\.\DISPLAY1", 0.5) is False


def test_set_night_mode_oserror():
    """_CreateDCW raises OSError."""
    from winrandr.features.gamma import set_night_mode

    with patch("winrandr.features.gamma._CreateDCW", side_effect=OSError("mock")):
        assert set_night_mode(r"\\.\DISPLAY1", 0.5) is False
