#!/usr/bin/env python3
import argparse
import logging
import os.path
import re
from shlex import quote
import shutil
from time import time

import pendulum

from lib.apt import Apt
from lib.cache import Cache
from lib.git import Git
from lib.github import GitHub
from lib.helpers import setup_logging, quote_all, execute, ProcessException


class Builder:
    directory = None
    docker_image = None
    updated_repos = None
    apt = None

    def __init__(self, branch, single_package, dirty_build, ignore_missing_binaries, skip_build,
                 skip_apt, force_build):
        self.branch = branch
        self.single_package = single_package
        self.dirty_build = dirty_build
        self.ignore_missing_binaries = ignore_missing_binaries
        self.skip_build = skip_build
        self.skip_apt = skip_apt
        self.force_build = force_build

        self.project_dir: str = os.path.realpath(os.path.dirname(__file__))
        self.github = GitHub()
        self.cache = Cache(os.path.join(self.project_dir, "build", "builder-cache-%s.json" % self.branch), dict, {})

    def build(self):
        if self.single_package is not None:
            logging.info("Executing single package build of %s" % self.single_package)

        logging.info("Building packages for %s" % self.branch)
        packages = self.get_packages_metadata()

        self.directory = os.path.join(os.getcwd(), "build", self.branch)
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

        self.apt = Apt(self.project_dir, self.branch, self.directory)

        logging.info("Pulling vyos-build docker image")
        self.docker_image = "vyos/vyos-build:%s" % self.branch
        execute("docker pull %s" % quote_all(self.docker_image), passthrough=True)

        self.updated_repos = []
        for package in packages.values():
            if self.single_package is not None and self.single_package != package["package_name"]:
                continue

            logging.info("Processing package: %s" % package["package_name"])
            self.build_package(package)

        logging.info("Done, see the result in: %s" % self.apt.get_repo_dir())

    def build_package(self, package):
        repo_name = package["repo_name"]

        my_state = self.cache.get(package["package_name"], default={}, data_type=dict)
        if "hash" not in my_state:
            my_state["hash"] = None

        repo_path = os.path.join(self.directory, repo_name)
        parent_path = repo_path

        if package["build_type"] == "dpkg-buildpackage":
            if not os.path.exists(repo_path):
                os.makedirs(repo_path)
            repo_path = os.path.join(repo_path, "sources")

        git = Git(repo_path)
        try:
            changed = git.resolve_changes(package["change_patterns"], my_state["hash"])
            if not changed and not self.force_build:
                logging.info("Package is up to date, skipping build")
                return
        except ProcessException as e:
            if "not a git repository" in str(e):
                shutil.rmtree(parent_path)
            else:
                raise

        new = False
        if repo_name not in self.updated_repos:
            self.updated_repos.append(repo_name)

            if os.path.exists(parent_path) and not self.dirty_build:
                shutil.rmtree(parent_path)

            if not os.path.exists(repo_path):
                logging.info("Cloning repository %s" % package["git_url"])
                git.clone(package["git_url"], package["branch"])
                new = True
            else:
                logging.info("Pulling repository %s" % package["git_url"])
                git.pull()
        else:
            logging.info("Using shared repository %s" % package["git_url"])

        if package["build_type"] == "build.py":
            my_directory = os.path.join(self.directory, "vyos-build", package["path"])
            if not self.skip_build or new:
                self.docker_run("bash -i -c 'python3 ./build.py'", "/vyos/%s" % package["path"])

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

        dsc_files, binary_files = self.apt.scan_for_dist_files(my_directory)
        if len(binary_files) == 0:
            message = "%s: something is wrong, no binary files found" % package["package_name"]
            if self.ignore_missing_binaries:
                logging.error(message)
            else:
                raise Exception(message)
        else:
            my_state["hash"] = git.get_last_commit_hash()

        if not self.skip_apt or new:
            self.apt.fill_apt_repository(dsc_files, binary_files)

        self.cache.set(package["package_name"], my_state)

    def docker_run(self, command, work_dir, extra_mounts=None):
        pieces = [
            "docker run --rm -it",
            "-v %s:/vyos" % quote(os.path.join(self.directory, "vyos-build")),
        ]

        if extra_mounts is not None:
            for mount in extra_mounts:
                pieces.append("-v %s:%s" % quote_all(*mount))

        pieces.extend([
            "-w %s --privileged --sysctl net.ipv6.conf.lo.disable_ipv6=0" % quote(work_dir),
            "-e GOSU_UID=%s -e GOSU_GID=%s" % (os.getuid(), os.getgid()),
            self.docker_image,
            command,
        ])

        command = " ".join(pieces)
        return execute(command, passthrough=True)

    def get_packages_metadata(self):
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
        parser.add_argument("--skip-apt", action="store_true")
        parser.add_argument("--force-build", action="store_true")
        args = parser.parse_args()

        builder = Builder(**vars(args))
        builder.build()

    except KeyboardInterrupt:
        exit(1)
    except Exception as e:
        logging.exception(e)
        exit(1)
