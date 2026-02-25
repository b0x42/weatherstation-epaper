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
- [Uninstall](#uninstall)

## 1. Enable SPI Interface

```bash
sudo raspi-config
# Navigate to "Interfacing Options" → "SPI" and enable it
```

> **DietPi users:** If `raspi-config` is not available, use `sudo dietpi-config` instead.

## 2. Install System Dependencies

```bash
sudo apt install python3-pip python3-dev python3-venv pipx git fonts-dejavu build-essential libjpeg-dev libfreetype-dev zlib1g-dev python3-rpi-lgpio
```

## 3. Install Weather Station

### Option A: pipx

```bash
pipx install "git+https://github.com/b0x42/weatherstation-epaper.git"
```

### Option B: venv

```bash
cd ~
git clone https://github.com/b0x42/weatherstation-epaper.git
cd weatherstation-epaper
python3 -m venv venv
source venv/bin/activate
pip install .
```

## 4. Configure Environment Variables

### Option A (pipx)

Create `~/.env` manually:

```bash
cat > ~/.env <<EOF
# Configuration docs: https://github.com/b0x42/weatherstation-epaper#configuration
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

## Uninstall

### 1. Stop and remove the service

```bash
sudo systemctl stop weatherstation
sudo systemctl disable weatherstation
sudo rm /etc/systemd/system/weatherstation.service
sudo systemctl daemon-reload
```

### 2. Remove the application

**pipx:**

```bash
pipx uninstall weatherstation-epaper
```

**venv:**

```bash
rm -rf ~/weatherstation-epaper
```

### 3. Remove configuration and logs

```bash
rm ~/.env
sudo rm /var/log/weatherstation.log
```
