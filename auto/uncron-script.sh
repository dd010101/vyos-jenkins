#!/usr/bin/env bash
set -e

# Ensure we are jenkins user
if [ "$EUID" -ne 1006 ]
  then echo "Please run as jenkins"
  exit
fi

if [ -d uncron ]; then
  echo "Updating Uncron git repository..."
  cd uncron
  git pull > /dev/null 2>&1
else
  echo "Cloning Uncron git repository..."
  git clone https://github.com/vyos/uncron.git > /dev/null 2>&1
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

echo "Building Uncron..."
dune build
