# Pi Zero ReadBusy Hang Fix

## Problem Description

On Raspberry Pi Zero hardware, the weatherstation display update hangs indefinitely at "Displaying weather on e-Paper display..." and never completes. The process consumes 20-40% CPU in a busy-wait loop.

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

On certain hardware (specifically Pi Zero with certain display batches), the BUSY pin never signals completion, causing an infinite loop. This is a known hardware quirk where the busy pin state doesn't match expected behavior.

## Solution

The fix involves three components:

1. **Use GitHub waveshare-epd driver** (provides access to source code for patching)
2. **Create compatibility wrapper** (allows existing code to work with waveshare_epd)
3. **Patch ReadBusy with timeout** (bypass the infinite wait)

## Implementation Steps

### 1. Remove PyPI Package and Install GitHub Driver

```bash
# Remove PyPI waveshare-epaper if installed
pipx runpip weatherstation-epaper uninstall -y waveshare-epaper

# Clone and install GitHub version
CLONE_DIR=$(mktemp -d)
git clone --depth 1 --filter=blob:none --sparse --quiet \
    https://github.com/waveshareteam/e-Paper.git "$CLONE_DIR/e-Paper"
git -C "$CLONE_DIR/e-Paper" sparse-checkout set --quiet RaspberryPi_JetsonNano/python
pipx inject --force weatherstation-epaper "$CLONE_DIR/e-Paper/RaspberryPi_JetsonNano/python/"
rm -rf "$CLONE_DIR"
```

### 2. Create Compatibility Wrapper

The weatherstation code expects to `import epaper` but the GitHub package provides `waveshare_epd`. Create a wrapper:

```bash
cat > ~/.local/pipx/venvs/weatherstation-epaper/lib/python3.11/site-packages/epaper.py << 'EOF'
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

**Note:** Adjust the path if using a different Python version (check with `ls ~/.local/pipx/venvs/weatherstation-epaper/lib/`).

### 3. Patch ReadBusy Function

Create and run this patch script:

```bash
cat > /tmp/patch_readbusy.py << 'EOF'
import re

# Path to the display driver (adjust for your display model)
DRIVER_PATH = "/root/.local/pipx/venvs/weatherstation-epaper/lib/python3.11/site-packages/waveshare_epd/epd2in13bc.py"

# Read the file
with open(DRIVER_PATH, "r") as f:
    content = f.read()

# Replace the ReadBusy function
old_readbusy = """    def ReadBusy(self):
        logger.debug("e-Paper busy")
        while(epdconfig.digital_read(self.busy_pin) == 0):      # 0: idle, 1: busy
            epdconfig.delay_ms(100)
        logger.debug("e-Paper busy release")"""

new_readbusy = """    def ReadBusy(self):
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

content = content.replace(old_readbusy, new_readbusy)

# Write back
with open(DRIVER_PATH, "w") as f:
    f.write(content)

print("Patched successfully!")
EOF

python3 /tmp/patch_readbusy.py
```

**Important:** Change `epd2in13bc.py` to match your display model:
- `epd2in13bc.py` - 2.13" bi-color (B/R)
- `epd2in13d.py` - 2.13" monochrome (D)
- `epd2in13_V4.py` - 2.13" V4 monochrome
- etc.

### 4. Clear Python Cache and Restart

```bash
# Clear bytecode cache
rm -rf ~/.local/pipx/venvs/weatherstation-epaper/lib/python3.11/site-packages/waveshare_epd/__pycache__

# Restart service
sudo systemctl restart weatherstation
```

## Verification

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

The "e-Paper busy timeout" warnings are **normal and expected** for this hardware. They indicate the patch is working correctly.

## Why This Works

1. **Timeout prevents infinite loop** - After 10 seconds (configurable), the code proceeds anyway
2. **Display still updates** - Despite the busy pin not signaling, the display controller has usually finished by the timeout
3. **Service remains stable** - The update cycle completes and waits for the next interval

## Adjusting Timeout

If you get multiple timeout warnings or display corruption, you can adjust the timeout:

```python
timeout = 100  # 10 seconds (current)
timeout = 150  # 15 seconds (more conservative)
timeout = 50   # 5 seconds (more aggressive)
```

Edit the patched file and change the timeout value, then restart the service.

## Alternative: Automated Patch Script

For easier deployment, you can create a post-install script:

```bash
#!/usr/bin/env bash
# fix-pi-zero-readbusy.sh

VENV_PATH="$HOME/.local/pipx/venvs/weatherstation-epaper"
PYTHON_VERSION=$(ls "$VENV_PATH/lib/" | grep python)
SITE_PACKAGES="$VENV_PATH/lib/$PYTHON_VERSION/site-packages"

# Detect display model from .env
DISPLAY_MODEL=$(grep DISPLAY_MODEL ~/.env | cut -d= -f2 | tr -d '"')

echo "Applying Pi Zero ReadBusy fix for $DISPLAY_MODEL..."

# Install GitHub driver
CLONE_DIR=$(mktemp -d)
git clone --depth 1 --filter=blob:none --sparse --quiet \
    https://github.com/waveshareteam/e-Paper.git "$CLONE_DIR/e-Paper"
git -C "$CLONE_DIR/e-Paper" sparse-checkout set --quiet RaspberryPi_JetsonNano/python
pipx inject --force weatherstation-epaper "$CLONE_DIR/e-Paper/RaspberryPi_JetsonNano/python/"
rm -rf "$CLONE_DIR"

# Create compatibility wrapper
cat > "$SITE_PACKAGES/epaper.py" << 'EOF'
import importlib
def epaper(model_name):
    class EPDWrapper:
        def __init__(self):
            module = importlib.import_module(f"waveshare_epd.{model_name}")
            self.EPD = getattr(module, "EPD")
    return EPDWrapper()
EOF

# Patch ReadBusy
python3 << EOF
import re
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
        timeout = 100
        count = 0
        while(epdconfig.digital_read(self.busy_pin) == 0):
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
EOF

# Clear cache
rm -rf "$SITE_PACKAGES/waveshare_epd/__pycache__"

echo "Fix applied! Restart the service with: sudo systemctl restart weatherstation"
```

## Known Limitations

1. **Timeout warnings in logs** - Normal behavior, not errors
2. **Display model specific** - Patch must be reapplied if switching display models
3. **Survives service restart** - But NOT pipx upgrades (patch gets overwritten)
4. **Hardware specific** - Only needed on Pi Zero with affected display batches

## When Updates Overwrite the Fix

After running `pipx upgrade weatherstation-epaper`, you'll need to reapply steps 2-4 (the GitHub driver install happens automatically now via pyproject.toml on some platforms, but the compatibility wrapper and patch need manual reapplication).

## Why Not Fix This Upstream?

This fix is hardware-specific to certain Pi Zero + display combinations. The upstream Waveshare library is designed to work across many hardware configurations, and adding a timeout might mask other legitimate issues. This is a workaround for a specific hardware quirk rather than a general solution.

## Related Issues

- Original issue: Driver version mismatches and ReadBusy timeout
- Affects: Raspberry Pi Zero W with certain 2.13" e-Paper display batches
- Does not affect: Pi 3, Pi 4, Pi 5 (usually)
- Waveshare GitHub: https://github.com/waveshareteam/e-Paper

## Testing

To verify the fix works without waiting 30 minutes:

```bash
# Stop the service
sudo systemctl stop weatherstation

# Run manually
weatherstation

# Watch for timeout messages and successful completion
```

Expected completion time: 30-60 seconds (including timeouts).
