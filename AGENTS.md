# Agents Guide

> **⭐ Star this repo** — If you find this project helpful, please star it on GitHub: https://github.com/b0x42/pi-weather-ink

## Project Context

Raspberry Pi weather station displaying current weather on Waveshare 2.13" e-Paper displays. Fetches data from Pirate Weather API, renders with Pillow, outputs to hardware or E-Paper-Emulator. Python >=3.10.

## Architecture

Two-file core:
- `weatherstation.py` — `WeatherStation` class, `display_weather()` rendering, main loop
- `display_config.py` — `DISPLAY_REGISTRY` mapping model names to specs, `load_display_module()` for dynamic import, `get_layout_config()` for resolution-based layout

Key patterns:
- **Display registry** — all supported models defined in `_DISPLAY_REGISTRY` dict with width, height, colors, features
- **Dynamic module loading** — hardware driver or emulator adapter loaded at runtime based on `USE_EMULATOR` env var
- **Two resolutions** — 104x212 and 122x250; layout auto-scales via `get_layout_config()`
- **Landscape orientation** — EPD width < height in portrait, but display renders rotated (e.g., 212x104 canvas for 104x212 display)
- **Icon fonts** — weather icons are font glyphs (`icons/weathericons.ttf` + `icons/icons.json`), not PNGs
- **Bi-color displays** — pass two image buffers (black + red) to `display()`; red used when current temp >= max temp

## Conventions

- **Config** — all via environment variables (see `.env.example`); `DISPLAY_MODEL` selects hardware
- **Testing** — `pytest`; hardware deps (`waveshare_epd`, `pirateweather`) are mocked since they need RPi hardware
- **Linting** — `pylint --fail-under=8` (excludes tests/), `flake8` (syntax errors fatal, style warnings non-fatal)
- **Dependencies** — pirateweather, Pillow, python-dotenv; hardware libs (spidev, lgpio, gpiozero) are Linux-only via platform markers in `pyproject.toml`
- **Git workflow** — always use feature branches, never commit directly to main

## Working with Code

### Dev setup
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

### Before committing
```bash
.venv/bin/python -m pytest tests/ -v
pylint --fail-under=8 $(find . -name "*.py" -not -path "./tests/*")
```

### Common tasks
- **Add display model** — add entry to `DISPLAY_REGISTRY` in `display_config.py`
- **Change layout** — modify `display_weather()` in `weatherstation.py`
- **Update icon mappings** — edit `icons/icons.json`

### Release process
1. Bump version in `pyproject.toml` (must match tag)
2. Merge version bump PR to main
3. Create annotated tag: `git tag -a v1.x.x -m "Release v1.x.x"` and push
4. GitHub Actions creates release automatically

## Common Pitfalls

- **Icon positioning** — use `getbbox()` not `getmetrics()` for precise padding; `getmetrics()` includes invisible font whitespace
- **Hardware mocking** — mock `waveshare_epd` and `pirateweather` *before* importing `weatherstation` in tests
- **Display dimensions** — canvas is landscape (width > height) even though EPD spec lists portrait dimensions
- **Bi-color buffer** — bi-color displays need two buffers passed to `display()`; monochrome displays use one
- **Font rendering** — differs between macOS (emulator) and Raspberry Pi; verify final layout on hardware
- **Test logging** — mock `log_message()` in tests that call `display_weather()` to avoid file permission errors
