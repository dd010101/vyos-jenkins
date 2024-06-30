#!/usr/bin/env bash
set -e

#
# This script seeds Jenkins jobs via list of packages in jobs.json
# it iterates through all packages
# it checks if job for package exists
# it updates job if exists otherwise creates new one.
# It can also start build for all jobs.
#
# This script has two modes, first mode is create
# ./seed-jobs.sh create
# this will update or create jobs
#
# Second mode is build
# ./seed-jobs.sh build
# this will trigger build for all jobs
#
# You need to wait after create some time, Jenkins need to complete branch indexing.
# Check Jenkins Build Queue and Build Executor Status to be empty. Then you can run build.
#
# dependency: apt install -y xmlstarlet jq
#
# Refer to Jenkins documentation to create a token
# https://www.jenkins.io/doc/book/system-administration/authenticating-scripted-clients/
#   The API token is available in your personal configuration page.
#   Click your name on the top right corner on every page, then click "Configure"
#   to see your API token.

jenkinsUser="" # fill your username here or set via export JENKINS_USER
jenkinsToken="" # fill your token here or set via export JENKINS_TOKEN
jenkinsHost="172.17.17.17:8080"
workDir="/tmp/seed-jobs"

mkdir -p "$workDir"

templatePath="../jobs/jobTemplate.xml"
jenkinsUser=${jenkinsUser:-$JENKINS_USER}
jenkinsToken=${jenkinsToken:-$JENKINS_TOKEN}
jenkinsUrl="http://${jenkinsUser}:${jenkinsToken}@$jenkinsHost"

mode="$1"
availableModes=("create" "build")

get() {
  curl -sS -g --fail-with-body "${jenkinsUrl}${1}"
}

post() {
  curl -sS -g --fail-with-body -X POST "${jenkinsUrl}${1}"
}

push() {
  curl -sS -g --fail-with-body -X POST -d "@${2}" -H "Content-Type: text/xml" "${jenkinsUrl}${1}"
}

echo -n "testing jenkins connection: "
get > /dev/null
echo "ok"

if [[ "$mode" == "create" ]]; then
  while read item
  do
    jobName=$(echo "$item" | jq -r .name)
    echo -n "$jobName:"

    description=$(echo "$item" | jq -r .description)
    gitUrl=$(echo "$item" | jq -r .gitUrl)
    branchRegex=$(echo "$item" | jq -r .branchRegex)
    jenkinsfilePath=$(echo "$item" | jq -r .jenkinsfilePath)

    # create job.xml by using jobTemplate.xml
    jobPath="$workDir/$jobName.xml"
    project="org.jenkinsci.plugins.workflow.multibranch.WorkflowMultiBranchProject"
    branchSource="$project/sources/data/jenkins.branch.BranchSource/source"
    regexTrait="$branchSource/traits/jenkins.scm.impl.trait.RegexSCMHeadFilterTrait"
    xmlstarlet ed --update "//$project/description" --value "$description" \
      --update "//$branchSource/remote" --value "$gitUrl" \
      --update "//$regexTrait/regex" --value "$branchRegex" \
      --update "//$project/factory/scriptPath" --value "$jenkinsfilePath" \
      "$templatePath" > "$jobPath" 2>/dev/null

    # check if job exists
    result=$(get "/checkJobName?value=$jobName" || true)
    if [[ "$result" == *"already exists"* ]]; then
      # update job
      push "/job/$jobName/config.xml" "$jobPath"
    else
      # create job
      push "/createItem?name=$jobName" "$jobPath"
    fi

    echo " ok"

  done < <(cat jobs.json | jq -c '.[]')

elif [[ "$mode" == "build" ]]; then

  get "/api/xml?tree=jobs[name]" | xmlstarlet sel -t -v "//hudson/job/name" | while read jobName || [ -n "$jobName" ]; do

    echo -n "$jobName:"

    # trigger build - it's not easy to know what branches job has
    # thus we trigger all possible ones and ignore not found
    post "/job/$jobName/job/equuleus/build" > /dev/null 2>/dev/null || true
    post "/job/$jobName/job/sagitta/build" > /dev/null 2>/dev/null || true
    post "/job/$jobName/job/current/build" > /dev/null 2>/dev/null || true

    echo " ok"

  done

else
  echo "ERROR: unknown mode '$mode'"
  echo "available modes: ${availableModes[*]}"
fi
