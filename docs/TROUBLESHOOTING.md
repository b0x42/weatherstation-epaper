# Troubleshooting

## Display not updating

1. Check SPI is enabled: `ls /dev/spi*`
2. Verify wiring connections
3. Check logs: `tail -f /var/log/weatherstation.log`

## API errors

1. Verify your API key: `echo $PIRATE_WEATHER_API_KEY`
2. Check internet: `ping pirateweather.net`
3. Ensure coordinates are valid decimal numbers

## Service not starting

1. Check status: `sudo systemctl status weatherstation`
2. Verify paths in service file match your installation
3. Ensure `.env` file exists with valid API key

## Permission errors

```bash
sudo touch /var/log/weatherstation.log
sudo chmod 666 /var/log/weatherstation.log
```

## Display hangs or infinite busy wait (Pi Zero)

If the display appears stuck with no updates and logs show it hanging at "Displaying weather on e-Paper display...", the Waveshare driver is waiting indefinitely for the BUSY pin.

> **Note:** As of `waveshare-epaper>=1.4.0`, the PyPI package is synchronized with the upstream GitHub repository. The GitHub clone method below may not be necessary unless you need unreleased patches or the PyPI package falls behind again. Try the latest PyPI version first before resorting to the manual GitHub installation.

### Symptoms

- Logs show: `[timestamp] Displaying weather on e-Paper display...` with no completion message
- `weatherstation` process uses constant CPU (20-40%)
- Display never updates
- Service appears running but is stuck
- Issue occurs with both PyPI `waveshare-epaper` and GitHub `waveshare-epd` packages

### Root Cause

The Waveshare display driver's `ReadBusy()` function contains an infinite while loop with no timeout:

```python
def ReadBusy(self):
    logger.debug("e-Paper busy")
    while(epdconfig.digital_read(self.busy_pin) == 0):  # 0: idle, 1: busy
        epdconfig.delay_ms(100)
    logger.debug("e-Paper busy release")
```

On Raspberry Pi Zero, the Driver HAT's power management circuit can cause the display controller to lose power during reset. The Pi Zero's slow CPU stretches what should be a 2-5ms reset pulse to 15ms+, crossing a threshold that triggers the HAT to cut power entirely. The BUSY pin then floats LOW forever, causing an infinite loop.

### Quick Fix

```bash
curl -fsSL https://raw.githubusercontent.com/benjaminburzan/weatherstation-epaper/main/fix-pi-zero-readbusy.sh | bash
sudo systemctl restart weatherstation
```

This installs the upstream GitHub driver (which includes PWR_PIN support), creates a compatibility wrapper, and patches ReadBusy with a 10-second timeout.

**Note:** The fix must be reapplied after `pipx upgrade weatherstation-epaper`.

### Manual Fix

The fix involves three components:

1. **Use GitHub waveshare-epd driver** (provides access to source code for patching)
2. **Create compatibility wrapper** (allows existing code to work with waveshare_epd)
3. **Patch ReadBusy with timeout** (bypass the infinite wait)

#### 1. Locate Your pipx Virtual Environment

```bash
VENV_PATH="$HOME/.local/share/pipx/venvs/weatherstation-epaper"
PYTHON_VERSION=$(ls "$VENV_PATH/lib/" | grep python)
SITE_PACKAGES="$VENV_PATH/lib/$PYTHON_VERSION/site-packages"
echo "Site packages: $SITE_PACKAGES"
```

#### 2. Remove PyPI Package and Install GitHub Driver

```bash
# Remove PyPI waveshare-epaper if installed
pipx runpip weatherstation-epaper uninstall -y waveshare-epaper

# Clone and install GitHub version
CLONE_DIR=$(mktemp -d)
git clone --depth 1 --filter=blob:none --sparse \
    https://github.com/waveshareteam/e-Paper.git "$CLONE_DIR/e-Paper"
git -C "$CLONE_DIR/e-Paper" sparse-checkout set RaspberryPi_JetsonNano/python
pipx inject --force weatherstation-epaper "$CLONE_DIR/e-Paper/RaspberryPi_JetsonNano/python/"
rm -rf "$CLONE_DIR"
```

#### 3. Create Compatibility Wrapper

The weatherstation code expects to `import epaper` but the GitHub package provides `waveshare_epd`. Create a wrapper:

```bash
cat > "$SITE_PACKAGES/epaper.py" << 'EOF'
"""
Compatibility wrapper to make waveshare_epd work with code expecting epaper module
"""
import importlib

def epaper(model_name):
    """Load the appropriate display module from waveshare_epd"""
    class EPDWrapper:
        def __init__(self):
            # Import the specific display module from waveshare_epd
            module = importlib.import_module(f"waveshare_epd.{model_name}")
            self.EPD = getattr(module, "EPD")

    return EPDWrapper()
EOF
```

#### 4. Patch ReadBusy Function

```bash
python3 << PYEOF
driver_path = "$SITE_PACKAGES/waveshare_epd/$DISPLAY_MODEL.py"
with open(driver_path, "r") as f:
    content = f.read()

old = """    def ReadBusy(self):
        logger.debug("e-Paper busy")
        while(epdconfig.digital_read(self.busy_pin) == 0):      # 0: idle, 1: busy
            epdconfig.delay_ms(100)
        logger.debug("e-Paper busy release")"""

new = """    def ReadBusy(self):
        logger.debug("e-Paper busy")
        timeout = 100  # 10 seconds timeout (100 * 100ms)
        count = 0
        while(epdconfig.digital_read(self.busy_pin) == 0):      # 0: idle, 1: busy
            epdconfig.delay_ms(100)
            count += 1
            if count > timeout:
                logger.warning("e-Paper busy timeout - proceeding anyway")
                break
        logger.debug("e-Paper busy release")"""

content = content.replace(old, new)
with open(driver_path, "w") as f:
    f.write(content)
print("Patched successfully!")
PYEOF
```

**Important:** Set `DISPLAY_MODEL` to match your display (e.g., `epd2in13bc`, `epd2in13d`, `epd2in13_V4`).

#### 5. Clear Python Cache and Restart

```bash
# Clear bytecode cache
rm -rf "$SITE_PACKAGES/waveshare_epd/__pycache__"

# Restart service
sudo systemctl restart weatherstation
```

### Verification

Check logs to confirm it's working:

```bash
tail -f /var/log/weatherstation.log
```

**Expected output:**
```
[timestamp] Weather Station started.
[timestamp] Fetching weather data...
[timestamp] Weather data: X° / Y°, Description. Icon: icon_name
[timestamp] Displaying weather on e-Paper display...
e-Paper busy timeout - proceeding anyway
e-Paper busy timeout - proceeding anyway
[timestamp] Display updated successfully.
[timestamp] Waiting 30 minutes until next update...
```

The "e-Paper busy timeout" warnings are **normal and expected** for this hardware.

### Adjusting Timeout

If you get multiple timeout warnings or display corruption, you can adjust the timeout:

```python
timeout = 100  # 10 seconds (current)
timeout = 150  # 15 seconds (more conservative)
timeout = 50   # 5 seconds (more aggressive)
```

Edit the patched file and change the timeout value, then restart the service.

### Known Limitations

1. **Timeout warnings in logs** - Normal behavior, not errors
2. **Display model specific** - Patch must be reapplied if switching display models
3. **Survives service restart** - But NOT pipx upgrades (patch gets overwritten)
4. **Hardware specific** - Only needed on Pi Zero with affected display batches

### Related Issues

- Affects: Raspberry Pi Zero W with certain 2.13" e-Paper display batches
- Does not affect: Pi 3, Pi 4, Pi 5 (usually)
- Waveshare GitHub: https://github.com/waveshareteam/e-Paper
