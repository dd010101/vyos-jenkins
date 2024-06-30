#!/usr/bin/env bash

source ./auto/helper-logic

# Clear the screen and print the header
PrintHeader "7-build-project-jobs.sh"

# Ensure we are running as root
EnsureRoot

# Ensure stage 6 is complete
EnsureStageIsComplete 6

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

# Build the jobs.
BuildJobs "jobs/project-jobs.json"

if [ $? -eq 0 ]; then
  echo
  echo "All packages have been built."
  echo "Part 7 of the installer is now done."
  echo "Please run part eight (8-nginx.sh) to set up NGINX."
  echo
else
  echo
  echo "One or more packages failed to build."
  echo "A list of failed jobs is printed above."
  echo "Please check inside Jenkins to see what went wrong, and run a new build of the failed package."
  echo "Once this is done, please run part eight (8-nginx.sh) to set up NGINX."
  echo
fi

# Create marker file
CreateMarkerFile 7