import argparse
from datetime import datetime
import json
import logging
import os
import re
import shutil

from debian.deb822 import Deb822
import requests

from lib.git import Git
from lib.helpers import setup_logging, ProcessException, execute, quote_all


class TarballRepoSync:
    def __init__(self, branch, source_org, target_org, skip_analyze, single_package):
        self.branch = branch
        self.source_org = source_org
        self.target_org = target_org
        self.skip_analyze = skip_analyze
        self.single_package = single_package
        self.source_dir = os.path.realpath("./sources")
        self.working_dir = os.path.realpath("./work")
        self.package_aliases = {
            "cloud-init": "vyos-cloud-init",
            "libvyosconfig0": "libvyosconfig",
        }

    def run(self):
        if not os.path.exists(self.working_dir):
            os.makedirs(self.working_dir)

        matched_path = os.path.join(self.working_dir, "matched.json")
        matched = None
        if not self.skip_analyze:
            logging.info("scanning metadata...")
            source_packages = self.scan_sources()
            matched = []
            missing = []
            for info in source_packages:
                response = requests.request("head", "https://github.com/%s/%s/tree/%s" % (
                    self.source_org, info["name"], self.branch
                ))
                if response.status_code == 200:
                    matched.append(info)
                elif response.status_code == 404:
                    missing.append("%s (%s)" % (info["name"], info["path"]))

            if len(missing):
                raise Exception("found packages without repository:\n%s" % ("\n".join(missing)))

            with open(matched_path, "w") as file:
                json.dump(matched, file, indent=True)

        if matched is None:
            logging.info("reusing previous analyzed metadata")
            with open(matched_path, "r") as file:
                matched = json.load(file)

        logging.info("found %s package(s)" % len(matched))

        self.sync_repositories(matched)

    def scan_sources(self):
        found = []
        for directory_name in [self.branch, "vyos-tarballs"]:
            directory = os.path.join(self.source_dir, directory_name)
            for parent, directories, files in os.walk(directory):
                for file_name in files:
                    path = os.path.join(parent, file_name)

                    name = None
                    version = None
                    if re.search(r"\.dsc$", file_name, flags=re.I):
                        with open(path, "r") as file:
                            dsc = Deb822(file)
                            name = dsc.get_as_string("Source")
                            version = dsc.get_as_string("Version")

                            source_files = dsc.get_as_string("Files").strip().splitlines()
                            for source_file in source_files:
                                parts = source_file.split(" ", maxsplit=2)
                                path = os.path.join(os.path.dirname(path), parts[-1])
                                if "orig.tar" in path:
                                    break

                    else:
                        match = re.search(r"^([a-z-]+)\.tar", file_name, flags=re.I)
                        if match:
                            name = match.group(1)

                    if name is not None:
                        if name in self.package_aliases:
                            name = self.package_aliases[name]

                        found.append({
                            "path": path,
                            "name": name,
                            "version": version,
                        })

        return found

    def sync_repositories(self, matched):
        for info in matched:
            if self.single_package is not None and info["name"] != self.single_package:
                continue

            logging.info("processing %s - https://github.com/%s/%s/tree/%s - %s" % (
                info["name"], self.target_org, info["name"], self.branch, info["path"]
            ))

            repo_path = os.path.join(self.working_dir, info["name"])
            git = Git(repo_path)
            if git.exists():
                shutil.rmtree(repo_path)

            git.clone("git@github.com:%s/%s.git" % (self.target_org, info["name"]))
            try:
                git.checkout(self.branch)
            except ProcessException as e:
                if re.search("pathspec .* did not match any file", str(e)):
                    git.add_remote("https://github.com/%s/%s" % (self.source_org, info["name"]), "upstream")
                    git.fetch()
                    git.checkout("upstream/%s" % self.branch, self.branch)
                else:
                    raise

            sources_path = os.path.join(self.working_dir, "%s-sources" % info["name"])
            if os.path.exists(sources_path):
                shutil.rmtree(sources_path)
            os.makedirs(sources_path)
            os.chdir(sources_path)
            execute("tar -xf %s" % quote_all(info["path"]))

            sources_path = self.find_root_directory(sources_path)
            source_git_path = os.path.join(sources_path, ".git")
            if os.path.exists(source_git_path):
                try:
                    git.rm_remote("local")
                except ProcessException as e:
                    if "No such remote" not in str(e):
                        raise

                git.add_remote("file://%s" % source_git_path, "local")
                git.pull("local", "HEAD", ff_only=True)

            else:
                for entry in os.scandir(repo_path):
                    if entry.name != ".git":
                        self.destroy_path(entry.path)

                for entry in os.scandir(sources_path):
                    src_path = entry.path
                    dest_path = os.path.join(repo_path, src_path[len(sources_path) + 1:])
                    self.copy_path(src_path, dest_path)

                git.add()
                try:
                    source_name = os.path.basename(info["path"])
                    if info["version"] is None:
                        tarball_time = os.path.getmtime(info["path"])
                        source_name += " [%s]" % datetime.fromtimestamp(tarball_time).strftime("%Y-%m-%d %H:%M:%S")
                    git.commit("Updated from %s" % source_name)
                except ProcessException as e:
                    if "nothing to commit, working tree clean" not in str(e):
                        raise

            git.push("origin")

    def find_root_directory(self, path):
        for parent, directories, files in os.walk(path):
            if len(directories) > 1 or len(files) > 0:
                return parent

    def destroy_path(self, path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)

    def copy_path(self, src_path, dst_path):
        if os.path.isdir(src_path):
            shutil.copytree(src_path, dst_path)
        else:
            shutil.copy2(src_path, dst_path)


if __name__ == "__main__":
    setup_logging(name="tarball-repo-sync")

    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--branch", default="circinus")
        parser.add_argument("--source-org", default="vyos")
        parser.add_argument("--target-org", default="NOTvyos")
        parser.add_argument("--skip-analyze", action="store_true")
        parser.add_argument("--single-package")

        args = parser.parse_args()
        values = vars(args)

        TarballRepoSync(**values).run()
    except KeyboardInterrupt:
        exit(1)
    except Exception as e:
        logging.exception(e)
        exit(1)
