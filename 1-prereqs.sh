#!/usr/bin/env bash

source ./auto/helper-logic

# Clear the screen and print the header
PrintHeader

# Ensure we are running as root
EnsureRoot

#region Update apt sources
Run "apt-get update" \
  "Updating apt sources..." \
  "Failed to update apt sources." \
  "Updated apt sources."
#endregion

#region Download cURL
if [ $(dpkg-query -W -f='${Status}' curl 2>/dev/null | grep -c "ok installed") -eq 1 ]; then
  PrintOkIndicator "cURL is already installed."
else
  function DownloadCurl {
    apt-get install curl -y
  }

  Run "DownloadCurl" \
    "Installing cURL..." \
    "Failed to install cURL." \
    "Installed cURL."
fi
#endregion

#region Set up sources.list.d files for Jenkins
if [ -f /etc/apt/sources.list.d/jenkins.list ]; then
  PrintOkIndicator "Jenkins sources.list.d has already been set up."
else
  function SetupJenkinsSourceListD {
    curl -s -S https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key -o /usr/share/keyrings/jenkins-keyring.asc --fail-with-body
    echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc]" https://pkg.jenkins.io/debian-stable binary/ | tee /etc/apt/sources.list.d/jenkins.list
  }

  Run "SetupJenkinsSourceListD" \
    "Setting up Jenkins sources.list.d files..." \
    "Failed to download or set up Jenkins sources.list.d files." \
    "Jenkins sources.list.d files has been set up."
fi
#endregion

#region Set up sources.list.d files for Docker
if [ -f /etc/apt/sources.list.d/docker.list ]; then
  PrintOkIndicator "Docker sources.list.d has already been set up."
else
  function SetupDockerSourceListD {
    curl -s -S https://download.docker.com/linux/debian/gpg -o /usr/share/keyrings/docker.asc --fail-with-body
    echo "deb [signed-by=/usr/share/keyrings/docker.asc]" https://download.docker.com/linux/debian bookworm stable | tee /etc/apt/sources.list.d/docker.list
  }

  Run "SetupDockerSourceListD" \
    "Setting up Docker sources.list.d files..." \
    "Failed to download or set up Docker sources.list.d files." \
    "Docker sources.list.d files has been set up."
fi
#endregion

#region Update apt sources again
Run "apt-get update" \
  "Updating apt sources..." \
  "Failed to update apt sources." \
  "Updated apt sources."
#endregion

#region Jenkins user and group
if grep -q "^jenkins:" /etc/group; then
  PrintOkIndicator "Jenkins group already exist."
else
  function CreateJenkinsGroup {
    groupadd --gid 1006 jenkins
  }

  Run "CreateJenkinsGroup" \
    "Creating jenkins group with GID 1006..." \
    "Failed to create jenkins group." \
    "Created jenkins group."
fi

if id -u jenkins > /dev/null 2>&1; then
  PrintOkIndicator "Jenkins user already exist."
else
  function CreateJenkinsUser {
    useradd --comment Jenkins --shell /bin/bash --uid 1006 --gid 1006 --home-dir /var/lib/jenkins jenkins
  }

  Run "CreateJenkinsUser" \
    "Creating jenkins user with UID 1006..." \
    "Failed to create jenkins user." \
    "Created jenkins user."
fi
#endregion

#region Install needed tools
declare -A tools
tools["Git"]="git"
tools["GnuPG"]="gpg"
tools["SSH"]="openssh-server openssh-client openssh-sftp-server"
tools["Reprepro"]="reprepro"
tools["XMLStarlet"]="xmlstarlet"
tools["Jq"]="jq"
tools["NGINX"]="nginx"
tools["Java"]="openjdk-17-jre fontconfig"
tools["Docker"]="docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin"
tools["OCaml"]="opam ocaml socat"
tools["Jenkins"]="jenkins"
tools["AptCacherNg"]="apt-cacher-ng"

for key in "${!tools[@]}"
do
  VALUES=$(sed -e 's/ /\n/g' <<< "${tools[$key]}")

  ALL_INSTALLED="true"

  for package in $VALUES; do
    if [ $(dpkg-query -W -f='${Status}' $package 2>/dev/null | grep -c "ok installed") -ne 1 ]; then
      ALL_INSTALLED="false"
    fi
  done

  if [[ $ALL_INSTALLED == "true" ]]; then
    PrintOkIndicator "$key is already installed."
  else
    function InstallTool {
      DEBIAN_FRONTEND=noninteractive apt-get -yq install $@
    }

    Run "InstallTool ${tools[$key]}" \
      "Installing $key..." \
      "Failed to install $key." \
      "Installed $key."
  fi
done
#endregion

#region Add jenkins user to docker group
if grep "^docker:" /etc/group |grep -q ":jenkins"; then
  PrintOkIndicator "Jenkins user is already added to the Docker group."
else
  function AddJenkinsUserToDockerGroup {
    usermod -a -G docker jenkins
  }

  function RestartJenkins {
    systemctl restart jenkins.service
  }

  Run "AddJenkinsUserToDockerGroup" \
    "Adding Jenkins user to Docker group..." \
    "Failed to add Jenkins user to Docker group." \
    "Added Jenkins user to Docker group."

  Run "RestartJenkins" \
    "Restarting Jenkins..." \
    "Failed to restart Jenkins." \
    "Restarted Jenkins."
fi
#endregion

#region Add dummy0 interface
if [ -f /etc/network/interfaces.d/dummy0.interface ]; then
  PrintOkIndicator "Network interface dummy0 has already been configured."
else
  function CopyInterfaceFile {
    cp ./auto/dummy0.interface /etc/network/interfaces.d
  }

  Run "CopyInterfaceFile" \
    "Configuring network interface dummy0..." \
    "Failed to configure network interface dummy0." \
    "Network interface dummy0 has been configured."
fi
#endregion

#region Start network interface dummy0
if ip a show dummy0 2>/dev/null > /dev/null; then
  PrintOkIndicator "Network interface dummy0 is already started."
else
  Run "ifup dummy0" \
    "Starting network interface dummy0..." \
    "Failed to start network interface dummy0." \
    "Started network interface dummy0."
fi
#endregion

#region Install Docker Registry
if [ -f /etc/docker/daemon.json ]; then
  PrintOkIndicator "Docker Registry has already been configured."
else
  function CreateDockerRegistryConfig {
    cp ./auto/daemon.json /etc/docker/
  }

  function RestartDocker {
    systemctl restart docker.service
  }

  Run "CreateDockerRegistryConfig" \
    "Configuring Docker Registry..." \
    "Failed to configure Docker Registry." \
    "Docker registry has been configured."

  Run "RestartDocker" \
    "Restarting Docker..." \
    "Failed to restart Docker." \
    "Restarted Docker."
fi
#endregion

#region Pull image if it doesn't exist locally.
if docker image inspect registry:2.7 > /dev/null 2>&1; then
  PrintOkIndicator "Docker Registry image has already been pulled."
else
  function PullDockerRegistryImage {
    docker pull registry:2.7
  }

  Run "PullDockerRegistryImage" \
    "Pulling Docker Registry image..." \
    "Failed to pull Docker Registry image." \
    "Docker Registry image has been pulled."
fi
#endregion

#region Start Docker Registry
if docker container inspect registry > /dev/null 2>&1; then
  PrintOkIndicator "Docker Registry is already running."
else
  function StartDockerRegistry {
    docker run -d -p 5000:5000 --restart always --name registry registry:2.7
  }

  Run "StartDockerRegistry" \
    "Starting Docker Registry..." \
    "Failed to start Docker Registry." \
    "Docker Registry has been started."
fi
#endregion

echo
echo "Part 1 of the installer is now done."
echo "Please run part two (2-jenkins.sh) to set up Jenkins."

# Create marker file
CreateMarkerFile 1