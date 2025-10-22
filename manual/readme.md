> [!CAUTION]
> This project is an **independent build script for NOTvyos**.
> It is **not affiliated with, endorsed by, or sponsored by VyOS Networks Corporation** by any means.
> VyOS® is a registered trademark of VyOS Networks Corporation.

Manual guide
==

**No longer updated.** It's recommended to use automated scripts instead.

General expectations
--

Unless specified otherwise all commands/scripts in the instructions should run as `root`.
If you don't use root account then use `sudo -i` from your user to switch to root.
Where other user is expected we provide note and `su` command.

The current working directory doesn't matter unless specified with `cd`.

The build system was designed to use 3 or more machines that's why some steps may seem a bit unusual.
This guide merges everything to single host under single user to make it simpler and faster to get started.
You may use another machine as build node for Jenkins (or multiple nodes), you may also use another machine
for reprepro but here it's assumed everything is one host under one user.

Before you install Jenkins, create its user and group
--

Most of Jenkinfiles do respect your UID/GID but not all, for
example [linux-kernel/Jenkinsfile](https://github.com/vyos/vyos-build/blob/equuleus/packages/linux-kernel/Jenkinsfile)
has hardcoded UID and GID to 1006 and this will fail build if you don't have 1006:1006 user.

That's why we want to create jenkins user and group with ID 1006 before installing Jenkins from apt.

```bash
groupadd --system --gid 1006 jenkins
useradd --system --comment Jenkins --shell /bin/bash --uid 1006 --gid 1006 --home-dir /var/lib/jenkins jenkins
```

If you have already existing user then please [change its UID/GID](extras/legacy-uid-gid.md).

Install Jenkins, and its java
--

Install java, then Jenkins. Let setup guide to install recommended plugins.

Just follow the usual guide via APT https://www.jenkins.io/doc/book/installing/linux/#debianubuntu

Install docker
--

Just follow the usual guide via APT https://docs.docker.com/engine/install/debian/

Allow Jenkins to use docker:

```bash
usermod -a -G docker jenkins
```

Setup local IP
--

This guide will simplify the unknown by using static IP on dummy interface, this is hopefully outside your subnet if
not please change all references of this IP with your own.

```bash
cat << EOT >> /etc/network/interfaces

auto dummy0
iface dummy0 inet static
    address 172.17.17.17/32
    pre-up ip link add dummy0 type dummy
EOT
```

```bash
ifup dummy0
```

Now we can locally point to known IP `172.17.17.17` as it was the host itself.

After adding docker group and/or after UID/GID change restart Jenkins
--

```bash
systemctl restart jenkins.service
```

Launch local registry and set it, so it always runs when Docker runs
--

```bash
docker run -d -p 5000:5000 --restart always --name registry registry:2.7
```

**Allow insecure docker access to local registry:**

Add your local IP with 5000 port to `insecure-registries` section in `/etc/docker/daemon.json`, something like this:

```bash
cat << EOF > /etc/docker/daemon.json
{
   "insecure-registries": [
      "172.17.17.17:5000"
   ]
}
EOF
```

Then restart docker:

```bash
systemctl restart docker.service
```

Install apt-cacher-ng for ELTS mirror
--

This is currently used only by equuleus.

```bash
apt install apt-cacher-ng
```

This will allow us to use `http://172.17.17.17:3142/deb.freexian.com/extended-lts` as ELTS mirror.

Build patched vyos-build docker images
--

The vyos/vyos-build docker image from dockerhub doesn't work for all packages as of now, thus we made some
patches to make it work. If this changed in future then this step can be skipped.

The below script clones the (patched) vyos-build, then builds and pushes the images to your custom Docker repository.

```bash
#!/usr/bin/env bash
set -e

CUSTOM_DOCKER_REPO="172.17.17.17:5000"
ELTS_MIRROR="http://172.17.17.17:3142/deb.freexian.com/extended-lts"

#
# Clone (patched) vyos-build

git clone https://github.com/dd010101/vyos-build.git
cd vyos-build/docker

#
# Build and Push equuleus

git checkout equuleus
docker build --build-arg "ELTS_MIRROR=$ELTS_MIRROR" \
    --no-cache -t vyos/vyos-build:equuleus .

docker tag vyos/vyos-build:equuleus ${CUSTOM_DOCKER_REPO}/vyos/vyos-build:equuleus
docker push ${CUSTOM_DOCKER_REPO}/vyos/vyos-build:equuleus

#
# Build and Push sagitta

git checkout sagitta
docker build --no-cache -t vyos/vyos-build:sagitta .

docker tag vyos/vyos-build:sagitta ${CUSTOM_DOCKER_REPO}/vyos/vyos-build:sagitta
docker push ${CUSTOM_DOCKER_REPO}/vyos/vyos-build:sagitta

#
# Build and Push current -- (current is required for some sagitta packages)

git checkout current
docker build --no-cache -t vyos/vyos-build:current .

docker tag vyos/vyos-build:current ${CUSTOM_DOCKER_REPO}/vyos/vyos-build:current
docker push ${CUSTOM_DOCKER_REPO}/vyos/vyos-build:current
```

Install Jenkins plugins
--
**Manage Jenkins -> Plugins -> Available plugins**

- Docker
- Docker Pipeline
- Copy Artifact
- SSH Agent
- Pipeline Utility Steps
- Job DSL

Configure Built-In node
--
**Manage Jenkins -> Nodes -> Built-In Node**

**Add labels (tags)**

- Docker
- docker
- ec2_amd64

Separated by space thus "Docker docker ec2_amd64" as result

Configure Jenkins System
--
**Manage Jenkins -> System**

**Global properties -> Environmental Variables -> Add**

> **Name:** DEV_PACKAGES_VYOS_NET_HOST\
> **Value:** jenkins@172.17.17.17

This user+IP/host will be used for SSH access to reprepro, it can be another host, we use the host itself,
this IP needs to be accessible from docker container thus this should be LAN IP not localhost.

**Global properties -> Environmental Variables -> Add**


> **Name:** ARM64_BUILD_DISABLED\
> **Value:** true

This is used to disable ARM64 support. The vyos-build expects that you have ARM64 build node and that's not
something that is easy to obtain or emulate on x86. If you have ARM64 build node then skip this step and make sure
your ARM64 node has tag `ec2_arm64`. If you try to build ARM64 without ARM node then most sagitta builds will wait
and eventually fail.

**Global properties -> Environmental Variables -> Add**

> **Name:** CUSTOM_BUILD_CHECK_DISABLED\
> **Value:** true

This is used to disable custom build check. Custom build check would normally skip upload to reprepro repository
if package is built from non-vyos repository. Unfortunately currently it's impossible to build all packages
from VyOS repositories, and thus we need to use custom repositories. Because some packages don't have
functional build scripts or don't exist at all. This check doesn't make sense anyway since we are using our
reprepro repository.

**Global properties -> Environmental Variables -> Add**

> **Name:** CUSTOM_DOCKER_REPO\
> **Value:** 172.17.17.17:5000

This variable is used to specify local docker registry for automatic `vyos-build` docker image rebuild.

**Global Pipeline Libraries -> Add**

> **Name:** vyos-build\
> **Project** repository: https://github.com/dd010101/vyos-build.git

Currently patched version of vyos-build is required, in the future the official
`https://github.com/vyos/vyos-build.git` may work but doesn't currently.

Note for developers: equuleus is using only equuleus branch of vyos-build but sagitta is using both sagitta and
current, thus if you fix something aimed at sagitta, you need to backports these changes to current as well,
since some packages will use current and some sagitta branch.

**Declarative Pipeline (Docker)**

> **Docker registry URL:** http://172.17.17.17:5000

This is required to tell Jenkins to use your own (patched) vyos-build docker image and not the DockerHub version.

Credentials for ssh-agent
--
You need to set up SSH key authentication for the host specified in `DEV_PACKAGES_VYOS_NET_HOST` variable.
Basically we want to allow Jenkins to SSH into itself with its own SSH key.

Login as target user:

```bash
su - jenkins
```

Generate regular SSH key:

```bash
ssh-keygen -t ed25519 -C "jenkins"
```

Update authenticated_keys to allow Jenkins to log in to itself, something like this:

```bash
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
```

Accept signature and verify SSH works:

```bash
ssh 172.17.17.17
```

Then you can add this private key to Jenkins:

**Manage Jenkins -> Credentials -> System -> Global credentials (unrestricted) -> Add Credentials**

> **Kind:** SSH Username with private key\
> **ID:** SSH-dev.packages.vyos.net\
> **Username:** jenkins

**Private Key -> Enter directly -> Add**

> <paste private key of the generated ssh key like the contents of cat ~/.ssh/id_ed25519>

Preparation for reprepro SSH host
--

Install some packages:

```bash
apt install reprepro gpg
```

Generate GPG signing key (without passphrase):

```bash
sudo -u jenkins gpg --pinentry-mode loopback --full-gen-key
```

This key **needs to be without passphrase**. The reprepro uses this key in background thus there is no way to enter
passphrase.

Remember your pub key, it's random string like "934824D5C6A72DA964B3AFBD27A7E25D86BB7E2A".

Create expected folder structure, prepare reprepro config and give Jenkins access, this is done for each release
codename.

Set SIGN_PUB_KEY:

```bash
export SIGN_PUB_KEY="<pub key idenitifier from step above>"
```

Set RELEASE name:

```bash
export RELEASE=equuleus
```

or

```bash
export RELEASE=sagitta
```

Then create reprepro repository for each RELEASE:

```bash
export REPOSITORY=/home/sentrium/web/dev.packages.vyos.net/public_html/repositories/$RELEASE
mkdir -p $REPOSITORY
mkdir $REPOSITORY/conf

cat << EOF > $REPOSITORY/conf/distributions
Origin: $RELEASE
Label: $RELEASE
Codename: $RELEASE
Architectures: source amd64
Components: main
Description: $RELEASE
SignWith: $SIGN_PUB_KEY
EOF

cat << EOF > $REPOSITORY/conf/options
verbose
EOF

chown -R jenkins:jenkins /home/sentrium
```

uncron
--
This is required addition for the reprepro.

**Install dependencies**

```bash
apt install opam ocaml socat
```

**Login as reprepro user and build uncon, then exit (if asked - confirm defaults)**

You may have default opem switch already, then you will
see `[ERROR] There already is an installed switch named default` -
if you do then ignore this message and continue.

```bash
su - jenkins

git clone https://github.com/vyos/uncron.git
cd uncron

opam init
opam switch create default 4.13.1
eval $(opam env --switch=default)
opam install lwt lwt_ppx logs containers
eval $(opam env)

dune build
exit
```

**Setup uncron service**

```bash
cp /var/lib/jenkins/uncron/_build/install/default/bin/uncron /usr/local/sbin/

cat <<'EHLO' > /etc/systemd/system/uncron.service
[Unit]
Description=Command Queue Service
After=auditd.service systemd-user-sessions.service time-sync.target

[Service]
EnvironmentFile=/etc/uncron.conf
ExecStart=/usr/local/sbin/uncron
ExecReload=/bin/kill -HUP $MAINPID
KillMode=process
User=jenkins
Group=jenkins
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EHLO

touch /etc/uncron.conf

systemctl daemon-reload
systemctl enable --now uncron.service

chmod +x /var/lib/jenkins/uncron/src/uncron-add
```

**Create uncron-add script**

We also use this as hack to fix some of VyOS packaging issues.

```bash
cat << 'EOF' > /usr/local/bin/uncron-add
#!/usr/bin/env bash
set -e

COMMAND="$1"

# this is hack to workaround a issue where vyos didn't create sagitta branch
# like the case of vyos-xe-guest-utilities, thus we need to build current
# branch and then redirect from here to sagitta repository
if [ ! -L ~/VyOS/current ]; then
    rm -rf ~/VyOS/current
    mkdir -p ~/VyOS/sagitta
    ln -s ~/VyOS/sagitta ~/VyOS/current
fi
if [[ "$COMMAND" == *"repositories/current"* ]]; then
    COMMAND=${COMMAND//current/sagitta}
fi
if [[ "$COMMAND" == *"vyos-xe-guest-utilities"* ]] && [[ "$COMMAND" == *"current"* ]]; then
    COMMAND=${COMMAND//current/sagitta}
fi

/var/lib/jenkins/uncron/src/uncron-add "$COMMAND"
EOF

chmod +x /usr/local/bin/uncron-add
```

Multibranch Pipelines (by script)
--

Script exists to automate pipeline/job creation.

**Generate Jenkins API token:**

**User account (click on your username - top-right corner) -> Configure**\
**API Token -> Current token(s) -> Add new Token**

> **Name:** CLI\
> -> [Generate] -> [copy generated key and save it for later use]

**Get the script**

```bash
git clone https://github.com/dd010101/vyos-jenkins.git
cd vyos-jenkins/manual
```

**Install dependencies**

```bash
apt install -y xmlstarlet jq
```

**Adjust settings to suit your Jenkins**

```bash
export JENKINS_USER=<your-username>
export JENKINS_TOKEN=<your-token>
```

**If you want to build only specific branch**

Configure `BRANCH` environment variable to desired branch before you run the script.
Not defined or empty value means all branches (the default).

```bash
export BRANCH="sagitta"
```

**Create jobs**

Then wait for branch indexing to complete.

```bash
./seed-jobs.sh create
```

**After branch indexing you can trigger build for everything**

Make sure you have >=16GB RAM or 8GB RAM + 8GB swap, since running build for everything like this eats more memory
than building one by one this is also dependent on how many Number of executors you have.

```bash
./seed-jobs.sh build
```

Now wait for build to complete and check Build History and Dashboard for failed builds. If you find any failed
builds then read Console Output to see why it did failed.

This process is required only once. After you create Jenkins jobs, and you do first build then Jenkins will
periodically check if GIT repository for job changed and will do automatically build given job/packages.

You can also create Multibranch Pipelines manually, [see bellow](#multibranch-pipelines-manual).

Mirror preparation
--

Use the default procedure to build ISO (via docker) but you need to specify your `--vyos-mirror` and your gpg
signing key `--custom-apt-key`.

To make `--vyos-mirror` is easy, you just install your favorite webserver and point the webroot
to `/home/sentrium/web/dev.packages.vyos.net/public_html/repositories/`. For example nginx vhost looks
something like this:

```
server {
	listen 80;
	listen [::]:80;

	root /home/sentrium/web/dev.packages.vyos.net/public_html/repositories;
	autoindex on;

	server_name _;

	location / {
		try_files $uri $uri/ =404;
	}

	location ~ /(.*)/conf {
		deny all;
	}

	location ~ /(.*)/db {
		deny all;
	}
}
```

This will give you HTTP APT repository, like this `http://172.17.17.17/equuleus`.

To create `--custom-apt-key` you need to export your gpg signing public key, for example:

```bash
sudo -u jenkins gpg --armor --output /home/sentrium/web/dev.packages.vyos.net/public_html/repositories/apt.gpg.key \
  --export-options export-minimal --export vyos
```

This will give you `/home/sentrium/web/dev.packages.vyos.net/public_html/repositories/apt.gpg.key` or
`http://172.17.17.17/apt.gpg.key`.

If you have the `--vyos-mirror` URL of your own repository and your own signing key `--custom-apt-key` then you
can use these two pieces to build ISO from your own package mirror.

How to build ISO
--

Complete instructions to illustrate how to build ISO via Docker method included with the extra options outline above.

We assume you already have Docker running if not follow
the [official instructions](https://docs.docker.com/engine/install/debian/) for your OS.

**Obtain the sources:**

```bash
git clone https://github.com/dd010101/vyos-build
cd vyos-build
```

**Select branch of your choice**

For all following steps will use BRANCH environment variable since the branch repeats a lot.

```bash
export BRANCH=equuleus
```

or

```bash
export BRANCH=sagitta
```

**Switch to branch**

```bash
git checkout "$BRANCH"
```

**Clear previous build resources (if any)**

There is `make clean` but that doesn't always clean everything and may produce corrupted build environment.
The `make clean` is trying to remove specific parts of `build` directory, but it doesn't always do so correctly.
This happens mainly if you switch branches - that's why it's better to always delete the whole `build` directory.

```bash
rm -rf build/
```

**Obtain vyos-build docker container**

You can reuse your docker container image if you already
have [custom registry](#launch-local-registry-and-set-it-so-it-always-runs-when-docker-runs)
with [patched vyos-build docker container](#build-patched-vyos-build-docker-images).

Change the registry URL if you build on other machine.

```bash
docker pull "172.17.17.17:5000/vyos/vyos-build:$BRANCH"
docker tag "172.17.17.17:5000/vyos/vyos-build:$BRANCH" "vyos/vyos-build:$BRANCH"
```

If you don't have custom registry then build the container - this will take a while:

```bash
docker build -t "vyos/vyos-build:$BRANCH" docker
```

You should rebuild the container from time to time - not very frequently but sometimes the build will break
if you have too old container.

**Obtain apt signing key for your custom mirror**

```bash
wget http://172.17.17.17/apt.gpg.key -O /tmp/apt.gpg.key
```

**Launch the vyos-build docker container**

This is the usual run command from official documentation, we need to add extra mount for our apt signing key
for later use via `-v "/tmp/apt.gpg.key:/opt/apt.gpg.key"`.

The docker run command will mount current working directory for use inside the container that's why you need to
execute this command inside the `vyos-build` directory (that is the GIT repository you cloned above).
You can also replace the `-v "$(pwd)":/vyos` with static path if you like not to depend on current directory
(for example `-v /opt/vyos-build:/vyos`).

```bash
docker run --rm -it \
    -v "$(pwd)":/vyos \
    -v "/tmp/apt.gpg.key:/opt/apt.gpg.key" \
    -w /vyos --privileged --sysctl net.ipv6.conf.lo.disable_ipv6=0 \
    -e GOSU_UID=$(id -u) -e GOSU_GID=$(id -g) \
    "vyos/vyos-build:$BRANCH" bash
```

Now we should be inside the container.

**Configure and build the ISO**

Command for configuring changed over time, equuleus has `./configure`, sagitta has `./build-vyos-image iso` instead.

You may want to customize the configuration options, see what is available:

For equuleus:

```bash
sudo ./configure --help
```

For sagitta:

```bash
sudo ./build-vyos-image --help
```

We need to add extra two options to configure `--vyos-mirror` and `--custom-apt-key`. We also add smoketest
via `--custom-package vyos-1x-smoketest` for good measure.

Here are examples - please adjust options to your liking:

For equuleus:

```bash
sudo ./configure --architecture amd64 --build-by "myself@localhost" \
   --build-type release --version "1.3.x" \
   --vyos-mirror http://172.17.17.17/equuleus --custom-apt-key /opt/apt.gpg.key \
   --debian-elts-mirror http://172.17.17.17:3142/deb.freexian.com/extended-lts \
   --custom-package vyos-1x-smoketest \
   && sudo make iso
```

For sagitta:

```bash
sudo ./build-vyos-image iso --architecture amd64 --build-by "myself@localhost" \
   --build-type release --version "1.4.x" \
   --vyos-mirror http://172.17.17.17/sagitta --custom-apt-key /opt/apt.gpg.key \
   --custom-package vyos-1x-smoketest
```

This will take a while - after all is done then you can `exit` the container and you should have
`build/live-image-amd64.hybrid.iso`.

Multibranch Pipelines (manual)
--

Use + button on Jenkins dashboard to add Multibranch Pipeline. Each Jenkinsfile needs its own Multibranch Pipeline,
the setup is the same for all packages, and you just adjust location of Jenkinsfile and/or GIT repository to whatever
you want to build. See packages info bellow for list of all GIT repository and location their Jenkinsfile.

It makes sense to configure one pipeline and then use "Copy from" and just change the Jenkinsfile location and/or GIT
repository. Start with something small like dropbear, and after you verify your setup works then try the bigger stuff
like linux-kernel.

There are two types of configurations - first you have single shared GIT repository with many Jenkinsfile, like
the https://github.com/vyos/vyos-build.git, thus each pipeline points to different Jenkinsfile, but they share same GIT
url. Rest of the packages have their own GIT repository with single root Jenkinsfile, thus the Jenkinsfile stays
"Jenkinsfile" and you change the GIT url only. The https://github.com/vyos/vyos-build.git repository has also its own
root Jenkinsfile - ignore it since that one is trying to build ISO with default (blocked) apt mirror.

You can see all packages and information about them in the [packages.md](extras/packages.md) file.

**Branch Sources -> Add source -> Git**

> **Project Repository:** https://github.com/vyos/vyos-build.git

(or any other repository, like https://github.com/vyos/vyos-1x.git)

You may want to restrict to only branches you care about, thus:

**Behaviours -> Add -> Filter by name (with regular expression)**

> *Regular expression:** (equuleus|sagitta)

**Behaviours -> Add -> Advanced clone behaviours**

> **Fetch tags:** [✓]

(leave defaults)

Advanced clone is required for some packages to obtain all tags (specifically `vyos-cloud-init` and `vyos-1x`).
It doesn't hurt to have advanced clone for everything, thus you can set-it and copy for everything without
worrying about what to use it for.

**Build Configuration -> Mode (by Jenkinsfile)**

> **Script Path:** packages/dropbear/Jenkinsfile

(if you want to build package from vyos/vyos-build repository)

> **Script Path:** Jenkinsfile

(or leave just Jenkinsfile if you want to build repository like vyos/vyos-1x where there is just one package)

**Scan Multibranch Pipeline Triggers**

> [✓] **Periodically if not otherwise run**
>
> **Interval:** 1 hour

Jenkins will check the source GIT repository if changes were made and execute automatic build if needed. This
will keep packages up to date.

Try to build
--

Now it's possible to select some **Multibranch Pipeline**, select your **branch**, and you can press build button
to see what happens! If all is well you should see .deb appearing in
`/home/sentrium/web/dev.packages.vyos.net/public_html/repositories/`:

```bash
find /home/sentrium/web/dev.packages.vyos.net/public_html/repositories/ -name '*.deb' -print
```

If build fails then click the specific build number and check **Console Output** for hints why it does so.
