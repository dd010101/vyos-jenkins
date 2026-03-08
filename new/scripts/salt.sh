#!/usr/bin/env bash
set -e

chmod +x build.sh

if [ -f ./build.py ]; then
  python3 ./build.py
else
  /my-build-scripts/generic-build-script.sh
fi
