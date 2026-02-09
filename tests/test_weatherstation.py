"""Tests for weatherstation module."""
import json
import os
import sys
from unittest.mock import MagicMock, patch

# Project root for imports and file paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Mock hardware dependencies before importing weatherstation
sys.modules['pirateweather'] = MagicMock()

# Only mock waveshare_epd if not using emulator
if os.environ.get("USE_EMULATOR", "false").lower() != "true":
    sys.modules['waveshare_epd'] = MagicMock()
    # Mock display modules for both supported displays
    for display_model in ['epd2in13bc', 'epd2in13d']:
        sys.modules[f'waveshare_epd.{display_model}'] = MagicMock()

from weatherstation import wrap_text, get_line_height, fit_summary_to_lines, display_weather
from display_config import get_layout_config

ICONS_PATH = os.path.join(PROJECT_ROOT, "icons", "icons.json")


def test_icons_json_exists():
    assert os.path.exists(ICONS_PATH)


def test_icons_json_valid():
    with open(ICONS_PATH, "r", encoding="utf-8") as f:
        icons = json.load(f)

    assert isinstance(icons, dict)
    assert "clear-day" in icons
    assert "rain" in icons


def test_weather_icons_font_exists():
    font_path = os.path.join(PROJECT_ROOT, "icons", "weathericons.ttf")
    assert os.path.isfile(font_path)


def test_env_example_exists():
    env_path = os.path.join(PROJECT_ROOT, ".env.example")
    assert os.path.exists(env_path)


def test_wrap_text_single_line():
    """Test that short text stays on one line."""
    mock_font = MagicMock()
    mock_font.getlength.return_value = 50  # Text fits

    result = wrap_text("Short text", mock_font, max_width=100, max_lines=2)

    assert result == ["Short text"]


def test_wrap_text_wraps_long_text():
    """Test that long text wraps to multiple lines."""
    mock_font = MagicMock()
    # Simulate: each word is ~30px, max_width is 70px (fits ~2 words per line)
    def mock_getlength(text):
        return len(text.split()) * 30
    mock_font.getlength.side_effect = mock_getlength

    result = wrap_text("One two three four", mock_font, max_width=70, max_lines=3)

    assert len(result) == 2
    assert result[0] == "One two"
    assert result[1] == "three four"


def test_wrap_text_respects_max_lines():
    """Test that wrap_text respects max_lines limit."""
    mock_font = MagicMock()
    # Each word is 40px, max_width is 50px (one word per line)
    mock_font.getlength.side_effect = lambda text: len(text.split()) * 40

    result = wrap_text("One two three four five", mock_font, max_width=50, max_lines=2)

    assert len(result) == 2
    assert result[0] == "One"
    assert result[1] == "two"


def test_wrap_text_empty_string():
    """Test wrap_text with empty string."""
    mock_font = MagicMock()
    mock_font.getlength.return_value = 0

    result = wrap_text("", mock_font, max_width=100, max_lines=2)

    assert not result


def test_get_line_height():
    """Test get_line_height calculates correct height."""
    mock_font = MagicMock()
    mock_font.getmetrics.return_value = (14, 4)  # ascent=14, descent=4

    result = get_line_height(mock_font)

    assert result == 20  # 14 + 4 + 2 (spacing)


@patch('weatherstation.ImageFont.truetype')
def test_fit_summary_short_text_uses_max_size(mock_truetype):
    """Test that short text uses the maximum font size."""
    mock_font = MagicMock()
    mock_font.getlength.return_value = 50  # Text fits easily
    mock_truetype.return_value = mock_font

    _, lines = fit_summary_to_lines("Short", "/fake/path.ttf", max_width=200, max_lines=2, max_size=18, min_size=12)

    # Should use max size (18) on first try
    mock_truetype.assert_called_with("/fake/path.ttf", 18)
    assert lines == ["Short"]


@patch('weatherstation.ImageFont.truetype')
def test_fit_summary_long_text_reduces_font_size(mock_truetype):
    """Test that long text triggers font size reduction."""
    def mock_font_factory(_path, size):
        mock_font = MagicMock()
        # At size >= 17: text doesn't fit; at size 16: text fits on 2 lines
        if size >= 17:
            mock_font.getlength.side_effect = lambda text: len(text.split()) * 60
        else:
            mock_font.getlength.side_effect = lambda text: len(text.split()) * 40
        return mock_font

    mock_truetype.side_effect = mock_font_factory

    fit_summary_to_lines("One two three", "/fake/path.ttf", max_width=100, max_lines=2, max_size=18, min_size=12)

    # Should have tried sizes 18, 17, then succeeded at 16
    assert mock_truetype.call_count == 3
    assert mock_truetype.call_args_list[-1][0] == ("/fake/path.ttf", 16)


@patch('weatherstation.ImageFont.truetype')
def test_fit_summary_respects_minimum_size(mock_truetype):
    """Test that minimum size is respected even if text doesn't fit."""
    mock_font = MagicMock()
    # Text never fits - each word is 200px, way over max_width
    mock_font.getlength.side_effect = lambda text: len(text.split()) * 200
    mock_truetype.return_value = mock_font

    fit_summary_to_lines("Very long text here", "/fake/path.ttf", max_width=100, max_lines=2, max_size=18, min_size=12)

    # Should end at minimum size (12)
    # Called for sizes 18, 17, 16, 15, 14, 13, 12, then final call at 12
    final_call = mock_truetype.call_args_list[-1]
    assert final_call[0] == ("/fake/path.ttf", 12)


def _create_mock_epd():
    """Create a mock EPD with standard 104x212 dimensions."""
    mock_epd = MagicMock()
    mock_epd.width = 104
    mock_epd.height = 212
    mock_epd.getbuffer.side_effect = lambda img: img
    return mock_epd


def test_display_weather_red_layer_when_temp_equals_max():
    """Test that temperature is drawn on red layer when current temp >= max temp."""
    mock_epd = _create_mock_epd()
    layout = get_layout_config('epd2in13bc')

    display_weather(mock_epd, temperature=5, temperature_max=5,
                    summary="Clear", icon_char="\uf00d",
                    has_red_layer=True, layout=layout)

    mock_epd.display.assert_called_once()
    args = mock_epd.display.call_args[0]
    assert len(args) == 2, "Bi-color display should receive two buffers"

    image_black = args[0]
    image_red = args[1]

    red_pixels = list(image_red.get_flattened_data())
    assert 0 in red_pixels, "Red layer should contain ink when temp >= max temp"

    black_pixels = list(image_black.get_flattened_data())
    assert 0 in black_pixels, "Black layer should contain ink for icon and summary"


def test_display_weather_black_layer_when_temp_below_max():
    """Test that temperature is drawn on black layer when current temp < max temp."""
    mock_epd = _create_mock_epd()
    layout = get_layout_config('epd2in13bc')

    display_weather(mock_epd, temperature=3, temperature_max=5,
                    summary="Clear", icon_char="\uf00d",
                    has_red_layer=True, layout=layout)

    mock_epd.display.assert_called_once()
    args = mock_epd.display.call_args[0]
    image_red = args[1]

    # Red layer should be all white (no ink) since temp < max
    red_pixels = list(image_red.get_flattened_data())
    assert 0 not in red_pixels, "Red layer should have no ink when temp < max temp"
