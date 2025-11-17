import argparse
from datetime import datetime
import json
import logging
import os
import re
import shutil

from debian.deb822 import Deb822

from lib.git import Git
from lib.github import GitHub
from lib.helpers import setup_logging, ProcessException, execute, quote_all, resources_dir


class TarballRepoSync:
    def __init__(self, branch, version, source_org, target_org, skip_analyze, ignore_missing, single_package,
                 skip_until, debug, trademark_only):
        self.branch = branch
        self.version = version
        self.source_org = source_org
        self.target_org = target_org
        self.skip_analyze = skip_analyze
        self.ignore_missing = [ignore_missing] if not isinstance(ignore_missing, list) else ignore_missing
        self.single_package = single_package
        self.skip_until = skip_until
        self.debug = debug
        self.trademark_only = trademark_only
        current_dir = os.path.dirname(os.path.realpath(__file__))
        self.source_dir = os.path.join(current_dir, "sources")
        self.working_dir = os.path.join(current_dir, "work")
        self.my_resources_dir = os.path.join(current_dir, "resources")
        self.package_aliases = {
            "cloud-init": "vyos-cloud-init",
            "libvyosconfig0": "libvyosconfig",
            "libnss-tacplus": ("libnss-tacplus", "master"),
            "libtacplus-map": ("libtacplus-map", "master"),
        }
        self.expected_packages = ["cloud-init"]

    def run(self):
        if not os.path.exists(self.working_dir):
            os.makedirs(self.working_dir)

        matched_path = os.path.join(self.working_dir, "matched.json")
        matched = None
        if not self.skip_analyze:
            logging.info("scanning metadata...")
            source_packages = {}
            for item in self.scan_sources():
                source_packages[item["name"]] = item

            repositories = GitHub().find_org_repositories_with_branches(self.target_org)

            matched = []
            missing = []
            for repository, branches in repositories.items():
                if "circinus" not in branches:
                    continue

                if repository in source_packages:
                    matched.append(source_packages[repository])
                else:
                    if repository in self.ignore_missing:
                        continue
                    missing.append(repository)

            if len(missing) > 0:
                raise Exception("found repositories with missing packages:\n%s" % ("\n".join(missing)))

        if matched is None:
            logging.info("reusing previous analyzed metadata")
            with open(matched_path, "r") as file:
                matched = json.load(file)

        matched = sorted(matched, key=lambda item: item["name"])

        logging.info("found %s package(s)" % len(matched))

        self.sync_repositories(matched)

    def scan_sources(self):
        found = []
        for parent_dir_name in [self.branch, "src", "vyos-tarballs"]:
            parent_dir_path = os.path.join(self.source_dir, parent_dir_name)
            if not os.path.exists(parent_dir_path):
                continue

            directory_mode = None
            for parent, directories, files in os.walk(parent_dir_path):
                if directory_mode is None:
                    directory_mode = True
                    for file_name in files:
                        if re.search(r"\.tar$", file_name, flags=re.I):
                            directory_mode = False
                            break

                if directory_mode:
                    for directory in directories:
                        path = os.path.join(parent_dir_path, directory)

                        nested_dir = None
                        for entry in os.scandir(path):
                            if not entry.is_dir():
                                nested_dir = None
                                break
                            if entry.is_dir():
                                if nested_dir is None:
                                    nested_dir = entry.name
                                else:
                                    nested_dir = None
                                    break

                        if nested_dir is None:
                            continue

                        for package_name in self.expected_packages:
                            if package_name in nested_dir:
                                nested_dir = package_name
                                break

                        if not directory.startswith(nested_dir):
                            continue

                        version = self.version
                        if directory != nested_dir:
                            version = directory[len(nested_dir) + 1:]

                        if version in ["master", self.branch]:
                            version = self.version

                        name = nested_dir

                        if name in self.package_aliases:
                            name = self.package_aliases[name]

                        if isinstance(name, tuple):
                            name, branch = name
                        else:
                            branch = self.branch

                        found.append({
                            "path": path,
                            "name": name,
                            "version": version,
                            "branch": branch,
                        })
                    break

                for file_name in files:
                    path = os.path.join(parent, file_name)

                    name = None
                    version = self.version
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
                        match = re.search(r"^([a-z-_]+)\.tar", file_name, flags=re.I)
                        if match:
                            name = match.group(1)
                            for suffix in ["_master", "_%s" % self.branch]:
                                if name.endswith(suffix):
                                    name = name[:-len(suffix)]
                                    break

                    if name is not None:
                        if name in self.package_aliases:
                            name = self.package_aliases[name]

                        if isinstance(name, tuple):
                            name, branch = name
                        else:
                            branch = self.branch

                        found.append({
                            "path": path,
                            "name": name,
                            "version": version,
                            "branch": branch,
                        })

        return found

    def sync_repositories(self, matched):
        skipping = self.skip_until is not None
        for info in matched:
            if self.single_package is not None and info["name"] != self.single_package:
                continue

            if skipping and info["name"] != self.skip_until:
                continue
            skipping = False

            logging.info("processing %s - https://github.com/%s/%s/tree/%s - %s" % (
                info["name"], self.target_org, info["name"], self.branch, info["path"]
            ))

            repo_path = os.path.join(self.working_dir, info["name"])
            git = Git(repo_path, debug=self.debug)

            if git.exists():
                shutil.rmtree(repo_path)

            git.clone("git@github.com:%s/%s.git" % (self.target_org, info["name"]))

            try:
                git.checkout(self.branch)
            except ProcessException as e:
                if re.search("pathspec .* did not match any file", str(e)):
                    git.add_remote("https://github.com/%s/%s" % (self.source_org, info["name"]), "upstream")
                    git.fetch()
                    git.checkout("upstream/%s" % info["branch"], self.branch)
                else:
                    raise

            if self.trademark_only:
                self.handle_trademark(git, repo_path, info["name"], commit=True)
            else:
                sources_path = os.path.join(self.working_dir, "%s-sources" % info["name"])
                if os.path.exists(sources_path):
                    shutil.rmtree(sources_path)

                if os.path.isdir(info["path"]):
                    shutil.copytree(info["path"], sources_path)
                    os.chdir(sources_path)
                else:
                    os.makedirs(sources_path)
                    os.chdir(sources_path)
                    execute("tar -xf %s" % quote_all(info["path"]))

                sources_path = self.find_root_directory(sources_path)

                for parent, directories, files in os.walk(sources_path):
                    for file_name in files:
                        name, extension = os.path.splitext(file_name)
                        extension = extension[1:].lower()
                        if extension in ["deb", "buildinfo", "changes"] and info["name"] in name:
                            os.remove(os.path.join(parent, file_name))
                            logging.info("removed '%s"'' % file_name)

                source_git_path = os.path.join(sources_path, ".git")
                if os.path.exists(source_git_path):
                    try:
                        git.rm_remote("local")
                    except ProcessException as e:
                        if "No such remote" not in str(e):
                            raise

                    git.add_remote("file://%s" % source_git_path, "local")
                    git.pull("local", "HEAD", ff_only=True)

                    self.handle_trademark(git, repo_path, info["name"], commit=True)

                else:
                    for entry in os.scandir(repo_path):
                        if entry.name != ".git":
                            self.destroy_path(entry.path)

                    for entry in os.scandir(sources_path):
                        src_path = entry.path
                        dest_path = os.path.join(repo_path, src_path[len(sources_path) + 1:])
                        self.copy_path(src_path, dest_path)

                    self.handle_trademark(git, repo_path, info["name"], commit=False)

                    git.add()

                    try:
                        source_name = os.path.basename(info["path"])
                        if info["version"] is None:
                            tarball_time = os.path.getmtime(info["path"])
                            source_name += " [%s]" % datetime.fromtimestamp(tarball_time).strftime("%Y-%m-%d %H:%M:%S")
                        elif info["version"] not in source_name:
                            source_name += " [%s]" % info["version"]
                        else:
                            source_name += " [%s]" % self.version

                        message = "Updated from %s" % source_name
                        git.commit(message)
                        logging.info("%s new commit: %s" % (info["name"], message))
                    except ProcessException as e:
                        if "nothing to commit, working tree clean" not in str(e):
                            raise

            output = git.push("origin")
            if "up-to-date" in output:
                logging.info("%s is up to date" % info["name"])
            else:
                logging.info("%s was updated" % info["name"])

    def handle_trademark(self, git, repo_path, repo_name, commit):
        readme_path = None
        for entry in os.scandir(repo_path):
            if entry.is_file() and re.search("^readme\.md$", entry.name, flags=re.I):
                readme_path = entry.path
                break

        if readme_path is None:
            if (os.path.exists(os.path.join(repo_path, "README"))
                    or os.path.exists(os.path.join(repo_path, "README.rst"))
                    or repo_name in ["vyos-world", "live-boot", "vyos-1x"]):
                readme_path = os.path.join(repo_path, "readme.md")
                with open(readme_path, "w") as file:
                    file.write("")

        if readme_path is None:
            raise Exception("unable to find readme file: %s" % repo_path)

        if repo_name == "vyos-build":
            target_splash = os.path.join(repo_path, "data/live-build-config/includes.binary/isolinux/splash.png")
            if not os.path.exists(target_splash):
                raise Exception("splash.png not found: %s" % target_splash)

            new_splash = os.path.join(resources_dir, "not-vyos/splash.png")
            shutil.copy2(new_splash, target_splash)

        with open(os.path.join(self.my_resources_dir, "disclaimer.md"), "r") as file:
            disclaimer = file.read().strip()

        with open(readme_path, "r") as file:
            contents = file.read().lstrip()

        changed = False
        if disclaimer not in contents:
            lines = []
            disclaimer_block = False
            for line in contents.splitlines(keepends=True):
                if "DISCLAIMER tE4AWE_AQahaxUGUpugu BEGIN" in line:
                    disclaimer_block = True
                elif "DISCLAIMER tE4AWE_AQahaxUGUpugu END" in line:
                    disclaimer_block = False
                else:
                    if not disclaimer_block:
                        lines.append(line)

            contents = disclaimer + "\n\n" + "".join(lines).lstrip()

            with open(readme_path, "w") as file:
                file.write(contents)

            changed = True

        trademarks_template_path = os.path.join(self.my_resources_dir, "TRADEMARKS.md")
        trademarks_path = os.path.join(repo_path, "TRADEMARKS.md")
        if os.path.exists(trademarks_path):
            with open(trademarks_path, "r") as file:
                actual = file.read()
            with open(trademarks_template_path, "r") as file:
                expected = file.read()

            if actual != expected:
                raise Exception("TRADEMARKS.md already exists: %s" % trademarks_path)

        if not os.path.exists(trademarks_path):
            shutil.copy2(trademarks_template_path, trademarks_path)
            changed = True

        if changed and commit:
            git.add()
            git.commit("Updated readme for trademark purposes")

    def find_root_directory(self, path):
        for parent, directories, files in os.walk(path):
            if len(directories) > 1 or len(files) > 0:
                return parent
        raise Exception("unable to find root directory")

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
        parser.add_argument("--skip-until", help="skip packages until this one")
        parser.add_argument("--debug", action="store_true")
        parser.add_argument("--trademark-only", action="store_true")
        parser.add_argument("--version")
        parser.add_argument("--ignore-missing", action="append")

        args = parser.parse_args()
        values = vars(args)

        TarballRepoSync(**values).run()
    except KeyboardInterrupt:
        exit(1)
    except Exception as e:
        logging.exception(e)
        exit(1)
