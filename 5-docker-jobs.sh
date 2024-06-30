#!/usr/bin/env bash

source ./auto/helper-logic

# Clear the screen and print the header
PrintHeader

# Ensure we are running as root
EnsureRoot

# Ensure stage 4 is complete
EnsureStageIsComplete 4

# If the username and token has been saved, we use those instead of asking the user.
if ([ ! -f $USERNAME_FILE ] || [ ! -f $TOKEN_FILE ]); then
  echo
  read -p "Please enter your username here: " USERNAME
  read -p "Please enter your Jenkins token here: " TOKEN
  echo
else
  USERNAME=`cat $USERNAME_FILE`
  TOKEN=`cat $TOKEN_FILE`
fi

# Define the JENKINS url using the username and token provided.
JENKINS_URL="http://${USERNAME}:${TOKEN}@172.17.17.17:8080"

# Ensure the Jenkins CLI has been downloaded.
EnsureJenkinsCli

# Test the connection to make sure Jenkins is ready.
TestJenkinsConnection $USERNAME $TOKEN

echo

# Provision the jobs.
ProvisionJobs "jobs/docker-container-jobs.json"

echo

# Build the jobs.
BuildJobs "jobs/docker-container-jobs.json"

if [ $? -eq 0 ]; then
  echo
  echo "Containers has been built."
  echo "Part 5 of the installer is now done."
  echo "Please run part six (6-provision-project-jobs.sh) to set up the project jobs."
  echo
else
  echo
  echo "One or more container failed to build."
  echo "Please check inside Jenkins to see what went wrong, and run a new build of the failed container."
  echo "Once this is done, please run part six (6-provision-project-jobs.sh) to set up the project job."
  echo
fi

# Create marker file
CreateMarkerFile 5
