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

## Development Notes
- Hardware libraries are mocked in tests - see `tests/test_weatherstation.py`
- Display uses landscape orientation (212x104 pixels)
- Supports tri-color: black, white, and red (red used when current temp >= max temp)
- All config via environment variables (see `.env.example`)
- Weather icons use font glyphs, not PNG files

## Common Tasks
- Update icon mappings: Edit `icons.json`
- Change display layout: Modify `display_weather()` in `weatherstation.py`
- Add new config options: Add to environment variables section at top of `weatherstation.py`
