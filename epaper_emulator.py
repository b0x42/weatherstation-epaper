"""Shim to load EPD class from EPD-Emulator without package name conflicts."""

import importlib.util
from pathlib import Path

_emulator_file = Path(__file__).parent / "EPD-Emulator" / "epaper_emulator" / "emulator.py"
_spec = importlib.util.spec_from_file_location("_epaper_emulator_impl", _emulator_file)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

EPD = _module.EPD  # noqa: F401
