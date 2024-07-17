#!/usr/bin/env bash
set -e

#
# Companion script for github-mirror.sh. This script calls backup command when the delta between latest change
# and backup reached specified threshold.
#
# Configuration:
#
# The root path is the base directory - needs to be same as for the github-mirror.sh:
#   export ROOT_PATH="/opt/github-mirror"
#
# Optional variables:
#   export BACKUP_COMMAND="duply github-mirror backup && duply github-mirror purgeFull --force"
#   export BACKUP_DELTA_THRESHOLD="10800"
#

rootPath="/opt/github-mirror"
rootPath=${ROOT_PATH:-$rootPath}
dataDir="$rootPath/data"
reposDir="$rootPath/repos"
changeTimestampFileName="change-timestamp"

backupCommand="duply github-mirror backup && duply github-mirror purgeFull --force"
backupCommand=${BACKUP_COMMAND:-$backupCommand}
backupDeltaThreshold=10800
backupDeltaThreshold=${BACKUP_DELTA_THRESHOLD:-$backupDeltaThreshold}

function formatDate {
    date '+%Y-%m-%d %H:%M:%S' -d "@$1"
}

if [ ! -d "$dataDir" ] || [ ! -d "$reposDir" ]; then
    >&2 echo "ERROR: nothing to backup, make sure the ROOT_PATH ($ROOT_PATH) is correct"
    exit 1
fi

echo "Namespaces:"

changeTimestamp=0
for namespacePath in $dataDir/*/ ; do
    changeTimestampPath="$namespacePath/$changeTimestampFileName"
    if [ ! -f "$changeTimestampPath" ]; then
        echo "WARNING: $changeTimestampPath is missing"
        continue
    fi
    myChangeTimestamp=$(cat "$changeTimestampPath")
    myChangeTimestamp=$(( myChangeTimestamp ))
    namespace=$(basename "$namespacePath")
    echo "$(formatDate "$myChangeTimestamp") $namespace"
    if [ $changeTimestamp -lt $myChangeTimestamp ]; then
        changeTimestamp=$myChangeTimestamp
    fi
done

echo "Decision:"

backupTimestamp=0
backupTimestampPath="$dataDir/backup-timestamp"
if [ -f "$backupTimestampPath" ]; then
  backupTimestamp=$(cat "$backupTimestampPath")
  backupTimestamp=$(( backupTimestamp ))
fi

delta=$(( "$changeTimestamp" - "$backupTimestamp" ))
echo "Latest change: $(formatDate "$changeTimestamp")"
echo "Latest backup: $(formatDate "$backupTimestamp")"
echo "Delta: $delta seconds (threshold: $backupDeltaThreshold seconds)"

if [ $delta -ge $backupDeltaThreshold ]; then
    echo "Running backup now"
    eval "$backupCommand"
    date +%s > "$backupTimestampPath"
else
    echo "Condition wasn't satisfied, try again later"
fi
