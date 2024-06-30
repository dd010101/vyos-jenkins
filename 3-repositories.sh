#!/usr/bin/env bash

source ./auto/helper-logic

# Clear the screen and print the header
PrintHeader

# Ensure we are running as root
EnsureRoot

# Ensure stage 2 is complete
EnsureStageIsComplete 2

# Declare variables
declare -a RELEASES=("equuleus" "sagitta")

#region GnuPG signing key
# We need to find the public key, since it should be written into the repo config file.
PrintEmptyIndicator "Getting GnuPG signing key..."
SIGN_PUB_KEY=`GNUPGHOME="/var/lib/jenkins/.gnupg" gpg --list-secret-keys --keyid-format=long 2>&1 | grep --only-matching --extended-regexp "[[:xdigit:]]{40}"`

if [ ! -z $SIGN_PUB_KEY ]; then
  ClearPreviousLine
  PrintOkIndicator "Found GnuPG signing key."
else
  ClearPreviousLine
  PrintErrorIndicator "Failed to find GnuPG signing key."
fi
#endregion

#region Repository folders and files
for release in ${RELEASES[@]}; do
  REPOSITORY=/home/sentrium/web/dev.packages.vyos.net/public_html/repositories/$release

  if [ -d $REPOSITORY ]; then
    PrintOkIndicator "Repository for $release already exists."
  else
    function CreateRepositoryFolder {
      mkdir -p $1/conf
    }

    Run "CreateRepositoryFolder $REPOSITORY" \
      "Creating repository for release $release..." \
      "Failed to create folder for release $release." \
      "Repository for release $release has been created."
  fi

  if [ -f $REPOSITORY/conf/distributions ]; then
    PrintOkIndicator "Distributions file for $release already exists."
  else
    function CreateDistributionsFile {
      cat << EOF > $1/conf/distributions
Origin: $release
Label: $release
Codename: $release
Architectures: source amd64
Components: main
Description: $release
SignWith: $SIGN_PUB_KEY
EOF
    }

    Run "CreateDistributionsFile $REPOSITORY" \
      "Creating distributions file for release $release..." \
      "Failed to create distributions file for release $release." \
      "Distributions file for release $release has been created."
  fi

  if [ -f $REPOSITORY/conf/options ]; then
    PrintOkIndicator "Options file for $release already exists."
  else
    function CreateOptionsFile {
      cat << EOF > $1/conf/options
verbose
EOF
    }

    Run "CreateOptionsFile $REPOSITORY" \
      "Creating options file for release $release..." \
      "Failed to create options file for release $release." \
      "Options file for release $release has been created."
  fi
done
#endregion

#region Install GnuPG signing public key
if [ -f /home/sentrium/web/dev.packages.vyos.net/public_html/repositories/apt.gpg.key ]; then
  PrintOkIndicator "GnuPG key has already been exported."
else
  function ExportGnuPGKey {
    # We need to move 2 to /dev/null to prevent warnings about permissions on the .gnupg folder (they are not important in this case)
    GNUPGHOME="/var/lib/jenkins/.gnupg" gpg --armor --output /home/sentrium/web/dev.packages.vyos.net/public_html/repositories/apt.gpg.key --export-options export-minimal --export vyos 2>&1
  }

  Run "ExportGnuPGKey" \
    "Exporting GnuPG key to file..." \
    "Failed to export GnuPG key to file." \
    "GnuPG key has been exported to file."
fi
#endregion

# Finally we need to make sure the jenkins user and group owns the sentrium folder and all files in it.
chown -R jenkins:jenkins /home/sentrium

echo
echo "Part 3 of the installer is now done."
echo "Please run part four (4-uncron.sh) to set up uncron."

# Create marker file
CreateMarkerFile 3
