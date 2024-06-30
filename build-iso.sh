#!/usr/bin/env bash

source ./helper-logic

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
read -p "Please enter your email address: " EMAIL
echo

if ([ "$BRANCH" != "equuleus" ] && [ "$BRANCH" != "sagitta" ]); then
  echo -e "${RED}Invalid branch${NOCOLOR}"
  exit
fi

if [ -d vyos-build ]; then
  echo "Removing old vyos-build directory..."
  rm -rf vyos-build
fi

echo "Cloning the VyOS build repository..."
git clone https://github.com/dd010101/vyos-build > /dev/null 2>&1
pushd vyos-build > /dev/null

echo "Checking out the $BRANCH branch..."
git checkout "$BRANCH" > /dev/null 2>&1

echo "Downloading apt signing key..."
wget http://172.17.17.17/apt.gpg.key -O /tmp/apt.gpg.key > /dev/null 2>&1

DATE=$(date +%Y%m%d)

popd > /dev/null

function GetLatestTag {
  # Clone the vyos-1x repo
  git clone --bare https://github.com/vyos/vyos-1x.git -b $1 temp-git-tag > /dev/null 2>&1
  pushd temp-git-tag > /dev/null

  # The the latest tag for this branch
  git describe --tags --abbrev=0

  popd > /dev/null
  rm -rf temp-git-tag
}

function RunWithLazyStdout {
    set -e
    command=$1

    # stop the background command on ctrl+c
    # and cleanup temporary file and tail on exit
    stty -echoctl
    trap stop INT TERM
    trap cleanup EXIT

    function stop {
        kill $pid || true

        wait $pid
        exitCode=$?

        cleanup
        exit $exitCode
    }

    function cleanup {
        stty echo
        if [ "$buffer" != "" ]; then
            rm -f $buffer 2> /dev/null || true
        fi
        if [ "$tailPid" != "" ]; then
            kill $tailPid || true
        fi
    }

    buffer=$(mktemp -p /tmp --suffix=-background-buffer)

    $command > $buffer &
    pid=$!

    echo "Show output? Press y..."
    while ps -p $pid > /dev/null
    do
        if [ "$tailPid" == "" ]; then
            read -s -n 1 -t 1 input || true
            if [ "$input" == "y" ]; then
                tail -f -n +1 $buffer &
                tailPid=$!
            fi
        else
            sleep 1
        fi
    done

    wait $pid
    exit $?
}

function FilterStderr {
    ( set -e; eval "$1" 2>&1 1>&3 | (grep -v -E "$2" || true); exit ${PIPESTATUS[0]}; ) 1>&2 3>&1
    return $?
}

echo "Building the ISO..."
if [ "$BRANCH" == "equuleus" ]; then
  LATEST=`GetLatestTag equuleus`
  RELEASE_NAME="$LATEST-release-$DATE"

  function DockerBuild {
    docker run --rm --privileged -v ./vyos-build/:/vyos -v "/tmp/apt.gpg.key:/opt/apt.gpg.key" -w /vyos --sysctl net.ipv6.conf.lo.disable_ipv6=0 -e GOSU_UID=$(id -u) -e GOSU_GID=$(id -g) -w /vyos vyos/vyos-build:equuleus \
      sudo ./configure \
      --architecture amd64 \
      --build-by "$1" \
      --build-type release \
      --version "$2" \
      --vyos-mirror http://172.17.17.17/equuleus \
      --debian-elts-mirror http://172.17.17.17:3142/deb.freexian.com/extended-lts \
      --custom-apt-key /opt/apt.gpg.key \
      --custom-package vyos-1x-smoketest

    docker run --rm --privileged --name="vyos-build" -v ./vyos-build/:/vyos -v "/tmp/apt.gpg.key:/opt/apt.gpg.key" -w /vyos --sysctl net.ipv6.conf.lo.disable_ipv6=0 -e GOSU_UID=$(id -u) -e GOSU_GID=$(id -g) -w /vyos vyos/vyos-build:equuleus \
      sudo make iso
  }

  (
    FilterStderr "( RunWithLazyStdout \"DockerBuild $EMAIL $RELEASE_NAME\" )" "(useradd warning)"
    exit $?
  )

  BUILD_EXIT_CODE=$?
elif [ "$BRANCH" == "sagitta" ]; then
  LATEST=`GetLatestTag sagitta`
  RELEASE_NAME="$LATEST-release-$DATE"

  function DockerBuild {
    docker run --rm --privileged --name="vyos-build" -v ./vyos-build/:/vyos -v "/tmp/apt.gpg.key:/opt/apt.gpg.key" -w /vyos --sysctl net.ipv6.conf.lo.disable_ipv6=0 -e GOSU_UID=$(id -u) -e GOSU_GID=$(id -g) -w /vyos vyos/vyos-build:sagitta \
      sudo --preserve-env ./build-vyos-image iso \
      --architecture amd64 \
      --build-by "$1" \
      --build-type release \
      --debian-mirror http://deb.debian.org/debian/ \
      --version "$2" \
      --vyos-mirror http://172.17.17.17/sagitta \
      --custom-apt-key /opt/apt.gpg.key \
      --custom-package vyos-1x-smoketest
  }

  (
    FilterStderr "( RunWithLazyStdout \"DockerBuild $EMAIL $RELEASE_NAME\" )" "(useradd warning)"
    exit $?
  )

  BUILD_EXIT_CODE=$?
else
  echo -e "${RED}Invalid branch${NOCOLOR}"
  exit
fi

if [ $BUILD_EXIT_CODE != 0 ]; then
  echo -e "${RED}ISO build failed${NOCOLOR}"
  exit
fi

if [ -f vyos-build/build/live-image-amd64.hybrid.iso ]; then
  mv vyos-build/build/live-image-amd64.hybrid.iso ./vyos-$RELEASE_NAME-iso-amd64.iso
  echo
  echo -e "${GREEN}ISO build is complete.${NOCOLOR}"
  echo -e "The file is called: ${GREEN}vyos-${RELEASE_NAME}-iso-amd64.iso${NOCOLOR}".
else
  echo
  echo -e "${RED}Failed to locate ISO file.${NOCOLOR}"
  exit
fi

if [ -d vyos-build ]; then
  echo
  echo "Cleaning up..."
  rm -rf vyos-build
fi