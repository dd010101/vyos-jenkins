#!/usr/bin/env python3
import argparse
from datetime import datetime
import logging
import os.path
from shlex import quote
from time import time, monotonic

from lib.apt import Apt
from lib.cache import Cache
from lib.debranding import Debranding
from lib.docker import Docker
from lib.git import Git
from lib.github import GitHub
from lib.helpers import setup_logging, ProcessException, refuse_root, get_my_log_file, data_dir, build_dir, scripts_dir


class PackageBuilder:
    my_build_dir = None
    docker_image = None
    updated_repos = None
    apt = None
    docker = None

    def __init__(self, branch, single_package, dirty_build, ignore_missing_binaries, skip_build, skip_apt,
                 force_build, vyos_build_docker, rescan_packages, debranding: Debranding):
        self.branch = branch
        self.single_package = single_package
        self.dirty_build = dirty_build
        self.ignore_missing_binaries = ignore_missing_binaries
        self.skip_build = skip_build
        self.skip_apt = skip_apt
        self.force_build = force_build
        self.vyos_build_docker = vyos_build_docker
        self.rescan_packages = rescan_packages
        self.debranding = debranding

        self.github = GitHub()
        self.cache = Cache(os.path.join(data_dir, "builder-cache-%s.json" % self.branch), dict, {})

    def build(self):
        begin = monotonic()
        if self.single_package is not None:
            logging.info("Executing single package build of %s" % self.single_package)

        logging.info("Building packages for %s" % self.branch)
        packages = self.get_packages_metadata()

        self.my_build_dir = os.path.join(build_dir, self.branch)
        if not os.path.exists(self.my_build_dir):
            os.makedirs(self.my_build_dir)

        self.apt = Apt(self.branch, self.my_build_dir)

        logging.info("Pulling vyos-build docker image")
        vyos_build_repo = os.path.join(os.path.join(self.my_build_dir, "vyos-build"))
        self.docker = Docker(self.vyos_build_docker, self.branch, vyos_build_repo)
        self.docker.pull()

        self.updated_repos = []
        found = 0
        built = 0
        for package in packages.values():
            found += 1
            if self.single_package is not None and self.single_package != package["package_name"]:
                continue

            logging.info("Processing package: %s" % package["package_name"])
            self.build_package(package)
            built += 1

        if built == 0:
            if self.single_package is not None:
                logging.error("Specified --single-package=%s was not found" % self.single_package)
            else:
                if found == 0:
                    logging.error("Something's wrong, no packages were found!")
                else:
                    logging.error("Something's wrong, no packages were built but these were found: %s" % packages)
            exit(1)

        elapsed = round(monotonic() - begin, 3)
        logging.info("Done in %s seconds, see the result in: %s" % (elapsed, self.apt.get_repo_dir()))

    def build_package(self, package):
        repo_name = package["repo_name"]

        my_state = self.cache.get(package["package_name"], default={}, data_type=dict)
        if "hash" not in my_state:
            my_state["hash"] = None

        repo_path = os.path.join(self.my_build_dir, repo_name)
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
                self.docker.rmtree(parent_path)
            else:
                raise

        new = False
        if repo_name not in self.updated_repos:
            self.updated_repos.append(repo_name)

            if os.path.exists(parent_path) and not self.dirty_build:
                # We want to delete original repo and do fresh clone to clean cached build files.
                self.docker.rmtree(parent_path)

            if not os.path.exists(repo_path):
                logging.info("Cloning repository %s" % package["git_url"])
                git.clone(package["git_url"], package["branch"])
                new = True
            else:
                logging.info("Pulling repository %s" % package["git_url"])
                git.pull()
        else:
            logging.info("Using shared repository %s" % package["git_url"])

        self.debranding.remove_package_branding(repo_path, package["package_name"])

        if package["build_type"] == "build.py":
            my_directory = os.path.join(self.my_build_dir, "vyos-build", package["path"])
            if not self.skip_build or new:
                # It's important to run bash in interactive mode, non-interactive shell breaks dependency on .bashrc.
                # It's also required to call python explicitly since some scripts don't have correct shebang.
                self.docker.run("bash -i -c 'python3 ./build.py'", work_dir="/vyos/%s" % package["path"])

        elif package["build_type"] == "dpkg-buildpackage":
            my_directory = os.path.join(self.my_build_dir, repo_name)
            virtual_dir = "/vyos-%s" % package["package_name"]

            virtual_scripts = "%s-scripts" % virtual_dir

            build_script = "generic-build-script.sh"
            custom_build_script = os.path.join(scripts_dir, "%s.sh" % package["package_name"])
            if os.path.exists(custom_build_script):
                build_script = os.path.basename(custom_build_script)

            sources_dir = os.path.join(virtual_dir, "sources")
            if not self.skip_build or new:
                # Again, interactive shell is essential.
                virtual_build_script = os.path.join(virtual_scripts, build_script)
                self.docker.run("bash -i %s" % quote(virtual_build_script), work_dir=sources_dir, extra_mounts=[
                    (my_directory, virtual_dir),
                    (scripts_dir, virtual_scripts),
                ])

        else:
            logging.error("Unknown build_type: %s" % package)
            return

        dsc_files, binary_files = self.apt.scan_for_dist_files(my_directory)
        if len(binary_files) == 0:
            message = "%s: something is wrong, no binary files found" % package["package_name"]
            message += ", build dir: %s," % my_directory
            message += ", log file: %s" % get_my_log_file()
            if self.ignore_missing_binaries:
                logging.error(message)
            else:
                raise Exception(message)
        else:
            my_state["hash"] = git.get_last_commit_hash()

        if not self.skip_apt or new:
            self.apt.fill_apt_repository(dsc_files, binary_files)

        self.cache.set(package["package_name"], my_state)

    def get_packages_metadata(self):
        packages_timestamp = self.cache.get("packages_timestamp")
        packages = self.cache.get("packages")

        if not packages_timestamp or not packages or packages_timestamp <= time() - 3600 * 24 or self.rescan_packages:
            logging.info("Fetching vyos repository list")
            repositories = self.github.find_repositories("org", "vyos")

            logging.info("Analyzing package metadata")
            packages = self.github.analyze_repositories_workflow("vyos", repositories, self.branch)

            self.cache.set("packages_timestamp", time())
            self.cache.set("packages", packages)

        else:
            date = datetime.fromtimestamp(float(packages_timestamp)).astimezone().strftime("%Y-%m-%d %H:%M:%S")
            logging.info("Using previously generated package metadata (%s)" % date)

        return packages


if __name__ == "__main__":
    setup_logging(name="package_builder")

    try:
        refuse_root()

        debranding = Debranding()

        parser = argparse.ArgumentParser()
        parser.add_argument("branch", help="VyOS branch (current, circinus)")
        parser.add_argument("--single-package", help="Build only this package")
        parser.add_argument("--dirty-build", action="store_true",
                            help="Build with reused sources - don't clone fresh sources")
        parser.add_argument("--ignore-missing-binaries", action="store_true")
        parser.add_argument("--skip-build", action="store_true")
        parser.add_argument("--skip-apt", action="store_true")
        parser.add_argument("--force-build", action="store_true")
        parser.add_argument("--rescan-packages", action="store_true")
        parser.add_argument("--vyos-build-docker", default="vyos/vyos-build",
                            help="Default option uses vyos/vyos-build from dockerhub")

        debranding.populate_cli_parser(parser)

        args = parser.parse_args()
        values = vars(args)

        debranding.extract_cli_values(values)

        builder = PackageBuilder(debranding=debranding, **values)
        builder.build()

    except KeyboardInterrupt:
        exit(1)
    except Exception as e:
        logging.exception(e)
        logging.error("Something went wrong, log file: %s" % get_my_log_file())
        exit(1)
