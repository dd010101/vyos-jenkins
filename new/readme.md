New build method (only for **circinus/1.5.x** or **current** branch)
==

New build method was developed since the VyOS team dropped support for the Jenkins build method.
The new method is much simplified (thanks to removal of Jenkins), has few steps and only basic dependencies.
This should make it easier to run anywhere (compared to the old method). 
The only external services it uses is the Docker. It doesn't modify anything in the system apart from using 
the docker to manage its own container. Thus, the new method is big shift from the Jenkins method - they have
practically nothing in common.

This quick start guide is made for Debian or Ubuntu (tested on Debian Bookworm and Ubuntu 24.04) but it can
be easily adopted to any other distro that also uses the APT package manager. There is no real dependency
on the distro so if you install dependencies manually then you can run this on any other Linux system. 

Build environment
--

This quick start script will prepare the build environment with new `vyos_bld` user, but you may as well use your 
user or any other regular user. If you want to use different or existing user then simply adapt or skip the steps 
with the `vyos_bld` user.

If you want to use other APT-based distro than Debian/Ubuntu then please install 
[Docker](https://docs.docker.com/engine/install/) first according to your distro and then continue.

Execute installation as `root` or use `sudo -i` if you don't have `root` account.

```bash
apt update -y && apt install -y git sudo
useradd -s /bin/bash -m vyos_bld
sudo -u vyos_bld -i git clone https://github.com/dd010101/vyos-jenkins.git
/home/vyos_bld/vyos-jenkins/new/install-dependencies.sh
usermod -aG docker vyos_bld
```

The `root` account can't be used for the build due to limitation of build scripts. That's why you need to use any
regular user. Thus, the `root` privileges are used only to for this part and everything following is executed
as regular user.

Now you should have the environment ready to use. You can use it to build or update package repository
as well to build images (ISO). You should keep the environment around since then only changed 
packages are rebuilt and this will make the next build faster. 

If you want you may as well build everything every time - then delete the `vyos-jenkins` directory and clone again.

There is no reason you need to use distro with APT, you can use any distro you want.
To do so you need to install dependencies via other means than APT, follow the contents of the
`vyos-jenkins/new/install-dependnecies.sh` to see what you need to install with your package manager.
This shall be the only distribution-dependent part.

Usage
--

Log-in as the `vyos_bld` user or user of your choice:

```bash
sudo -u vyos_bld -i
```

To update the scripts:

```bash
git -C ~/vyos-jenkins pull
```

Firstly build or update the packages (this will take long time, mostly for the first time):

```bash
~/vyos-jenkins/new/package_builder.py circinus
```

If you call package builder again it will check if any packages received new commits and automatically only rebuild
those packages where it's needed.

Then you can build image (ISO) from those packages (this will take some time):

```bash
~/vyos-jenkins/new/image_builder.py circinus
```

Now you should have ISO image available in your current directory.

NOTvyos
--

Given the public VyOS repositories don't receive updates anymore I did decide to create
[NOTvyos](https://github.com/NOTvyos) collection of [VyOS](https://github.com/vyos) repositories and those
[get updated](./tools/tarball-repo-sync.py) from [VyOS Stream](https://vyos.net/get/stream/) tarballs.
Currently, the default options use the VyOS repositories, 
thus we need to use extra options to use the updated NOTvyos repositories instead.

**If we want to switch between VyOS and NOTvyos then we need to start fresh, delete the vyos-jenkins repository
and fetch fresh clone (or at least purge the `new/build` and `new/data` directories).**

Extra options for package build:

```bash
~/vyos-jenkins/new/package_builder.py circinus --clone-org NOTvyos
```

Extra options for image build:

```bash
~/vyos-jenkins/new/image_builder.py circinus --vyos-build-git https://github.com/NOTvyos/vyos-build.git
```

Extra options
--

Both commands have optional arguments for customization and debugging, use `--help` to see all options:

```bash
~/vyos-jenkins/new/package_builder.py --help
~/vyos-jenkins/new/image_builder.py --help
```

Directory structure
--

- **./apt/** - This directory contains the APT repository containing packages, and it's used to build the image.
- **./build/** - Temporary directory used for build of packages and images, you can delete these files, they will
  be recreated on next build. These files are also used to speed up and save resources when checking if packages
  were updated so it's better to leave them between builds to speed up the next build.
- **./data/** - Persistent data used for the build, you shouldn't delete those files unless you know what you're doing,
  mainly the `./data/.gnupg` directory is important to keep because otherwise you need to delete everything and 
  rebuild everything since this directory stores the key to sign packages.
- **./lib/**, **./resources/**, **./scripts/** - Internally used files, they shall not be modified.
