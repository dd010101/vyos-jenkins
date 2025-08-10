#!/usr/bin/env bash
set -e
sudo apt-get update
sudo apt-get install -y ocaml dune
eval $(opam env --root=/opt/opam --set-root)
/my-build-scripts/generic-build-script.sh
