#!/usr/bin/env bash
set -e

# Ensure we are jenkins user
if [ "$EUID" -ne 1006 ]; then
  >&2 echo "Please run as jenkins"
  exit 1
fi

if [ -f ~/.gnupg/pubring.kbx ]; then
  echo "GnuPG Keypair has already been generated."
else
  echo "Generating GnuPG keypair..."
  gpg --batch --gen-key > /dev/null 2>&1 <<EOF
  %no-protection
  Key-Type:1
  Key-Length:3072
  Subkey-Type:1
  Subkey-Length:3072
  Name-Real: NOTvyos Signing Key
  Name-Email: signing@not-vyos.org
  Expire-Date:0
EOF
fi
