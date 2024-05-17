WORK IN PROGRESS
--

I recommend debian and dedicated virtual machine for security purposes. Since this setup isn't isolating the build
from the host and in theory Jenkins can compromise your build host if you execute some malicious
build so don't share the os with anything else. This isn't the ideal setup - this is just quick and dirty.

I use bullseye virtualbox VM on my desktop PC. Bookworm should work as well. Some builds are RAM heavy
and I did see OOM crashes if I had 4GB RAM so make sure you have 8GB or better 16GB RAM and/or
enough swap space to compensate. You will also build some vast packages so fast CPU is good idea
because you may need to recompile kernel multiple times for debugging purposes.

I assume single shared host for jenkins and x86 node (Built-In Node). I also assume the SSH host for reprepro
repositories is the same as the jenkins host. Not recommended, but it's the simple way to get experimental
environment started all in one. Normally you would have these roles split into more VMs but that's redundant
for our purpose and thus everything is on one host under one single user.

The basic mode of operation is that Jenkins fetches sources from repository then executes build commands
inside docker container (vyos-build from dockerhub), at last Jenkins picks up what docker produces and puts
it over SSH into reprepro repository. Thus, Jenkins itself is not doing the build - it delegates build
to docker container and thus if you see for example that the build fails due to missing cmake don't try to
install cmake on the Jenkins host or as Jenkins plugin, since that's not how it is used. In this case you would need
to install such package inside the docker container.

Install jenkins, and it's java
--

Just follow the usual guide via APT https://www.jenkins.io/doc/book/installing/linux/#debianubuntu
Install java, then jenkins. Let setup guide to install recommended plugins.

Install docker
--

Just follow the usual guide via APT https://docs.docker.com/engine/install/debian/

Allow jenkins to use docker:

```
usermod -a -G docker jenkins
```

UID / GID issue
--
Most of Jenkinfiles do respect your UID/GID but not all, for
example https://github.com/vyos/vyos-build/blob/equuleus/packages/linux-kernel/Jenkinsfile has hardcoded UID and GID to
1006 and this will fail build if you don't have 1006:1006 user.

That's why we want change jenkins to 1006/1006:

```
usermod -u 1006 jenkins
groupmod -g 1006 jenkins
chown -R jenkins:jenkins /var/lib/jenkins/ /var/cache/jenkins/ /var/log/jenkins/
```

After adding docker group and/or after UID/GID change restart jenkins
--

```
systemctl restart jenkins.service
```

Build patched vyos-build docker image and create local registry
--

The vyos/vyos-build docker image from dockerhub doesn't work for all packages as of now, thus I made some
patches to make it work. If this changed in future then this step can be skipped.

This may take a while.

```
git clone https://github.com/dd010101/vyos-build.git
cd vyos-build

git checkout equuleus
cd docker
docker build . -t vyos/vyos-build:equuleus

git checkout sagitta
docker build . -t vyos/vyos-build:sagitta

docker run -d -p 5000:5000 --restart always --name registry registry:2.7
```

Install jenkins plugins
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

**Limit Number of executors** to 1 (otherwise builds may crash due to reprepro concurrency).

**Add tags**

- Docker
- ec2_amd64

Separated by space thus "Docker ec2_amd64" as result

Configure DEV_PACKAGES_VYOS_NET_HOST variable and add global vyos-build jenkins library
--
**Manage Jenkins -> System**

**Global properties -> Environmental Variables -> Add**

```
Name: DEV_PACKAGES_VYOS_NET_HOST
Value: jenkins@<ip of the host system>
```

This user+IP/host will be used for SSH access to reprepro, it can be another host or you can point this to the jenkins
host as well, the ip needs to be accesible from docker container thus this should be LAN IP, localhost will not work. I
assume everything is on single host thus this IP is IP of the jenkins host. Mine is `172.17.17.17` so if you see it
somewhere replace it with your own.

**Global Pipeline Libraries -> Add**

```
Name: vyos-build
Project repository: https://github.com/dd010101/vyos-build.git
```

Currently patched version of vyos-build is required, in the future the official 
`https://github.com/vyos/vyos-build.git` may work but doesn't currently.

**Declarative Pipeline (Docker)**

(this applies only if using patched vyos-build docker image)

```
Docker registry URL: http://<ip of the host system>:5000
```

Credentials for ssh-agent
--
You need to set up SSH key authentication for the host specified in `DEV_PACKAGES_VYOS_NET_HOST` variable. 
Basically we want to allow jenkins to SSH into itself with its own SSH key.

Login as target user:

```
su - jenkins
```

Generate regular SSH key:

```
ssh-keygen -t ed25519 -C "jenkins"
```

Update authenticated_keys to allow jenkins to log in to itself, something like this:

```
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
```

Accept signature and verify SSH works:

```
ssh <ip of the host system>
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

Create expected folder structure, prepare reprepro config and give jenkins access, this is done for each release
codename.

Set RELEASE name:

```
export RELEASE=equuleus
```

or


```
export RELEASE=sagitta
```

...

Then create reprepro repository **REPLACE \<your singing pub key>**:

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
SignWith: <your singing pub key>
EOF

cat << EOF > $REPOSITORY/conf/options
verbose
EOF

chown -R jenkins: $REPOSITORY
```

uncron
--
All SSH commands are wrapped by this command, normally it would be calling this https://github.com/vyos/uncron but you
can just replace it with dummy passthrough alias to execute reprepro commands directly.

```
cat << EOF > /usr/local/bin/uncron-add
#!/bin/bash
bash -c "\$1"
EOF

chmod +x /usr/local/bin/uncron-add
```

Multibranch Pipelines
--
Each Jenkinsfile needs its own Multibranch Pipeline, the setup is the same for all packages, and you just adjust
location of Jenkinsfile and/or GIT repository to whatever you want to build.

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

(leave defaults)

**Build Configuration -> Mode (by Jenkinsfile)**
```
Script Path: packages/dropbear/Jenkinsfile
```
(if you want to bulild package from vyos/vyos-build repository)


```
Script Path: Jenkinsfile
```

(or leave just Jenkinsfile if you want to build repository like vyos/vyos-1x where there is just one package)

If someone made script to create Multibranch Pipelines automatically from list of repos/Jenkinsfile locations
that would be nice since this is very repetitive to do via the GUI.

Try to build
--

Now it's possible to select some **Multibranch Pipeline**, select your **branch**, and you can press build button 
to see what happens! If all is well you should see .deb appearing in 
`/home/sentrium/web/dev.packages.vyos.net/public_html/repositories/`:

```
find /home/sentrium/web/dev.packages.vyos.net/public_html/repositories/ -name *.deb -print
```

If build fails then click the specific build number and check **Console Output** for hints why it does so.

If you use your own version of package for debugging purposes (not the one from vyos github) then your need to hack
the Global Pipeline Library (see above). Just add `return false` before the return in 
`vyos-build/vars/isCustomBuild.groovy` and use your own local clone of the `vyos-build` in Global Pipeline Library.
Otherwise, the build skips the reprepro step, and thus you won't see .deb appearing in your reprepro repository even
if the build is successful - quite confusing.

How to try to build ISO
--

You can try to build ISO to get idea what packages are missing.

Use the default procedure to build ISO (via docker) but you need to specify your `--vyos-mirror` and your gpg singing 
key `--custom-apt-key`. 

To make `--vyos-mirror` is easy, you just install your favorite webserver and point the webroot
to `/home/sentrium/web/dev.packages.vyos.net/public_html/repositories/`. For example nginx vhost looks
something like this:
```
server {
	listen 80 default_server;
	listen [::]:80 default_server;

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
2) Mount your `apt.gpg.key` when your running `docker run` by adding `-v /where/is/your/key:/opt/apt.gpg.key`
3) When you running `./configure` (equuleus) or `./build-vyos-image` (sagitta) add your mirror
`--vyos-mirror http://172.17.17.17/equuleus` or `--vyos-mirror http://172.17.17.17/sagitta` and your singing key
` --custom-apt-key /opt/apt.gpg.key`.
4) Now the builder uses your mirror instead of `http://dev.packages.vyos.net/`.
