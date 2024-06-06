Prologue
--

If you're trying to build VyOS ISO image with the usual way you may see following errors:

```
E: Failed to fetch http://dev.packages.vyos.net/repositories/equuleus/dists/equuleus/InRelease  403  Forbidden [IP: 104.18.30.79 443]
E: The repository 'http://dev.packages.vyos.net/repositories/equuleus equuleus InRelease' is not signed.
E: Failed to fetch http://dev.packages.vyos.net/repositories/sagitta/dists/sagitta/InRelease  403  Forbidden [IP: 104.18.30.79 443]
E: The repository 'http://dev.packages.vyos.net/repositories/sagitta sagitta InRelease' is not signed.
```

You may also see `Sorry, you have been blocked` if you try to visit these links, but you aren't blocked - everyone
is blocked. This is due to [change in VyOS policy](https://blog.vyos.io/community-contributors-userbase-and-lts-builds)
where they don't offer their `dev.packages.vyos.net/repositories` for public anymore. This change applies only to
stable branches (like 1.3 equuleus/1.4 sagitta), you can still build current/development branch as usual with
`dev.packages.vyos.net/repositories`.

You want to continue to use VyOS long term? Then you can switch to current/development branch if you think
that's good idea for your use case. If you like to use stable branch then you would need to obtain
[VyOS subscription](https://vyos.io/subscriptions/support). The only other option currently is to build your own
`dev.packages.vyos.net` package repository and that's what this project is all about.

State
--

Currently, it should be possible to use this information to build all required packages for equuleus and sagitta and
as result you get apt repository that can be used to build ISO images.

The goal of this project is to reproduce package repositories of stable branches formerly available at
`dev.packages.vyos.net`. This isn't exactly possible due to the state of VyOS build system and VyOS packages.
The result isn't exactly the same, but it's nearly identical replacement for `dev.packages.vyos.net` and it
produces ISO images that are expected to be equivalent but of course with any custom image build you need
to verify and test the resulting image yourself.

Thanks to @pittagurneyi for providing build scripts for missing packages.

Host requirements and precautions
--

I recommend stable Debian and dedicated virtual machine for security purposes. This setup isn't isolating the build
from the Jenskins and in theory if you execute malicious build it can compromise your Jenkins and possibly your
host. Thus don't share the Jenkins with other projects and ideally don't share the operating system with anything else
either. This risk isn't likely, but it does exist since you will execute code from GitHub under the jenkins user.

The hardware requirements are significant - 8GB RAM, 200GB HDD and appropriate CPU. You will need 16GB of RAM but
this doesn't need to be RAM, you can do 8GB RAM + 8GB swap, and you will still get good performance this way.

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

```
groupadd --system --gid 1006 jenkins
useradd --system --comment Jenkins --shell /bin/bash --uid 1006 --gid 1006 --home-dir /var/lib/jenkins jenkins
```

If you have already existing user then please [change its UID/GID](legacy-uid-gid.md).

Install Jenkins, and its java
--

Install java, then Jenkins. Let setup guide to install recommended plugins.

Just follow the usual guide via APT https://www.jenkins.io/doc/book/installing/linux/#debianubuntu

Install docker
--

Just follow the usual guide via APT https://docs.docker.com/engine/install/debian/

Allow Jenkins to use docker:

```
usermod -a -G docker jenkins
```

Setup local IP
--

This guide will simplify the unknown by using static IP on dummy interface, this is hopefully outside your subnet if
not please change all references of this IP with your own.

```
cat << EOT >> /etc/network/interfaces

auto dummy0
iface dummy0 inet static
    address 172.17.17.17/32
    pre-up ip link add dummy0 type dummy
EOT
```

```
ifup dummy0
```

Now we can locally point to known IP `172.17.17.17` as it was the host itself.

After adding docker group and/or after UID/GID change restart Jenkins
--

```
systemctl restart jenkins.service
```

Launch local registry and set it, so it always runs when Docker runs
--

```
docker run -d -p 5000:5000 --restart always --name registry registry:2.7
```

**Allow insecure docker access to local registry:**

Add your local IP with 5000 port to `insecure-registries` section in `/etc/docker/daemon.json`, something like this:

```
cat << EOF > /etc/docker/daemon.json
{
   "insecure-registries": [
      "172.17.17.17:5000"
   ]
}
EOF
```

Then restart docker:

```
systemctl restart docker.service
```

Build patched vyos-build docker images
--

The vyos/vyos-build docker image from dockerhub doesn't work for all packages as of now, thus I made some
patches to make it work. If this changed in future then this step can be skipped.

The below script clones the (patched) vyos-build, then builds and pushes the images to your custom Docker repository.

```bash
#!/usr/bin/env bash
set -e

CUSTOM_DOCKER_REPO="172.17.17.17:5000"

#
# Clone (patched) vyos-build

git clone https://github.com/dd010101/vyos-build.git
cd vyos-build/docker

#
# Build and Push equuleus

git checkout equuleus
docker build --no-cache -t vyos/vyos-build:equuleus .

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

Configure environment variables and add global vyos-build Jenkins library
--
**Manage Jenkins -> System**

**Global properties -> Environmental Variables -> Add**

```
Name: DEV_PACKAGES_VYOS_NET_HOST
Value: jenkins@172.17.17.17
```

This user+IP/host will be used for SSH access to reprepro, it can be another host, we use the host itself,
this IP needs to be accesible from docker container thus this should be LAN IP not localhost.

**Global properties -> Environmental Variables -> Add**

```
Name: ARM64_BUILD_DISABLED
Value: true
```

This is used to disable ARM64 support. The vyos-build expects that you have ARM64 build node and that's not
something that is easy to obtain or emulate on x86. If you have ARM64 build node then skip this step and make sure
your ARM64 node has tag `ec2_arm64`. If you try to build ARM64 without ARM node then most sagitta builds will wait
and eventually fail.

**Global properties -> Environmental Variables -> Add**

```
Name: CUSTOM_BUILD_CHECK_DISABLED
Value: true
```

This is used to disable custom build check. Custom build check would normally skip upload to reprepro repository
if package is built from non-vyos repository. Unfortunately VyOS has bugs not only in their build system but as
well in their packages, some packages are also missing, thus it's currently impossible to build all packages
from VyOS repositories, and thus we need to use custom repositories.

**Global properties -> Environmental Variables -> Add**

```
Name: CUSTOM_DOCKER_REPO
Value: 172.17.17.17:5000
```

This variable is used to specify local docker registry for automatic `vyos-build` docker image rebuild,
[see bellow for details](#additional-jobs).

**Global Pipeline Libraries -> Add**

```
Name: vyos-build
Project repository: https://github.com/dd010101/vyos-build.git
```

Currently patched version of vyos-build is required, in the future the official
`https://github.com/vyos/vyos-build.git` may work but doesn't currently.

Note for developers: equuleus is using only equuleus branch of vyos-build but sagitta is using both sagitta and
current, thus if you fix something aimed at sagitta, you need to backports these changes to current as well,
since some packages will use current and some sagitta branch.

**Declarative Pipeline (Docker)**

```
Docker registry URL: http://172.17.17.17:5000
```

This will allow Jenkins to use your own (patched) vyos-build docker image.

Credentials for ssh-agent
--
You need to set up SSH key authentication for the host specified in `DEV_PACKAGES_VYOS_NET_HOST` variable.
Basically we want to allow Jenkins to SSH into itself with its own SSH key.

Login as target user:

```
su - jenkins
```

Generate regular SSH key:

```
ssh-keygen -t ed25519 -C "jenkins"
```

Update authenticated_keys to allow Jenkins to log in to itself, something like this:

```
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
```

Accept signature and verify SSH works:

```
ssh 172.17.17.17
```

Then you can add this private key to Jenkins:

**Manage Jenkins -> Credentials -> System -> Global credentials (unrestricted) -> Add Credentials**

```
Kind: SSH Username with private key
ID: SSH-dev.packages.vyos.net
Username: jenkins
```

**Private Key -> Enter directly -> Add**

```
<paste private key of the generated ssh key like the contents of cat ~/.ssh/id_ed25519>
```

Preparation for reprepro SSH host
--

Install some packages:

```
apt install reprepro gpg
```

Generate GPG singing key (without passphrase):

```
sudo -u jenkins gpg --pinentry-mode loopback --full-gen-key
```

Remember your pub key, it's random string like "934824D5C6A72DA964B3AFBD27A7E25D86BB7E2A".

Create expected folder structure, prepare reprepro config and give Jenkins access, this is done for each release
codename.

Set SIGN_PUB_KEY:

```
export SIGN_PUB_KEY="<pub key idenitifier from step above>"
```

Set RELEASE name:

```
export RELEASE=equuleus
```

or

```
export RELEASE=sagitta
```

...

Then create reprepro repository for each RELEASE:

```
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

```
# install dependencies
apt install opam ocaml socat

# login as reprepro user and build uncon, then exit (if asked - confirm defaults)
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

# setup uncron service
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

We also use this as hack to fix some of VyOS packaging issues.

```
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

Experimental script exists to automate pipeline/job creation.

Check the `jenkins-scripts/seed-jobs.sh` for details.

**Get the script seed-jobs.sh**

And its assets (jobs.json, jobTemplate.xml).

```
git clone git@github.com:dd010101/vyos-jenkins.git
cd vyos-jenkins/jenkins-scripts
```

**Install dependencies**

```
apt install -y xmlstarlet jq
```

**Adjust settings to suit your Jenkins**

```
cat seed-jobs.sh
```

**Create jobs**

Then wait for branch indexing to complete.

```
./seed-jobs.sh create
```

**After branch indexing you can trigger build for everything**

Make sure you have >=16GB RAM or 8GB RAM + 8GB swap, since running build for everything like this eats more memory
than building one by one this is also dependent on how many Number of executors you have.

```
./seed-jobs.sh build
```

Now wait for build to complete and check Build History and Dashboard for failed builds. If you find any failed
builds then read Console Output to see why it did failed.

This process is required only once. After you create Jenkins jobs, and you do first build then Jenkins will
periodically check if GIT repository for job changed and will do automatically build given job/packages.
This setup doesn't require much maintenance, but you will need to do some manual maintenance - for example
you will need to rebuild the docker containers from time to time. There is also possible that some jobs
will change and of course major overhaul is required to add support for next major release of VyOS.

You can also create Multibranch Pipelines manually, [see bellow](#multibranch-pipelines-manual).

How to build ISO
--

Use the default procedure to build ISO (via docker) but you need to specify your `--vyos-mirror` and your gpg
singing key `--custom-apt-key`.

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

To create `--custom-apt-key` you need to export your gpg singing public key, for example:

```
sudo -u jenkins gpg --armor --output /home/sentrium/web/dev.packages.vyos.net/public_html/repositories/apt.gpg.key \
  --export-options export-minimal --export vyos
```

This will give you `/home/sentrium/web/dev.packages.vyos.net/public_html/repositories/apt.gpg.key` or
`http://172.17.17.17/apt.gpg.key`.

How to use your mirror:

1) Download your `apt.gpg.key` to where you want to build your ISO.
2) Mount your `apt.gpg.key` when your run `docker run` by adding `-v /where/is/your/key:/opt/apt.gpg.key`
3) When you run `./configure` (equuleus) or `./build-vyos-image` (sagitta) add your mirror
   `--vyos-mirror http://172.17.17.17/equuleus` or `--vyos-mirror http://172.17.17.17/sagitta` and your singing key
   ` --custom-apt-key /opt/apt.gpg.key`.
4) Now the builder uses your mirror instead of `http://dev.packages.vyos.net/`.

Smoketest
--

It's not bad idea to sanity check your ISO image. This is why VyOS has testing procedure called smoketest.
This test checks mainly configuration, it's not complete test, it will only tell you if something
is very wrong, passed test doesn't mean image will be necessarily fully functional - with that said it's still useful,
just don't put too much trust in it.

You will need host that supports virtualization and thus can run KVM. Main test (`make test`) takes around two hours
to complete, additional tests are significantly faster.

I like to run smoketest individually, there is way to run automated smoketest via `vyos-build/Jenkinsfile` but
that requires Jenkins, and also it starts all tests in parallel thus requiring more RAM since multiple virtual
machines run in parallel.

There is requirement to include `vyos-1x-smoketest` package in your ISO image build. By default, ISO build doesn't
include smoketest thus you need to include it via the usual parameter for custom packages.
When you run `./configure` (equuleus) or `./build-vyos-image` (sagitta) add `--custom-package vyos-1x-smoketest`.

If you have your image with smoketest then you can test it. If you did build it yourself, then your likely already
have clone of `vyos-build` repository.

If not clone it and switch to your branch.

```
git clone https://github.com/dd010101/vyos-build.git
cd vyos-build

# pick one
git checkout sagitta
git checkout equuleus
```

There is known issue with smoketest that it will fail if you have too many CPU cores/threads. The test is designed
to use half of your cores, but it will fail if calculates more than 4, thus if you have 8 or more cores/threads
then test likely will fail. If you do apply this patch to cap cores to 3:

```
sed -i 's~cpu /= 2~cpu = 3~' scripts/check-qemu-install
```

More cores don't increase speed, the test is single threas anyway, it usually uses <2 cores and thus 3 is more than
enough. More cores will not speed up the test - it will only make the test fail due to OOM
inside the test virtual machine.

If you did build your image, then you should have `build` directory and there should be your ISO as
`live-image-amd64.hybrid.iso`. If you want to test arbitrary ISO then you can plant whatever ISO into
the expected path `build/live-image-amd64.hybrid.iso`. You of course need ISO image that includes
`vyos-1x-smoketest` package.

Install dependencies:

```
apt install qemu-kvm python3-tomli python3-pexpect
```

And then you can launch virtual machine to do tests thing via `make`. There are multiple tests:

CLI configuration test

```
make test
```

Configuration file load test

```
make testc
```

RAID1 test

```
make testraid
```

You can as well run smoketest directly from installed VyOS, but you need many network interfaces otherwise
some tests will fail. The test is expecting 8 or more network ports. You do it by simply including
`vyos-1x-smoketest` package in your ISO image build. Then you can boot and run `vyos-smoketest`.
I'm not sure if all 8 are required but with few the test will fail for sure.

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

**Branch Sources -> Add source -> Git**

```
Project Repository: https://github.com/vyos/vyos-build.git
```

(or any other repository, like https://github.com/vyos/vyos-1x.git)

You may want to restrict to only branches you care about, thus:

**Behaviours -> Add -> Filter by name (with regular expression)**

```
Regular expression: (equuleus|sagitta)
```

**Behaviours -> Add -> Advanced clone behaviours**

```
Fetch tags: [✓]
```

(leave defaults)

Advanced clone is required for some packages to obtain all tags (specifically `vyos-cloud-init` and `vyos-1x`).
It doesn't hurt to have advanced clone for everything, thus you can set-it and copy for everything without
worrying about what to use it for.

**Build Configuration -> Mode (by Jenkinsfile)**

```
Script Path: packages/dropbear/Jenkinsfile
```

(if you want to bulild package from vyos/vyos-build repository)

```
Script Path: Jenkinsfile
```

(or leave just Jenkinsfile if you want to build repository like vyos/vyos-1x where there is just one package)

**Scan Multibranch Pipeline Triggers**

```
[✓] Periodically if not otherwise run

Interval: 1 hour
```

Jenkins will check the source GIT repository if changes were made and execute automatic build if needed. This
will keep packages up to date.

Try to build
--

Now it's possible to select some **Multibranch Pipeline**, select your **branch**, and you can press build button
to see what happens! If all is well you should see .deb appearing in
`/home/sentrium/web/dev.packages.vyos.net/public_html/repositories/`:

```
find /home/sentrium/web/dev.packages.vyos.net/public_html/repositories/ -name '*.deb' -print
```

If build fails then click the specific build number and check **Console Output** for hints why it does so.

Package info for equuleus
--

List of required packages and their Jenkinsfile:

Some packages aren't in the VyOS repositories at all (`python3-inotify`), that's why
`https://github.com/dd010101/vyos-missing.git` is required.

| Package                 | GIT repository                                      | Branch   | Location of Jenkinsfile              |
|-------------------------|-----------------------------------------------------|----------|--------------------------------------|
| dropbear                | https://github.com/vyos/vyos-build.git              | equuleus | packages/dropbear/Jenkinsfile        |
| frr                     | https://github.com/vyos/vyos-build.git              | equuleus | packages/frr/Jenkinsfile             |
| hostap                  | https://github.com/vyos/vyos-build.git              | equuleus | packages/hostap/Jenkinsfile          |
| hvinfo                  | https://github.com/vyos/hvinfo.git                  | equuleus | Jenkinsfile                          |
| ipaddrcheck             | https://github.com/vyos/ipaddrcheck.git             | equuleus | Jenkinsfile                          |
| iproute2                | https://github.com/vyos/vyos-build.git              | equuleus | packages/iproute2/Jenkinsfile        |
| keepalived              | https://github.com/vyos/vyos-build.git              | equuleus | packages/keepalived/Jenkinsfile      |
| libnss-mapuser          | https://github.com/vyos/libnss-mapuser.git          | equuleus | Jenkinsfile                          |
| libpam-radius-auth      | https://github.com/vyos/libpam-radius-auth.git      | equuleus | Jenkinsfile                          |
| libvyosconfig           | https://github.com/vyos/libvyosconfig.git           | equuleus | Jenkinsfile                          |
| linux-kernel            | https://github.com/vyos/vyos-build.git              | equuleus | packages/linux-kernel/Jenkinsfile    |
| live-boot               | https://github.com/vyos/live-boot.git               | equuleus | Jenkinsfile                          |
| mdns-repeater           | https://github.com/vyos/mdns-repeater.git           | equuleus | Jenkinsfile                          |
| minisign                | https://github.com/vyos/vyos-build.git              | equuleus | packages/minisign/Jenkinsfile        |
| netfilter               | https://github.com/vyos/vyos-build.git              | equuleus | packages/netfilter/Jenkinsfile       |
| ocserv                  | https://github.com/vyos/vyos-build.git              | equuleus | packages/ocserv/Jenkinsfile          |
| python3-inotify         | **https://github.com/dd010101/vyos-missing.git**    | equuleus | packages/python3-inotify/Jenkinsfile |
| telegraf                | https://github.com/vyos/vyos-build.git              | equuleus | packages/telegraf/Jenkinsfile        |
| udp-broadcast-relay     | https://github.com/vyos/udp-broadcast-relay.git     | equuleus | Jenkinsfile                          |
| vyatta-bash             | https://github.com/vyos/vyatta-bash.git             | equuleus | Jenkinsfile                          |
| vyatta-biosdevname      | https://github.com/vyos/vyatta-biosdevname.git      | equuleus | Jenkinsfile                          |
| vyatta-cfg              | https://github.com/vyos/vyatta-cfg.git              | equuleus | Jenkinsfile                          |
| vyatta-cfg-firewall     | https://github.com/vyos/vyatta-cfg-firewall.git     | equuleus | Jenkinsfile                          |
| vyatta-cfg-qos          | https://github.com/vyos/vyatta-cfg-qos.git          | equuleus | Jenkinsfile                          |
| vyatta-cfg-quagga       | https://github.com/vyos/vyatta-cfg-quagga.git       | equuleus | Jenkinsfile                          |
| vyatta-cfg-system       | https://github.com/vyos/vyatta-cfg-system.git       | equuleus | Jenkinsfile                          |
| vyatta-cfg-vpn          | https://github.com/vyos/vyatta-cfg-vpn.git          | equuleus | Jenkinsfile                          |
| vyatta-cluster          | https://github.com/vyos/vyatta-cluster.git          | equuleus | Jenkinsfile                          |
| vyatta-config-mgmt      | https://github.com/vyos/vyatta-config-mgmt.git      | equuleus | Jenkinsfile                          |
| vyatta-conntrack        | https://github.com/vyos/vyatta-conntrack.git        | equuleus | Jenkinsfile                          |
| vyatta-nat              | https://github.com/vyos/vyatta-nat.git              | equuleus | Jenkinsfile                          |
| vyatta-op               | https://github.com/vyos/vyatta-op.git               | equuleus | Jenkinsfile                          |
| vyatta-op-firewall      | https://github.com/vyos/vyatta-op-firewall.git      | equuleus | Jenkinsfile                          |
| vyatta-op-qos           | https://github.com/vyos/vyatta-op-qos.git           | equuleus | Jenkinsfile                          |
| vyatta-op-vpn           | https://github.com/vyos/vyatta-op-vpn.git           | equuleus | Jenkinsfile                          |
| vyatta-wanloadbalance   | https://github.com/vyos/vyatta-wanloadbalance.git   | equuleus | Jenkinsfile                          |
| vyatta-zone             | https://github.com/vyos/vyatta-zone.git             | equuleus | Jenkinsfile                          |
| vyos-1x                 | https://github.com/vyos/vyos-1x.git                 | equuleus | Jenkinsfile                          |
| vyos-cloud-init         | https://github.com/vyos/vyos-cloud-init.git         | equuleus | Jenkinsfile                          |
| vyos-http-api-tools     | https://github.com/vyos/vyos-http-api-tools.git     | equuleus | Jenkinsfile                          |
| vyos-nhrp               | https://github.com/vyos/vyos-nhrp.git               | equuleus | Jenkinsfile                          |
| vyos-opennhrp           | https://github.com/vyos/vyos-opennhrp.git           | equuleus | Jenkinsfile                          |
| vyos-strongswan         | https://github.com/vyos/vyos-strongswan.git         | equuleus | Jenkinsfile                          |
| vyos-user-utils         | https://github.com/vyos/vyos-user-utils.git         | equuleus | Jenkinsfile                          |
| vyos-utils              | https://github.com/vyos/vyos-utils.git              | equuleus | Jenkinsfile                          |
| vyos-world              | https://github.com/vyos/vyos-world.git              | equuleus | Jenkinsfile                          |
| vyos-xe-guest-utilities | https://github.com/vyos/vyos-xe-guest-utilities.git | equuleus | Jenkinsfile                          |
| wide-dhcpv6             | https://github.com/vyos/vyos-build.git              | equuleus | packages/wide-dhcpv6/Jenkinsfile     |

<details>
<summary>Expected list of resulting .deb files after build (/home/sentrium/web/dev.packages.vyos.net/public_html):</summary>

```
repositories/equuleus/pool/main/a/accel-ppp/accel-ppp_1.12.0-170-g0b4ef98_amd64.deb
repositories/equuleus/pool/main/c/cloud-init/cloud-init_22.1-454-ge9842fcd-1~bddeb_all.deb
repositories/equuleus/pool/main/c/conntrack-tools/conntrack-dbgsym_1.4.6-1_amd64.deb
repositories/equuleus/pool/main/c/conntrack-tools/conntrackd-dbgsym_1.4.6-1_amd64.deb
repositories/equuleus/pool/main/c/conntrack-tools/conntrackd_1.4.6-1_amd64.deb
repositories/equuleus/pool/main/c/conntrack-tools/conntrack_1.4.6-1_amd64.deb
repositories/equuleus/pool/main/c/conntrack-tools/nfct-dbgsym_1.4.6-1_amd64.deb
repositories/equuleus/pool/main/c/conntrack-tools/nfct_1.4.6-1_amd64.deb
repositories/equuleus/pool/main/d/dropbear/dropbear-bin-dbgsym_2019.78-2_amd64.deb
repositories/equuleus/pool/main/d/dropbear/dropbear-bin_2019.78-2_amd64.deb
repositories/equuleus/pool/main/d/dropbear/dropbear-initramfs_2019.78-2_all.deb
repositories/equuleus/pool/main/d/dropbear/dropbear-run_2019.78-2_all.deb
repositories/equuleus/pool/main/d/dropbear/dropbear_2019.78-2_all.deb
repositories/equuleus/pool/main/f/frr/frr-dbgsym_7.5.1-20240517-02-g90ecb06ce-0_amd64.deb
repositories/equuleus/pool/main/f/frr/frr-doc_7.5.1-20240517-02-g90ecb06ce-0_all.deb
repositories/equuleus/pool/main/f/frr/frr-pythontools_7.5.1-20240517-02-g90ecb06ce-0_all.deb
repositories/equuleus/pool/main/f/frr/frr-rpki-rtrlib-dbgsym_7.5.1-20240517-02-g90ecb06ce-0_amd64.deb
repositories/equuleus/pool/main/f/frr/frr-rpki-rtrlib_7.5.1-20240517-02-g90ecb06ce-0_amd64.deb
repositories/equuleus/pool/main/f/frr/frr-snmp-dbgsym_7.5.1-20240517-02-g90ecb06ce-0_amd64.deb
repositories/equuleus/pool/main/f/frr/frr-snmp_7.5.1-20240517-02-g90ecb06ce-0_amd64.deb
repositories/equuleus/pool/main/f/frr/frr_7.5.1-20240517-02-g90ecb06ce-0_amd64.deb
repositories/equuleus/pool/main/h/hvinfo/hvinfo-dbgsym_1.2.0_amd64.deb
repositories/equuleus/pool/main/h/hvinfo/hvinfo_1.2.0_amd64.deb
repositories/equuleus/pool/main/i/ipaddrcheck/ipaddrcheck-dbgsym_1.2_amd64.deb
repositories/equuleus/pool/main/i/ipaddrcheck/ipaddrcheck_1.2_amd64.deb
repositories/equuleus/pool/main/i/iproute2/iproute2-dbgsym_5.4.0-1~bpo10+1_amd64.deb
repositories/equuleus/pool/main/i/iproute2/iproute2-doc_5.4.0-1~bpo10+1_all.deb
repositories/equuleus/pool/main/i/iproute2/iproute2_5.4.0-1~bpo10+1_amd64.deb
repositories/equuleus/pool/main/k/keepalived/keepalived-dbgsym_2.2.8_amd64.deb
repositories/equuleus/pool/main/k/keepalived/keepalived_2.2.8_amd64.deb
repositories/equuleus/pool/main/l/linux-5.4.268-amd64-vyos/linux-headers-5.4.268-amd64-vyos_5.4.268-1_amd64.deb
repositories/equuleus/pool/main/l/linux-5.4.268-amd64-vyos/linux-image-5.4.268-amd64-vyos_5.4.268-1_amd64.deb
repositories/equuleus/pool/main/l/linux-5.4.268-amd64-vyos/linux-libc-dev_5.4.268-1_amd64.deb
repositories/equuleus/pool/main/l/linux-5.4.268-amd64-vyos/linux-tools-5.4.268-amd64-vyos_5.4.268-1_amd64.deb
repositories/equuleus/pool/main/l/live-boot/live-boot-doc_20151213_all.deb
repositories/equuleus/pool/main/l/live-boot/live-boot-initramfs-tools_20151213_all.deb
repositories/equuleus/pool/main/l/live-boot/live-boot_20151213_all.deb
repositories/equuleus/pool/main/libn/libnetfilter-conntrack/libnetfilter-conntrack-dev_1.0.8-1_amd64.deb
repositories/equuleus/pool/main/libn/libnetfilter-conntrack/libnetfilter-conntrack3-dbgsym_1.0.8-1_amd64.deb
repositories/equuleus/pool/main/libn/libnetfilter-conntrack/libnetfilter-conntrack3_1.0.8-1_amd64.deb
repositories/equuleus/pool/main/libn/libnftnl/libnftnl-dev_1.1.7-1_amd64.deb
repositories/equuleus/pool/main/libn/libnftnl/libnftnl11-dbgsym_1.1.7-1_amd64.deb
repositories/equuleus/pool/main/libn/libnftnl/libnftnl11_1.1.7-1_amd64.deb
repositories/equuleus/pool/main/libn/libnss-mapuser/libnss-mapuser-dbgsym_1.1.0-cl3u1_amd64.deb
repositories/equuleus/pool/main/libn/libnss-mapuser/libnss-mapuser_1.1.0-cl3u1_amd64.deb
repositories/equuleus/pool/main/libp/libpam-radius-auth/libpam-radius-auth-dbgsym_1.5.0-cl3u1_amd64.deb
repositories/equuleus/pool/main/libp/libpam-radius-auth/libpam-radius-auth_1.5.0-cl3u1_amd64.deb
repositories/equuleus/pool/main/libp/libpam-radius-auth/radius-shell-dbgsym_1.5.0-cl3u1_amd64.deb
repositories/equuleus/pool/main/libp/libpam-radius-auth/radius-shell_1.5.0-cl3u1_amd64.deb
repositories/equuleus/pool/main/libv/libvyosconfig0/libvyosconfig0-dbgsym_1.3-1_amd64.deb
repositories/equuleus/pool/main/libv/libvyosconfig0/libvyosconfig0_1.3-1_amd64.deb
repositories/equuleus/pool/main/m/mdns-repeater/mdns-repeater_1.3-1_amd64.deb
repositories/equuleus/pool/main/m/minisign/minisign_0.9_amd64.deb
repositories/equuleus/pool/main/n/nftables/libnftables-dev_0.9.6-1_amd64.deb
repositories/equuleus/pool/main/n/nftables/libnftables1-dbgsym_0.9.6-1_amd64.deb
repositories/equuleus/pool/main/n/nftables/libnftables1_0.9.6-1_amd64.deb
repositories/equuleus/pool/main/n/nftables/nftables-dbgsym_0.9.6-1_amd64.deb
repositories/equuleus/pool/main/n/nftables/nftables_0.9.6-1_amd64.deb
repositories/equuleus/pool/main/n/nftables/python3-nftables_0.9.6-1_amd64.deb
repositories/equuleus/pool/main/o/ocserv/ocserv-dbgsym_1.1.6-3_amd64.deb
repositories/equuleus/pool/main/o/ocserv/ocserv_1.1.6-3_amd64.deb
repositories/equuleus/pool/main/p/python-inotify/python3-inotify_0.2.10-4_all.deb
repositories/equuleus/pool/main/s/strongswan/charon-cmd-dbgsym_5.7.2-2+vyos1.3_amd64.deb
repositories/equuleus/pool/main/s/strongswan/charon-cmd_5.7.2-2+vyos1.3_amd64.deb
repositories/equuleus/pool/main/s/strongswan/charon-systemd-dbgsym_5.7.2-2+vyos1.3_amd64.deb
repositories/equuleus/pool/main/s/strongswan/charon-systemd_5.7.2-2+vyos1.3_amd64.deb
repositories/equuleus/pool/main/s/strongswan/libcharon-extra-plugins-dbgsym_5.7.2-2+vyos1.3_amd64.deb
repositories/equuleus/pool/main/s/strongswan/libcharon-extra-plugins_5.7.2-2+vyos1.3_amd64.deb
repositories/equuleus/pool/main/s/strongswan/libstrongswan-dbgsym_5.7.2-2+vyos1.3_amd64.deb
repositories/equuleus/pool/main/s/strongswan/libstrongswan-extra-plugins-dbgsym_5.7.2-2+vyos1.3_amd64.deb
repositories/equuleus/pool/main/s/strongswan/libstrongswan-extra-plugins_5.7.2-2+vyos1.3_amd64.deb
repositories/equuleus/pool/main/s/strongswan/libstrongswan-standard-plugins-dbgsym_5.7.2-2+vyos1.3_amd64.deb
repositories/equuleus/pool/main/s/strongswan/libstrongswan-standard-plugins_5.7.2-2+vyos1.3_amd64.deb
repositories/equuleus/pool/main/s/strongswan/libstrongswan_5.7.2-2+vyos1.3_amd64.deb
repositories/equuleus/pool/main/s/strongswan/strongswan-charon-dbgsym_5.7.2-2+vyos1.3_amd64.deb
repositories/equuleus/pool/main/s/strongswan/strongswan-charon_5.7.2-2+vyos1.3_amd64.deb
repositories/equuleus/pool/main/s/strongswan/strongswan-libcharon-dbgsym_5.7.2-2+vyos1.3_amd64.deb
repositories/equuleus/pool/main/s/strongswan/strongswan-libcharon_5.7.2-2+vyos1.3_amd64.deb
repositories/equuleus/pool/main/s/strongswan/strongswan-pki-dbgsym_5.7.2-2+vyos1.3_amd64.deb
repositories/equuleus/pool/main/s/strongswan/strongswan-pki_5.7.2-2+vyos1.3_amd64.deb
repositories/equuleus/pool/main/s/strongswan/strongswan-scepclient-dbgsym_5.7.2-2+vyos1.3_amd64.deb
repositories/equuleus/pool/main/s/strongswan/strongswan-scepclient_5.7.2-2+vyos1.3_amd64.deb
repositories/equuleus/pool/main/s/strongswan/strongswan-starter-dbgsym_5.7.2-2+vyos1.3_amd64.deb
repositories/equuleus/pool/main/s/strongswan/strongswan-starter_5.7.2-2+vyos1.3_amd64.deb
repositories/equuleus/pool/main/s/strongswan/strongswan-swanctl-dbgsym_5.7.2-2+vyos1.3_amd64.deb
repositories/equuleus/pool/main/s/strongswan/strongswan-swanctl_5.7.2-2+vyos1.3_amd64.deb
repositories/equuleus/pool/main/s/strongswan/strongswan_5.7.2-2+vyos1.3_all.deb
repositories/equuleus/pool/main/t/telegraf/telegraf_1.23.1-1_amd64.deb
repositories/equuleus/pool/main/u/udp-broadcast-relay/udp-broadcast-relay_1.3-1_amd64.deb
repositories/equuleus/pool/main/v/vici/python3-vici_5.7.2-1_all.deb
repositories/equuleus/pool/main/v/vyatta-bash/vyatta-bash-dbgsym_4.1.48+vyos1.3_amd64.deb
repositories/equuleus/pool/main/v/vyatta-bash/vyatta-bash_4.1.48+vyos1.3_amd64.deb
repositories/equuleus/pool/main/v/vyatta-biosdevname/vyatta-biosdevname-dbgsym_0.3.11+vyos1.3_amd64.deb
repositories/equuleus/pool/main/v/vyatta-biosdevname/vyatta-biosdevname_0.3.11+vyos1.3_amd64.deb
repositories/equuleus/pool/main/v/vyatta-cfg-firewall/vyatta-cfg-firewall_1.3-1_all.deb
repositories/equuleus/pool/main/v/vyatta-cfg-qos/vyatta-cfg-qos_1.3-1_all.deb
repositories/equuleus/pool/main/v/vyatta-cfg-quagga/vyatta-cfg-quagga_1.3-1_all.deb
repositories/equuleus/pool/main/v/vyatta-cfg-system/vyatta-cfg-system-dbgsym_1.3-1_amd64.deb
repositories/equuleus/pool/main/v/vyatta-cfg-system/vyatta-cfg-system_1.3-1_amd64.deb
repositories/equuleus/pool/main/v/vyatta-cfg-vpn/vyatta-cfg-vpn_1.3-1_all.deb
repositories/equuleus/pool/main/v/vyatta-cfg/libvyatta-cfg-dev_1.3-1_amd64.deb
repositories/equuleus/pool/main/v/vyatta-cfg/libvyatta-cfg1-dbgsym_1.3-1_amd64.deb
repositories/equuleus/pool/main/v/vyatta-cfg/libvyatta-cfg1_1.3-1_amd64.deb
repositories/equuleus/pool/main/v/vyatta-cfg/vyatta-cfg-dbgsym_1.3-1_amd64.deb
repositories/equuleus/pool/main/v/vyatta-cfg/vyatta-cfg_1.3-1_amd64.deb
repositories/equuleus/pool/main/v/vyatta-cluster/vyatta-cluster_1.3-1_all.deb
repositories/equuleus/pool/main/v/vyatta-config-mgmt/vyatta-config-mgmt_1.3-1_all.deb
repositories/equuleus/pool/main/v/vyatta-conntrack/vyatta-conntrack-dbgsym_1.3-1_amd64.deb
repositories/equuleus/pool/main/v/vyatta-conntrack/vyatta-conntrack_1.3-1_amd64.deb
repositories/equuleus/pool/main/v/vyatta-nat/vyatta-nat_1.3.0_all.deb
repositories/equuleus/pool/main/v/vyatta-op-firewall/vyatta-op-firewall_1.3-1_all.deb
repositories/equuleus/pool/main/v/vyatta-op-qos/vyatta-op-qos_1.3-1_all.deb
repositories/equuleus/pool/main/v/vyatta-op-vpn/vyatta-op-vpn_1.3-1_all.deb
repositories/equuleus/pool/main/v/vyatta-op/vyatta-op_1.3-1_all.deb
repositories/equuleus/pool/main/v/vyatta-wanloadbalance/vyatta-wanloadbalance-dbgsym_1.3-1_amd64.deb
repositories/equuleus/pool/main/v/vyatta-wanloadbalance/vyatta-wanloadbalance_1.3-1_amd64.deb
repositories/equuleus/pool/main/v/vyatta-zone/vyatta-zone_0.15+vyos2+current1_all.deb
repositories/equuleus/pool/main/v/vyos-1x/vyos-1x-dbgsym_1.3dev0-4112-gd29c8c36d_amd64.deb
repositories/equuleus/pool/main/v/vyos-1x/vyos-1x-smoketest_1.3dev0-4112-gd29c8c36d_all.deb
repositories/equuleus/pool/main/v/vyos-1x/vyos-1x-vmware_1.3dev0-4112-gd29c8c36d_amd64.deb
repositories/equuleus/pool/main/v/vyos-1x/vyos-1x_1.3dev0-4112-gd29c8c36d_amd64.deb
repositories/equuleus/pool/main/v/vyos-drivers-intel-ice/vyos-drivers-intel-ice_1.11.14-1_amd64.deb
repositories/equuleus/pool/main/v/vyos-drivers-realtek-r8152/vyos-drivers-realtek-r8152_2.17.1-1_amd64.deb
repositories/equuleus/pool/main/v/vyos-http-api-tools/vyos-http-api-tools-dbgsym_2.1_amd64.deb
repositories/equuleus/pool/main/v/vyos-http-api-tools/vyos-http-api-tools_2.1_amd64.deb
repositories/equuleus/pool/main/v/vyos-intel-qat/vyos-intel-qat_1.7.l.4.9.0-00008-0_amd64.deb
repositories/equuleus/pool/main/v/vyos-linux-firmware/vyos-linux-firmware_20201218_all.deb
repositories/equuleus/pool/main/v/vyos-nhrp/vyos-nhrp_1.3-1_all.deb
repositories/equuleus/pool/main/v/vyos-opennhrp/vyos-opennhrp-dbgsym_0.14.1-vyos1.3_amd64.deb
repositories/equuleus/pool/main/v/vyos-opennhrp/vyos-opennhrp_0.14.1-vyos1.3_amd64.deb
repositories/equuleus/pool/main/v/vyos-user-utils/vyos-user-utils_1.3.0-1_all.deb
repositories/equuleus/pool/main/v/vyos-utils/vyos-utils-dbgsym_1.3-2_amd64.deb
repositories/equuleus/pool/main/v/vyos-utils/vyos-utils_1.3-2_amd64.deb
repositories/equuleus/pool/main/v/vyos-world/vyos-world_1.3-1_all.deb
repositories/equuleus/pool/main/v/vyos-xe-guest-utilities/vyos-xe-guest-utilities_7.13.0+vyos1.3_amd64.deb
repositories/equuleus/pool/main/w/wide-dhcpv6/wide-dhcpv6-client-dbgsym_20080615-23_amd64.deb
repositories/equuleus/pool/main/w/wide-dhcpv6/wide-dhcpv6-client_20080615-23_amd64.deb
repositories/equuleus/pool/main/w/wide-dhcpv6/wide-dhcpv6-relay-dbgsym_20080615-23_amd64.deb
repositories/equuleus/pool/main/w/wide-dhcpv6/wide-dhcpv6-relay_20080615-23_amd64.deb
repositories/equuleus/pool/main/w/wide-dhcpv6/wide-dhcpv6-server-dbgsym_20080615-23_amd64.deb
repositories/equuleus/pool/main/w/wide-dhcpv6/wide-dhcpv6-server_20080615-23_amd64.deb
repositories/equuleus/pool/main/w/wireguard-linux-compat/wireguard-modules_1.0.20201112-1~bpo10+1_all.deb
repositories/equuleus/pool/main/w/wpa/eapoltest-dbgsym_2.10-520-gb704dc72e_amd64.deb
repositories/equuleus/pool/main/w/wpa/eapoltest_2.10-520-gb704dc72e_amd64.deb
repositories/equuleus/pool/main/w/wpa/hostapd-dbgsym_2.10-520-gb704dc72e_amd64.deb
repositories/equuleus/pool/main/w/wpa/hostapd_2.10-520-gb704dc72e_amd64.deb
repositories/equuleus/pool/main/w/wpa/libwpa-client-dev_2.10-520-gb704dc72e_amd64.deb
repositories/equuleus/pool/main/w/wpa/wpasupplicant-dbgsym_2.10-520-gb704dc72e_amd64.deb
repositories/equuleus/pool/main/w/wpa/wpasupplicant_2.10-520-gb704dc72e_amd64.deb
```

</details>

Package info for sagitta
--

List of required packages and their Jenkinsfile:

Some packages (`pam_tacplus`, `strongswan`) are broken right now, that's why
fork `https://github.com/dd010101/vyos-build.git` is required. Until they are fixed.

Some packages aren't in the vyos repositories at all (`libnss-tacplus`), that's why
`https://github.com/dd010101/vyos-missing.git` is required.

Another special case is `vyos-xe-guest-utilities` where `current` branch is required.

| Package                                  | GIT repository                                      | Branch      | Location of Jenkinsfile                                       |
|------------------------------------------|-----------------------------------------------------|-------------|---------------------------------------------------------------|
| aws-gateway-load-balancer-tunnel-handler | https://github.com/vyos/vyos-build.git              | sagitta     | packages/aws-gateway-load-balancer-tunnel-handler/Jenkinsfile |
| ddclient                                 | https://github.com/vyos/vyos-build.git              | sagitta     | packages/ddclient/Jenkinsfile                                 |
| dropbear                                 | https://github.com/vyos/vyos-build.git              | sagitta     | packages/dropbear/Jenkinsfile                                 |
| ethtool                                  | https://github.com/vyos/vyos-build.git              | sagitta     | packages/ethtool/Jenkinsfile                                  |
| frr                                      | https://github.com/vyos/vyos-build.git              | sagitta     | packages/frr/Jenkinsfile                                      |
| hostap                                   | https://github.com/vyos/vyos-build.git              | sagitta     | packages/hostap/Jenkinsfile                                   |
| hsflowd                                  | https://github.com/vyos/vyos-build.git              | sagitta     | packages/hsflowd/Jenkinsfile                                  |
| hvinfo                                   | https://github.com/vyos/hvinfo.git                  | sagitta     | Jenkinsfile                                                   |
| ipaddrcheck                              | https://github.com/vyos/ipaddrcheck.git             | sagitta     | Jenkinsfile                                                   |
| isc-dhcp                                 | https://github.com/vyos/vyos-build.git              | sagitta     | packages/isc-dhcp/Jenkinsfile                                 |
| keepalived                               | https://github.com/vyos/vyos-build.git              | sagitta     | packages/keepalived/Jenkinsfile                               |
| libnss-mapuser                           | https://github.com/vyos/libnss-mapuser.git          | sagitta     | Jenkinsfile                                                   |
| libnss-tacplus                           | **https://github.com/dd010101/vyos-missing.git**    | sagitta     | packages/libnss-tacplus/Jenkinsfile                           |
| libpam-radius-auth                       | https://github.com/vyos/libpam-radius-auth.git      | sagitta     | Jenkinsfile                                                   |
| libvyosconfig                            | https://github.com/vyos/libvyosconfig.git           | sagitta     | Jenkinsfile                                                   |
| linux-kernel                             | https://github.com/vyos/vyos-build.git              | sagitta     | packages/linux-kernel/Jenkinsfile                             |
| live-boot                                | https://github.com/vyos/live-boot.git               | sagitta     | Jenkinsfile                                                   |
| ndppd                                    | https://github.com/vyos/vyos-build.git              | sagitta     | packages/ndppd/Jenkinsfile                                    |
| netfilter                                | https://github.com/vyos/vyos-build.git              | sagitta     | packages/netfilter/Jenkinsfile                                |
| opennhrp                                 | https://github.com/vyos/vyos-build.git              | sagitta     | packages/opennhrp/Jenkinsfile                                 |
| openvpn-otp                              | https://github.com/vyos/vyos-build.git              | sagitta     | packages/openvpn-otp/Jenkinsfile                              |
| owamp                                    | https://github.com/vyos/vyos-build.git              | sagitta     | packages/owamp/Jenkinsfile                                    |
| pam_tacplus                              | **https://github.com/dd010101/vyos-build.git**      | sagitta     | packages/pam_tacplus/Jenkinsfile                              |
| pmacct                                   | https://github.com/vyos/vyos-build.git              | sagitta     | packages/pmacct/Jenkinsfile                                   |
| pyhumps                                  | https://github.com/vyos/vyos-build.git              | sagitta     | packages/pyhumps/Jenkinsfile                                  |
| radvd                                    | https://github.com/vyos/vyos-build.git              | sagitta     | packages/radvd/Jenkinsfile                                    |
| strongswan                               | **https://github.com/dd010101/vyos-build.git**      | sagitta     | packages/strongswan/Jenkinsfile                               |
| telegraf                                 | https://github.com/vyos/vyos-build.git              | sagitta     | packages/telegraf/Jenkinsfile                                 |
| udp-broadcast-relay                      | https://github.com/vyos/udp-broadcast-relay.git     | sagitta     | Jenkinsfile                                                   |
| vyatta-bash                              | https://github.com/vyos/vyatta-bash.git             | sagitta     | Jenkinsfile                                                   |
| vyatta-biosdevname                       | https://github.com/vyos/vyatta-biosdevname.git      | sagitta     | Jenkinsfile                                                   |
| vyatta-cfg                               | https://github.com/vyos/vyatta-cfg.git              | sagitta     | Jenkinsfile                                                   |
| vyatta-cfg-system                        | https://github.com/vyos/vyatta-cfg-system.git       | sagitta     | Jenkinsfile                                                   |
| vyatta-op                                | https://github.com/vyos/vyatta-op.git               | sagitta     | Jenkinsfile                                                   |
| vyatta-wanloadbalance                    | https://github.com/vyos/vyatta-wanloadbalance.git   | sagitta     | Jenkinsfile                                                   |
| vyos-1x                                  | https://github.com/vyos/vyos-1x.git                 | sagitta     | Jenkinsfile                                                   |
| vyos-cloud-init                          | https://github.com/vyos/vyos-cloud-init.git         | sagitta     | Jenkinsfile                                                   |
| vyos-http-api-tools                      | https://github.com/vyos/vyos-http-api-tools.git     | sagitta     | Jenkinsfile                                                   |
| vyos-user-utils                          | https://github.com/vyos/vyos-user-utils.git         | sagitta     | Jenkinsfile                                                   |
| vyos-utils                               | https://github.com/vyos/vyos-utils.git              | sagitta     | Jenkinsfile                                                   |
| vyos-world                               | https://github.com/vyos/vyos-world.git              | sagitta     | Jenkinsfile                                                   |
| vyos-xe-guest-utilities                  | https://github.com/vyos/vyos-xe-guest-utilities.git | **current** | Jenkinsfile                                                   |
| wide-dhcpv6                              | https://github.com/vyos/vyos-build.git              | sagitta     | packages/wide-dhcpv6/Jenkinsfile                              |

<details>
<summary>Expected list of resulting .deb files after build (/home/sentrium/web/dev.packages.vyos.net/public_html):</summary>

```
repositories/sagitta/pool/main/a/accel-ppp/accel-ppp_1.12.0-260-g19c36e5_amd64.deb
repositories/sagitta/pool/main/a/aws-gwlbtun/aws-gwlbtun_1-eb51d33_amd64.deb
repositories/sagitta/pool/main/c/cloud-init/cloud-init_22.1-442-gd436f231-1~bddeb_all.deb
repositories/sagitta/pool/main/d/ddclient/ddclient_3.11.2+vyos0_all.deb
repositories/sagitta/pool/main/d/dropbear/dropbear-bin-dbgsym_2022.83-1+deb12u1_amd64.deb
repositories/sagitta/pool/main/d/dropbear/dropbear-bin_2022.83-1+deb12u1_amd64.deb
repositories/sagitta/pool/main/d/dropbear/dropbear-initramfs_2022.83-1+deb12u1_all.deb
repositories/sagitta/pool/main/d/dropbear/dropbear-run_2022.83-1+deb12u1_all.deb
repositories/sagitta/pool/main/d/dropbear/dropbear_2022.83-1+deb12u1_all.deb
repositories/sagitta/pool/main/e/ethtool/ethtool-dbgsym_6.6-1_amd64.deb
repositories/sagitta/pool/main/e/ethtool/ethtool_6.6-1_amd64.deb
repositories/sagitta/pool/main/f/frr/frr-dbgsym_9.1-160-g488c106e7_amd64.deb
repositories/sagitta/pool/main/f/frr/frr-doc_9.1-160-g488c106e7_all.deb
repositories/sagitta/pool/main/f/frr/frr-pythontools_9.1-160-g488c106e7_all.deb
repositories/sagitta/pool/main/f/frr/frr-rpki-rtrlib-dbgsym_9.1-160-g488c106e7_amd64.deb
repositories/sagitta/pool/main/f/frr/frr-rpki-rtrlib_9.1-160-g488c106e7_amd64.deb
repositories/sagitta/pool/main/f/frr/frr-snmp-dbgsym_9.1-160-g488c106e7_amd64.deb
repositories/sagitta/pool/main/f/frr/frr-snmp_9.1-160-g488c106e7_amd64.deb
repositories/sagitta/pool/main/f/frr/frr_9.1-160-g488c106e7_amd64.deb
repositories/sagitta/pool/main/h/hsflowd/hsflowd_2.0.55-1_all.deb
repositories/sagitta/pool/main/h/hvinfo/hvinfo-dbgsym_1.2.0_amd64.deb
repositories/sagitta/pool/main/h/hvinfo/hvinfo_1.2.0_amd64.deb
repositories/sagitta/pool/main/i/ipaddrcheck/ipaddrcheck-dbgsym_1.2_amd64.deb
repositories/sagitta/pool/main/i/ipaddrcheck/ipaddrcheck_1.2_amd64.deb
repositories/sagitta/pool/main/i/isc-dhcp/isc-dhcp-client-dbgsym_4.4.3-P1-4_amd64.deb
repositories/sagitta/pool/main/i/isc-dhcp/isc-dhcp-client-ddns-dbgsym_4.4.3-P1-4_amd64.deb
repositories/sagitta/pool/main/i/isc-dhcp/isc-dhcp-client-ddns_4.4.3-P1-4_amd64.deb
repositories/sagitta/pool/main/i/isc-dhcp/isc-dhcp-client_4.4.3-P1-4_amd64.deb
repositories/sagitta/pool/main/i/isc-dhcp/isc-dhcp-common_4.4.3-P1-4_amd64.deb
repositories/sagitta/pool/main/i/isc-dhcp/isc-dhcp-dev_4.4.3-P1-4_amd64.deb
repositories/sagitta/pool/main/i/isc-dhcp/isc-dhcp-keama-dbgsym_4.4.3-P1-4_amd64.deb
repositories/sagitta/pool/main/i/isc-dhcp/isc-dhcp-keama_4.4.3-P1-4_amd64.deb
repositories/sagitta/pool/main/i/isc-dhcp/isc-dhcp-relay-dbgsym_4.4.3-P1-4_amd64.deb
repositories/sagitta/pool/main/i/isc-dhcp/isc-dhcp-relay_4.4.3-P1-4_amd64.deb
repositories/sagitta/pool/main/i/isc-dhcp/isc-dhcp-server-dbgsym_4.4.3-P1-4_amd64.deb
repositories/sagitta/pool/main/i/isc-dhcp/isc-dhcp-server-ldap-dbgsym_4.4.3-P1-4_amd64.deb
repositories/sagitta/pool/main/i/isc-dhcp/isc-dhcp-server-ldap_4.4.3-P1-4_amd64.deb
repositories/sagitta/pool/main/i/isc-dhcp/isc-dhcp-server_4.4.3-P1-4_amd64.deb
repositories/sagitta/pool/main/j/jool/jool-dbgsym_4.1.9+bf4c7e3669-1_amd64.deb
repositories/sagitta/pool/main/j/jool/jool_4.1.9+bf4c7e3669-1_amd64.deb
repositories/sagitta/pool/main/k/keepalived/keepalived-dbgsym_2.2.8-1_amd64.deb
repositories/sagitta/pool/main/k/keepalived/keepalived_2.2.8-1_amd64.deb
repositories/sagitta/pool/main/l/linux-upstream/linux-headers-6.6.31-amd64-vyos_6.6.31-1_amd64.deb
repositories/sagitta/pool/main/l/linux-upstream/linux-image-6.6.31-amd64-vyos_6.6.31-1_amd64.deb
repositories/sagitta/pool/main/l/linux-upstream/linux-libc-dev_6.6.31-1_amd64.deb
repositories/sagitta/pool/main/l/live-boot/live-boot-doc_20151213-vyos0_all.deb
repositories/sagitta/pool/main/l/live-boot/live-boot-initramfs-tools_20151213-vyos0_all.deb
repositories/sagitta/pool/main/l/live-boot/live-boot_20151213-vyos0_all.deb
repositories/sagitta/pool/main/libn/libnftnl/libnftnl-dev-doc_1.2.6-2_all.deb
repositories/sagitta/pool/main/libn/libnftnl/libnftnl-dev_1.2.6-2_amd64.deb
repositories/sagitta/pool/main/libn/libnftnl/libnftnl11-dbgsym_1.2.6-2_amd64.deb
repositories/sagitta/pool/main/libn/libnftnl/libnftnl11_1.2.6-2_amd64.deb
repositories/sagitta/pool/main/libn/libnss-mapuser/libnss-mapuser-dbgsym_1.1.0-cl3u3_amd64.deb
repositories/sagitta/pool/main/libn/libnss-mapuser/libnss-mapuser_1.1.0-cl3u3_amd64.deb
repositories/sagitta/pool/main/libn/libnss-tacplus/libnss-tacplus-dbgsym_1.0.4-cl5.1.0u11_amd64.deb
repositories/sagitta/pool/main/libn/libnss-tacplus/libnss-tacplus_1.0.4-cl5.1.0u11_amd64.deb
repositories/sagitta/pool/main/libp/libpam-radius-auth/libpam-radius-auth-dbgsym_1.5.0-cl3u7_amd64.deb
repositories/sagitta/pool/main/libp/libpam-radius-auth/libpam-radius-auth_1.5.0-cl3u7_amd64.deb
repositories/sagitta/pool/main/libp/libpam-radius-auth/radius-shell-dbgsym_1.5.0-cl3u7_amd64.deb
repositories/sagitta/pool/main/libp/libpam-radius-auth/radius-shell_1.5.0-cl3u7_amd64.deb
repositories/sagitta/pool/main/libp/libpam-tacplus/libpam-tacplus-dbgsym_1.4.3-cl5.1.0u5_amd64.deb
repositories/sagitta/pool/main/libp/libpam-tacplus/libpam-tacplus-dev_1.4.3-cl5.1.0u5_amd64.deb
repositories/sagitta/pool/main/libp/libpam-tacplus/libpam-tacplus_1.4.3-cl5.1.0u5_amd64.deb
repositories/sagitta/pool/main/libp/libpam-tacplus/libtac-dev_1.4.3-cl5.1.0u5_amd64.deb
repositories/sagitta/pool/main/libp/libpam-tacplus/libtac2-bin-dbgsym_1.4.3-cl5.1.0u5_amd64.deb
repositories/sagitta/pool/main/libp/libpam-tacplus/libtac2-bin_1.4.3-cl5.1.0u5_amd64.deb
repositories/sagitta/pool/main/libp/libpam-tacplus/libtac2-dbgsym_1.4.3-cl5.1.0u5_amd64.deb
repositories/sagitta/pool/main/libp/libpam-tacplus/libtac2_1.4.3-cl5.1.0u5_amd64.deb
repositories/sagitta/pool/main/libp/libpam-tacplus/libtac5-bin-dbgsym_1.7.0-0.1_amd64.deb
repositories/sagitta/pool/main/libp/libpam-tacplus/libtac5-bin_1.7.0-0.1_amd64.deb
repositories/sagitta/pool/main/libp/libpam-tacplus/libtac5-dbgsym_1.7.0-0.1_amd64.deb
repositories/sagitta/pool/main/libp/libpam-tacplus/libtac5_1.7.0-0.1_amd64.deb
repositories/sagitta/pool/main/libr/librtr0/librtr-dbg_0.8.0_amd64.deb
repositories/sagitta/pool/main/libr/librtr0/librtr-dev_0.8.0_amd64.deb
repositories/sagitta/pool/main/libr/librtr0/librtr-doc_0.8.0_all.deb
repositories/sagitta/pool/main/libr/librtr0/librtr0_0.8.0_amd64.deb
repositories/sagitta/pool/main/libr/librtr0/rtr-tools-dbg_0.8.0_amd64.deb
repositories/sagitta/pool/main/libr/librtr0/rtr-tools_0.8.0_amd64.deb
repositories/sagitta/pool/main/libt/libtacplus-map/libtacplus-map-dev_1.0.1-cl5.1.0u9_amd64.deb
repositories/sagitta/pool/main/libt/libtacplus-map/libtacplus-map1-dbgsym_1.0.1-cl5.1.0u9_amd64.deb
repositories/sagitta/pool/main/libt/libtacplus-map/libtacplus-map1_1.0.1-cl5.1.0u9_amd64.deb
repositories/sagitta/pool/main/libv/libvyosconfig0/libvyosconfig0-dbgsym_0.0.10_amd64.deb
repositories/sagitta/pool/main/libv/libvyosconfig0/libvyosconfig0_0.0.10_amd64.deb
repositories/sagitta/pool/main/liby/libyang2/libyang-tools_2.1.148-1_all.deb
repositories/sagitta/pool/main/liby/libyang2/libyang2-dbgsym_2.1.148-1_amd64.deb
repositories/sagitta/pool/main/liby/libyang2/libyang2-dev_2.1.148-1_amd64.deb
repositories/sagitta/pool/main/liby/libyang2/libyang2-tools-dbgsym_2.1.148-1_amd64.deb
repositories/sagitta/pool/main/liby/libyang2/libyang2-tools_2.1.148-1_amd64.deb
repositories/sagitta/pool/main/liby/libyang2/libyang2_2.1.148-1_amd64.deb
repositories/sagitta/pool/main/n/ndppd/ndppd-dbgsym_0.2.5-6_amd64.deb
repositories/sagitta/pool/main/n/ndppd/ndppd_0.2.5-6_amd64.deb
repositories/sagitta/pool/main/n/nftables/libnftables-dev_1.0.9-1_amd64.deb
repositories/sagitta/pool/main/n/nftables/libnftables1-dbgsym_1.0.9-1_amd64.deb
repositories/sagitta/pool/main/n/nftables/libnftables1_1.0.9-1_amd64.deb
repositories/sagitta/pool/main/n/nftables/nftables-dbgsym_1.0.9-1_amd64.deb
repositories/sagitta/pool/main/n/nftables/nftables_1.0.9-1_amd64.deb
repositories/sagitta/pool/main/n/nftables/python3-nftables_1.0.9-1_amd64.deb
repositories/sagitta/pool/main/o/opennhrp/opennhrp_0.14-20-g613277f_amd64.deb
repositories/sagitta/pool/main/o/openvpn-dco/openvpn-dco_0.2.20231117_amd64.deb
repositories/sagitta/pool/main/o/openvpn-otp/openvpn-otp_1.0-4-g47f8ccf_amd64.deb
repositories/sagitta/pool/main/o/owamp/owamp-client-dbgsym_4.4.6-1_amd64.deb
repositories/sagitta/pool/main/o/owamp/owamp-client_4.4.6-1_amd64.deb
repositories/sagitta/pool/main/o/owamp/owamp-server-dbgsym_4.4.6-1_amd64.deb
repositories/sagitta/pool/main/o/owamp/owamp-server_4.4.6-1_amd64.deb
repositories/sagitta/pool/main/o/owamp/twamp-client-dbgsym_4.4.6-1_amd64.deb
repositories/sagitta/pool/main/o/owamp/twamp-client_4.4.6-1_amd64.deb
repositories/sagitta/pool/main/o/owamp/twamp-server-dbgsym_4.4.6-1_amd64.deb
repositories/sagitta/pool/main/o/owamp/twamp-server_4.4.6-1_amd64.deb
repositories/sagitta/pool/main/p/pmacct/pmacct-dbgsym_1.7.7-1_amd64.deb
repositories/sagitta/pool/main/p/pmacct/pmacct_1.7.7-1_amd64.deb
repositories/sagitta/pool/main/p/pyhumps/python3-pyhumps_3.8.0-1_all.deb
repositories/sagitta/pool/main/r/radvd/radvd_2.20-rc1-23-gf2de476_amd64.deb
repositories/sagitta/pool/main/s/strongswan/charon-cmd-dbgsym_5.9.11-2+vyos0_amd64.deb
repositories/sagitta/pool/main/s/strongswan/charon-cmd_5.9.11-2+vyos0_amd64.deb
repositories/sagitta/pool/main/s/strongswan/charon-systemd-dbgsym_5.9.11-2+vyos0_amd64.deb
repositories/sagitta/pool/main/s/strongswan/charon-systemd_5.9.11-2+vyos0_amd64.deb
repositories/sagitta/pool/main/s/strongswan/libcharon-extauth-plugins-dbgsym_5.9.11-2+vyos0_amd64.deb
repositories/sagitta/pool/main/s/strongswan/libcharon-extauth-plugins_5.9.11-2+vyos0_amd64.deb
repositories/sagitta/pool/main/s/strongswan/libcharon-extra-plugins-dbgsym_5.9.11-2+vyos0_amd64.deb
repositories/sagitta/pool/main/s/strongswan/libcharon-extra-plugins_5.9.11-2+vyos0_amd64.deb
repositories/sagitta/pool/main/s/strongswan/libstrongswan-dbgsym_5.9.11-2+vyos0_amd64.deb
repositories/sagitta/pool/main/s/strongswan/libstrongswan-extra-plugins-dbgsym_5.9.11-2+vyos0_amd64.deb
repositories/sagitta/pool/main/s/strongswan/libstrongswan-extra-plugins_5.9.11-2+vyos0_amd64.deb
repositories/sagitta/pool/main/s/strongswan/libstrongswan-standard-plugins-dbgsym_5.9.11-2+vyos0_amd64.deb
repositories/sagitta/pool/main/s/strongswan/libstrongswan-standard-plugins_5.9.11-2+vyos0_amd64.deb
repositories/sagitta/pool/main/s/strongswan/libstrongswan_5.9.11-2+vyos0_amd64.deb
repositories/sagitta/pool/main/s/strongswan/strongswan-charon-dbgsym_5.9.11-2+vyos0_amd64.deb
repositories/sagitta/pool/main/s/strongswan/strongswan-charon_5.9.11-2+vyos0_amd64.deb
repositories/sagitta/pool/main/s/strongswan/strongswan-libcharon-dbgsym_5.9.11-2+vyos0_amd64.deb
repositories/sagitta/pool/main/s/strongswan/strongswan-libcharon_5.9.11-2+vyos0_amd64.deb
repositories/sagitta/pool/main/s/strongswan/strongswan-nm_5.9.11-2+vyos0_amd64.deb
repositories/sagitta/pool/main/s/strongswan/strongswan-pki-dbgsym_5.9.11-2+vyos0_amd64.deb
repositories/sagitta/pool/main/s/strongswan/strongswan-pki_5.9.11-2+vyos0_amd64.deb
repositories/sagitta/pool/main/s/strongswan/strongswan-starter-dbgsym_5.9.11-2+vyos0_amd64.deb
repositories/sagitta/pool/main/s/strongswan/strongswan-starter_5.9.11-2+vyos0_amd64.deb
repositories/sagitta/pool/main/s/strongswan/strongswan-swanctl-dbgsym_5.9.11-2+vyos0_amd64.deb
repositories/sagitta/pool/main/s/strongswan/strongswan-swanctl_5.9.11-2+vyos0_amd64.deb
repositories/sagitta/pool/main/s/strongswan/strongswan_5.9.11-2+vyos0_all.deb
repositories/sagitta/pool/main/t/telegraf/telegraf_1.28.3-1_amd64.deb
repositories/sagitta/pool/main/u/udp-broadcast-relay/udp-broadcast-relay_0.1+vyos3+equuleus1_amd64.deb
repositories/sagitta/pool/main/v/vici/python3-vici_5.9.11-1_all.deb
repositories/sagitta/pool/main/v/vyatta-bash/vyatta-bash-dbgsym_4.1-3+vyos2+current2_amd64.deb
repositories/sagitta/pool/main/v/vyatta-bash/vyatta-bash_4.1-3+vyos2+current2_amd64.deb
repositories/sagitta/pool/main/v/vyatta-biosdevname/vyatta-biosdevname-dbgsym_0.3.11+vyos2+current2_amd64.deb
repositories/sagitta/pool/main/v/vyatta-biosdevname/vyatta-biosdevname_0.3.11+vyos2+current2_amd64.deb
repositories/sagitta/pool/main/v/vyatta-cfg-system/vyatta-cfg-system_0.20.44+vyos2+current22_amd64.deb
repositories/sagitta/pool/main/v/vyatta-cfg/libvyatta-cfg-dev_0.102.0+vyos2+current5_amd64.deb
repositories/sagitta/pool/main/v/vyatta-cfg/libvyatta-cfg1-dbgsym_0.102.0+vyos2+current5_amd64.deb
repositories/sagitta/pool/main/v/vyatta-cfg/libvyatta-cfg1_0.102.0+vyos2+current5_amd64.deb
repositories/sagitta/pool/main/v/vyatta-cfg/vyatta-cfg-dbgsym_0.102.0+vyos2+current5_amd64.deb
repositories/sagitta/pool/main/v/vyatta-cfg/vyatta-cfg_0.102.0+vyos2+current5_amd64.deb
repositories/sagitta/pool/main/v/vyatta-op/vyatta-op_0.14.0+vyos2+current8_all.deb
repositories/sagitta/pool/main/v/vyatta-wanloadbalance/vyatta-wanloadbalance-dbgsym_0.13.70+vyos2+current1_amd64.deb
repositories/sagitta/pool/main/v/vyatta-wanloadbalance/vyatta-wanloadbalance_0.13.70+vyos2+current1_amd64.deb
repositories/sagitta/pool/main/v/vyos-1x/vyos-1x-dbgsym_1.4.0-epa2-374-gef31f7025_amd64.deb
repositories/sagitta/pool/main/v/vyos-1x/vyos-1x-smoketest_1.4.0-epa2-374-gef31f7025_all.deb
repositories/sagitta/pool/main/v/vyos-1x/vyos-1x-vmware_1.4.0-epa2-374-gef31f7025_amd64.deb
repositories/sagitta/pool/main/v/vyos-1x/vyos-1x_1.4.0-epa2-374-gef31f7025_amd64.deb
repositories/sagitta/pool/main/v/vyos-http-api-tools/vyos-http-api-tools-dbgsym_2.3_amd64.deb
repositories/sagitta/pool/main/v/vyos-http-api-tools/vyos-http-api-tools_2.3_amd64.deb
repositories/sagitta/pool/main/v/vyos-intel-ixgbe/vyos-intel-ixgbe_5.20.3_amd64.deb
repositories/sagitta/pool/main/v/vyos-intel-ixgbevf/vyos-intel-ixgbevf_4.18.9_amd64.deb
repositories/sagitta/pool/main/v/vyos-intel-qat/vyos-intel-qat_4.24.0-00005-0_amd64.deb
repositories/sagitta/pool/main/v/vyos-linux-firmware/vyos-linux-firmware_20231211_all.deb
repositories/sagitta/pool/main/v/vyos-user-utils/vyos-user-utils_1.4.0+vyos1+current_all.deb
repositories/sagitta/pool/main/v/vyos-utils/vyos-utils-dbgsym_0.0.3_amd64.deb
repositories/sagitta/pool/main/v/vyos-utils/vyos-utils_0.0.3_amd64.deb
repositories/sagitta/pool/main/v/vyos-world/vyos-world_1.4.0+vyos1+current_all.deb
repositories/sagitta/pool/main/v/vyos-xe-guest-utilities/vyos-xe-guest-utilities_7.13.0+vyos1.3_amd64.deb
repositories/sagitta/pool/main/w/wide-dhcpv6/wide-dhcpv6-client-dbgsym_20080615-23_amd64.deb
repositories/sagitta/pool/main/w/wide-dhcpv6/wide-dhcpv6-client_20080615-23_amd64.deb
repositories/sagitta/pool/main/w/wide-dhcpv6/wide-dhcpv6-relay-dbgsym_20080615-23_amd64.deb
repositories/sagitta/pool/main/w/wide-dhcpv6/wide-dhcpv6-relay_20080615-23_amd64.deb
repositories/sagitta/pool/main/w/wide-dhcpv6/wide-dhcpv6-server-dbgsym_20080615-23_amd64.deb
repositories/sagitta/pool/main/w/wide-dhcpv6/wide-dhcpv6-server_20080615-23_amd64.deb
repositories/sagitta/pool/main/w/wpa/eapoltest-dbgsym_2.10-1028-g6b9c86466_amd64.deb
repositories/sagitta/pool/main/w/wpa/eapoltest_2.10-1028-g6b9c86466_amd64.deb
repositories/sagitta/pool/main/w/wpa/hostapd-dbgsym_2.10-1028-g6b9c86466_amd64.deb
repositories/sagitta/pool/main/w/wpa/hostapd_2.10-1028-g6b9c86466_amd64.deb
repositories/sagitta/pool/main/w/wpa/libwpa-client-dev_2.10-1028-g6b9c86466_amd64.deb
repositories/sagitta/pool/main/w/wpa/wpasupplicant-dbgsym_2.10-1028-g6b9c86466_amd64.deb
repositories/sagitta/pool/main/w/wpa/wpasupplicant_2.10-1028-g6b9c86466_amd64.deb
```

</details>

Additional jobs
--

These jobs aren't packages, but they are made in the same spirit to make configuration simpler. Configuration on
Jenkins side is identical to configuration for packages.

| Job                  | GIT repository                                 | Branch       | Location of Jenkinsfile                   |
|----------------------|------------------------------------------------|--------------|-------------------------------------------|
| vyos-build-container | **https://github.com/dd010101/vyos-build.git** | **equuleus** | packages/vyos-build-container/Jenkinsfile |
| vyos-build-container | **https://github.com/dd010101/vyos-build.git** | **sagitta**  | packages/vyos-build-container/Jenkinsfile |
| vyos-build-container | **https://github.com/dd010101/vyos-build.git** | **current**  | packages/vyos-build-container/Jenkinsfile |

Job `vyos-build-container` builds `vyos-build` docker container image. This image is pushed to local registry specified
with environment variable `CUSTOM_DOCKER_REPO`. The `vyos-build` docker container is used to build all packages.
This job is used as automation to do the same process as described above in
[Build patched vyos-build docker images](#build-patched-vyos-build-docker-images)
to keep the docker images up to date - this replaces the need to rebuild images from time to time and thus reduces
maintenance.
