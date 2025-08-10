#!/usr/bin/env bash
set -e
source /my-build-scripts/env.sh

# just to be sure
sudo apt-get update

# generic .deb packages
if [ -d debian ]; then
  if [ -f debian/control ]; then
    sudo mk-build-deps --install --tool "apt-get --yes --no-install-recommends"
    sudo dpkg -i *build-deps*.deb
  fi

  set +e
  dpkg-buildpackage -uc -us -tc -F

  if [ $? -ne 0 ]; then
    set -e
    echo "Source packages build failed, ignoring - building binaries only"
    dpkg-buildpackage -uc -us -tc -b
  fi

  exit 0
fi

# vyos-cloud-init is using it's own dpkg-buildpackage
if [ -f ./packages/bddeb ]; then
  ./packages/bddeb
  exit 0
fi

echo "I don't know what to do"
ls -alh
exit 1
