#!/usr/bin/env bash
set -e

#
# You can use this script to mirror all GitHub repositories of org/user for safekeeping purposes.
# It's good idea to use some kind of backup with versioning ability, like the duplicity/duply.
# To make sure you can go back in time, if something you want from the repositories gets purged.
#
# Configuration:
# The root path is the base directory for all repositories and metadata
#   export ROOT_PATH="/opt/github-mirror"
# Namespace is sub-directory, so you can divide repositories of multiple orgs/users
#   export NAMESPACE="vyos"
# The GITHUB_SUBJECT sets the GitHub org/user you want to mirror and the GITHUB_KIND sets type of the subject
#   export GITHUB_KIND="org"
#   export GITHUB_SUBJECT="vyos"
# or
#   export GITHUB_KIND="user"
#   export GITHUB_SUBJECT="dd010101"
#
# This script will produce $ROOT_PATH/data and $ROOT_PATH/repos directories
# The data contains working data used by this script.
# The repos contains git mirrors divided by namespaces.
#

namespace="vyos"
namespace=${NAMESPACE:-$namespace}
githubKind="org"
githubKind=${GITHUB_KIND:-$githubKind}
githubSubject="vyos"
githubSubject=${GITHUB_SUBJECT:-$githubSubject}
rootPath="/opt/github-mirror"
rootPath=${ROOT_PATH:-$rootPath}
dataDir="$rootPath/data/$namespace"
reposDir="$rootPath/repos/$namespace"

mkdir -p "$dataDir"
mkdir -p "$reposDir"

page=1
while [ $page -le 1000 ]
do
    echo "Processing page $page"

    path="$dataDir/repos-$page.json"
    params="?per_page=50&page=$page"
    curl -sS --fail-with-body "https://api.github.com/${githubKind}s/$githubSubject/repos$params" -o "$path"

    emptyPage=true
    while read -r item
    do
        gitUrl=$(jq -r '.clone_url' <<< "$item")
        description=$(jq -r '.description' <<< "$item")
        if [ "$description" == "null" ]; then
            description=""
        fi

        directory=$(echo "$gitUrl" | grep -oP '([^/]+).git')
        fullPath="$reposDir/$directory"
        if [ -d "$fullPath" ]; then
            echo "Updating $gitUrl in $fullPath"
            git -C "$fullPath" remote update 2>&1
            if [ $? -ne 0 ]; then
                >&2 echo "ERROR: failed to 'git remote update' for $fullPath"
            fi
        else
            echo "Cloning $gitUrl as $fullPath"
            mkdir -p "$fullPath"
            git -C "$fullPath" clone --mirror "$gitUrl" .
        fi

        echo "$description" > "$fullPath/description"

        emptyPage=false
    done < <(cat "$path" | jq -c '.[]')

    if [ $emptyPage = true ]; then
        echo "All done"
        break
    fi

    page=$((page+1))
done
