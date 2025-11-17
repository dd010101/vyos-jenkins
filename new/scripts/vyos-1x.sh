#!/usr/bin/env bash
set -e
sudo apt-get update

# detection if vyos-1x is built from vyos-build instead of standalone repo
if [ -d ../strongswan/ ]; then
  # build and install python3-vici dependency
  cd ../strongswan/
  commit_id=$(awk -F'"' '/commit_id/ {print $2; exit}' package.toml)
  scm_url=$(awk -F'"' '/scm_url/ {print $2; exit}' package.toml)
  git clone "$scm_url" -b "$commit_id"
  ./build-vici.sh
  sudo apt-get install -y ./python3-vici*.deb
  cd ../vyos-1x

  # fix opam pcre2 package missing from vyos1x-config
  sudo apt-get install -y ocaml dune libpcre2-dev
  sudo sh -c 'eval $(opam env --root=/opt/opam --set-root); opam init --auto-setup && opam install pcre2 -y'
fi

python3 ./build.py
