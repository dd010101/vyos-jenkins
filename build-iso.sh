#!/usr/bin/env bash

source ./auto/helper-logic

# Clear the screen first
clear

# Print banner
echo "####################################"
echo "# Unofficial VyOS ISO builder v1.0 #"
echo "####################################"
echo

# Ensure we are running as root
EnsureRoot

# Ensure stage 8 is complete
EnsureStageIsComplete 8

read -p "Please enter which branch you want to build (equuleus or sagitta): " BRANCH
read -p "Please enter your build-by identifier (like e-mail): " BUILD_BY
echo

if ([ "$BRANCH" != "equuleus" ] && [ "$BRANCH" != "sagitta" ]); then
  >&2 echo -e "${RED}Invalid branch${NOCOLOR}"
  exit 1
fi

if [ -d vyos-build ]; then
  echo "Removing old vyos-build directory..."
  rm -rf vyos-build
fi

echo "Cloning the VyOS build repository..."
git clone -q https://github.com/dd010101/vyos-build > /dev/null
pushd vyos-build > /dev/null

echo "Checking out the $BRANCH branch..."
git checkout "$BRANCH" > /dev/null

function HandleBranding {
  if [ "$NOT_VYOS" != "" ]; then
    name="$NOT_VYOS"
    if [ "$name" == "yes" ]; then
      name="NOTvyos"
    fi

    echo "Removing branding..."
    cp ../extras/not-vyos/splash.png ./data/live-build-config/includes.binary/isolinux/splash.png
    sed -i "s/VyOS/$name/" ./data/live-build-config/includes.binary/isolinux/menu.cfg
    defaultToml="./data/defaults.toml"
    if [ -f "$defaultToml" ]; then
      sed -i -E 's/website_url =.*/website_url = "localhost"/' "$defaultToml"
      sed -i -E 's/support_url =.*/support_url = "There is no official support."/' "$defaultToml"
      sed -i -E 's/bugtracker_url =.*/bugtracker_url = "DO NOT report bugs to VyOS!"/' "$defaultToml"
      sed -i -E "s/project_news_url =.*/project_news_url = \"This is unofficial $name build.\"/" "$defaultToml"
    fi
    defaultMotd="./data/live-build-config/includes.chroot/usr/share/vyos/default_motd"
    if [ -f "$defaultMotd" ]; then
      sed -i "s/VyOS/$name/" "$defaultMotd"
      sed -i -E "s/Check out project news at.*/This is unofficial $name build./" "$defaultMotd"
      sed -i -E 's/and feel free to report bugs at.*/DO NOT report bugs to VyOS!/' "$defaultMotd"
    fi
  fi
}
(set -e; HandleBranding)
if [ $? -ne 0 ]; then
  PrintErrorIndicator "Branding removal failed"
fi

echo "Downloading apt signing key..."
curl -s -S --fail-with-body http://172.17.17.17/apt.gpg.key -o /tmp/apt.gpg.key

DATE=$(date +%Y%m%d)

popd > /dev/null

function GetLatestTag {
  # Clone the vyos-1x repo
  git clone -q --bare https://github.com/vyos/vyos-1x.git -b $1 temp-git-tag > /dev/null
  pushd temp-git-tag > /dev/null

  # The the latest tag for this branch
  git describe --tags --abbrev=0

  popd > /dev/null
  rm -rf temp-git-tag
}

customPackages="vyos-1x-smoketest"
customPackages=${CUSTOM_PACKAGES:-$customPackages}

echo "Building the ISO..."
if [ "$BRANCH" == "equuleus" ]; then
  LATEST=`GetLatestTag equuleus`
  RELEASE_NAME="$LATEST-release-$DATE"

  function DockerBuild {
    echo "Using arguments: --build-by '$1' --version '$2' --custom-package '$3'"
    docker run --rm --privileged -v ./vyos-build/:/vyos -v "/tmp/apt.gpg.key:/opt/apt.gpg.key" -w /vyos --sysctl net.ipv6.conf.lo.disable_ipv6=0 -e GOSU_UID=$(id -u) -e GOSU_GID=$(id -g) -w /vyos vyos/vyos-build:equuleus \
      sudo ./configure \
      --architecture amd64 \
      --build-by "$1" \
      --build-type release \
      --version "$2" \
      --vyos-mirror http://172.17.17.17/equuleus \
      --debian-elts-mirror http://172.17.17.17:3142/deb.freexian.com/extended-lts \
      --custom-apt-key /opt/apt.gpg.key \
      --custom-package "$3"

    docker run --rm --privileged --name="vyos-build" -v ./vyos-build/:/vyos -v "/tmp/apt.gpg.key:/opt/apt.gpg.key" -w /vyos --sysctl net.ipv6.conf.lo.disable_ipv6=0 -e GOSU_UID=$(id -u) -e GOSU_GID=$(id -g) -w /vyos vyos/vyos-build:equuleus \
      sudo make iso
  }
elif [ "$BRANCH" == "sagitta" ]; then
  LATEST=`GetLatestTag sagitta`
  RELEASE_NAME="$LATEST-release-$DATE"

  function DockerBuild {
    echo "Using arguments: --build-by '$1' --version '$2' --custom-package '$3'"
    docker run --rm --privileged --name="vyos-build" -v ./vyos-build/:/vyos -v "/tmp/apt.gpg.key:/opt/apt.gpg.key" -w /vyos --sysctl net.ipv6.conf.lo.disable_ipv6=0 -e GOSU_UID=$(id -u) -e GOSU_GID=$(id -g) -w /vyos vyos/vyos-build:sagitta \
      sudo --preserve-env ./build-vyos-image iso \
      --architecture amd64 \
      --build-by "$1" \
      --build-type release \
      --debian-mirror http://deb.debian.org/debian/ \
      --version "$2" \
      --vyos-mirror http://172.17.17.17/sagitta \
      --custom-apt-key /opt/apt.gpg.key \
      --custom-package "$3"
  }
else
  >&2 echo -e "${RED}Invalid branch${NOCOLOR}"
  exit 1
fi

dockerBuild="DockerBuild \"$BUILD_BY\" \"$RELEASE_NAME\" \"$customPackages\""
if ! IsFlagSet "-v" "$@"; then
  dockerBuild=${dockerBuild//\"/\\\"} # escape double quotes with backslash
  dockerBuild="RunWithLazyStdout \"$dockerBuild\""
fi

(
  FilterStderr "( $dockerBuild )" "(useradd warning)"
  exit $?
)

BUILD_EXIT_CODE=$?

if [ $BUILD_EXIT_CODE != 0 ]; then
  >&2 echo -e "${RED}ISO build failed${NOCOLOR}"
  exit 1
fi

if [ -f vyos-build/build/live-image-amd64.hybrid.iso ]; then
  mv vyos-build/build/live-image-amd64.hybrid.iso ./vyos-$RELEASE_NAME-iso-amd64.iso
  echo
  echo -e "${GREEN}ISO build is complete.${NOCOLOR}"
  echo -e "The file is called: ${GREEN}vyos-${RELEASE_NAME}-iso-amd64.iso${NOCOLOR}".
else
  echo
  >&2 echo -e "${RED}Failed to locate ISO file.${NOCOLOR}"
  exit 1
fi

if [ -d vyos-build ]; then
  echo
  echo "Cleaning up..."
  rm -rf vyos-build
fi
