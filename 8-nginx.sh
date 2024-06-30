#!/usr/bin/env bash

source ./helper-logic

# Clear the screen and print the header
PrintHeader

# Ensure we are running as root
EnsureRoot

# Ensure stage 7 is complete
EnsureStageIsComplete 7

# Add NGINX configuration
echo "Configuring NGINX..."

#region NGINX default configuration
if [ -f /etc/nginx/sites-enabled/default ]; then
  function RemoveDefaultNginxConfiguration() {
    rm /etc/nginx/sites-enabled/default
  }

  Run "RemoveDefaultNginxConfiguration" \
    "Removing default NGINX configuration..." \
    "Failed to remove default NGINX configuration." \
    "Default NGINX configuration has been removed."
fi
#endregion

#region NGINX apt-mirror configuration
if [ -f /etc/nginx/sites-available/apt-mirror ]; then
  function RemoveAptMirrorNginxConfiguration() {
    rm /etc/nginx/sites-available/apt-mirror
  }

  Run "RemoveAptMirrorNginxConfiguration" \
    "Removing apt-mirror NGINX configuration..." \
    "Failed to remove apt-mirror NGINX configuration." \
    "Apt-mirror NGINX configuration has been removed."
fi

function CopyAvailableSiteFile {
  cp install-files/nginx-site /etc/nginx/sites-available/apt-mirror
}

Run "CopyAvailableSiteFile" \
  "Copying apt-mirror NGINX configuration file..." \
  "Failed to copy apt-mirror NGINX configuration." \
  "Apt-mirror NGINX configuration has been copied."
#endregion

#region Enable NGINX apt-mirror configuration
if [ ! -f /etc/nginx/sites-enabled/apt-mirror ]; then
  function LinkAptMirrorNginxConfiguration() {
    ln -s /etc/nginx/sites-available/apt-mirror /etc/nginx/sites-enabled/apt-mirror
  }

  Run "LinkAptMirrorNginxConfiguration" \
    "Linking apt-mirror NGINX configuration file..." \
    "Failed to link apt-mirror NGINX configuration." \
    "Apt-mirror NGINX configuration has been linked."
fi
#endregion

#region Restart NGINX
function RestartNginx() {
  systemctl restart nginx
}

Run "RestartNginx" \
  "Restarting NGINX..." \
  "Failed to restart NGINX." \
  "NGINX has been restarted."
#endregion

echo
echo "Part 8 of the installer is now done."
echo "The installation is now done - you can build the ISO by running the build-iso bash script."

# Create marker file
CreateMarkerFile 8