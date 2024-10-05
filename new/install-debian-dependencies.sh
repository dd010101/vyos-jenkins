#!/usr/bin/env bash

# You can use this script to install dependencies under Debian.
# If you don't use Debian then find and install equivalent of these dependencies via your favorite package manager.
# For Python dependencies you can as well use pip install but that should be done under venv (virtualenv).

# python3-yaml is pyyaml
apt-get install -y python3-yaml python3-requests python3-pendulum

# TODO: install docker
