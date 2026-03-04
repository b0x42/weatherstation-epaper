"""Display configuration system for Waveshare e-Paper displays.

Provides a registry of supported displays, dynamic module loading,
and layout configuration for the weather station.
"""

import os

# Display Registry - Maps model names to their specifications
_DISPLAY_REGISTRY = {
    # 104x212 resolution displays
    'epd2in13bc': {
        'width': 104,
        'height': 212,
        'colors': ['black', 'white', 'red'],
        'has_red': True,
        'features': [],
        'description': '2.13" Bi-color (black/red)',
    },
    'epd2in13d': {
        'width': 104,
        'height': 212,
        'colors': ['black', 'white'],
        'has_red': False,
        'features': ['partial_update'],
        'description': '2.13" Monochrome with partial update',
    },
    # 122x250 resolution displays
    'epd2in13': {
        'width': 122,
        'height': 250,
        'colors': ['black', 'white'],
        'has_red': False,
        'features': [],
        'description': '2.13" Monochrome (original)',
    },
    'epd2in13_V2': {
        'width': 122,
        'height': 250,
        'colors': ['black', 'white'],
        'has_red': False,
        'features': ['partial_update'],
        'description': '2.13" Monochrome V2',
    },
    'epd2in13_V3': {
        'width': 122,
        'height': 250,
        'colors': ['black', 'white'],
        'has_red': False,
        'features': ['partial_update'],
        'description': '2.13" Monochrome V3',
    },
    'epd2in13_V4': {
        'width': 122,
        'height': 250,
        'colors': ['black', 'white'],
        'has_red': False,
        'features': ['partial_update', 'fast_refresh'],
        'description': '2.13" Monochrome V4 with fast refresh',
    },
    'epd2in13b_V3': {
        'width': 122,
        'height': 250,
        'colors': ['black', 'white', 'red'],
        'has_red': True,
        'features': [],
        'description': '2.13" Bi-color V3 (black/red)',
    },
    'epd2in13b_V4': {
        'width': 122,
        'height': 250,
        'colors': ['black', 'white', 'red'],
        'has_red': True,
        'features': [],
        'description': '2.13" Bi-color V4 (black/red)',
    },
    'epd2in13g': {
        'width': 122,
        'height': 250,
        'colors': ['black', 'white', 'yellow', 'red'],
        'has_red': True,
        'features': ['4_color'],
        'description': '2.13" 4-color (black/white/yellow/red)',
    },
    # 400x300 resolution displays (width/height swapped so canvas formula creates landscape)
    'epd4in2': {
        'width': 300,
        'height': 400,
        'colors': ['black', 'white'],
        'has_red': False,
        'features': [],
        'description': '4.2" Monochrome',
    },
    'epd4in2_V2': {
        'width': 300,
        'height': 400,
        'colors': ['black', 'white'],
        'has_red': False,
        'features': ['partial_update', 'fast_refresh'],
        'description': '4.2" Monochrome V2 with partial and fast refresh',
    },
    'epd4in2b': {
        'width': 300,
        'height': 400,
        'colors': ['black', 'white', 'red'],
        'has_red': True,
        'features': [],
        'description': '4.2" Bi-color (black/red)',
    },
    'epd4in2b_V2': {
        'width': 300,
        'height': 400,
        'colors': ['black', 'white', 'red'],
        'has_red': True,
        'features': [],
        'description': '4.2" Bi-color V2 (black/red)',
    },
    'epd4in2c': {
        'width': 300,
        'height': 400,
        'colors': ['black', 'white', 'yellow'],
        'has_red': True,
        'features': [],
        'description': '4.2" Bi-color (black/yellow)',
    },
    'epd4in2g': {
        'width': 300,
        'height': 400,
        'colors': ['black', 'white', 'red', 'yellow'],
        'has_red': True,
        'features': ['4_color'],
        'description': '4.2" 4-color (black/white/red/yellow)',
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

    Checks USE_EMULATOR environment variable to decide between
    hardware and emulator backend.

    Args:
        model_name: Display model identifier (e.g., 'epd2in13bc')

    Returns:
        EPD class (hardware or emulator adapter)

    Raises:
        ValueError: If model_name is not in registry
        ImportError: If display module cannot be imported
    """
    _validate_model(model_name)

    # Check if emulator mode is enabled
    use_emulator = os.environ.get("USE_EMULATOR", "false").lower() == "true"

    if use_emulator:
        # Load emulator adapter
        try:
            from emulator_adapter import EmulatorAdapter, EMULATOR_AVAILABLE

            if not EMULATOR_AVAILABLE:
                raise ImportError(
                    "USE_EMULATOR=true but E-Paper-Emulator not installed. "
                    "Install from: https://github.com/benjaminburzan/EPD-Emulator"
                )

            # Get display config to determine if color is supported
            config = _DISPLAY_REGISTRY[model_name]
            use_color = config['has_red']

            # Check if Tkinter mode is enabled (default: False for Flask/browser mode)
            use_tkinter = os.environ.get("USE_TKINTER", "false").lower() == "true"

            # Return factory function that creates adapter
            # Using default arguments to capture current values (closure)
            def create_adapter(model=model_name, color=use_color, tkinter=use_tkinter):
                return EmulatorAdapter(
                    model_name=model,
                    use_color=color,
                    use_tkinter=tkinter,
                    update_interval=1
                )
            return create_adapter

        except ImportError as e:
            raise ImportError(
                f"Failed to load emulator for {model_name}: {e}"
            ) from e
    else:
        # Load hardware driver via waveshare-epaper package
        try:
            import epaper
            module = epaper.epaper(model_name)
            return module.EPD
        except (ImportError, AttributeError) as e:
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
    _validate_model(model_name)
    return _DISPLAY_REGISTRY[model_name]


def get_layout_config(model_name=None):
    """Get layout constants for the specified display model.

    Args:
        model_name: Display model identifier. If None, returns 104x212 layout.

    Returns:
        Dictionary with layout constants (padding, font sizes, etc.)
    """
    # Determine resolution from model
    if model_name and model_name in _DISPLAY_REGISTRY:
        width = _DISPLAY_REGISTRY[model_name]['width']
    else:
        width = 104  # Default to smaller resolution

    if width == 300:
        # Layout for 400x300 displays (epd4in2 — width/height swapped in registry)
        # Canvas is landscape 400x300: epd.height=400 (horiz), epd.width=300 (vert)
        return {
            'PADDING': 10,
            'FONT_SIZE_TEMPERATURE': 60,
            'FONT_SIZE_SUMMARY_MAX': 30,
            'FONT_SIZE_SUMMARY_MIN': 16,
            'ICON_SIZE': 60,
            'MAX_SUMMARY_LINES': 5,
            'TEMP_HEIGHT_RATIO': 0.45,
            'LINE_SPACING': 8,
        }

    if width == 122:
        # Layout for 122x250 displays (larger)
        return {
            'PADDING': 6,
            'FONT_SIZE_TEMPERATURE': 36,
            'FONT_SIZE_SUMMARY_MAX': 18,
            'FONT_SIZE_SUMMARY_MIN': 12,
            'ICON_SIZE': 56,
            'MAX_SUMMARY_LINES': 3,
            'TEMP_HEIGHT_RATIO': 0.48,
            'LINE_SPACING': 5,
        }

    # Layout for 104x212 displays (original)
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
