#!/usr/bin/env bash
set -e

providedBy="$1"
repositoryUrl="$2"
outputPath="$3"

if [ "$providedBy" == "" ] || [ "$repositoryUrl" == "" ] || [ "$outputPath" == "" ]; then
    echo "Usage: ./generate-mirror-html.sh [PROVIDED_BY] [REPOSITORY_URL] [OUTPUT_PATH]"
    echo -e "\t[PROVIDED_BY] shall be your or mirror name"
    echo -e "\t[REPOSITORY_URL] shall be URL prefix, like http://1.2.3.4 if your repository is in / or http://1.2.3.4/apt if your repository is in /apt"
    echo -e "\t[OUTPUT_PATH] shall be output path, like /tmp/index.html"
    exit 0
fi

cp ./resources/template.html "$outputPath"
sed -i "s/\[PROVIDED_BY\]/${providedBy//\//\\/}/" "$outputPath"
sed -i "s/\[REPOSITORY_URL\]/${repositoryUrl//\//\\/}/" "$outputPath"
