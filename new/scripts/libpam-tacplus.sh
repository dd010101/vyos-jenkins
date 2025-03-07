#!/usr/bin/env bash
set -e

# The build script for trio of libtacplus-map + libpam-tacplus + libnss-tacplus is missing right now.
# Se we put it here, the commit hashed are based on the contents of latest stream tarball.
mkdir others && cd others

# build libtacplus-map
sudo apt-get install -y libaudit-dev
git clone https://github.com/vyos/libtacplus-map.git
cd libtacplus-map
git reset --hard 09baf66
# Make it buildable for newer gcc version:
# https://stackoverflow.com/questions/47185819/building-debian-ubuntu-packages-with-old-gcc-cflag-adjustment
# map_tacplus_user.c:388:31: error: the comparison will always evaluate as 'true' for the address of 'tac_mappedname' will never be NULL [-Werror=address]
# man 1 dpkg-buildflags
export DEB_CFLAGS_APPEND="-Wno-address -Wno-stringop-truncation"
/my-build-scripts/generic-build-script.sh
cd .. && sudo dpkg -i *.deb

# build libpam-tacplus
git clone https://github.com/vyos/libpam-tacplus.git
cd libpam-tacplus
git reset --hard f00e40f
/my-build-scripts/generic-build-script.sh
cd .. && sudo dpkg -i *.deb

# build libnss-tacplus
git clone https://github.com/vyos/libnss-tacplus.git
cd libnss-tacplus
git reset --hard 3ead03a
/my-build-scripts/generic-build-script.sh
