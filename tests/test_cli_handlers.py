"""Tests for CLI handler functions with dry-run mode."""

from argparse import Namespace
import pytest
from winrandr.cli import (
    _handle_mode, _handle_pos, _handle_gamma,
    _handle_brightness, _handle_reflect, _handle_relative,
    _handle_auto, _handle_rotate, _handle_primary,
    _handle_preferred, _handle_off,
)


DN = r"\\.\DISPLAY1"


def _ns(**kwargs) -> Namespace:
    defaults = dict(dry_run=True, output="DISPLAY1",
                    mode=None, pos=None, rate=None, rotate=None,
                    primary=None, preferred=None, off=None,
                    brightness=None, reflect=None, gamma=None,
                    left_of=None, right_of=None, above=None, below=None, same_as=None)
    defaults.update(kwargs)
    return Namespace(**defaults)


# --- _handle_mode ---

def test_mode_valid():
    _handle_mode(_ns(mode="1920x1080"), DN)

def test_mode_valid_with_rate():
    _handle_mode(_ns(mode="1920x1080", rate=60), DN)

def test_mode_no_x():
    with pytest.raises(SystemExit):
        _handle_mode(_ns(mode="invalid"), DN)

def test_mode_bad_value():
    with pytest.raises(SystemExit):
        _handle_mode(_ns(mode="abcxdef"), DN)


# --- _handle_pos ---

def test_pos_valid():
    _handle_pos(_ns(pos="0x0"), DN)

def test_pos_plus_prefix():
    _handle_pos(_ns(pos="+1920x+0"), DN)

def test_pos_xrandr_plus_format():
    """xrandr style +1920+0 should be accepted and converted."""
    _handle_pos(_ns(pos="+1920+0"), DN)

def test_pos_negative_y():
    _handle_pos(_ns(pos="1920x-1080"), DN)

def test_pos_no_x():
    with pytest.raises(SystemExit):
        _handle_pos(_ns(pos="invalid"), DN)

def test_pos_bad_x():
    with pytest.raises(SystemExit):
        _handle_pos(_ns(pos="abcxdef"), DN)

def test_pos_extra_parts():
    with pytest.raises(SystemExit):
        _handle_pos(_ns(pos="1920x1080x32"), DN)


# --- _handle_gamma ---

def test_gamma_valid():
    _handle_gamma(_ns(gamma="1.0:0.9:0.8"), DN)

def test_gamma_single_value():
    _handle_gamma(_ns(gamma="0.8"), DN)

def test_gamma_bad_format():
    with pytest.raises(SystemExit):
        _handle_gamma(_ns(gamma="abc"), DN)

def test_gamma_wrong_count():
    with pytest.raises(SystemExit):
        _handle_gamma(_ns(gamma="1.0:0.9"), DN)


# --- _handle_brightness ---

def test_brightness_valid():
    _handle_brightness(_ns(brightness=1.0), DN)

def test_brightness_low():
    _handle_brightness(_ns(brightness=0.05), DN)


# --- _handle_reflect ---

def test_reflect_xy():
    _handle_reflect(_ns(reflect="xy"), DN)

def test_reflect_x_unsupported():
    with pytest.raises(SystemExit):
        _handle_reflect(_ns(reflect="x"), DN)


# --- _handle_relative ---

def test_relative_without_ref():
    """When no relative arg is set, handler should return silently."""
    _handle_relative(_ns(), DN)


# --- _handle_auto ---

def test_auto():
    _handle_auto(_ns(auto=True), DN)


# --- _handle_rotate ---

def test_rotate_normal():
    _handle_rotate(_ns(rotate="normal"), DN)


# --- _handle_primary ---

def test_primary():
    _handle_primary(_ns(primary=True), DN)


# --- _handle_preferred ---

def test_preferred():
    _handle_preferred(_ns(preferred=True), DN)


# --- _handle_off ---

def test_off():
    _handle_off(_ns(off=True), DN)
