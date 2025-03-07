import os.path
import re

from lib.helpers import execute, quote_all, ProcessException


class Git:
    def __init__(self, repo_path):
        self.repo_path = repo_path

    def exists(self):
        return os.path.exists(self.repo_path)

    def clone(self, git_url, branch=None):
        if branch is not None:
            execute("git clone -b %s --single-branch %s %s" % quote_all(
                branch, git_url, self.repo_path
            ))
        else:
            execute("git clone %s %s" % quote_all(
                git_url, self.repo_path
            ))

    def checkout(self, pathspec, branch=None):
        if branch is not None:
            execute("git -C %s checkout -b %s %s" % quote_all(self.repo_path, branch, pathspec))
        else:
            execute("git -C %s checkout %s" % quote_all(self.repo_path, pathspec))

    def add_remote(self, git_url, remote_name):
        execute("git -C %s remote add %s %s" % quote_all(self.repo_path, remote_name, git_url))

    def rm_remote(self, remote_name):
        execute("git -C %s remote rm %s" % quote_all(self.repo_path, remote_name))

    def get_remote_url(self, remote_name):
        return execute("git -C %s config --get remote.%s.url" % quote_all(self.repo_path, remote_name)).strip()

    def set_remote_url(self, remote_name, git_url):
        execute("git -C %s remote set-url %s %s" % quote_all(self.repo_path, remote_name, git_url))

    def fetch(self):
        execute("git -C %s fetch --all" % quote_all(self.repo_path))

    def pull(self, remote=None, branch=None, ff_only=False):
        execute("git -C %s reset --hard" % quote_all(self.repo_path))

        extra = ""
        if remote:
            extra += " %s" % quote_all(remote)
            if branch:
                extra += " %s" % quote_all(branch)
        if ff_only:
            extra += " --ff-only"

        execute("git -C %s pull%s" % tuple(quote_all(self.repo_path) + (extra,)))

    def push(self, remote):
        return execute("git -C %s push %s" % quote_all(self.repo_path, remote))

    def add(self):
        execute("git -C %s add --all" % quote_all(self.repo_path))

    def commit(self, message):
        execute("git -C %s commit -m %s" % quote_all(self.repo_path, message))

    def get_last_commit_hash(self):
        return execute("git -C %s rev-parse HEAD" % quote_all(self.repo_path)).strip()

    def get_changed_files(self, ref1, ref2):
        try:
            return execute("git diff --name-only %s %s" % quote_all(ref1, ref2)).strip()
        except ProcessException as e:
            if e.exit_code == 1 and "Could not access" in e.output:
                return ""  # ignore non-existing commits (caused by repo changed or force-push)
            raise

    def resolve_changes(self, change_patterns, previous_hash):
        if not self.exists():
            return True

        self.pull()
        current_hash = self.get_last_commit_hash()
        changed = current_hash != previous_hash
        if not changed or not previous_hash:
            return changed

        regexes = []
        for pattern in change_patterns:
            if re.search(r"^[*]+$", pattern):
                return True  # catch-all pattern

            pattern: str = re.escape(pattern)  # escape special characters
            pattern = pattern.replace("\\*", "*")  # undo escape of stars

            # convert stars into regex patterns
            pattern = pattern.replace("**", ".*")
            pattern = re.sub(r"[*]{2,}", ".*", pattern)
            pattern = pattern.replace("*", "[^/]+")

            regexes.append(re.compile(r"^%s$" % pattern, flags=re.I))

        matched = False
        for file in self.get_changed_files(current_hash, previous_hash):
            for regex in regexes:
                if regex.search(file):
                    matched = True
                    break

        if not matched:
            changed = False

        return changed
