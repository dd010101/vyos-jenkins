#!/usr/bin/env bash

source ./auto/helper-logic

# Clear the screen and print the header
PrintHeader

# Ensure we are running as root
EnsureRoot

# Ensure stage 3 is complete
EnsureStageIsComplete 3

#region Run Uncron script
cp ./auto/uncron-script.sh /var/lib/jenkins
chown jenkins:jenkins /var/lib/jenkins/uncron-script.sh

# Stop if already running
systemctl stop uncron.service > /dev/null 2>&1

# This script builds the uncron package.
echo "Running uncron script as jenkins user..."
runuser -l jenkins -c "./uncron-script.sh"
echo

rm /var/lib/jenkins/uncron-script.sh > /dev/null 2>&1
#endregion

#region Copy uncron into sbin
function InstallUncron {
  cp /var/lib/jenkins/uncron/_build/install/default/bin/uncron /usr/local/sbin/
}

Run "InstallUncron" \
  "Installing Uncron..." \
  "Failed to install Uncron." \
  "Uncron has been installed."
#endregion

#region Setup systemd service file
function CopySystemDServiceFile {
  cp ./auto/uncron.service /etc/systemd/system
}

Run "CopySystemDServiceFile" \
  "Copying SystemD service file..." \
  "Failed to copy SystemD service file." \
  "SystemD file has been copied."
#endregion

#region Install Uncron Add
function InstallUncronAdd {
  cp ./auto/uncron-add /usr/local/bin
  chmod +x /usr/local/bin/uncron-add
  chmod +x /var/lib/jenkins/uncron/src/uncron-add
}

Run "InstallUncronAdd" \
  "Installing Uncron Add..." \
  "Failed to install Uncron Add." \
  "Uncron Add has been installed."
#endregion

#region Uncron config
if [ ! -f /etc/uncron.conf ]; then
  touch /etc/uncron.conf
fi
#endregion

# Reload daemons.
systemctl daemon-reload > /dev/null 2>&1

# Ensure uncron service is enabled.
systemctl enable --now uncron.service > /dev/null 2>&1

# restart uncron service to fix user/group issue
systemctl restart uncron.service > /dev/null 2>&1

echo
echo "Part 4 of the installer is now done."
echo "Please run part five (5-docker-jobs.sh) to set up the vyos build container jobs."

# Create marker file
CreateMarkerFile 4
