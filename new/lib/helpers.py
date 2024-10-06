import logging
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


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)
