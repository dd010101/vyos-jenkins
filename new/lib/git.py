import os.path
import re

from lib.helpers import execute, quote_all


class Git:
    def __init__(self, repo_path):
        self.repo_path = repo_path

    def exists(self):
        return os.path.exists(self.repo_path)

    def clone(self, git_url, branch):
        execute("git clone -b %s --single-branch %s %s" % quote_all(
            branch, git_url, self.repo_path
        ))

    def pull(self):
        execute("git -C %s reset --hard" % quote_all(self.repo_path))
        execute("git -C %s pull" % quote_all(self.repo_path))

    def get_last_commit_hash(self):
        return execute("git -C %s rev-parse HEAD" % quote_all(self.repo_path)).strip()

    def get_changed_files(self, ref1, ref2):
        return execute("git diff --name-only %s %s" % quote_all(ref1, ref2)).strip()

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
