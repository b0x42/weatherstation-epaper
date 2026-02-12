#!/usr/bin/env bash
set -euo pipefail

# ─── Welcome ────────────────────────────────────────────────────────────────
echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   Weather Station e-Paper — Installer    ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""
echo "  Raspberry Pi weather station with Waveshare 2.13\""
echo "  bi-color and monochrome e-Paper display"
echo ""
echo "  https://github.com/benjaminburzan/weatherstation-epaper"
echo ""

# ─── Check platform ─────────────────────────────────────────────────────────
if [[ "$(uname)" != "Linux" ]]; then
    echo "  This installer is designed for Raspberry Pi OS or DietPi (Linux)."
    echo "  For macOS or other systems, see the README for development setup."
    exit 1
fi

# ─── Detect existing installation ───────────────────────────────────────────
IS_UPDATE=false
INSTALL_SERVICE=""
if pipx list 2>/dev/null | grep -q weatherstation-epaper; then
    IS_UPDATE=true
    echo "  An existing installation was found."
    echo "  The installer will update it and keep your configuration."
    echo ""
fi

# ─── Enable SPI ──────────────────────────────────────────────────────────────
echo "───────────────────────────────────────────────"
echo ""
echo "[1/6] SPI interface"
echo ""
if ls /dev/spi* &>/dev/null; then
    echo "  SPI is already enabled. Nothing to do."
else
    echo "  SPI is required for the e-Paper display to communicate"
    echo "  with your Raspberry Pi. Enabling it now..."
    echo ""
    if command -v raspi-config &>/dev/null; then
        sudo raspi-config nonint do_spi 0
        echo "  SPI has been enabled successfully."
    else
        echo "  WARNING: raspi-config not found. Please enable SPI manually."
        echo "  On DietPi, use: sudo dietpi-config"
    fi
fi

# ─── System dependencies ────────────────────────────────────────────────────
echo ""
echo "───────────────────────────────────────────────"
echo ""
echo "[2/6] System dependencies"
echo ""
REQUIRED_PKGS=(python3-pip python3-venv pipx git fonts-dejavu libjpeg-dev)
MISSING_PKGS=()
for pkg in "${REQUIRED_PKGS[@]}"; do
    if ! dpkg -s "$pkg" &>/dev/null; then
        MISSING_PKGS+=("$pkg")
    fi
done

if [[ ${#MISSING_PKGS[@]} -eq 0 ]]; then
    echo "  All required packages are already installed."
else
    echo "  Installing missing packages: ${MISSING_PKGS[*]}"
    echo ""
    sudo apt update
    sudo apt install -y "${MISSING_PKGS[@]}"
fi
echo ""
echo "  System dependencies are ready."

# ─── Install or update weatherstation-epaper via pipx ────────────────────────
echo ""
echo "───────────────────────────────────────────────"
echo ""
echo "[3/6] Weather station application"
echo ""
if [[ "$IS_UPDATE" == true ]]; then
    echo "  Upgrading weatherstation-epaper to the latest version..."
    echo ""
    pipx upgrade weatherstation-epaper
else
    echo "  Installing weatherstation-epaper via pipx..."
    echo "  This downloads and sets up the application in an isolated environment."
    echo "  This can take a while (up to 20 minutes on slower devices like the Pi Zero)."
    echo ""
    pipx install "git+https://github.com/benjaminburzan/weatherstation-epaper.git"
fi
echo ""
echo "  Weather station application is ready."

# ─── Install Waveshare e-Paper library (sparse checkout) ────────────────────
echo ""
echo "───────────────────────────────────────────────"
echo ""
echo "[4/6] Waveshare e-Paper display driver"
echo ""
echo "  Downloading the Waveshare e-Paper library..."
echo "  (Using sparse checkout to save time and bandwidth.)"
echo ""
CLONE_DIR=$(mktemp -d)
trap 'rm -rf "$CLONE_DIR"' EXIT
git clone --depth 1 --filter=blob:none --sparse \
    https://github.com/waveshareteam/e-Paper.git "$CLONE_DIR/e-Paper"
git -C "$CLONE_DIR/e-Paper" sparse-checkout set RaspberryPi_JetsonNano/python
pipx inject --force weatherstation-epaper "$CLONE_DIR/e-Paper/RaspberryPi_JetsonNano/python/"
rm -rf "$CLONE_DIR"
trap - EXIT
echo ""
echo "  Display driver installed."

# ─── Configure .env ─────────────────────────────────────────────────────────
echo ""
echo "───────────────────────────────────────────────"
echo ""
echo "[5/6] Configuration"
echo ""
if [[ -d "$HOME/.env" ]]; then
    echo "  ERROR: $HOME/.env exists but is a directory."
    echo "  Please remove or rename it, then re-run the installer:"
    echo ""
    echo "    rm -rf ~/.env"
    echo ""
    exit 1
elif [[ -f "$HOME/.env" ]]; then
    echo "  Your configuration file (~/.env) already exists."
    echo "  Keeping your current settings. You can edit them later with:"
    echo ""
    echo "    nano ~/.env"
else
    echo "  Let's set up your weather station. You'll need a free API key"
    echo "  from Pirate Weather: https://pirate-weather.apiable.io"
    echo ""
    echo "  Press Enter to accept the default value shown in [brackets]."
    echo ""

    PIRATE_WEATHER_API_KEY=""
    while [[ -z "$PIRATE_WEATHER_API_KEY" ]]; do
        read -rp "  Pirate Weather API key (required): " PIRATE_WEATHER_API_KEY </dev/tty
        if [[ -z "$PIRATE_WEATHER_API_KEY" ]]; then
            echo ""
            echo "  The API key is required for fetching weather data."
            echo "  Sign up for free at: https://pirate-weather.apiable.io"
            echo ""
        fi
    done

    echo ""
    echo "  Set your location (latitude/longitude). The default is Berlin, Germany."
    echo "  Tip: Find your coordinates at https://latlong.net"
    echo ""

    read -rp "  Latitude  [52.5200]: " LATITUDE </dev/tty
    LATITUDE="${LATITUDE:-52.5200}"
    if ! [[ "$LATITUDE" =~ ^-?[0-9]+\.?[0-9]*$ ]]; then
        echo "  Invalid latitude. Please enter a number (e.g. 52.5200)."
        exit 1
    fi

    read -rp "  Longitude [13.4050]: " LONGITUDE </dev/tty
    LONGITUDE="${LONGITUDE:-13.4050}"
    if ! [[ "$LONGITUDE" =~ ^-?[0-9]+\.?[0-9]*$ ]]; then
        echo "  Invalid longitude. Please enter a number (e.g. 13.4050)."
        exit 1
    fi

    echo ""
    echo "  Which Waveshare 2.13\" display model do you have?"
    echo "  Common models: epd2in13bc (bi-color), epd2in13_V4, epd2in13b_V4"
    echo "  See the full list in the README."
    echo ""

    read -rp "  Display model [epd2in13bc]: " DISPLAY_MODEL </dev/tty
    DISPLAY_MODEL="${DISPLAY_MODEL:-epd2in13bc}"

    echo ""
    echo "  Units for temperature and wind speed:"
    echo "    si = Celsius, m/s    us = Fahrenheit, mph"
    echo "    ca = Celsius, km/h   uk = Celsius, mph"
    echo ""

    read -rp "  Units [si]: " UNITS </dev/tty
    UNITS="${UNITS:-si}"

    echo ""
    echo "  Language for weather descriptions (e.g. en, de, fr, es, it, nl, pl)."
    echo ""

    read -rp "  Language [de]: " LANGUAGE </dev/tty
    LANGUAGE="${LANGUAGE:-de}"

    cat > "$HOME/.env" <<EOF
# Configuration docs: https://github.com/benjaminburzan/weatherstation-epaper#configuration
#
PIRATE_WEATHER_API_KEY="$PIRATE_WEATHER_API_KEY"
LATITUDE="$LATITUDE"
LONGITUDE="$LONGITUDE"
DISPLAY_MODEL="$DISPLAY_MODEL"
LANGUAGE="$LANGUAGE"
UNITS="$UNITS"
FLIP_DISPLAY="false"
UPDATE_INTERVAL_SECONDS="1800"
EOF
    chmod 600 "$HOME/.env"
    echo ""
    echo "  Configuration saved to ~/.env"
    echo "  You can change these settings anytime by editing that file."
fi

# ─── Log file ───────────────────────────────────────────────────────────────
echo ""
echo "───────────────────────────────────────────────"
echo ""
echo "[6/6] Finishing up"
echo ""
echo "  Setting up log file at /var/log/weatherstation.log..."
sudo touch /var/log/weatherstation.log
sudo chown "$(whoami):$(whoami)" /var/log/weatherstation.log
chmod 644 /var/log/weatherstation.log

# ─── Systemd service ────────────────────────────────────────────────────────
if [[ "$IS_UPDATE" == true ]] && systemctl is-enabled --quiet weatherstation 2>/dev/null; then
    echo ""
    if systemctl is-active --quiet weatherstation 2>/dev/null; then
        echo "  Restarting the weatherstation service to apply the update..."
        sudo systemctl restart weatherstation
        echo "  Service restarted successfully."
    else
        echo "  Starting the weatherstation service..."
        sudo systemctl start weatherstation
        echo "  Service started."
    fi
    INSTALL_SERVICE="Y"
else
    echo ""
    echo "  Would you like the weather station to start automatically"
    echo "  whenever your Raspberry Pi boots up? (Recommended)"
    echo ""
    read -rp "  Start on boot? [Y/n] " INSTALL_SERVICE </dev/tty
    INSTALL_SERVICE="${INSTALL_SERVICE:-Y}"

    if [[ "$INSTALL_SERVICE" =~ ^[Yy] ]]; then
        echo ""
        echo "  Setting up the systemd service..."
        CURRENT_USER=$(whoami)
        sudo tee /etc/systemd/system/weatherstation.service >/dev/null <<EOF
[Unit]
Description=Weather Station e-Paper Display
After=network.target

[Service]
EnvironmentFile=$HOME/.env
ExecStart=$HOME/.local/bin/weatherstation
StandardOutput=append:/var/log/weatherstation.log
StandardError=append:/var/log/weatherstation.log
Restart=always
User=$CURRENT_USER
Type=idle
ExecStartPre=/bin/sleep 5

[Install]
WantedBy=multi-user.target
EOF
        sudo systemctl daemon-reload
        sudo systemctl enable weatherstation
        sudo systemctl start weatherstation
        echo "  Service installed and started. It will run on every boot."
    else
        echo ""
        echo "  No problem! You can always set this up later by re-running"
        echo "  the installer or following the instructions in the README."
    fi
fi

# ─── Done ────────────────────────────────────────────────────────────────────
echo ""
echo "───────────────────────────────────────────────"
echo ""
if [[ "$IS_UPDATE" == true ]]; then
    echo "  ╔══════════════════════════════════════════╗"
    echo "  ║           Update complete!               ║"
    echo "  ╚══════════════════════════════════════════╝"
else
    echo "  ╔══════════════════════════════════════════╗"
    echo "  ║         Installation complete!           ║"
    echo "  ╚══════════════════════════════════════════╝"
    echo ""
    echo "  Installed to:"
    echo ""
    echo "    Application   $(which weatherstation)"
    echo "    Config        ~/.env"
    if [[ "$INSTALL_SERVICE" =~ ^[Yy] ]]; then
        echo "    Service       /etc/systemd/system/weatherstation.service"
    fi
fi
echo ""
echo "  Useful commands:"
echo ""
echo "    weatherstation              Run manually"
echo "    nano ~/.env                 Edit configuration"
echo "    tail -f /var/log/weatherstation.log"
echo "                                View live logs"
if [[ "$INSTALL_SERVICE" =~ ^[Yy] ]]; then
    echo ""
    echo "  Service commands:"
    echo ""
    echo "    sudo systemctl status weatherstation"
    echo "                                Check if it's running"
    echo "    sudo systemctl restart weatherstation"
    echo "                                Restart after config changes"
fi
echo ""
