# Manual Installation

Step-by-step guide for installing weatherstation-epaper without the automated installer.

## 1. Enable SPI Interface

```bash
sudo raspi-config
# Navigate to "Interfacing Options" → "SPI" and enable it
```

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
TMPDIR=$(mktemp -d)
git clone --depth 1 --filter=blob:none --sparse \
    https://github.com/waveshareteam/e-Paper.git "$TMPDIR/e-Paper"
git -C "$TMPDIR/e-Paper" sparse-checkout set RaspberryPi_JetsonNano/python
pipx inject weatherstation-epaper "$TMPDIR/e-Paper/RaspberryPi_JetsonNano/python/"
rm -rf "$TMPDIR"
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

```bash
cp .env.example .env
nano .env
```

At minimum, set your `PIRATE_WEATHER_API_KEY`. See [Configuration](../README.md#configuration) for all available options.

## 5. Set Up Log File

```bash
sudo touch /var/log/weatherstation.log
sudo chmod 666 /var/log/weatherstation.log
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
