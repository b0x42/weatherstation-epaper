#!/usr/bin/env bash
# fix-pi-zero-readbusy.sh
# Patches the Waveshare e-Paper driver with a ReadBusy timeout for Pi Zero hardware.
set -e

VENV_PATH="$HOME/.local/share/pipx/venvs/weatherstation-epaper"
if [ ! -d "$VENV_PATH/lib" ]; then
    echo "ERROR: pipx venv not found at $VENV_PATH"
    echo "Is weatherstation-epaper installed via pipx?"
    exit 1
fi

PYTHON_VERSION=$(ls "$VENV_PATH/lib/" | grep python | head -1)
SITE_PACKAGES="$VENV_PATH/lib/$PYTHON_VERSION/site-packages"

# Detect display model from .env
DISPLAY_MODEL=$(grep DISPLAY_MODEL ~/.env 2>/dev/null | cut -d= -f2 | tr -d '"' || true)
if [ -z "$DISPLAY_MODEL" ]; then
    DISPLAY_MODEL="epd2in13bc"
    echo "No DISPLAY_MODEL in ~/.env, defaulting to $DISPLAY_MODEL"
fi

echo "Pi Zero ReadBusy Fix"
echo "  Venv: $VENV_PATH"
echo "  Python: $PYTHON_VERSION"
echo "  Site packages: $SITE_PACKAGES"
echo "  Display model: $DISPLAY_MODEL"
echo ""

# Step 1: Install GitHub driver
echo "[1/4] Installing GitHub waveshare driver..."
pipx runpip weatherstation-epaper uninstall -y waveshare-epaper 2>/dev/null || true

CLONE_DIR=$(mktemp -d)
git clone --depth 1 --filter=blob:none --sparse \
    https://github.com/waveshareteam/e-Paper.git "$CLONE_DIR/e-Paper"
git -C "$CLONE_DIR/e-Paper" sparse-checkout set RaspberryPi_JetsonNano/python
pipx inject --force weatherstation-epaper "$CLONE_DIR/e-Paper/RaspberryPi_JetsonNano/python/"
rm -rf "$CLONE_DIR"
echo "  Done."
echo ""

# Step 2: Create compatibility wrapper
echo "[2/4] Creating epaper compatibility wrapper..."
cat > "$SITE_PACKAGES/epaper.py" << 'EOF'
"""Compatibility wrapper: translates import epaper to waveshare_epd."""
import importlib

def epaper(model_name):
    class EPDWrapper:
        def __init__(self):
            module = importlib.import_module(f"waveshare_epd.{model_name}")
            self.EPD = getattr(module, "EPD")
    return EPDWrapper()
EOF
echo "  Created $SITE_PACKAGES/epaper.py"
echo ""

# Step 3: Patch ReadBusy
echo "[3/4] Patching ReadBusy with 10-second timeout..."
DRIVER_FILE="$SITE_PACKAGES/waveshare_epd/$DISPLAY_MODEL.py"
if [ ! -f "$DRIVER_FILE" ]; then
    echo "  ERROR: Driver file not found: $DRIVER_FILE"
    exit 1
fi

python3 << PYEOF
import sys

driver_path = "$DRIVER_FILE"
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

if old not in content:
    print("  WARNING: ReadBusy pattern not found (may already be patched)")
    sys.exit(0)

content = content.replace(old, new)
with open(driver_path, "w") as f:
    f.write(content)
print("  Patched successfully!")
PYEOF
echo ""

# Step 4: Clear cache
echo "[4/4] Clearing Python cache..."
rm -rf "$SITE_PACKAGES/waveshare_epd/__pycache__"
echo "  Done."
echo ""

echo "Fix applied! Restart the service with:"
echo "  sudo systemctl restart weatherstation"
