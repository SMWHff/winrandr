#!/usr/bin/env python3
"""winrandr — Windows xrandr-like display configuration tool.

Thin entry point that delegates to winrandr.cli.
Use `python -m winrandr` or the `winrandr` console script instead.
"""

from winrandr.cli import main

main()
