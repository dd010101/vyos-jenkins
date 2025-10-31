#!/usr/bin/env python3
import argparse
from datetime import datetime
import logging
import os.path
from shlex import quote
from time import time, monotonic

import tomlkit

from lib.apt import Apt
from lib.debranding import Debranding
from lib.docker import Docker
from lib.git import Git
from lib.helpers import setup_logging, ProcessException, refuse_root, get_my_log_file, data_dir, build_dir, scripts_dir, \
    quote_all, TerminalTitle, ensure_directories, replace_github_repo_org, sanitize_filename
from lib.objectstorage import ObjectStorage
from lib.packagedefinitions import PackageDefinitions
from lib.scripting import Scripting


class PackageBuilder:
    my_build_dir = None
    docker_image = None
    updated_repos = None
    apt = None
    docker = None

    def __init__(self, branch, analyze_org, clone_org, single_package, dirty_build, ignore_missing_binaries,
                 skip_build, skip_apt, force_build, vyos_build_docker, rescan_packages, pre_build_hook,
                 debranding: Debranding):
        self.branch = branch
        self.analyze_org = analyze_org
        self.clone_org = clone_org
        self.single_package = single_package
        self.dirty_build = dirty_build
        self.ignore_missing_binaries = ignore_missing_binaries
        self.skip_build = skip_build
        self.skip_apt = skip_apt
        self.force_build = force_build
        self.vyos_build_docker = vyos_build_docker
        self.rescan_packages = rescan_packages
        self.pre_build_hook = pre_build_hook
        self.debranding = debranding

        self.vyos_stream_mode = self.clone_org != "vyos"
        self.package_definitions = PackageDefinitions(self.vyos_stream_mode)
        self.build_data = ObjectStorage(
            os.path.join(data_dir, "builder-data-%s.json" % self.branch), dict, {}
        )
        self.package_cache = ObjectStorage(
            os.path.join(data_dir, "package-metadata-cache-%s.json" % self.branch), dict, {}
        )
        self.scripting = Scripting()
        self.terminal_title = TerminalTitle("Package builder: ")

        ensure_directories()

    def build(self):
        self.terminal_title.set("Preparation...")
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
        self.docker = Docker(self.vyos_build_docker, self.branch, vyos_build_repo, self.vyos_stream_mode)
        self.docker.pull()

        self.updated_repos = []
        found = 0
        built = 0
        counter = 0
        total = 1 if self.single_package is not None else len(packages)
        for package in packages.values():
            found += 1
            if self.single_package is not None and self.single_package != package["package_name"]:
                continue

            counter += 1
            message = "Processing package: %s (%s of %s)" % (package["package_name"], counter, total)
            self.terminal_title.set(message)
            logging.info(message)

            self.build_package(package)
            built += 1

        if built == 0:
            self.terminal_title.set("ERROR")
            if self.single_package is not None:
                logging.error("Specified --single-package=%s was not found" % self.single_package)
            else:
                if found == 0:
                    logging.error("Something's wrong, no packages were found!")
                else:
                    logging.error("Something's wrong, no packages were built but these were found: %s" % packages)
            exit(1)

        elapsed = round(monotonic() - begin, 3)
        message = "Done in %s seconds" % elapsed
        self.terminal_title.set(message)
        logging.info(message)

    def build_package(self, package):
        repo_name = package["repo_name"]

        my_state = self.build_data.get(package["package_name"], default={}, data_type=dict)
        if "hash" not in my_state:
            my_state["hash"] = None

        repo_path = os.path.join(self.my_build_dir, repo_name)
        parent_path = repo_path

        if package["build_type"] == "dpkg-buildpackage":
            if not os.path.exists(repo_path):
                os.makedirs(repo_path)
            repo_path = os.path.join(repo_path, "sources")

        git_url = replace_github_repo_org(package["git_url"], self.clone_org)
        git = Git(repo_path)

        if git.exists() and not os.path.exists(git.git_dir):
            self.docker.rmtree(parent_path)

        if git.exists() and self.clone_org not in git.get_remote_url("origin"):
            git.set_remote_url("origin", git_url)
            git.fetch()

        if git.exists():
            up_to_date = False

            try:
                changed = git.resolve_changes(package["change_patterns"], my_state["hash"])
                if not changed:
                    up_to_date = True
            except ProcessException as e:
                if "not a git repository" in str(e):
                    self.docker.rmtree(parent_path)
                else:
                    raise

            if "dependencies" in package:
                if "dependencies" in my_state:
                    previous_dependency_hashes = my_state["dependencies"]
                else:
                    previous_dependency_hashes = {}

                for dependency_git_url in package["dependencies"]:
                    dependency_repo_name = "dependency-%s" % sanitize_filename(dependency_git_url)
                    dependency_repo_path = os.path.join(self.my_build_dir, dependency_repo_name)
                    dependency_git = Git(dependency_repo_path)
                    if dependency_git.exists():
                        dependency_git.pull()
                    else:
                        dependency_git.clone(dependency_git_url, package["branch"])

                    if dependency_git_url in previous_dependency_hashes:
                        my_previous_hash = previous_dependency_hashes[dependency_git_url]
                    else:
                        my_previous_hash = None

                    my_current_hash = dependency_git.get_last_commit_hash()
                    if my_previous_hash != my_current_hash:
                        up_to_date = False
                        break

            if up_to_date and not self.force_build:
                logging.info("Package is up to date, skipping build")
                return

        new = False
        if repo_name not in self.updated_repos:
            self.updated_repos.append(repo_name)

            if os.path.exists(parent_path) and not self.dirty_build:
                # We want to delete original repo and do fresh clone to clean cached build files.
                self.docker.rmtree(parent_path)

            if not os.path.exists(repo_path):
                logging.info("Cloning repository %s" % git_url)
                git.clone(git_url, package["branch"])
                new = True
            else:
                git_url = git.get_remote_url("origin")
                logging.info("Pulling repository %s" % git_url)
                git.pull()
        else:
            git_url = git.get_remote_url("origin")
            logging.info("Using shared repository %s" % git_url)

        self.debranding.remove_package_branding(repo_path, package["package_name"])

        if self.pre_build_hook:
            self.scripting.run(self.pre_build_hook, repo_path, vars={
                "BRANCH": self.branch,
                "PACKAGE_NAME": package["package_name"],
            })

        virtual_scripts = "/my-build-scripts"
        if package["build_type"] == "build.py":
            my_directory = os.path.join(self.my_build_dir, "vyos-build", package["path"])
            if not self.skip_build or new:
                package_toml_path = os.path.join(my_directory, "package.toml")
                if os.path.exists(package_toml_path):
                    self.modify_package_toml(package_toml_path)
                # It's important to run bash in interactive mode, non-interactive shell breaks dependency on .bashrc.
                build_script = os.path.join(virtual_scripts, "build_py.sh")
                vyos_dir = "/vyos/%s" % package["path"]
                self.docker.run(
                    "bash -i -c '%s %s'" % quote_all(build_script, package["package_name"]),
                    work_dir=vyos_dir,
                    extra_mounts=[
                        (scripts_dir, virtual_scripts)
                    ],
                )

        elif package["build_type"] == "dpkg-buildpackage":
            my_directory = os.path.join(self.my_build_dir, repo_name)
            virtual_dir = "/vyos-%s" % package["package_name"]

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

        self.build_data.set(package["package_name"], my_state)

    def modify_package_toml(self, path):
        with open(path, "r") as file:
            payload = tomlkit.load(file)

        changed = False
        if "packages" in payload:
            for package in payload["packages"]:
                if "scm_url" in package:
                    scm_url = replace_github_repo_org(
                        package["scm_url"], self.clone_org, whitelist_orgs=["vyos", "VyOS-Networks"]
                    )
                    if scm_url != package["scm_url"]:
                        changed = True
                        logging.info("Updating package.toml GIT url from %s to %s" % (package["scm_url"], scm_url))
                        package["scm_url"] = scm_url
                        if "commit_id" in package and package["commit_id"] in ["master", "main"]:
                            package["commit_id"] = self.branch

        if changed:
            with open(path, "w") as file:
                tomlkit.dump(payload, file)

    def get_packages_metadata(self):
        if self.package_definitions.is_static(self.branch):
            packages = self.package_definitions.get_definitions(self.analyze_org, self.branch)
        else:
            packages_timestamp = self.package_cache.get("packages_timestamp")
            packages = self.package_cache.get("packages")

            if not packages_timestamp or not packages or packages_timestamp <= time() - 3600 * 24 or self.rescan_packages:
                packages = self.package_definitions.get_definitions(self.analyze_org, self.branch)
                self.package_cache.set("packages_timestamp", time())
                self.package_cache.set("packages", packages)

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
        parser.add_argument("branch", help="Branch (current, circinus)")
        parser.add_argument("--analyze-org", default="vyos",
                            help="What GitHub organization to use for analysis (used only for current)")
        parser.add_argument("--clone-org", default="NOTvyos", help="What GitHub organization to use for sources")
        parser.add_argument("--single-package", help="Build only this package")
        parser.add_argument("--force-build", action="store_true", help="Force build even if package is up to date")
        parser.add_argument("--rescan-packages", action="store_true",
                            help="Force package metadata scan even if last scan was run recently")
        parser.add_argument("--vyos-build-docker", default="vyos/vyos-build",
                            help="Default option uses vyos/vyos-build from dockerhub")
        scripting_info = "the current working directory is the repo of given package"
        scripting_info += ", available environment variables: VYOS_BUILD_BRANCH, VYOS_BUILD_PACKAGE_NAME"
        parser.add_argument("--pre-build-hook", help="Script to execute before build, %s" % scripting_info)
        debranding.populate_cli_parser(parser)
        parser.add_argument("--dirty-build", action="store_true",
                            help="DEV - Build with reused sources (don't clone fresh sources) for existing packages")
        parser.add_argument("--ignore-missing-binaries", action="store_true",
                            help="DEV - Don't terminate when missing binaries are detected")
        parser.add_argument("--skip-build", action="store_true", help="DEV - Skip build stage for existing packages")
        parser.add_argument("--skip-apt", action="store_true", help="DEV - Skip reprepro stage for existing packages")

        args = parser.parse_args()
        values = vars(args)

        debranding.extract_cli_values(values)

        builder = PackageBuilder(debranding=debranding, **values)
        try:
            builder.build()
        except Exception:
            builder.terminal_title.set("ERROR")
            raise

    except KeyboardInterrupt:
        exit(1)
    except Exception as e:
        logging.exception(e)
        logging.error("Something went wrong, log file: %s" % get_my_log_file())
        exit(1)
