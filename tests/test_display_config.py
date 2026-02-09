"""Tests for display_config module."""
import os
import sys
from unittest.mock import MagicMock

import pytest

# Mock waveshare_epd before importing display_config
sys.modules['waveshare_epd'] = MagicMock()
ALL_DISPLAY_MODELS = [
    'epd2in13bc', 'epd2in13d',  # 104x212
    'epd2in13', 'epd2in13_V2', 'epd2in13_V3', 'epd2in13_V4',  # 122x250 mono
    'epd2in13b_V3', 'epd2in13b_V4', 'epd2in13g',  # 122x250 color
]
for display_model in ALL_DISPLAY_MODELS:
    mock_module = MagicMock()
    mock_module.EPD = MagicMock()
    sys.modules[f'waveshare_epd.{display_model}'] = mock_module

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from display_config import (
    DISPLAY_REGISTRY,
    get_display_config,
    get_layout_config,
    load_display_module,
)


def test_display_registry_contains_all_displays():
    """Test that all 2.13" displays are registered."""
    for model in ALL_DISPLAY_MODELS:
        assert model in DISPLAY_REGISTRY, f"Missing model: {model}"
    assert len(DISPLAY_REGISTRY) == 9


def test_epd2in13bc_config():
    """Test epd2in13bc display configuration."""
    config = get_display_config('epd2in13bc')
    assert config['width'] == 104
    assert config['height'] == 212
    assert config['has_red'] is True
    assert 'black' in config['colors']
    assert 'white' in config['colors']
    assert 'red' in config['colors']


def test_epd2in13d_config():
    """Test epd2in13d display configuration."""
    config = get_display_config('epd2in13d')
    assert config['width'] == 104
    assert config['height'] == 212
    assert config['has_red'] is False
    assert 'black' in config['colors']
    assert 'white' in config['colors']
    assert 'red' not in config['colors']
    assert 'partial_update' in config['features']


def test_get_display_config_invalid_model():
    """Test that invalid model raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        get_display_config('invalid_model')
    assert 'Unknown display model' in str(exc_info.value)
    assert 'invalid_model' in str(exc_info.value)


def test_load_display_module_valid():
    """Test loading valid display module."""
    # Ensure emulator mode is disabled for this test
    original_value = os.environ.get("USE_EMULATOR")
    try:
        os.environ["USE_EMULATOR"] = "false"
        epd_class = load_display_module('epd2in13bc')
        assert epd_class is not None
        # Verify it's the mocked EPD class
        assert callable(epd_class)
    finally:
        if original_value is None:
            os.environ.pop("USE_EMULATOR", None)
        else:
            os.environ["USE_EMULATOR"] = original_value


def test_load_display_module_invalid():
    """Test loading invalid display module raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        load_display_module('invalid_model')
    assert 'Unknown display model' in str(exc_info.value)


def test_layout_config_104x212():
    """Test layout config for 104x212 displays."""
    layout = get_layout_config('epd2in13bc')

    assert layout['PADDING'] == 5
    assert layout['FONT_SIZE_TEMPERATURE'] == 30
    assert layout['FONT_SIZE_SUMMARY_MAX'] == 16
    assert layout['FONT_SIZE_SUMMARY_MIN'] == 10
    assert layout['ICON_SIZE'] == 48
    assert layout['MAX_SUMMARY_LINES'] == 3
    assert layout['TEMP_HEIGHT_RATIO'] == 0.50
    assert layout['LINE_SPACING'] == 4


def test_layout_config_122x250():
    """Test layout config for 122x250 displays."""
    layout = get_layout_config('epd2in13_V4')

    assert layout['PADDING'] == 6
    assert layout['FONT_SIZE_TEMPERATURE'] == 36
    assert layout['FONT_SIZE_SUMMARY_MAX'] == 18
    assert layout['FONT_SIZE_SUMMARY_MIN'] == 12
    assert layout['ICON_SIZE'] == 56
    assert layout['MAX_SUMMARY_LINES'] == 3
    assert layout['TEMP_HEIGHT_RATIO'] == 0.48
    assert layout['LINE_SPACING'] == 5


def test_displays_grouped_by_resolution():
    """Test that displays are correctly grouped by resolution."""
    # 104x212 displays
    for model in ['epd2in13bc', 'epd2in13d']:
        config = get_display_config(model)
        assert config['width'] == 104
        assert config['height'] == 212

    # 122x250 displays
    for model in ['epd2in13', 'epd2in13_V2', 'epd2in13_V3', 'epd2in13_V4',
                  'epd2in13b_V3', 'epd2in13b_V4', 'epd2in13g']:
        config = get_display_config(model)
        assert config['width'] == 122
        assert config['height'] == 250


def test_color_capabilities_differ():
    """Test that color capabilities differ between displays."""
    bc_config = get_display_config('epd2in13bc')
    d_config = get_display_config('epd2in13d')

    assert bc_config['has_red'] is True
    assert d_config['has_red'] is False
    assert len(bc_config['colors']) > len(d_config['colors'])


def test_display_registry_structure():
    """Test that all registry entries have required fields."""
    required_fields = ['width', 'height', 'colors', 'has_red', 'features']

    for model_name, config in DISPLAY_REGISTRY.items():
        for field in required_fields:
            assert field in config, f"Display {model_name} missing field: {field}"

        # Validate types
        assert isinstance(config['width'], int)
        assert isinstance(config['height'], int)
        assert isinstance(config['colors'], list)
        assert isinstance(config['has_red'], bool)
        assert isinstance(config['features'], list)
