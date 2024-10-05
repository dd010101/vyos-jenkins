#!/usr/bin/env python3
import logging
from pprint import pprint
import sys

import requests
from requests import HTTPError
import yaml

from helpers import Cache, setup_logging


class GitHub:
    """
        This class has the job to:
            1) find all repositories
            2) filter repositories with defined workflow
            3) construct package metadata from workflow definition
    """

    def analyze_repositories_workflow(self, org_name, repositories, branch):
        packages = {}
        for repo_name, git_url in repositories.items():
            expected_workflow = "trigger-rebuild-repo-package.yml"
            if repo_name == "vyos-build":
                expected_workflow = "trigger_rebuild_packages.yml"

            url = "https://raw.githubusercontent.com/%s/%s/refs/heads/%s/.github/workflows/%s" % (
                org_name, repo_name, branch, expected_workflow
            )

            try:
                response = requests.request("get", url)
                response.raise_for_status()
                contents = response.text

                workflow = yaml.load(contents, Loader=yaml.Loader)

                if "jobs" in workflow:
                    if "trigger-build" in workflow["jobs"]:
                        definition = workflow["jobs"]["trigger-build"]["with"]
                        if "ref_name" not in definition["branch"]:
                            raise Exception("%s: unknown branch: %s" % (repo_name, definition))
                        if "PACKAGE_NAME" not in definition["package_name"]:
                            raise Exception("%s: unknown package_name: %s" % (repo_name, definition))

                        packages[repo_name] = {
                            "repo_name": repo_name,
                            "branch": branch,
                            "package_name": repo_name,
                            "build_type": "dpkg-buildpackage",
                            "path": "",
                            "change_patterns": ["*"],
                            "git_url": git_url,
                        }

                    if "changes" in workflow["jobs"]:
                        for item in workflow["jobs"]["changes"]["steps"]:
                            if "uses" in item and "paths-filter" in item["uses"]:
                                filters = yaml.load(item["with"]["filters"], Loader=yaml.Loader)
                                for package_name, patterns in filters.items():
                                    pseudo_repo_name = "%s-%s" % (repo_name, package_name)
                                    packages[pseudo_repo_name] = {
                                        "repo_name": repo_name,
                                        "branch": branch,
                                        "package_name": package_name,
                                        "build_type": "build.py",
                                        "path": "scripts/package-build/%s" % package_name,
                                        "change_pattern": patterns,
                                        "git_url": git_url,
                                    }

            except HTTPError as e:
                if e.response.status_code == 404:
                    continue
                raise

        return packages

    def find_org_repositories(self, name):
        return self.find_repositories("org", name)

    def find_repositories(self, kind, name):
        url = "https://api.github.com/%ss/%s/repos" % (kind, name)
        items = self.fetch_all_pages(url)

        repositories = {}
        for item in items:
            repositories[item["name"]] = item["clone_url"]

        return repositories

    def fetch_all_pages(self, base_url, give_up=1000):
        page = 1
        items = []
        while True:
            response = requests.request("get", base_url, params={
                "page": page,
                "per_page": 50,
            })
            response.raise_for_status()
            payload = response.json()

            if len(payload) == 0:
                break

            items.extend(payload)

            if page >= give_up:
                raise Exception("%s: something is wrong, reached page %s and no end in sight" % (base_url, page))

            page += 1

        return items


if __name__ == "__main__":
    setup_logging()

    try:
        command = sys.argv[1] if len(sys.argv) > 1 else None

        if command is None:
            print("What do you want?")

        elif command == "vyos-repos":
            pprint(GitHub().find_org_repositories("vyos"))

        elif command == "vyos-analyze":
            branch = sys.argv[2] if len(sys.argv) > 2 else None
            if branch is None:
                print("ERROR: missing branch, provide branch as second argument", file=sys.stderr)
                exit(1)

            github = GitHub()

            cache = Cache("data/github-vyos-cache.json", dict, {})
            repositories = cache.callback("repos", callback=lambda: github.find_org_repositories("vyos"))

            pprint(github.analyze_repositories_workflow("vyos", repositories, "circinus"))

        else:
            print("ERROR: unknown command: %s" % command, file=sys.stderr)
            exit(1)

    except KeyboardInterrupt:
        exit(1)
    except Exception as e:
        logging.exception(e)
        exit(1)
