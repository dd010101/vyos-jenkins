#!/usr/bin/env bash
set -e
sudo apt-get update
sudo apt-get install -y libpcre2-dev
python3 ./build.py
