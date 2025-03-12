import logging

from lib.definitions import packages_circinus_frozen, packages_circinus_stream
from lib.github import GitHub


class PackageDefinitions:
    def __init__(self, vyos_stream_mode=False):
        self.vyos_stream_mode = vyos_stream_mode
        self.static_definitions = {
            "circinus-stream": packages_circinus_stream.definitions,
            "circinus": packages_circinus_frozen.definitions,
        }

    def get_definitions(self, github_org, branch):
        virtual_branch = self.get_virtual_branch(branch)
        if virtual_branch in self.static_definitions:
            packages = self.static_definitions[virtual_branch]
        else:
            github = GitHub(self.vyos_stream_mode)
            logging.info("Fetching vyos repository list")
            repositories = github.find_repositories("org", github_org)
            logging.info("Analyzing package metadata")
            packages = github.analyze_repositories_workflow(github_org, repositories, branch)

        packages = dict(sorted(packages.items(), key=lambda item: item[1]["package_name"]))
        return packages

    def is_static(self, branch):
        virtual_branch = self.get_virtual_branch(branch)
        return virtual_branch in self.static_definitions

    def get_virtual_branch(self, branch):
        virtual_branch = branch
        if self.vyos_stream_mode:
            virtual_branch += "-stream"
        return virtual_branch
