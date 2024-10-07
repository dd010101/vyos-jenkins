import logging
import os
import re
from shlex import quote

from lib.helpers import quote_all, execute, data_dir, resources_dir, apt_dir


class Apt:
    _repo_dir = None

    def __init__(self, branch, directory):
        self.branch = branch
        self.directory = directory
        self.gpg_keyring_path = os.path.join(data_dir, ".gnupg")

    def scan_for_dist_files(self, directory):
        dsc_files = []
        binary_files = []
        binary_names = []

        for parent, directories, files in os.walk(directory):
            for file_name in files:
                path = os.path.join(parent, file_name)
                name, ext = os.path.splitext(file_name)
                ext = ext.lower()[1:]
                if ext == "dsc":
                    dsc_files.append(path)
                elif ext == "deb":
                    # exclude build dependency packages
                    if "build-deps_" in name:
                        continue

                    # exclude packages that don't follow name_version_arch.deb
                    if not re.search(r"[^_]+_[^_]+_[^_]+", name):
                        continue

                    # exclude duplicates packages
                    if file_name in binary_names:
                        continue
                    binary_names.append(file_name)

                    binary_files.append(path)

        return dsc_files, binary_files

    def initialize_repository(self):
        pub_keyring_path = os.path.join(self.gpg_keyring_path, "pubring.kbx")
        if not os.path.exists(pub_keyring_path):
            logging.info("Generating GPG singing key")
            material_path = os.path.join(resources_dir, "gpg-gen-key.txt")
            execute("gpg --homedir %s --batch --gen-key < %s" % quote_all(self.gpg_keyring_path, material_path))

        conf_dir = os.path.join(apt_dir, self.branch, "conf")
        if not os.path.exists(conf_dir):
            logging.info("Initializing APT repository")
            os.makedirs(conf_dir)

        dist_path = os.path.join(conf_dir, "distributions")
        if not os.path.exists(dist_path):
            material_path = os.path.join(resources_dir, "apt-distributions.txt")
            with open(material_path, "r") as file:
                contents = file.read()
                contents = contents.replace("%branch%", self.branch)
                contents = contents.replace("%keyId%", self.get_key_id())

            with open(dist_path, "w") as file:
                file.write(contents)

        options_path = os.path.join(conf_dir, "options")
        if not os.path.exists(options_path):
            material_path = os.path.join(resources_dir, "apt-options.txt")
            with open(material_path, "r") as file:
                contents = file.read()

            with open(options_path, "w") as file:
                file.write(contents)

        repo_dir = os.path.dirname(conf_dir)
        root_dir = os.path.dirname(repo_dir)

        pub_key_path = os.path.join(root_dir, "apt.gpg.key")
        if not os.path.exists(pub_key_path):
            execute("gpg --homedir %s --armor --output %s --export-options export-minimal --export %s" % (
                self.gpg_keyring_path, pub_key_path, self.get_key_id()
            ))

        return repo_dir

    def get_repo_dir(self):
        if self._repo_dir is None:
            self._repo_dir = self.initialize_repository()
        return self._repo_dir

    def get_key_id(self):
        output = execute("gpg --homedir %s --list-keys --keyid-format=long signing@not-vyos" % self.gpg_keyring_path)
        we_in_pub = False
        key_id = None
        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("pub"):
                we_in_pub = True
            elif we_in_pub:
                key_id = line
                break

        if not key_id:
            raise Exception("Unable to parser gpg key ID from: %s" % output)

        if not re.search(r"^[a-z0-9]+$", key_id, flags=re.I):
            raise Exception("Get invalid gpg key ID '%s' from: %s" % (key_id, output))

        return key_id

    def fill_apt_repository(self, dsc_files, binary_files):
        repo_dir = self.get_repo_dir()

        prefix_len = len(self.directory)

        for dsc_file in dsc_files:
            with open(dsc_file, "r") as file:
                fields = self.parse_package_info(file.read(), dsc_file, ["Source"])

            package = fields["Source"]

            logging.info("Removing sources of %s from the APT repository" % package)

            execute("reprepro --gnupghome %s  -v -b %s removesrc %s %s" % quote_all(
                self.gpg_keyring_path, repo_dir, self.branch, package
            ))

        for binary_file in binary_files:
            output = execute("dpkg-deb -f %s" % quote_all(binary_file))
            fields = self.parse_package_info(output, binary_file, ["Package", "Architecture"])

            package = fields["Package"]
            architecture = fields["Architecture"]

            logging.info("Removing binaries of %s from the APT repository" % package)

            extra = self.construct_reprepro_bin_extra(architecture)
            execute("reprepro --gnupghome %s  -v -b %s%s remove %s %s" % (
                self.gpg_keyring_path, repo_dir, extra, self.branch, package
            ))

        execute("reprepro --gnupghome %s -v -b %s deleteunreferenced" % (
            self.gpg_keyring_path, repo_dir
        ))

        for dsc_file in dsc_files:
            logging.info("Pushing %s to the APT repository" % dsc_file[prefix_len:])

            execute("reprepro --gnupghome %s -v -b %s includedsc %s %s" % quote_all(
                self.gpg_keyring_path, repo_dir, self.branch, dsc_file
            ))

        for binary_file in binary_files:
            logging.info("Pushing %s to the APT repository" % binary_file[prefix_len:])

            output = execute("dpkg-deb -f %s" % quote_all(binary_file))
            fields = self.parse_package_info(output, binary_file, ["Architecture"])

            architecture = fields["Architecture"]

            extra = self.construct_reprepro_bin_extra(architecture)
            execute("reprepro --gnupghome %s -v -b %s%s includedeb %s %s" % (
                self.gpg_keyring_path, repo_dir, extra, self.branch, binary_file
            ))

    def construct_reprepro_bin_extra(self, architecture):
        additional_params = []
        if architecture != "all":
            additional_params.extend(["-A", quote(architecture)])

        extra = " ".join(additional_params)
        if extra:
            extra = " " + extra
        return extra

    def parse_package_info(self, contents, subject, required_keys: list):
        fields = {}
        for line in contents.split("\n"):
            line = line.strip()
            parts = line.split(":", maxsplit=1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                fields[key] = value

        for key in required_keys:
            if key not in fields:
                raise Exception("%s: unable to parse %s field" % (subject, key))

        return fields

    def validate_package_info(self, dsc_file, fields, required_keys):
        for key in required_keys:
            if key not in fields:
                raise Exception("%s: unable to parse %s field" % (dsc_file, key))
