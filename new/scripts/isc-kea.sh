#!/usr/bin/env bash
set -e

echo "deb http://deb.debian.org/debian bookworm-backports main" | sudo tee /etc/apt/sources.list.d/bookworm-backports.list
sudo apt-get update
sudo apt-get install -y -t bookworm-backports meson

if [ -f ./build.py ]; then
  python3 ./build.py
else
  /my-build-scripts/generic-build-script.sh
fi
