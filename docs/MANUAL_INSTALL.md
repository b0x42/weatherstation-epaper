# Manual Installation

Step-by-step guide for installing weatherstation-epaper without the automated installer.

## Table of Contents

- [1. Enable SPI Interface](#1-enable-spi-interface)
- [2. Install System Dependencies](#2-install-system-dependencies)
- [3. Install Weather Station](#3-install-weather-station)
- [4. Configure Environment Variables](#4-configure-environment-variables)
- [5. Set Up Log File](#5-set-up-log-file)
- [6. Run as System Service (optional)](#6-run-as-system-service-optional)
- [Update](#update)

## 1. Enable SPI Interface

```bash
sudo raspi-config
# Navigate to "Interfacing Options" → "SPI" and enable it
```

> **DietPi users:** If `raspi-config` is not available, use `sudo dietpi-config` instead.

## 2. Install System Dependencies

```bash
sudo apt install python3-pip python3-venv pipx git fonts-dejavu libjpeg-dev
```

## 3. Install Weather Station

### Option A: pipx

```bash
pipx install "git+https://github.com/benjaminburzan/weatherstation-epaper.git"
```

Install the Waveshare e-Paper library using sparse checkout (required for Pi Zero due to repo size):

```bash
CLONE_DIR=$(mktemp -d)
git clone --depth 1 --filter=blob:none --sparse \
    https://github.com/waveshareteam/e-Paper.git "$CLONE_DIR/e-Paper"
git -C "$CLONE_DIR/e-Paper" sparse-checkout set RaspberryPi_JetsonNano/python
pipx inject weatherstation-epaper "$CLONE_DIR/e-Paper/RaspberryPi_JetsonNano/python/"
rm -rf "$CLONE_DIR"
```

### Option B: venv

```bash
cd ~
git clone https://github.com/benjaminburzan/weatherstation-epaper.git
cd weatherstation-epaper
python3 -m venv venv
source venv/bin/activate
pip install .
pip install "git+https://github.com/waveshareteam/e-Paper.git#subdirectory=RaspberryPi_JetsonNano/python"
```

## 4. Configure Environment Variables

### Option A (pipx)

Create `~/.env` manually:

```bash
cat > ~/.env <<EOF
# Configuration docs: https://github.com/benjaminburzan/weatherstation-epaper#configuration
#
PIRATE_WEATHER_API_KEY=your_api_key_here
LATITUDE=52.5200
LONGITUDE=13.4050
DISPLAY_MODEL=epd2in13bc
LANGUAGE=de
UNITS=si
FLIP_DISPLAY=false
UPDATE_INTERVAL_SECONDS=1800
EOF
chmod 600 ~/.env
```

### Option B (venv)

```bash
cp .env.example .env
nano .env
```

At minimum, set your `PIRATE_WEATHER_API_KEY`. See [Configuration](../README.md#configuration) for all available options.

## 5. Set Up Log File

```bash
sudo touch /var/log/weatherstation.log
sudo chown "$(whoami):$(whoami)" /var/log/weatherstation.log
chmod 644 /var/log/weatherstation.log
```

## 6. Run as System Service (optional)

See [Usage](../README.md#usage) in the README for systemd setup instructions.

## Update

### pipx

```bash
pipx upgrade weatherstation-epaper
```

### venv

```bash
cd ~/weatherstation-epaper
source venv/bin/activate
git pull
pip install .
```
