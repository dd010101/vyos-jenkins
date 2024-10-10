#!/usr/bin/env bash
set -e

# build libpam-tacplus
python3 ./build.py

# The libnss-tacplus is missing right now, so we put it here.
# There is a catch - the libnss-tacplus and libtacplus-map1 won't compile with the used libpam-tacplus 1.7.0.
# Thus we need to temporarily build the libpam-tacplus 1.4.3, we use it for build and then throw it away.
if [ ! -d libnss-tacplus ]; then
  mkdir others && cd others

  # build libtacplus-map
  sudo apt-get install -y libaudit-dev
  git clone https://github.com/vyos/libtacplus-map.git
  cd libtacplus-map
  git reset --hard fe47203
  # Make it buildable for newer gcc version:
  # https://stackoverflow.com/questions/47185819/building-debian-ubuntu-packages-with-old-gcc-cflag-adjustment
  # map_tacplus_user.c:388:31: error: the comparison will always evaluate as 'true' for the address of 'tac_mappedname' will never be NULL [-Werror=address]
  # man 1 dpkg-buildflags
  export DEB_CFLAGS_APPEND="-Wno-address -Wno-stringop-truncation"
  /my-build-scripts/generic-build-script.sh
  cd .. && sudo dpkg -i *.deb

  # build libnss-tacplus 1.4.3, install, throw away
  mkdir temp && cd temp
  git clone https://github.com/vyos/libpam-tacplus.git
  cd libpam-tacplus
  git reset --hard 0d38f9b
  /my-build-scripts/generic-build-script.sh
  cd .. && sudo dpkg -i *.deb
  cd .. && sudo rm -rf temp

  # build libnss-tacplus
  git clone https://github.com/vyos/libnss-tacplus.git
  cd libnss-tacplus
  git reset --hard 049d284
  /my-build-scripts/generic-build-script.sh
fi
