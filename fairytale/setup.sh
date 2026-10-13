#!/usr/bin/env bash
# Install rendering dependencies (Debian/Ubuntu).
set -e
if ! command -v ffmpeg >/dev/null || ! command -v espeak-ng >/dev/null || ! pkg-config --exists cairo 2>/dev/null; then
  apt-get update -qq
  apt-get install -y -qq ffmpeg espeak-ng libcairo2-dev pkg-config >/dev/null
fi
python3 -c "import cairo" 2>/dev/null || pip install -q --ignore-installed pycairo
python3 -c "import PIL, numpy" 2>/dev/null || pip install -q pillow numpy
echo "fairytale: dependencies ready"
