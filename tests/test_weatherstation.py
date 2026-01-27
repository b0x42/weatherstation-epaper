import json
import os

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_icons_json_exists():
    icons_path = os.path.join(PROJECT_ROOT, "icons.json")
    assert os.path.exists(icons_path)


def test_icons_json_valid():
    icons_path = os.path.join(PROJECT_ROOT, "icons.json")
    with open(icons_path, "r") as f:
        icons = json.load(f)

    assert isinstance(icons, dict)
    assert "clear-day" in icons
    assert "rain" in icons


def test_weather_icons_directory_exists():
    icons_dir = os.path.join(PROJECT_ROOT, "weather-icons")
    assert os.path.isdir(icons_dir)


def test_env_example_exists():
    env_path = os.path.join(PROJECT_ROOT, ".env.example")
    assert os.path.exists(env_path)
