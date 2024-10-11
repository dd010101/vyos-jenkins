#!/usr/bin/env bash
set -e

# You can use this script to install dependencies under Debian.
# If you don't use Debian then find and install equivalent of these dependencies via your favorite package manager.
# For Python dependencies you can as well use pip install but then everything should be done inside venv/virtualenv.

if ! apt -v > /dev/null 2>&1; then
  >&2 echo "APT not found. Please install dependencies manually according to this file."
  exit 1
fi

sudo apt-get update -y

# install general packages
sudo apt-get install -y \
  git \
  gpg \
  reprepro

# install python dependencies (python3-yaml is pyyaml)
sudo apt-get install -y \
  python3 \
  python3-yaml \
  python3-requests \
  python3-netifaces \
  python3-tomlkit

# install docker according to https://docs.docker.com/engine/install/
if docker > /dev/null 2>&1; then
  echo "Docker is present, skipping installation"
else
  install=false
  if cat /etc/os-release | grep Debian > /dev/null 2>&1; then
    sudo wget https://download.docker.com/linux/debian/gpg -O /etc/apt/keyrings/docker.asc
    arch=$(dpkg --print-architecture)
    codename=$(. /etc/os-release && echo "$VERSION_CODENAME")
    echo "deb [arch=$arch signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $codename stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    install=true
  elif cat /etc/os-release | grep Ubuntu > /dev/null 2>&1; then
    sudo wget https://download.docker.com/linux/ubuntu/gpg -O /etc/apt/keyrings/docker.asc
    arch=$(dpkg --print-architecture)
    codename=$(. /etc/os-release && echo "$VERSION_CODENAME")
    echo "deb [arch=$arch signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $codename stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    install=true
  fi

  if $install; then
    sudo apt-get update -y
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  else
    >&2 echo "WARNING: Docker is missing yet won't be installed since this is not Debian/Ubuntu system"
    >&2 echo "Please install Docker yourself before continuing: https://docs.docker.com/engine/install/"
  fi
fi
