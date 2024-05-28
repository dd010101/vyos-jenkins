#!/usr/bin/env bash
set -e

# Ensure we are jenkins user
if [ "$EUID" -ne 1006 ]
  then echo "Please run as jenkins"
  exit
fi

if [ -f ~/.ssh/id_ed25519.pub ]; then
  echo "SSH keypair has already been generated."
else
  echo "Generating SSH keypair..."
  ssh-keygen -t ed25519 -C "jenkins" -N "" -f /var/lib/jenkins/.ssh/id_ed25519 > /dev/null 2>&1
fi

if [ -f ~/.ssh/authorized_keys ]; then
  echo "SSH key has already been authorized."
else
  echo "Authorizing SSH key..."
  cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
fi

echo "Ensuring SSH host key is trusted..."
ssh -oStrictHostKeyChecking=no 172.17.17.17 "pwd > /dev/null 2>&1" > /dev/null 2>&1
