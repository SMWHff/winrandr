"""winrandr — Windows xrandr-like display configuration tool."""

__version__ = "0.6.0"

__all__ = [
    "DisplayInfo", "DisplayMode",
    "list_displays", "set_resolution", "set_preferred_resolution", "set_auto",
    "set_position", "set_position_relative", "set_rotation", "set_primary",
    "set_off", "set_noprimary", "set_brightness", "set_gamma", "set_reflect",
    "list_providers", "get_display_props", "enumerate_modes", "get_edid",
    "identify_display",
    "save_profile", "load_profile", "list_profiles", "delete_profile", "diff_profile", "preview_save",
    "ROTATION_NAMES", "ROTATION_FROM_NAME",
]

from winrandr.models import DisplayInfo as DisplayInfo, DisplayMode as DisplayMode
from winrandr.api import (
    list_displays as list_displays,
    set_resolution as set_resolution,
    set_preferred_resolution as set_preferred_resolution,
    set_auto as set_auto,
    set_position as set_position,
    set_position_relative as set_position_relative,
    set_rotation as set_rotation,
    set_primary as set_primary,
    set_off as set_off,
    set_noprimary as set_noprimary,
    set_brightness as set_brightness,
    set_gamma as set_gamma,
    set_reflect as set_reflect,
    list_providers as list_providers,
    identify_display as identify_display,
    get_display_props as get_display_props,
    enumerate_modes as enumerate_modes,
)
from winrandr.edid import get_edid as get_edid
from winrandr.profiles import (
    save_profile as save_profile, load_profile as load_profile,
    list_profiles as list_profiles, delete_profile as delete_profile,
    diff_profile as diff_profile, preview_save as preview_save,
)
from winrandr.win32.constants import (
    ROTATION_NAMES as ROTATION_NAMES,
    ROTATION_FROM_NAME as ROTATION_FROM_NAME,
)
