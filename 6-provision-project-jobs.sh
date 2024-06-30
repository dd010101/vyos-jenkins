#!/usr/bin/env bash

source ./auto/helper-logic

# Clear the screen and print the header
PrintHeader

# Ensure we are running as root
EnsureRoot

# Ensure stage 5 is complete
EnsureStageIsComplete 5

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
ProvisionJobs "jobs/project-jobs.json"

echo
echo "The project jobs has been provisioned."
echo "Part 6 of the installer is now done."
echo "Please run part seven (7-build-project-jobs.sh) to build the project jobs."

# Create marker file
CreateMarkerFile 6
