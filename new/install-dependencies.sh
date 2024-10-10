#!/usr/bin/env bash
set -e

# You can use this script to install dependencies under Debian.
# If you don't use Debian then find and install equivalent of these dependencies via your favorite package manager.
# For Python dependencies you can as well use pip install but then everything should be done inside venv/virtualenv.

sudo apt-get update -y

# general packages
sudo apt-get install -y git gpg reprepro

# python dependencies (python3-yaml is pyyaml)
sudo apt-get install -y python3 python3-yaml python3-requests python3-netifaces python3-tomlkit

# docker
if [ ! -f /etc/apt/sources.list.d/docker.list ]; then
  sudo curl -s -S --fail-with-body https://download.docker.com/linux/debian/gpg -o /usr/share/keyrings/docker.asc
  echo "deb [signed-by=/usr/share/keyrings/docker.asc]" https://download.docker.com/linux/debian bookworm stable | sudo tee /etc/apt/sources.list.d/docker.list
fi
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
