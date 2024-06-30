#!/usr/bin/env bash

source ./auto/helper-logic

# Clear the screen and print the header
PrintHeader "2-jenkins.sh"

# Ensure we are running as root
EnsureRoot

# Ensure stage 1 is complete
EnsureStageIsComplete 1

# Define variables
INITIAL_PASSWORD_FILE="/var/lib/jenkins/secrets/initialAdminPassword"
NETWORK_INTERFACES=`ls /sys/class/net/ -1 |grep -v -w "lo" |grep -v docker |grep -v dummy |grep -v veth`

#region Run SSH script
cp ./auto/ssh-script.sh /var/lib/jenkins
chown jenkins:jenkins /var/lib/jenkins/ssh-script.sh

# This script create the SSH key, adds it to the trusted keys and trusts the host itself.
echo "Running SSH script as jenkins user..."
runuser -l jenkins -c "./ssh-script.sh"
echo

rm /var/lib/jenkins/ssh-script.sh > /dev/null 2>&1
#endregion

#region Run GnuPG script
cp ./auto/gpg-script.sh /var/lib/jenkins
chown jenkins:jenkins /var/lib/jenkins/gpg-script.sh

# This script generates the GnuPG key pair.
echo "Running GnuPG script as jenkins user..."
runuser -l jenkins -c "./gpg-script.sh"
echo

rm /var/lib/jenkins/gpg-script.sh > /dev/null 2>&1
#endregion

#region Initial Jenkins user setup and ask for credentials
function PrintUrls {
  echo
  for INTERFACE in $NETWORK_INTERFACES; do
    IP_ADDRESS=`ifconfig $INTERFACE | grep 'inet '| cut -d: -f2 | awk '{ print $2}'`
    if [[ $IP_ADDRESS != "" ]]; then
      echo -e "${GREEN}http://$IP_ADDRESS:8080$1${NOCOLOR}"
    fi
  done
  echo
}

if [ -f $INITIAL_PASSWORD_FILE ]; then
  # This is the first run (or the previous run never made it to finish creating an admin user).
  INITIAL_PASSWORD=`cat /var/lib/jenkins/secrets/initialAdminPassword`

  echo -e "Please open a web browser, and go to one of these URLs:"
  PrintUrls
  echo -e "Then, login using this password: ${GREEN}$INITIAL_PASSWORD${NOCOLOR}"
  echo
  read -p "Press enter when you are logged on."
  echo
  echo -e "Now click the \"${GREEN}Install suggested plugins${NOCOLOR}\" button"
  echo
  read -p "Press enter when the plugins are done installing."
  echo
  echo "When prompted, create the first admin user."
  echo
  read -p "Please enter the username you choose here, and press enter: " USERNAME
  echo
  echo "Just leave the default url, and continue until you are greeted with the Welcome page."
  echo
else
  # This is a re-run, so the admin user has already been created.
  if ([ ! -f $USERNAME_FILE ] || [ ! -f $TOKEN_FILE ]); then
    # There is no USERNAME_FILE or TOKEN_FILE, so we ask the user to provide the username.
    echo -e "Please open a web browser, and go to one of these URLs:"
    PrintUrls
    echo -e "Then, login using the credentials you have created before."
    echo
    read -p "Please enter your username here: " USERNAME
    echo
  fi
fi

if ([ ! -f $USERNAME_FILE ] || [ ! -f $TOKEN_FILE ]); then
  # There is no USERNAME_FILE or TOKEN_FILE, so we ask the user to provide the token.
  echo
  echo "If you already have generated a token, and know it, skip this step and just enter it below instead of creating a new one."
  echo -e "Once you reach the Welcome page, please go to one of these URLs:"
  PrintUrls "/user/$USERNAME/configure"
  echo -e "Here you click the \"${GREEN}Add new Token${NOCOLOR}\" button, followed by the \"${GREEN}Generate${NOCOLOR}\" button (leave the text field empty)."
  echo
  read -p "Please enter the generated token here, and press enter: " TOKEN
  echo
fi

if ([ -f $USERNAME_FILE ] && [ -f $TOKEN_FILE ]); then
  # If we get here, the files already exists (so the user wouldn't have been asked above)
  # So we read them instead.
  USERNAME=`cat $USERNAME_FILE`
  TOKEN=`cat $TOKEN_FILE`
fi
#endregion

# Ensure the Jenkins CLI has been downloaded.
EnsureJenkinsCli

# Test the connection to make sure Jenkins is ready.
TestJenkinsConnection $USERNAME $TOKEN

#region Install needed plugins
# If we make it here, we know the username and token is valid, and Jenkins is running.
echo "Installing plugins..."
echo

declare -A plugins
plugins["docker-plugin"]="Docker"
plugins["docker-workflow"]="Docker Pipeline"
plugins["copyartifact"]="Copy Artifact"
plugins["ssh-agent"]="SSH Agent"
plugins["pipeline-utility-steps"]="Pipeline Utility Steps"
plugins["job-dsl"]="Job DSL"

for key in "${!plugins[@]}"
do
  if (java -jar jenkins-cli.jar -s http://172.17.17.17:8080 -auth $USERNAME:$TOKEN list-plugins $key > /dev/null 2>&1); then
    PrintOkIndicator "$key is already installed."
  else
    function InstallPlugin {
      java -jar jenkins-cli.jar -s http://172.17.17.17:8080 -auth $USERNAME:$TOKEN install-plugin $1 -deploy
    }

    Run "InstallPlugin $key" \
      "Installing $key plugin..." \
      "Failed to install $key plugin." \
      "Installed $key plugin."
  fi
done

echo
#endregion

#region Configure number of executors
# Find the number of CPU cores available to the machine.
NUMBER_OF_CPU_CORES="$(nproc)"

# If the number is less than 4, we bump it up to 4.
NUMBER_OF_CPU_CORES=$(( $NUMBER_OF_CPU_CORES < 4 ? 4 : $NUMBER_OF_CPU_CORES))

# Does the number of exectutors match the number of CPU cores?
if [ "$(xmlstarlet sel -t -v '//numExecutors' -n /var/lib/jenkins/config.xml 2>/dev/null)" -eq $NUMBER_OF_CPU_CORES ]; then
  # Yep.
  PrintOkIndicator "Executors already set to ${NUMBER_OF_CPU_CORES}."
else
  # Nope, so we stop Jenkins
  StopJenkins

  function ChangeExecutorCount {
    # We need to send 2 to /dev/null, since xmlstarlet prints warnings about xml version to stderr.
    xmlstarlet ed -L -u "/hudson/numExecutors" -v "$1" $JENKINS_CONFIG_FILE 2>/dev/null
  }

  # Then we update the config to match the number of CPU cores.
  Run "ChangeExecutorCount ${NUMBER_OF_CPU_CORES}" \
    "Changing executor count to ${NUMBER_OF_CPU_CORES}..." \
    "Failed to change executor count to ${NUMBER_OF_CPU_CORES}." \
    "Changed executor count to ${NUMBER_OF_CPU_CORES}."
fi
#endregion

#region Configure labels
# Has the labels been configured?
if grep -q ec2_amd64 $JENKINS_CONFIG_FILE; then
  # Yep.
  PrintOkIndicator "Labels are already configured."
else
  # Nope, so we stop Jenkins
  StopJenkins

  function ConfigureLabels {
    # We need to send 2 to /dev/null, since xmlstarlet prints warnings about xml version to stderr.
    xmlstarlet ed -L -u "/hudson/label" -v "Docker docker ec2_amd64" $JENKINS_CONFIG_FILE 2>/dev/null
  }

  # Then we update the config to include the labels.
  Run "ConfigureLabels" \
    "Configuring labels..." \
    "Failed to configure labels." \
    "Configured labels."
fi
#endregion

#region Configure environment variables
# Does the config contain the environment variables?
if grep -q ARM64_BUILD_DISABLED $JENKINS_CONFIG_FILE; then
  # Yep
  PrintOkIndicator "Environment variables are already configured."
else
  # Nope, so we stop Jenkins
  StopJenkins

  function ConfigureEnvironmentVariables {
    # We need to send 2 to /dev/null, since xmlstarlet prints warnings about xml version to stderr.
    xmlstarlet ed -L -s "/hudson/globalNodeProperties" -t elem -n "hudson.slaves.EnvironmentVariablesNodeProperty" -v "" \
    -s "//hudson.slaves.EnvironmentVariablesNodeProperty" -t elem -n "envVars" -v "" \
    -s "//envVars" -t attr -n "serialization" -v "custom" \
    -s "//envVars" -t elem -n "unserializable-parents" -v "" \
    -s "//envVars" -t elem -n "tree-map" -v "" \
    -s "//tree-map" -t elem -n "default" -v "" \
    -s "//default" -t elem -n "comparator" -v "" \
    -i "//comparator" -t attr -n "class" -v "java.lang.String\$CaseInsensitiveComparator" \
    -s "//tree-map" -t elem -n "int" -v "4" \
    -s "//tree-map" -t elem -n "string" -v "ARM64_BUILD_DISABLED" \
    -s "//tree-map" -t elem -n "string" -v "true" \
    -s "//tree-map" -t elem -n "string" -v "CUSTOM_BUILD_CHECK_DISABLED" \
    -s "//tree-map" -t elem -n "string" -v "true" \
    -s "//tree-map" -t elem -n "string" -v "CUSTOM_DOCKER_REPO" \
    -s "//tree-map" -t elem -n "string" -v "172.17.17.17:5000" \
    -s "//tree-map" -t elem -n "string" -v "DEV_PACKAGES_VYOS_NET_HOST" \
    -s "//tree-map" -t elem -n "string" -v "jenkins@172.17.17.17" \
    $JENKINS_CONFIG_FILE 2>/dev/null
  }

  # Then we update the config to include the environment variables.
  Run "ConfigureEnvironmentVariables" \
    "Configuring environment variables..." \
    "Failed to configure environment variables." \
    "Configured environment variables."
fi
#endregion

#region Configure Global Libraries
# Sometimes the GlobalLibraries config file isn't there yet.
if [ ! -f $JENKINS_GLOBALLIBRARIES_FILE ]; then
  # If that is the case, we copy a clean config into where it should be.
  cp ./auto/org.jenkinsci.plugins.workflow.libs.GlobalLibraries.xml $JENKINS_GLOBALLIBRARIES_FILE
fi

# Is the Global Libraries configured?
if grep -q "vyos-build" $JENKINS_GLOBALLIBRARIES_FILE; then
  # Yep.
  PrintOkIndicator "Global libraries are already configured."
else
  # Nope, so we stop Jenkins
  StopJenkins

  function ConfigureGlobalLibraries {
    # We need to send 2 to /dev/null, since xmlstarlet prints warnings about xml version to stderr.
    xmlstarlet ed -L \
    -d "/org.jenkinsci.plugins.workflow.libs.GlobalLibraries/libraries/@class" \
    -s "/org.jenkinsci.plugins.workflow.libs.GlobalLibraries/libraries" -t elem -n "org.jenkinsci.plugins.workflow.libs.LibraryConfiguration" -v "" \
    -s "//org.jenkinsci.plugins.workflow.libs.LibraryConfiguration" -t elem -n "name" -v "vyos-build" \
    -s "//org.jenkinsci.plugins.workflow.libs.LibraryConfiguration" -t elem -n "retriever" \
    -i "//retriever" -t attr -n "class" -v "org.jenkinsci.plugins.workflow.libs.SCMSourceRetriever" \
    -s "//retriever" -t elem -n "clone" -v "false" \
    -s "//retriever" -t elem -n "scm" \
    -i "//scm" -t attr -n "class" -v "jenkins.plugins.git.GitSCMSource" \
    -i "//scm" -t attr -n "plugin" -v "git@5.2.2" \
    -s "//scm" -t elem -n "id" -v "9d202e32-1889-4391-91e5-1b3445f035fd" \
    -s "//scm" -t elem -n "remote" -v "https://github.com/dd010101/vyos-build.git" \
    -s "//scm" -t elem -n "credentialsId" \
    -s "//scm" -t elem -n "traits" \
    -s "//traits" -t elem -n "jenkins.plugins.git.traits.BranchDiscoveryTrait" \
    -s "//org.jenkinsci.plugins.workflow.libs.LibraryConfiguration" -t elem -n "implicit" -v "false" \
    -s "//org.jenkinsci.plugins.workflow.libs.LibraryConfiguration" -t elem -n "allowVersionOverride" -v "true" \
    -s "//org.jenkinsci.plugins.workflow.libs.LibraryConfiguration" -t elem -n "includeInChangesets" -v "true" \
    $JENKINS_GLOBALLIBRARIES_FILE 2>/dev/null
  }

  # Then we update the config to global libraries configuration.
  Run "ConfigureGlobalLibraries" \
    "Configuring global libraries..." \
    "Failed to configure global libraries." \
    "Configured global libraries."
fi
#endregion

#region Configure Docker Declarative Pipeline
# Sometimes the Docker Declarative config file isn't there yet.
if [ ! -f $JENKINS_DOCKERDECLARATIVE_FILE ]; then
  # If that is the case, we copy a clean config into where it should be.
  cp ./auto/org.jenkinsci.plugins.docker.workflow.declarative.GlobalConfig.xml $JENKINS_DOCKERDECLARATIVE_FILE
fi

# Is the Docker Declarative plugin configured?
if grep -q "172.17.17.17" $JENKINS_DOCKERDECLARATIVE_FILE; then
  # Yep.
  PrintOkIndicator "Docker Declarativ Pipeline is already configured."
else
  # Nope, so we stop Jenkins
  StopJenkins

  function ConfigureDockerDeclarativePipeline {
    # We need to send 2 to /dev/null, since xmlstarlet prints warnings about xml version to stderr.
    xmlstarlet ed -L \
    -s "/org.jenkinsci.plugins.docker.workflow.declarative.GlobalConfig/registry" -t elem -n "url" -v "http://172.17.17.17:5000" \
    $JENKINS_DOCKERDECLARATIVE_FILE 2>/dev/null
  }

  # Then we update the config to global libraries configuration.
  Run "ConfigureDockerDeclarativePipeline" \
    "Configuring Docker Declarativ Pipeline..." \
    "Failed to configure Docker Declarativ Pipeline." \
    "Configured Docker Declarativ Pipeline."
fi
#endregion

# Restart Jenkins if it was stopped.
StartJenkins

#region Add SSH credentials
if (java -jar jenkins-cli.jar -s http://172.17.17.17:8080 -auth $USERNAME:$TOKEN get-credentials-as-xml system::system::jenkins _ SSH-dev.packages.vyos.net > /dev/null 2>&1); then
  PrintOkIndicator "SSH key credential has already been created."
else
  function CreateSshKeyCredential {
    java -jar jenkins-cli.jar -s http://172.17.17.17:8080 -auth $USERNAME:$TOKEN create-credentials-by-xml system::system::jenkins _ << EOF
<com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey plugin="ssh-credentials@337.v395d2403ccd4">
  <scope>GLOBAL</scope>
  <id>SSH-dev.packages.vyos.net</id>
  <description></description>
  <username>jenkins</username>
  <usernameSecret>false</usernameSecret>
  <privateKeySource class="com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey\$DirectEntryPrivateKeySource">
    <privateKey>`cat /var/lib/jenkins/.ssh/id_ed25519`</privateKey>
  </privateKeySource>
</com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey>
EOF
  }

  # We have to create the credential, since it is missing.
  Run "CreateSshKeyCredential" \
    "Creating SSH key credential..." \
    "Failed to create SSH key credential." \
    "SSH key credential has been created."
fi
#endregion

echo
echo "Part 2 of the installer is now done."
echo "Please run part three (3-repositories.sh) to set up the reprepro repositories."

# Create marker file
CreateMarkerFile 2