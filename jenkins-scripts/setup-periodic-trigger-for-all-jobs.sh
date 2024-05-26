#!/usr/bin/env bash
set -e

#
# This script lists all available jobs
# then obtains XML definition for each job
# then modifies XML definition (adds periodic trigger)
# and at last pushes modified XML definition to Jenkins
#
# This may not be useful to you but it shows how to interact with Jenkins in automated way.
#
# dependency: apt install xmlstarlet
#

jenkinsUser="" # fill your username here or set via export JENKINS_USER
jenkinsToken="" # fill your token here or set via export JENKINS_TOKEN
jenkinsHost="172.17.17.17:8080"
workDir="/opt/jenkins-cli"

mkdir -p "$workDir"

templatePath="jobTemplate.xml"
jenkinsUser=${jenkinsUser:-$JENKINS_USER}
jenkinsToken=${jenkinsToken:-$JENKINS_TOKEN}
jenkinsUrl="http://${jenkinsUser}:${jenkinsToken}@$jenkinsHost"

get() {
  curl -sS -g "${jenkinsUrl}${1}"
}

push() {
  curl -sS -g -X POST -d "@${2}" -H "Content-Type: text/xml" "${jenkinsUrl}${1}"
}

get "/api/xml?tree=jobs[name]" | xmlstarlet sel -t -v "//hudson/job/name" | while read jobName || [ -n "$jobName" ]; do

  echo -n "$jobName:"

  originalPath="$workDir/$jobName.xml"
  get "/job/$jobName/config.xml" > "$originalPath"

  updatedPath="$workDir/${jobName}_updated.xml"
  project="org.jenkinsci.plugins.workflow.multibranch.WorkflowMultiBranchProject"
  trigger="com.cloudbees.hudson.plugins.folder.computed.PeriodicFolderTrigger"
  plugin="cloudbees-folder@6.928.v7c780211d66e"
  xmlstarlet ed  --delete "//$project/triggers/$trigger" \
      --subnode "//$project/triggers" --type elem --name "$trigger" \
      --append "//$project/triggers/$trigger" --type attr --name plugin --value "$plugin" \
      --subnode "//$project/triggers/$trigger" --type elem --name spec --value "H/15 * * * *" \
      --subnode "//$project/triggers/$trigger" --type elem --name interval --value "3600000" \
      "$originalPath" > "$updatedPath" 2>/dev/null

  push "/job/$jobName/config.xml" "$updatedPath"

  echo " ok"

done
