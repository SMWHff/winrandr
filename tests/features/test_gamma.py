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


def test_identify_exception():
    from winrandr.features.gamma import identify_display
    with patch("winrandr.features.gamma._CreateDCW", side_effect=OSError("mock")):
        assert identify_display(r"\\.\DISPLAY1") is False
