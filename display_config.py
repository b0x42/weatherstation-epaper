"""Display configuration system for Waveshare e-Paper displays.

Provides a registry of supported displays, dynamic module loading,
and layout configuration for the weather station.
"""

# Display Registry - Maps model names to their specifications
DISPLAY_REGISTRY = {
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
    if model_name not in DISPLAY_REGISTRY:
        raise ValueError(
            f"Unknown display model: {model_name}. "
            f"Supported models: {', '.join(DISPLAY_REGISTRY.keys())}"
        )

    try:
        module = __import__(f'waveshare_epd.{model_name}', fromlist=[model_name])
        return getattr(module, 'EPD')
    except ImportError as e:
        raise ImportError(
            f"Failed to import display module for {model_name}: {e}"
        ) from e


def get_display_config(model_name):
    """Get configuration dictionary for specified display model.

    Args:
        model_name: Display model identifier (e.g., 'epd2in13bc')

    Returns:
        Dictionary with display specifications (width, height, colors, etc.)

    Raises:
        ValueError: If model_name is not in registry
    """
    if model_name not in DISPLAY_REGISTRY:
        raise ValueError(
            f"Unknown display model: {model_name}. "
            f"Supported models: {', '.join(DISPLAY_REGISTRY.keys())}"
        )
    return DISPLAY_REGISTRY[model_name]


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
        'PADDING': 10,
        'FONT_SIZE_TEMPERATURE': 32,
        'FONT_SIZE_SUMMARY_MAX': 18,
        'FONT_SIZE_SUMMARY_MIN': 12,
        'ICON_SIZE': 48,
        'MAX_SUMMARY_LINES': 2,
        'TEMP_HEIGHT_RATIO': 0.55,
    }
