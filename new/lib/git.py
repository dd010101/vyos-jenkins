import logging
import os.path
import re
import shlex

from lib.helpers import execute, quote_all, ProcessException, build_dir


class Git:
    def __init__(self, repo_path, debug=False):
        self.repo_path = repo_path
        self.git_dir = os.path.join(self.repo_path, ".git")
        self.debug = debug

    def exists(self):
        return os.path.exists(self.repo_path)

    def clone(self, git_url, branch=None):
        if branch is not None:
            self.execute("git clone -b %s --single-branch %s %s" % quote_all(
                branch, git_url, self.repo_path
            ))
        else:
            self.execute("git clone %s %s" % quote_all(
                git_url, self.repo_path
            ))

    def checkout(self, pathspec, branch=None):
        if branch is not None:
            self.execute("git --git-dir %s checkout -b %s %s" % quote_all(self.git_dir, branch, pathspec))
        else:
            self.execute("git --git-dir %s checkout %s" % quote_all(self.git_dir, pathspec))

    def add_remote(self, git_url, remote_name):
        self.execute("git --git-dir %s remote add %s %s" % quote_all(self.git_dir, remote_name, git_url))

    def rm_remote(self, remote_name):
        self.execute("git --git-dir %s remote rm %s" % quote_all(self.git_dir, remote_name))

    def get_remote_url(self, remote_name):
        return self.execute("git --git-dir %s config --get remote.%s.url" % quote_all(self.git_dir, remote_name)).strip()

    def set_remote_url(self, remote_name, git_url):
        self.execute("git --git-dir %s remote set-url %s %s" % quote_all(self.git_dir, remote_name, git_url))

    def fetch(self):
        self.execute("git --git-dir %s fetch --all" % quote_all(self.git_dir))

    def pull(self, remote=None, branch=None, ff_only=False):
        self.execute("git --git-dir %s reset --hard" % quote_all(self.git_dir))

        extra = ""
        if remote:
            extra += " %s" % quote_all(remote)
            if branch:
                extra += " %s" % quote_all(branch)
        if ff_only:
            extra += " --ff-only"

        self.execute("git --git-dir %s pull%s" % tuple(quote_all(self.git_dir) + (extra,)))

    def push(self, remote):
        return self.execute("git --git-dir %s push %s" % quote_all(self.git_dir, remote))

    def add(self):
        self.execute("git --git-dir %s add --all" % quote_all(self.git_dir))

    def commit(self, message):
        self.execute("git --git-dir %s commit -m %s" % quote_all(self.git_dir, message))

    def get_last_commit_hash(self):
        return self.execute("git --git-dir %s rev-parse HEAD" % quote_all(self.git_dir)).strip()

    def get_changed_files(self, ref1, ref2):
        try:
            return self.execute("git --git-dir %s diff --name-only %s %s" % quote_all(self.git_dir, ref1, ref2)).strip()
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
        changed_files = self.get_changed_files(current_hash, previous_hash).splitlines()
        for file in changed_files:
            for regex in regexes:
                if regex.search(file):
                    matched = True
                    break

        if not matched:
            changed = False

        return changed

    def execute(self, command, timeout: int = None, passthrough=False, passthrough_prefix=None, **kwargs):
        if os.path.exists(self.repo_path):
            os.chdir(self.repo_path)
        else:
            os.chdir(build_dir)

        if self.debug:
            logging.info("GIT command: '%s'" % command)
            if not passthrough:
                passthrough = True
                passthrough_prefix = "GIT: "

        if "env" not in kwargs:
            kwargs["env"] = os.environ.copy()
        kwargs["env"]["GIT_TERMINAL_PROMPT"] = "0"

        return execute(command, timeout, passthrough, passthrough_prefix, passthrough_output=self.debug, **kwargs)
