The end of public LTS
==

**The open era of LTS/stable branches is coming to an end.
The VyOS team [already moved](https://vyos.dev/T6781) the development of LTS branches to private organization, 
and they will not publish the LTS/stables branches on their public GitHub anymore, the only people who can 
receive the copy of LTS source code are those who receive the binaries thus only those who obtain subscription.**

**The only public branches will be the `current` and whatever branch is in the stream phase (today the `circinus`).
Thus moving forward only those branches can be built up to date.**

Purpose
--

This project can be used to build up-to-date packages/images of **stream** (currently **1.5.x circinus**). 
As of now the official APT of circinus isn't public either so if you want to build custom images you need to
build packages first and currently there isn't official way to build those packages either.

You can still build equuleus/sagitta packages/images, yet they will be frozen in time and won't get any updates from
the VyOS side. Thus, new builds will get incomplete bug/security updates - only the packages that are from
Debian repositories will be updated.

The stream/circinus
---

If you are interested in the **stream** (currently **1.5.x circinus**) then can build your own 
packages/images via the scripts in the **[./new](new)** directory.


The legacy
==

**The build scripts for equuleus/sagitta should still work but the source code isn't updated anymore.**

Prologue
--

If you're trying to build VyOS equuleus/sagitta ISO image with the usual way you may see following errors:

```
E: Failed to fetch http://dev.packages.vyos.net/repositories/equuleus/dists/equuleus/InRelease  403  Forbidden [IP: 104.18.30.79 443]
E: The repository 'http://dev.packages.vyos.net/repositories/equuleus equuleus InRelease' is not signed.
E: Failed to fetch http://dev.packages.vyos.net/repositories/sagitta/dists/sagitta/InRelease  403  Forbidden [IP: 104.18.30.79 443]
E: The repository 'http://dev.packages.vyos.net/repositories/sagitta sagitta InRelease' is not signed.
```

You may also see `Sorry, you have been blocked` if you try to visit these links, but you aren't blocked - everyone
is blocked. This is due to [change in VyOS policy](https://blog.vyos.io/community-contributors-userbase-and-lts-builds)
where they don't offer their `dev.packages.vyos.net/repositories` for public anymore. This change applies only to
stable branches (like 1.3 equuleus/1.4 sagitta), you can still build current/development branch with official
repository.

You want to continue to use VyOS long term? Then you can switch to current/development branch if you think
that's good idea for your use case. If you like to use stable branch then you would need to obtain
[VyOS subscription](https://vyos.io/subscriptions/support). ~~The only other option currently is to build your own
`dev.packages.vyos.net` package repository and that's what this project is all about.~~
**There is no other option anymore.**

Making your own repository
--

### Host requirements and precautions

All examples and scripts assume clean installation of **Debian 12 (Bookworm)**. Basic installation with
`standard system utilities` is enough.

We also recommend **dedicated virtual machine**.

The build scripts are running under the `jenkins` user and thus in theory if you
execute malicious build it can compromise your Jenkins and possibly your host. That's why you want dedicated OS
and you don't want to share the Jenkins with other projects and ideally don't share the operating system with
anything else either. This risk isn't likely - it would require compromised GitHub repositories to happen.

The hardware requirements are significant:

- 16GB total RAM (8GB RAM + 8GB swap is good option)
- 100GB HDD
- CPU will make builds faster or slower, there is no hard requirement

The builds are memory hungry, but you don't need 16GB of physical RAM. You can have large swap to compensate,
and you will still get good performance this way since the above 8GB threshold is reached only few times by few builds.

### The scripts

The scripts execute all required steps with minimal interaction. The process is divided into 8 steps/scripts that
configure Jenkins, prepare the package repositories, build the packages and there is also one
additional script to build ISO.

#### Obtain the scripts

```bash
wget https://github.com/dd010101/vyos-jenkins/archive/refs/heads/master.tar.gz -O /tmp/vyos-jenkins.tar.gz
tar -xf /tmp/vyos-jenkins.tar.gz -C /tmp
mv /tmp/vyos-jenkins-master /opt/vyos-jenkins
cd /opt/vyos-jenkins
```

#### If you want to build only specific branch

Configure `BRANCH` environment variable to desired branch before you run any script.
Default or empty value means all branches. This setting is remembered, you can override by defining empty value. 

```bash
export BRANCH="sagitta"
```

#### If you want to distribute ISO

Then you should remove VyOS branding, you can do this by configuring `NOT_VYOS` environment variable to `yes` 
before you run any script. If you set `yes` then `NOTvyos` name would be used as replacement for VyOS. If you
set any other non-empty value like `someos` then this name would be used instead of `NOTvyos`. 
Beware - by default, the ISO will include VyOS branding thus you shall not distribute the ISO. This setting
is remembered, you can override by defining empty value.

```bash
export NOT_VYOS="yes"
```

#### Then execute each script and follow instructions

- `1-prereqs.sh`- installs dependencies.
- `2-jenkins.sh` - configures Jenkins, **interaction required**:
    - It asks you to **log-in into Jenkins**, after you do then confirm.
    - Then it asks you to **install recommended plugins in Jenkins**, after it's completed confirm.
    - Then it asks you to **create admin Jenkins account**, after you do then enter your username and confirm.
    - At last, it will ask you to **create Jenkins API Token**, after you do then you enter the token and confirm.
- `3-repositories.sh` - creates empty package repositories.
- `4-uncron.sh` - prepares uncron service.
- `5-docker-jobs.sh` - builds vyos-build docker images, **takes a while**.
- `6-provision-project-jobs.sh` - prepares package jobs in Jenkins.
- `7-build-project-jobs.sh` - builds package jobs, **takes a long while**.
- `8-nginx.sh` - configures nginx vhost for APT repositories.

If all went well, then all steps should complete successfully and then you can:

- `build-iso.sh` - builds the ISO :), **interaction required**, **takes a while**:
    - It asks you to specify branch equuleus or sagitta, after you do then confirm.
    - At least, it asks you to specify build-by, after you do then confirm and wait. This identifier is used
      as the `--build-by` parameter, this can be e-mail or any other identifier.
    - There is also option to change what custom packages you want to include. By default, the only additional package
      is `vyos-1x-smoketest`. If you want more or different custom packages
      then you can override the default value via the `CUSTOM_PACKAGES` env variable, for example:
      `export CUSTOM_PACKAGES="vyos-1x-smoketest emacs"`. 
      If you want to use this then please set this variable always before you build ISO.

Now you should have the ISO(s) in current directory (`/opt/vyos-jenkins`).

**If something isn't right, then see [Something is wrong](#something-is-wrong).**

You can rerun the scripts as you wish and the scripts should do only required/changed steps.
It's also good idea to do this from time to time. If your scripts are somewhat old, and you face some error, 
then please first try to download and run latest scripts.

Beware - like with any custom ISO you shall test every ISO you build with your configuration and traffic flowing.
If are interested in the Smoketest see the [Smoketest](#smoketest) action. The Smoketest isn't substitute for 
real world testing.

Jenkins will automatically detect changes and build new packages, thus if you keep build server running then 
it should keep the repositories up to date by itself. This way you can just use build-iso.sh again and again.
You should check on the Jenkins **Build History** from time to time and/or before you build ISO to make sure all 
is going well. This is the same way how the official repository works.

There is also option to shut down the OS and use it only when you need it. The Jenkins checks if any package needs
rebuild in 1 hour interval, the check if 1 hour elapsed happens each 15th minute of hour. So if you boot the OS 
and start the Jenkins, then in worse case you would need to wait up to 15 minutes (to the closest 15th minute of hour),
before rebuild of package would start. Then you shall wait before the **Build Queue** and **Build Executor Status** 
is empty, then make sure no build failed in the **Build History**, after this you can use build-iso.sh again.

### Something is wrong

You may face situation when Jenkins build may fail or doesn't produce .deb packages and thus ISO build fails
with unmet dependencies. Sometimes the Jenkins build fails for temporary reason like network/server issue, thus
find the package/job/branch in question (like linux-kernel/sagitta) and retry the build with **Build now**.

Sometimes the build steps/instructions change over time (mainly due to changes on VyOS side), and thus for example
you need to change or add additional package. If you are using automated scripts then make sure you have the latest
version, if not then download scripts again and rerun all them.

There are two logs you should check for pointers.

1) In Jenkins - find the job/packages of your interest - select branch of interest and find last run with
   `Git SHA1: ...`. There may be other runs without `Git SHA1: ...` - those aren't build runs, those are
   branch indexing runs that check if package needs rebuild - ignore those. If you don't see any runs then
   use the **Build now** action to trigger new build run. In specific run you should see **Console Output**.
2) The `uncron.service` has log file you can access via `journalctl --no-pager -b -u uncron.service`, look
   for package in question and check if there isn't error output or `Job exited with code 0` other than 0.

If you face errors that don't make sense then it's likely your docker container is outdated or your Jenkins
configuration is missing some pieces. Thus, as first thing you can try to rebuild the
docker container and if that doesn't help then verify all the Jenkins configuration is in its place.

Smoketest
--

VyOS has testing procedure called smoketest. This test checks mainly configuration, it's not complete test, 
it will only tell you if something is very wrong, passed test doesn't mean image will be necessarily fully
functional - with that said it's still useful somewhat, just don't put too much trust in it. It also has tendencies
to generate a lot of false positives, beware.

### Requirements

You will need host that supports virtualization and thus can run KVM. Main test (`make testd`) takes around two hours
to complete, additional tests aren't that slow.

There is requirement to include `vyos-1x-smoketest` package in your ISO image build. Automated scripts by default
include the `vyos-1x-smoketest` unless you change it via `CUSTOM_PACKAGES`. If you build ISO via other means
then you need to include the package via the `--custom-package vyos-1x-smoketest` option when you run 
`./configure` (equuleus) or `./build-vyos-image iso` (sagitta).

### Testing environment

The automated scripts purge the vyos-build and rename the ISO, thus we need to reverse this if we want to run tests.
If you build your ISO manually then you can skip these steps since you should already have `vyos-build` repository
with the ISO in the `build` directory with the default name.

Clone the `vyos-build` repo:

```bash
git clone https://github.com/notvyos/vyos-build.git
cd vyos-build
```

Switch to correct branch (`equuleus` or `sagitta`):

```bash
git checkout sagitta
```

Copy your ISO to the `build` directory as `build/live-image-amd64.hybrid.iso`:

```bash
mkdir build
cp THE_PATH_TO_YOUR_ISO build/live-image-amd64.hybrid.iso
```

Change the `THE_PATH_TO_YOUR_ISO` to whatever location and name your ISO has.

### Workaround

There is known issue with smoketest that it will fail if you have too many CPU cores/threads. The test is designed
to use half of your cores, but it will fail if calculates more than 4, thus if you have 8 or more cores/threads
then test likely will fail. If you do apply this patch to cap cores to 3:

```bash
sed -i 's~cpu /= 2~cpu = 3~' scripts/check-qemu-install
```

More cores don't increase speed, the test is single thread anyway, it usually uses <2 cores and thus 3 is more than
enough. More cores will not speed up the test - it will only make the test fail due to OOM
inside the test virtual machine.

### Dependencies

Install dependencies:

```bash
apt install qemu-kvm python3-tomli python3-pexpect python3-git python3-jinja2 python3-psutil \
  sudo live-build pbuilder devscripts python3-pystache gdisk kpartx dosfstools
```

### The tests

There are multiple tests executed via the `make`:

**CLI configuration test:**

This test aims to verify that commands in the `configure` mode have correct result after `commit`. 
For example - if some command configures routes, then the test checks if those routes are correctly propagated
to the underlying system - in this example to the kernel/OS.

```bash
make testd
```

There is also `make test` that runs identical tests to the `make testd` and the difference is if 
the `vyos-configd.service` service is enabled or not. VyOS enables this service by default, that's 
why `make testd` is more accurate since it represents how VyOS runs in the wild.

**Configuration file load test:**

This test loads various `boot.config` like files and checks if `commit` doesn't fail.

```bash
make testc
```

**RAID1 test:**

This checks if the MDADM RAID1 installation works and if MDADM is able to resync after disk failure.

```bash
make testraid
```

If you encounter failures please rerun the test multiple times - there are known race conditions that can occur and
this causes false-positives.

You can as well run smoketest directly from **installed** VyOS, but you need many network interfaces otherwise
some tests will fail. The test is expecting 8 or more network ports. You do it by simply including
`vyos-1x-smoketest` package in your ISO image build. Then you can boot and run `vyos-smoketest`.
I'm not sure if all 8 are required but with few the test will fail for sure.
Also make sure you have <= 4 cores/threads and 4GB or more of RAM. If you have more cores/threads then you need more
RAM as well, try to keep it 1:1. Smoketest eats a lot of RAM and more so if you have more cores/threads.
