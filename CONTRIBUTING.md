# Contributing

Contributions are welcome — whether it's adding display model support, fixing bugs, or improving features. This guide walks you through the process.

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/weatherstation-epaper.git
   cd weatherstation-epaper
   ```
3. **Install** development dependencies:
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -e ".[dev]"
   ```
4. **Create** a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Making Changes

- Implement changes within your feature branch
- If modifying display logic, test with the emulator (`USE_EMULATOR=true python weatherstation.py`)
- Run the test suite:
  ```bash
  python -m pytest tests/ -v
  ```
- Run linting checks:
  ```bash
  flake8 weatherstation.py display_config.py emulator_adapter.py
  pylint --fail-under=8 weatherstation.py display_config.py emulator_adapter.py
  ```

### Pull Request Requirements

Before submitting, ensure:

- Clear description explaining what changed and why
- One feature or fix per PR
- All tests pass
- No linting errors (`flake8`) and pylint score >= 8.0
- Code follows existing patterns in `weatherstation.py` and `display_config.py`
- API compatibility maintained with Waveshare's Python EPD library

## Adding New Display Models

To support an additional Waveshare 2.13" display:

1. Add an entry to `DISPLAY_REGISTRY` in `display_config.py` with the model's width, height, color support, and features
2. Use exact resolutions from the official Waveshare datasheet
3. Name the key to match the Waveshare module identifier (e.g., `epd2in13_V4`)
4. Verify the layout works for the model's resolution via `get_layout_config()`
5. Update the supported displays table in `README.md`
6. Add corresponding test cases in `tests/test_display_config.py`

## Code Style

- Follow existing architectural patterns
- Use Pillow for all image operations
- Use icon fonts (`icons/icons.json` + `icons/weathericons.ttf`) for weather icons — not image files
- Keep canvas rendering in landscape orientation (width > height)
- For bi-color displays, pass separate black and red image buffers to `display()`
- Max line length: 127 characters

## Questions and Discussions

For non-bug questions or feature ideas, open a [GitHub Discussion](https://github.com/benjaminburzan/weatherstation-epaper/discussions) rather than filing an issue.
