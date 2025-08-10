#!/usr/bin/env bash
set -e
sudo apt-get update
sudo apt-get install -y cmake
python3 ./build.py
