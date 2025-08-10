#!/usr/bin/env bash
set -e
sudo apt-get update
sudo apt-get install -y bison flex libelf-dev:native libreadline-dev liblua5.3-dev
python3 ./build.py
