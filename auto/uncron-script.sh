#!/usr/bin/env bash
set -e

# Ensure we are jenkins user
if [ "$EUID" -ne 1006 ]; then
  >&2 echo "Please run as jenkins"
  exit 1
fi

if [ -d uncron ]; then
  echo "Updating Uncron git repository..."
  cd uncron
  git reset --hard origin/main > /dev/null 2>&1 # revert patches
  git pull > /dev/null 2>&1
else
  echo "Cloning Uncron git repository..."
  git clone https://github.com/notvyos/uncron.git > /dev/null 2>&1
  cd uncron
fi

if [ -d ~/.opam ]; then
  echo "OPAM has already been initialized."
else
  echo "Initializing OPAM..."
  opam init -n > /dev/null 2>&1
fi

eval $(opam env --switch=default)

echo "Ensuring packages have been installed..."
opam install lwt lwt_ppx logs containers -y > /dev/null 2>&1

eval $(opam env)

echo "Applying patches..."
sed -i 's~/run/uncron.sock~/run/uncron/uncron.sock~' src/uncron-add
sed -i 's~/run/uncron.sock~/run/uncron/uncron.sock~' src/uncron.ml

echo "Building Uncron..."
dune build
