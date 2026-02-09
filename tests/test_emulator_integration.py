"""Integration tests for E-Paper-Emulator adapter.

These tests require E-Paper-Emulator to be installed.
Run with: USE_EMULATOR=true pytest tests/test_emulator_integration.py
"""
import os
import sys

import pytest

# Only run tests if emulator is requested
pytestmark = pytest.mark.skipif(
    os.environ.get("USE_EMULATOR", "false").lower() != "true",
    reason="Emulator tests only run with USE_EMULATOR=true"
)

# Check if emulator is available
try:
    from emulator_adapter import EmulatorAdapter, EMULATOR_AVAILABLE
    if not EMULATOR_AVAILABLE:
        pytest.skip("E-Paper-Emulator not installed", allow_module_level=True)
except ImportError:
    pytest.skip("emulator_adapter not available", allow_module_level=True)


def test_emulator_adapter_initialization():
    """Test that emulator adapter can be initialized."""
    adapter = EmulatorAdapter('epd2in13bc', use_color=True, use_tkinter=False)
    assert adapter is not None
    assert adapter.width == 104
    assert adapter.height == 212


def test_emulator_adapter_interface():
    """Test that adapter implements required interface."""
    adapter = EmulatorAdapter('epd2in13bc', use_color=True, use_tkinter=False)

    # Check all required methods exist
    assert hasattr(adapter, 'init')
    assert hasattr(adapter, 'Clear')
    assert hasattr(adapter, 'getbuffer')
    assert hasattr(adapter, 'display')
    assert hasattr(adapter, 'sleep')
    assert hasattr(adapter, 'width')
    assert hasattr(adapter, 'height')


def test_emulator_adapter_invalid_model():
    """Test that adapter raises error for unsupported model."""
    with pytest.raises(ValueError, match="No emulator config mapping"):
        EmulatorAdapter('invalid_model', use_color=False, use_tkinter=False)


def test_display_config_loads_emulator():
    """Test that display_config loads emulator when USE_EMULATOR=true."""
    # Environment should already be set via pytestmark skipif condition
    # but ensure it's set for this specific test
    original_value = os.environ.get('USE_EMULATOR')
    os.environ['USE_EMULATOR'] = 'true'

    try:
        from display_config import load_display_module

        EPDClass = load_display_module('epd2in13bc')
        epd = EPDClass()

        # Check it's an emulator adapter
        assert 'EmulatorAdapter' in str(type(epd))
    finally:
        # Restore original environment state
        if original_value is None:
            os.environ.pop('USE_EMULATOR', None)
        else:
            os.environ['USE_EMULATOR'] = original_value


def test_emulator_adapter_bi_color_model():
    """Test adapter with bi-color model (epd2in13bc)."""
    adapter = EmulatorAdapter('epd2in13bc', use_color=True, use_tkinter=False)
    assert adapter._use_color is True
    assert adapter._model_name == 'epd2in13bc'


def test_emulator_adapter_monochrome_model():
    """Test adapter with monochrome model (epd2in13d)."""
    adapter = EmulatorAdapter('epd2in13d', use_color=False, use_tkinter=False)
    assert adapter._use_color is False
    assert adapter._model_name == 'epd2in13d'
