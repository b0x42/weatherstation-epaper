"""Adapter to make E-Paper-Emulator compatible with waveshare_epd interface."""

from PIL import Image, ImageChops

from display_config import get_display_config

try:
    from epaper_emulator import EPD as EmulatorEPD
    EMULATOR_AVAILABLE = True
except ImportError:
    EMULATOR_AVAILABLE = False
    EmulatorEPD = None


# Mapping from waveshare model names to emulator config files
EMULATOR_CONFIG_MAPPING = {
    # 104x212 resolution displays
    'epd2in13bc': 'epd2in13bc',   # Bi-color (black/red)
    'epd2in13d': 'epd2in13bc',    # Monochrome (uses same resolution)
    # 122x250 resolution displays
    'epd2in13': 'epd2in13',       # Original monochrome
    'epd2in13_V2': 'epd2in13v2',  # Monochrome V2
    'epd2in13_V3': 'epd2in13v2',  # Monochrome V3 (use v2 config)
    'epd2in13_V4': 'epd2in13v2',  # Monochrome V4 (use v2 config)
    'epd2in13b_V3': 'epd2in13',   # Bi-color V3 (use base config)
    'epd2in13b_V4': 'epd2in13',   # Bi-color V4 (use base config)
    'epd2in13g': 'epd2in13',      # 4-color (use base config)
}


class EmulatorAdapter:
    """Adapter to make E-Paper-Emulator compatible with waveshare_epd interface.

    Args:
        model_name: Waveshare model name (e.g., 'epd2in13bc')
        use_color: Whether display supports color (for emulator config)
        use_tkinter: Use Tkinter GUI (True) or Flask web server (False)
        update_interval: Display refresh interval in seconds
    """

    def __init__(self, model_name, use_color=False, use_tkinter=True,
                 update_interval=1):
        if not EMULATOR_AVAILABLE:
            raise ImportError(
                "E-Paper-Emulator not installed. "
                "Install from: https://github.com/benjaminburzan/E-Paper-Emulator"
            )

        config_file = EMULATOR_CONFIG_MAPPING.get(model_name)
        if not config_file:
            raise ValueError(
                f"No emulator config mapping for model: {model_name}. "
                f"Supported models: {list(EMULATOR_CONFIG_MAPPING.keys())}"
            )

        # reverse_orientation makes window landscape since weatherstation renders in landscape
        self._epd = EmulatorEPD(
            config_file=config_file,
            use_tkinter=use_tkinter,
            use_color=use_color,
            update_interval=update_interval,
            reverse_orientation=True
        )

        self._model_name = model_name
        self._use_color = use_color
        self._initialized = False
        config = get_display_config(model_name)
        self._resolution = (config['width'], config['height'])

    def init(self):
        """Initialize the emulated display."""
        self._epd.init()
        self._initialized = True

    def Clear(self):
        """Clear the display (waveshare signature - no parameters)."""
        # Emulator requires fill value; use tuple for RGB mode, int for mode "1"
        fill = (255, 255, 255) if self._use_color else 255
        self._epd.Clear(fill)

    def getbuffer(self, image):
        """Convert PIL Image to display buffer (waveshare-compatible passthrough)."""
        return image

    def display(self, *buffers):
        """Display buffer(s) on emulated screen.

        Supports both monochrome and bi-color signatures:
        - Monochrome: display(buffer_black)
        - Bi-color: display(buffer_black, buffer_red)
        """
        if not self._initialized:
            raise RuntimeError("Display not initialized. Call init() first.")

        if len(buffers) not in (1, 2):
            raise ValueError(f"Expected 1 or 2 buffers, got {len(buffers)}")

        buffer_black = buffers[0]

        # Composite black and red layers into an RGB image for the emulator
        if len(buffers) == 2 and self._use_color:
            black_l = buffer_black.convert('L')
            red_l = buffers[1].convert('L')
            r = ImageChops.lighter(ImageChops.invert(red_l), black_l)
            g = ImageChops.multiply(black_l, red_l)
            composited = Image.merge('RGB', (r, g, g))
        elif len(buffers) == 2:
            composited = ImageChops.multiply(buffer_black, buffers[1])
        else:
            composited = buffer_black

        # Rotate landscape (212x104) to portrait (104x212) for reverse_orientation window
        rotated = composited.rotate(-90, expand=True)
        self._epd.image = rotated.copy()
        self._epd.display(rotated)

    def sleep(self):
        """Put display into sleep mode (no-op for emulator)."""

    @property
    def width(self):
        """Display width in pixels."""
        return self._resolution[0]

    @property
    def height(self):
        """Display height in pixels."""
        return self._resolution[1]
