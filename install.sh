#!/usr/bin/env bash
set -e

# ─── Welcome ────────────────────────────────────────────────────────────────
echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   Weather Station e-Paper — Installer    ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""

# ─── Check platform ─────────────────────────────────────────────────────────
if [[ "$(uname)" != "Linux" ]]; then
    echo "Error: This installer is intended for Raspberry Pi OS (Linux)."
    echo "See the README for macOS/other development setup."
    exit 1
fi

# ─── Enable SPI ──────────────────────────────────────────────────────────────
echo "→ Checking SPI interface..."
if ls /dev/spi* &>/dev/null; then
    echo "  SPI is already enabled."
else
    echo "  Enabling SPI..."
    sudo raspi-config nonint do_spi 0
    echo "  SPI enabled."
fi

# ─── System dependencies ────────────────────────────────────────────────────
echo ""
echo "→ Installing system dependencies..."
sudo apt update
sudo apt install -y python3-pip python3-venv pipx git fonts-dejavu libjpeg-dev

# ─── Install weatherstation-epaper via pipx ──────────────────────────────────
echo ""
echo "→ Installing weatherstation-epaper..."
pipx install "git+https://github.com/benjaminburzan/weatherstation-epaper.git"

# ─── Install Waveshare e-Paper library (sparse checkout) ────────────────────
echo ""
echo "→ Installing Waveshare e-Paper library (sparse checkout)..."
TMPDIR=$(mktemp -d)
git clone --depth 1 --filter=blob:none --sparse \
    https://github.com/waveshareteam/e-Paper.git "$TMPDIR/e-Paper"
git -C "$TMPDIR/e-Paper" sparse-checkout set RaspberryPi_JetsonNano/python
pipx inject weatherstation-epaper "$TMPDIR/e-Paper/RaspberryPi_JetsonNano/python/"
rm -rf "$TMPDIR"

# ─── Configure .env ─────────────────────────────────────────────────────────
echo ""
echo "→ Configuring environment..."

PIRATE_WEATHER_API_KEY=""
while [[ -z "$PIRATE_WEATHER_API_KEY" ]]; do
    read -rp "  Pirate Weather API key (required): " PIRATE_WEATHER_API_KEY
    if [[ -z "$PIRATE_WEATHER_API_KEY" ]]; then
        echo "  API key cannot be empty. Get one free at https://pirate-weather.apiable.io"
    fi
done

read -rp "  Latitude  [52.5200]: " LATITUDE
LATITUDE="${LATITUDE:-52.5200}"

read -rp "  Longitude [13.4050]: " LONGITUDE
LONGITUDE="${LONGITUDE:-13.4050}"

read -rp "  Display model [epd2in13bc]: " DISPLAY_MODEL
DISPLAY_MODEL="${DISPLAY_MODEL:-epd2in13bc}"

cat > "$HOME/.env" <<EOF
PIRATE_WEATHER_API_KEY=$PIRATE_WEATHER_API_KEY
LATITUDE=$LATITUDE
LONGITUDE=$LONGITUDE
DISPLAY_MODEL=$DISPLAY_MODEL
LANGUAGE=de
UNITS=si
FLIP_DISPLAY=false
UPDATE_INTERVAL_SECONDS=1800
EOF
chmod 600 "$HOME/.env"
echo "  Configuration saved to ~/.env"

# ─── Log file ───────────────────────────────────────────────────────────────
echo ""
echo "→ Setting up log file..."
sudo touch /var/log/weatherstation.log
sudo chmod 666 /var/log/weatherstation.log

# ─── Systemd service (optional) ─────────────────────────────────────────────
echo ""
read -rp "→ Start weatherstation automatically on boot? [Y/n] " INSTALL_SERVICE
INSTALL_SERVICE="${INSTALL_SERVICE:-Y}"

if [[ "$INSTALL_SERVICE" =~ ^[Yy]$ ]]; then
    echo "  Installing systemd service..."
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
    echo "  Service installed and started."
fi

# ─── Done ────────────────────────────────────────────────────────────────────
echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║         Installation complete!           ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""
echo "  Configuration:  ~/.env"
echo "  Logs:           /var/log/weatherstation.log"
echo "  Run manually:   weatherstation"
echo ""
if [[ "$INSTALL_SERVICE" =~ ^[Yy]$ ]]; then
    echo "  Service status:   sudo systemctl status weatherstation"
    echo "  View logs:        tail -f /var/log/weatherstation.log"
    echo "  Restart service:  sudo systemctl restart weatherstation"
else
    echo "  To start on boot later, re-run the installer or see the README."
fi
echo ""
