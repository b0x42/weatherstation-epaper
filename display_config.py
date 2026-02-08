"""Display configuration system for Waveshare e-Paper displays.

Provides a registry of supported displays, dynamic module loading,
and layout configuration for the weather station.
"""

# Display Registry - Maps model names to their specifications
_DISPLAY_REGISTRY = {
    'epd2in13bc': {
        'width': 104,
        'height': 212,
        'colors': ['black', 'white', 'red'],
        'has_red': True,
        'features': [],
        'description': 'Bi-color (black/red) tri-color display',
    },
    'epd2in13d': {
        'width': 104,
        'height': 212,
        'colors': ['black', 'white'],
        'has_red': False,
        'features': ['partial_update'],
        'description': 'Monochrome (black/white) with partial update support',
    },
}

# Public read-only access to registry for tests
DISPLAY_REGISTRY = _DISPLAY_REGISTRY


def _validate_model(model_name):
    """Validate model name exists in registry.

    Args:
        model_name: Display model identifier to validate

    Raises:
        ValueError: If model_name is not in registry
    """
    if model_name not in _DISPLAY_REGISTRY:
        supported = ', '.join(_DISPLAY_REGISTRY.keys())
        raise ValueError(f"Unknown display model: {model_name}. Supported models: {supported}")


def load_display_module(model_name):
    """Dynamically import and return EPD class for specified model.

    Args:
        model_name: Display model identifier (e.g., 'epd2in13bc')

    Returns:
        EPD class from the waveshare_epd module

    Raises:
        ValueError: If model_name is not in registry
        ImportError: If display module cannot be imported
    """
    _validate_model(model_name)

    try:
        module = __import__(f'waveshare_epd.{model_name}', fromlist=[model_name])
        return getattr(module, 'EPD')
    except ImportError as e:
        raise ImportError(f"Failed to import display module for {model_name}: {e}") from e


def get_display_config(model_name):
    """Get configuration dictionary for specified display model.

    Args:
        model_name: Display model identifier (e.g., 'epd2in13bc')

    Returns:
        Dictionary with display specifications (width, height, colors, etc.)

    Raises:
        ValueError: If model_name is not in registry
    """
    _validate_model(model_name)
    return _DISPLAY_REGISTRY[model_name]


def get_layout_config():
    """Get layout constants for 104x212 displays.

    Returns fixed layout configuration suitable for 104x212 resolution.
    Both epd2in13bc and epd2in13d share these layout constants.

    Returns:
        Dictionary with layout constants (padding, font sizes, etc.)

    Note:
        When adding 122x250 displays in Phase 2, this function will need
        to implement resolution-based scaling logic.
    """
    return {
        'PADDING': 5,
        'FONT_SIZE_TEMPERATURE': 30,
        'FONT_SIZE_SUMMARY_MAX': 16,
        'FONT_SIZE_SUMMARY_MIN': 10,
        'ICON_SIZE': 48,
        'MAX_SUMMARY_LINES': 3,
        'TEMP_HEIGHT_RATIO': 0.50,
        'LINE_SPACING': 4,
    }
