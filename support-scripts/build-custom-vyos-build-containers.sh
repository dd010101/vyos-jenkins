#!/usr/bin/env bash
set -e

CUSTOM_DOCKER_REPO="172.17.17.17:5000"

#
# Clone (patched) vyos-build

git clone https://github.com/dd010101/vyos-build.git
cd vyos-build/docker

#
# Build and Push equuleus

git checkout equuleus
docker build --no-cache -t vyos/vyos-build:equuleus .

docker tag vyos/vyos-build:equuleus ${CUSTOM_DOCKER_REPO}/vyos/vyos-build:equuleus
docker push ${CUSTOM_DOCKER_REPO}/vyos/vyos-build:equuleus

#
# Build and Push sagitta

git checkout sagitta
docker build --no-cache -t vyos/vyos-build:sagitta .

docker tag vyos/vyos-build:sagitta ${CUSTOM_DOCKER_REPO}/vyos/vyos-build:sagitta
docker push ${CUSTOM_DOCKER_REPO}/vyos/vyos-build:sagitta

#
# Build and Push current -- (current is required for some sagitta packages)

git checkout current
docker build --no-cache -t vyos/vyos-build:current .

docker tag vyos/vyos-build:current ${CUSTOM_DOCKER_REPO}/vyos/vyos-build:current
docker push ${CUSTOM_DOCKER_REPO}/vyos/vyos-build:current
