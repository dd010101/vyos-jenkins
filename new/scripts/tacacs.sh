#!/usr/bin/env bash
set -e
sudo apt-get update
sudo apt-get install -y libssl-dev
python3 ./build.py
