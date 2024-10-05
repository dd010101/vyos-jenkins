#!/usr/bin/env python3
import argparse
import logging
import os.path
from shlex import quote
import shutil
import stat
import subprocess
import sys
from time import time

import pendulum

from github import GitHub
from helpers import Cache, setup_logging


class Builder:
    directory = None
    docker_image = None
    updated_repos = None
    debs = [] # TODO: remove me

    def __init__(self, branch, vyos_build_repo, single_package, dirty_build, ignore_missing_binaries, skip_build):
        self.branch = branch
        self.vyos_build_repo = vyos_build_repo
        self.single_package = single_package
        self.dirty_build = dirty_build
        self.ignore_missing_binaries = ignore_missing_binaries
        self.skip_build = skip_build

        self.project_dir = os.path.realpath(os.path.dirname(__file__))
        self.github = GitHub()
        self.cache = Cache("data/builder-cache-%s.json" % self.branch, dict, {})

    def build(self):
        if self.single_package is not None:
            logging.info("Executing single package build of %s" % self.single_package)

        logging.info("Building packages for %s" % self.branch)
        packages = self.get_packages()

        self.directory = os.path.join(os.getcwd(), "build", self.branch)
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

        logging.info("Pulling vyos-build docker image")
        self.docker_image = "vyos/vyos-build:%s" % self.branch
        self.execute("docker pull %s" % quote(self.docker_image), passthrough=True)

        # TODO: filter already built packages?
        # Compare previous commit hash, if identical then skip.
        # If hash differs then lookup the history until previous commit hash and compare change patterns if changed files.
        # Thus we will only build packages that did change or were not built yet.
        # If mismatch then delete repo and build.

        self.updated_repos = []
        for package in packages.values():
            if self.single_package is not None and self.single_package != package["package_name"]:
                continue

            logging.info("Processing package: %s" % package["package_name"])
            self.build_package(package)

        for deb in self.debs:
            print(deb)

    def build_package(self, package):
        repo_name = package["repo_name"]

        new = False
        if repo_name not in self.updated_repos:
            self.updated_repos.append(repo_name)

            repo_path = os.path.join(self.directory, repo_name)
            if os.path.exists(repo_path) and not self.dirty_build:
                shutil.rmtree(repo_path)

            if package["build_type"] == "dpkg-buildpackage":
                if not os.path.exists(repo_path):
                    os.makedirs(repo_path)
                repo_path = os.path.join(repo_path, "sources")

            if not os.path.exists(repo_path):
                logging.info("Cloning repository %s" % package["git_url"])
                self.execute("git clone -b %s --single-branch %s %s" % self.quote_all(
                    self.branch, package["git_url"], repo_path
                ))
                new = True
            else:
                logging.info("Pulling repository %s" % package["git_url"])
                self.execute("git -C %s pull" % self.quote_all(repo_path))
        else:
            logging.info("Using shared repository %s" % package["git_url"])

        if package["build_type"] == "build.py":
            my_directory = os.path.join(self.directory, "vyos-build", package["path"])
            if not self.skip_build or new:
                self.docker_run("bash -i ./build.py", "/vyos/%s" % package["path"])

        elif package["build_type"] == "dpkg-buildpackage":
            my_directory = os.path.join(self.directory, repo_name)
            virtual_dir = "/vyos-%s" % package["package_name"]

            scripts_dir = os.path.join(self.project_dir, "scripts")
            virtual_scripts = "%s-scripts" % virtual_dir

            build_script = "generic-build-script.sh"
            custom_build_script = os.path.join(scripts_dir, "%s.sh" % package["package_name"])
            if os.path.exists(custom_build_script):
                build_script = os.path.basename(custom_build_script)

            sources_dir = os.path.join(virtual_dir, "sources")
            if not self.skip_build or new:
                self.docker_run("bash -i %s/%s" % (virtual_scripts, build_script), sources_dir, extra_mounts=[
                    (my_directory, virtual_dir),
                    (scripts_dir, virtual_scripts),
                ])

        else:
            logging.error("Unknown build_type: %s" % package)
            return

        dsc_files, sources_files, binary_files = self.scan_for_dist_files(my_directory)
        if len(binary_files) == 0:
            message = "%s: something is wrong, no binary files found" % package["package_name"]
            if self.ignore_missing_binaries:
                logging.error(message)
            else:
                raise Exception(message)

        self.fill_repository(dsc_files, sources_files, binary_files)
        self.debs.extend(binary_files)

    def scan_for_dist_files(self, directory):
        dsc_files = []
        sources_files = []
        binary_files = []
        for parent, directories, files in os.walk(directory):
            for file_name in files:
                path = os.path.join(parent, file_name)
                name, ext = os.path.splitext(file_name)
                ext = ext.lower()[1:]
                if ext == "dsc":
                    dsc_files.append(path)
                elif ext.startswith("tar") and ext.endswith("z"):
                    sources_files.append(path)
                elif ext == "deb":
                    if "build-deps_" in name:
                        continue
                    binary_files.append(path)

        return dsc_files, sources_files, binary_files

    def fill_repository(self, dsc_files, sources_files, binary_files):
        # TODO: reprepro
        pass

    def get_packages(self):
        packages_timestamp = self.cache.get("packages_timestamp")
        packages = self.cache.get("packages")

        if not packages_timestamp or not packages or packages_timestamp <= time() - 3600 * 24:
            logging.info("Fetching vyos repository list")
            repositories = self.github.find_repositories("org", "vyos")

            logging.info("Analyzing package metadata")
            packages = self.github.analyze_repositories_workflow("vyos", repositories, self.branch)

            self.cache.set("packages_timestamp", time())
            self.cache.set("packages", packages)

        else:
            date = pendulum.from_timestamp(float(packages_timestamp)).in_tz("local").format("YYYY-MM-DD HH:mm:ss")
            logging.info("Using previously generated package metadata (%s)" % date)

        return packages

    def docker_run(self, command, work_dir, extra_mounts=None):
        pieces = [
            "docker run --rm -it",
            "-v %s:/vyos" % quote(os.path.join(self.directory, "vyos-build")),
        ]

        if extra_mounts is not None:
            for mount in extra_mounts:
                pieces.append("-v %s:%s" % self.quote_all(*mount))

        pieces.extend([
            "-w %s --privileged --sysctl net.ipv6.conf.lo.disable_ipv6=0" % quote(work_dir),
            "-e GOSU_UID=%s -e GOSU_GID=%s" % (os.getuid(), os.getgid()),
            self.docker_image,
            command,
        ])

        command = " ".join(pieces)
        return self.execute(command, passthrough=True)

    def execute(self, command, passthrough=False, **kwargs):
        if passthrough:
            kwargs["stdout"] = sys.stdout
            kwargs["stderr"] = sys.stderr

        if "stderr" not in kwargs:
            kwargs["stderr"] = subprocess.STDOUT
        if "shell" not in kwargs:
            kwargs["shell"] = True

        if passthrough:
            return subprocess.check_call(command, **kwargs)
        else:
            stdout = subprocess.check_output(command, **kwargs)
            return stdout.decode("utf-8")

    def quote_all(self, *args):
        quoted = []
        for arg in args:
            quoted.append(quote(arg))
        return tuple(quoted)


if __name__ == "__main__":
    setup_logging()

    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("branch", help="VyOS branch (current, circinus)")
        parser.add_argument("--single-package", help="Build only this package")
        parser.add_argument("--dirty-build", action="store_true",
                            help="Build with reused sources - don't clone fresh sources")
        parser.add_argument("--ignore-missing-binaries", action="store_true")
        parser.add_argument("--skip-build", action="store_true")
        parser.add_argument("--vyos-build-repo", default="https://github.com/vyos/vyos-build")
        args = parser.parse_args()

        builder = Builder(**vars(args))
        builder.build()

    except KeyboardInterrupt:
        exit(1)
    except Exception as e:
        logging.exception(e)
        exit(1)
