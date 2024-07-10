#!/bin/bash
set -e

#
# You can use this script to mirror VyOS repositories for safekeeping purposes.
# It's good idea to use some kind of backup with versioning ability, like the duplicity/duply.
# To make sure you can go back in time, if something you want from the repositories gets deleted.
#

rootDir="/opt/vyos-git"
dataDir="$rootDir/data"
reposDir="$rootDir/repos"

mkdir -p "$dataDir"
mkdir -p "$reposDir"

page=1
while [ $page -le 1000 ]
do
    echo "Processing page $page"

    path="$dataDir/repos-$page.json"
    curl -sS --fail-with-body "https://api.github.com/orgs/vyos/repos?per_page=50&page=$page" -o "$path"

    emptyPage=true
    while read gitUrl
    do
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

        emptyPage=false
    done < <(cat "$path" | jq -c -r '.[].clone_url')

    if [ $emptyPage = true ]; then
        echo "All done"
        break
    fi

    page=$((page+1))
done
