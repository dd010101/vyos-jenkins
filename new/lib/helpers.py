import logging
from logging import FileHandler
import os
import re
import shlex
import subprocess

import sys
from time import monotonic

project_dir: str = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
apt_dir: str = os.path.join(project_dir, "apt")
build_dir: str = os.path.join(project_dir, "build")
data_dir: str = os.path.join(project_dir, "data")
resources_dir: str = os.path.join(project_dir, "resources")
scripts_dir: str = os.path.join(project_dir, "scripts")


def ensure_directories():
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)


def quote_all(*args):
    quoted = []
    for arg in args:
        quoted.append(shlex.quote(arg))
    return tuple(quoted)


def execute(command, timeout: int = None, passthrough=False, passthrough_prefix=None, passthrough_output=False,
            **kwargs):
    if passthrough:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.STDOUT

    if "stdout" not in kwargs:
        kwargs["stdout"] = subprocess.PIPE
    if "stderr" not in kwargs:
        kwargs["stderr"] = subprocess.STDOUT
    if "shell" not in kwargs:
        kwargs["shell"] = True

    process = subprocess.Popen(command, **kwargs)
    buffer = None
    if passthrough:
        file_log_handler = find_file_log_handler()
        buffer = bytearray()
        terminal_buffer = TerminalLineBuffer()
        stdout = process.stdout

        deadline = monotonic() + timeout if timeout is not None else None
        while process.poll() is None and (deadline is None or deadline < monotonic()):
            # noinspection PyTypeChecker
            value: bytes = stdout.read(1)
            sys.stdout.buffer.write(value)
            buffer.extend(value)

            if file_log_handler is not None:
                terminal_buffer.feed(value)
                if terminal_buffer.is_complete():
                    sys.stdout.buffer.flush()
                    line = terminal_buffer.get_line()
                    file_log_handler.handle(create_stdout_log_record(line, passthrough_prefix))

        # noinspection PyTypeChecker
        rest: bytes = stdout.read()
        sys.stdout.buffer.write(rest)
        sys.stdout.buffer.flush()
        buffer.extend(rest)

        if file_log_handler is not None:
            terminal_buffer.feed(rest)
            line = terminal_buffer.get_line()
            if line:
                file_log_handler.handle(create_stdout_log_record(line, passthrough_prefix))

        if deadline is not None and deadline >= monotonic() and process.poll() is None:
            process.kill()
            raise subprocess.TimeoutExpired(process.args, timeout)
    else:
        process.wait(timeout)
    exit_code = process.returncode

    if exit_code != 0:
        message = "Command '%s' failed, exit code: %s" % (command, exit_code)
        output = None
        if not passthrough or passthrough_output:
            if passthrough_output:
                output = buffer.decode("utf-8")
            else:
                # noinspection PyUnresolvedReferences
                output = process.stdout.read().decode("utf-8")
            message += ", output: %s" % output
        raise ProcessException(message, exit_code, output)

    if passthrough:
        if passthrough_output:
            return buffer.decode("utf-8")
        return exit_code
    else:
        # noinspection PyUnresolvedReferences
        return process.stdout.read().decode("utf-8")


class ProcessException(Exception):
    def __init__(self, message, exit_code, output):
        super().__init__(message)
        self.exit_code = exit_code
        self.output = output


class TerminalLineBuffer:
    last_value: bytes

    def __init__(self):
        self.line_buffer = b""
        # ANSI control sequences
        self.control_sequences_regex = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        self.carriage_return_regex = re.compile(r"[\r\n]+\s*[\r\n]*")

    def feed(self, value: bytes):
        self.last_value = value
        self.line_buffer += value

    def is_complete(self):
        return self.last_value == b"\n"

    def get_line(self):
        line = self.line_buffer.decode("utf-8")
        self.line_buffer = b""
        line = self.carriage_return_regex.sub("\n", line)
        line = self.control_sequences_regex.sub("", line)
        return line.strip("\r\n") + "\n"


def create_stdout_log_record(message, passthrough_prefix=None, level=logging.INFO):
    message = message.rstrip()
    if passthrough_prefix is not None:
        message = "%s%s" % (passthrough_prefix, message)
    return logging.LogRecord("root", level, "", 0, message, None, None, None)


class LessThanLevelFilter(logging.Filter):
    def __init__(self, exclusive_maximum, name="LessThanLevelFilter"):
        super(LessThanLevelFilter, self).__init__(name)
        self.maximum_level = exclusive_maximum

    def filter(self, record):
        return 1 if record.levelno < self.maximum_level else 0


def setup_logging(name="test"):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    stderr_level = logging.WARNING

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.addFilter(LessThanLevelFilter(stderr_level))
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(stderr_level)
    stderr_handler.setFormatter(formatter)
    logger.addHandler(stderr_handler)

    log_file = os.path.join(build_dir, "%s.log" % name)
    if os.path.exists(log_file):
        previous_log_file = "%s.2" % log_file
        if os.path.exists(previous_log_file):
            os.remove(previous_log_file)
        os.rename(log_file, previous_log_file)
    file_handler = FileHandler(log_file, encoding="utf-8")
    file_handler.my_log_file = log_file
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)


def find_file_log_handler():
    file_log_handler = None
    for handler in logging.getLogger().handlers:
        if isinstance(handler, FileHandler):
            file_log_handler = handler
            break
    return file_log_handler


def get_my_log_file():
    file_log_handler = find_file_log_handler()
    if file_log_handler is not None and hasattr(file_log_handler, "my_log_file"):
        return file_log_handler.my_log_file
    return "can't find it"


def refuse_root():
    if os.geteuid() == 0:
        logging.error(
            "ERROR: 'root' user detected, please don't run this script as root,"
            " run as any other regular user that has docker access (usermod -aG docker YOUR_USER),"
            " the root privileges would break some packages.")
        exit(1)


def replace_github_repo_org(git_url, new_org, carefully_only_this_org=None):
    if carefully_only_this_org is not None:
        pattern = r"github\.com/%s" % re.escape(carefully_only_this_org)
    else:
        pattern = r"github\.com/[^/]+"
    return re.sub(pattern, "github.com/%s" % new_org, git_url)


def create_missing_package_exception(package):
    install_dependencies_script_path = os.path.join(project_dir, "install-dependencies.sh")
    raise Exception(
        "Missing dependency (%s), please install the missing package\n"
        "or rerun the dependencies script: %s" % (package, install_dependencies_script_path)
    )


class TerminalTitle:
    def __init__(self, prefix):
        self.prefix = prefix

    def is_supported(self):
        term = os.environ.get("TERM")
        if term is None:
            return False
        if term.startswith("xterm"):
            return True
        if term.startswith("screen"):
            return True
        if term == "linux":
            return True
        return False

    def set(self, title):
        if not self.is_supported():
            return

        if self.prefix is not None:
            title = str(self.prefix) + title

        sys.stdout.write("\33]0;" + title + "\a")
        sys.stdout.flush()
