import logging
import os
import shlex
import shutil
import subprocess

import sys


def rmtree(directory):
    try:
        shutil.rmtree(directory)
    except PermissionError:
        logging.error(
            "Unable to delete '%s' due to permissions."
            " Please delete this directory yourself"
            " with root privileges and then rerun again." % directory
        )
        exit(1)


def execute(command, passthrough=False, timeout=None, **kwargs):
    if passthrough:
        kwargs["stdout"] = sys.stdout
        kwargs["stderr"] = sys.stderr

    if "stdout" not in kwargs:
        kwargs["stdout"] = subprocess.PIPE
    if "stderr" not in kwargs:
        kwargs["stderr"] = subprocess.STDOUT
    if "shell" not in kwargs:
        kwargs["shell"] = True

    process = subprocess.Popen(command, **kwargs)
    process.wait(timeout)
    exit_code = process.returncode

    if exit_code != 0:
        message = "Command '%s' failed, exit code: %s" % (command, exit_code)
        if not passthrough:
            # noinspection PyUnresolvedReferences
            message += ", output: %s" % process.stdout.read().decode("utf-8")
        raise ProcessException(message)

    if passthrough:
        return exit_code
    else:
        # noinspection PyUnresolvedReferences
        return process.stdout.read().decode("utf-8")


class ProcessException(Exception):
    pass


def quote_all(*args):
    quoted = []
    for arg in args:
        quoted.append(shlex.quote(arg))
    return tuple(quoted)


class LessThanLevelFilter(logging.Filter):
    def __init__(self, exclusive_maximum, name="LessThanLevelFilter"):
        super(LessThanLevelFilter, self).__init__(name)
        self.maximum_level = exclusive_maximum

    def filter(self, record):
        return 1 if record.levelno < self.maximum_level else 0


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    stderr_level = logging.WARNING

    stdout = logging.StreamHandler(sys.stdout)
    stdout.setLevel(logging.INFO)
    stdout.addFilter(LessThanLevelFilter(stderr_level))
    stdout.setFormatter(formatter)
    logger.addHandler(stdout)

    stderr = logging.StreamHandler(sys.stderr)
    stderr.setLevel(stderr_level)
    stderr.setFormatter(formatter)
    logger.addHandler(stderr)


def refuse_root():
    if os.geteuid() == 0:
        logging.error(
            "ERROR: 'root' user detected, please don't run this script as root,"
            " run as any other regular user that has docker access (usermod -aG docker YOUR_USER),"
            " the root privileges would break some packages.")
        exit(1)
