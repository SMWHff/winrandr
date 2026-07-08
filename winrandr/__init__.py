"""winrandr — Windows xrandr-like display configuration tool."""

__version__ = "0.3.0"

from winrandr.models import DisplayInfo
from winrandr.api import (
    list_displays,
    set_resolution,
    set_preferred_resolution,
    set_auto,
    set_position,
    set_position_relative,
    set_rotation,
    set_primary,
    set_off,
    set_noprimary,
    set_brightness,
    set_gamma,
    set_reflect,
    list_providers,
    get_display_props,
)
from winrandr.edid import get_edid
from winrandr.win32.constants import ROTATION_NAMES, ROTATION_FROM_NAME
