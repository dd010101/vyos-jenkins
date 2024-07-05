#!/usr/bin/env bash
set -e

#
# This script can maintain file mirror with minimum lag.
# Yet it will not waste resources by running synchronization many times in short period.
#
# We use "marker files" to detect changes in order to trigger synchronization.
# The synchronization may be postponed to avoid synchronizing incomplete source.
#
# With this mechanism we can run this script at very rapid interval (like every minute)
# with minimal overhead since most of the time we just compare few timestamps.
#
# In this example we use rsync, but you can replace rsync with any other program
# that doesn't need to be as efficient as rsync is since it will run only when necessary.
#
# Extra dependencies:
#   apt install --no-install-recommends -y curl jq rsync procmail
#
# Configuration:
#   export TARGET_PATH=mirror@10.0.0.127:/var/www/...
#   export JENKINS_USER="YOUR_USERNAME"
#   export JENKINS_TOKEN="API_TOKEN"
#

sourcePath="/home/sentrium/web/dev.packages.vyos.net/public_html/repositories"
targetPath="/tmp/repositories/"
targetPath=${TARGET_PATH:-$targetPath}

# Jenkins configuration.
jenkinsHost="172.17.17.17:8080"
jenkinsHost=${jenkinsHost:-$JENKINS_HOST}
jenkinsUser="$JENKINS_USER"
jenkinsToken="$JENKINS_TOKEN"
jenkinsUrl="http://${jenkinsUser}:${jenkinsToken}@$jenkinsHost"

# Marker files tells us if the source changed by their modification time.
markerFiles=(
    "/home/sentrium/web/dev.packages.vyos.net/public_html/repositories/equuleus/dists/equuleus/Release"
    "/home/sentrium/web/dev.packages.vyos.net/public_html/repositories/sagitta/dists/sagitta/Release"
)

# Metadata.
workDir="/tmp/reprepro-mirror"
lastSyncPath="$workDir/lastSync"
lockPath="$workDir/lock"

# Should be synchronization postponed? Return 1 if yes otherwise 0.
function isSynchronizationPostponed {
    jenkinsIdle=$(curl -Ss -g --fail-with-body "$jenkinsUrl/computer/api/json" | jq .computer[0].idle)
    exitCode=$?
    if [ "$exitCode" -ne 0 ]; then
        exit $exitCode
    fi
    if [ "$jenkinsIdle" == "true" ]; then
        return 0
    fi
    return 1
}

# The logic.
if lockfile -0 -r 0 -! "$lockPath" > /dev/null 2>&1; then
    echo "Other synchronization is already in progress."
    exit 0
fi

function cleanup {
    rm -f "$lockPath"
}
trap '(exit 130)' INT; trap '(exit 143)' TERM; trap cleanup EXIT

function formatDate {
    echo $(date -d "@$1" "+%Y-%m-%d %H:%M:%S")
}

if ! [ -f "$workDir" ]; then
    mkdir -p "$workDir"
fi

lastSync=0
if [ -f "$lastSyncPath" ]; then
    lastSync=$(stat -c %Y "$lastSyncPath")
fi
if [ "$1" == "force" ]; then
    lastSync=0
fi

lastChange=0
for markerPath in "${markerFiles[@]}"
do
    markerTime=$(stat -c %Y "$markerPath")
    if [ "$markerTime" -gt "$lastChange" ]; then
        lastChange="$markerTime"
    fi
done

if [ "$lastChange" == 0 ]; then
    >&2 echo "ERROR: unable to detect modification time of ${markerFiles[@]}!"
    exit 1
fi

echo "Last change: $(formatDate "$lastChange")"
echo "last sync: $(formatDate "$lastSync")"

if [ "$lastSync" -ge "$lastChange" ]; then
    echo "No synchronization required."
    exit 0
fi

echo "Synchronization is required."

if ! isSynchronizationPostponed; then
    echo "Operation is postponed, please try later."
    exit 0
fi

# The synchronization command.
rsync -azv --progress --delete "$sourcePath" "$targetPath"

touch "$lastSyncPath"
