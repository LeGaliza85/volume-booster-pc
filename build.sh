#!/usr/bin/env bash
# Build the standalone Linux binary.
set -euo pipefail
cd "$(dirname "$0")"

python3 tools/make_icon.py

python3 -m PyInstaller --noconfirm --clean --onefile \
    --name VolumeBooster \
    --add-data "assets/volume-amplifier.ico:assets" \
    app.py

echo
echo "Built dist/VolumeBooster"
