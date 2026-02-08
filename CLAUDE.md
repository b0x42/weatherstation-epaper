# Claude Code Context

## Project Overview
Raspberry Pi weather station that displays current weather on a Waveshare 2.13" tri-color e-Paper display. Fetches data from Pirate Weather API.

## Tech Stack
- Python 3
- Pirate Weather API for weather data
- Waveshare e-Paper library for display
- PIL/Pillow for image rendering
- pytest for testing

## Key Files
- `weatherstation.py` - Main application with WeatherStation class and display logic
- `display_config.py` - Display configuration and dynamic module loading
- `weathericons.ttf` - Erik Flowers weather icons font
- `icons.json` - Maps weather condition names to font unicode characters
- `.env.example` - Environment variable template
- `weatherstation.service` - Systemd service file for auto-start

## Running Tests
```bash
.venv/bin/python -m pytest tests/ -v
```

**Always run tests locally before pushing.**

## Git Workflow
Always create a feature branch for new features, functions, or bug fixes. Never commit directly to main.

## Release Process
1. Update version in `pyproject.toml` to match the new release version (e.g., 1.1.3)
2. Merge version bump PR to main
3. Create and push annotated tag:
   ```bash
   git tag -a v1.x.x -m "Release v1.x.x"
   git push origin v1.x.x
   ```
4. GitHub Actions will automatically create the release with changelog and build artifacts

**IMPORTANT:** Always ensure the version in `pyproject.toml` matches the git tag version before creating a release.

Tests mock the hardware dependencies (`waveshare_epd`, `pirateweather`) since they require actual Raspberry Pi hardware.

## Supported Displays

The weather station supports Waveshare 2.13" e-Paper displays (104x212 resolution):

- **epd2in13bc** (default) - Bi-color (black/red)
- **epd2in13d** - Monochrome (black/white) with partial update support

Configure via `DISPLAY_MODEL` environment variable in `.env` file.
Both displays share the same layout (104x212 landscape).

## Development Notes
- Hardware libraries are mocked in tests - see `tests/test_weatherstation.py`
- Display uses landscape orientation (212x104 pixels)
- Bi-color displays: black, white, and red (red used when current temp >= max temp)
- Monochrome displays: all text rendered in black
- All config via environment variables (see `.env.example`)
- Weather icons use font glyphs, not PNG files

### Icon Positioning with Precise Padding

Icon fonts have invisible whitespace around the visible glyph. Using `font.getmetrics()` alone gives imprecise positioning because it includes this whitespace. To get precise pixel-perfect padding:

**Use `getbbox()` instead of `getmetrics()`:**

```python
# Get actual bounding box of the visible glyph (excludes font whitespace)
icon_bbox = font_icon.getbbox(icon_char)
# Returns (left, top, right, bottom) of the actual visible pixels

icon_actual_width = icon_bbox[2] - icon_bbox[0]   # right - left
icon_actual_height = icon_bbox[3] - icon_bbox[1]  # bottom - top
icon_left_whitespace = icon_bbox[0]   # invisible space on left
icon_top_whitespace = icon_bbox[1]    # invisible space above

# Position so visible icon has 5px padding from right edge
icon_x = display_width - padding - icon_actual_width - icon_left_whitespace

# Position so visible icon has 5px padding from top edge
icon_y = padding - icon_top_whitespace
```

**Example values for fog icon at size 44:**
```
icon_bbox: (0, 10, 39, 38)
icon_actual_width: 39px
icon_top_whitespace: 10px (glyph starts 10px below font baseline)
```

**Key insight:** Font metrics (`getmetrics()`) return the font's design dimensions, while `getbbox()` returns the actual visible pixel bounds for a specific character. This difference is significant for icon fonts.

**Note:** Font rendering may differ slightly between emulator (macOS) and hardware (Raspberry Pi) due to different font rendering engines. Always verify final layout on actual hardware.

## Common Tasks
- Update icon mappings: Edit `icons.json`
- Change display layout: Modify `display_weather()` in `weatherstation.py`
- Add new config options: Add to environment variables section at top of `weatherstation.py`
- Add support for new display models: Add to `DISPLAY_REGISTRY` in `display_config.py`
