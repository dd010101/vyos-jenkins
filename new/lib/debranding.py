import argparse
import logging
import os
import re
from shlex import quote
import shutil

import tomlkit

from lib.objectstorage import ObjectStorage
from lib.helpers import resources_dir, data_dir


class Debranding:
    DEFAULT = "NOTvyos"

    keep_branding = None
    remove_branding = None
    alternative_name = None
    logged = False

    def __init__(self):
        self.cache = ObjectStorage(os.path.join(data_dir, "debranding-cache.json"), dict, {})

    def populate_cli_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument("--keep-branding", action="store_true", help="Keep branding as opposite to debranding")
        parser.add_argument("--remove-branding", action="store_true", help="Remove branding (default)")
        parser.add_argument("--debranding-name", help="The default name is 'NOTvyos'")

    def extract_cli_values(self, values):
        self.keep_branding = values["keep_branding"]
        del values["keep_branding"]
        self.remove_branding = values["remove_branding"]
        del values["remove_branding"]
        self.alternative_name = values["debranding_name"]
        del values["debranding_name"]
        self.remember_settings()

    def remove_package_branding(self, root_dir, package_name):
        self.log_settings()
        if not self.is_debranding_enabled():
            return
        alternative_name = self.get_effective_name()

        if package_name == "vyos-1x":
            logging.info("Applying debranding for %s..." % package_name)

            # sagitta & circinus
            motd_path = os.path.join(root_dir, "data/templates/login/default_motd.j2")
            self.replace_patterns_in_file(motd_path, [
                ("VyOS", alternative_name),
            ])

            motd_path = os.path.join(root_dir, "data/templates/login/motd_vyos_nonproduction.j2")
            if os.path.exists(motd_path):
                with open(motd_path, "w") as file:
                    file.truncate()

            motd_path = os.path.join(root_dir, "data/templates/login/techpreview_warning.j2")
            if os.path.exists(motd_path):
                with open(motd_path, "w") as file:
                    file.truncate()

            login_banner_path = os.path.join(root_dir, "src/conf_mode/system_login_banner.py")
            self.replace_patterns_in_file(login_banner_path, [
                ("Welcome to VyOS", "Welcome to %s" % alternative_name),
            ])

            router_init_path = os.path.join(root_dir, "src/init/vyos-router")
            self.replace_patterns_in_file(router_init_path, [
                ("VyOS Config", "%s Config" % alternative_name),
                ("VyOS router", "%s router" % alternative_name),
            ])

            version_path = os.path.join(root_dir, "src/op_mode/version.py")
            self.replace_patterns_in_file(version_path, [
                ("VyOS {{version}}", "%s {{version}}" % alternative_name),
            ])

            airbag_path = os.path.join(root_dir, "python/vyos/airbag.py")
            self.replace_patterns_in_file(airbag_path, [
                ("VyOS {{version}}", "%s {{version}}" % alternative_name),
            ])

            # equuleus
            login_banner_path = os.path.join(root_dir, "src/conf_mode/system-login-banner.py")
            self.replace_patterns_in_file(login_banner_path, [
                ("Welcome to VyOS", "Welcome to %s" % alternative_name),
            ])

            version_path = os.path.join(root_dir, "src/op_mode/show_version.py")
            self.replace_patterns_in_file(version_path, [
                ("VyOS {{version}}", "%s {{version}}" % alternative_name),
            ])

        elif package_name == "vyatta-cfg":
            logging.info("Applying debranding for %s..." % package_name)

            # equuleus
            router_init_path = os.path.join(root_dir, "scripts/init/vyos-router")
            self.replace_patterns_in_file(router_init_path, [
                ("VyOS Config", "%s Config" % alternative_name),
                ("VyOS router", "%s router" % alternative_name),
            ])

    def remove_image_branding(self, root_dir):
        self.log_settings()
        if not self.is_debranding_enabled():
            return
        alternative_name = self.get_effective_name()

        logging.info("Applying debranding...")

        new_splash = os.path.join(resources_dir, "not-vyos/splash.png")
        target_splash = os.path.join(root_dir, "data/live-build-config/includes.binary/isolinux/splash.png")
        shutil.copy2(new_splash, target_splash)

        # sagitta & circinus
        defaults_toml_path = os.path.join(root_dir, "data/defaults.toml")
        if os.path.exists(defaults_toml_path):
            with open(defaults_toml_path, "r") as file:
                data = tomlkit.load(file)

            data["website_url"] = "localhost"
            data["support_url"] = "There is no official support."
            data["bugtracker_url"] = "DO NOT report bugs to VyOS!"
            data["project_news_url"] = "This is unofficial %s build." % alternative_name

            with open(defaults_toml_path, "w") as file:
                tomlkit.dump(data, file)

        # equuleus
        motd_path = os.path.join(root_dir, "data/live-build-config/includes.chroot/usr/share/vyos/default_motd")
        self.replace_patterns_in_file(motd_path, [
            ("VyOS", alternative_name),
            (re.compile(r"Check out project news at.*"), "This is unofficial %s build."),
            (re.compile(r"and feel free to report bugs at.*"), "DO NOT report bugs to VyOS!"),
        ])

    def replace_patterns_in_file(self, path, patterns):
        if not os.path.exists(path):
            return

        with open(path, "r") as file:
            contents = file.read()

        changed = False
        for pattern, replacement in patterns:
            if isinstance(pattern, re.Pattern):
                contents = pattern.sub(replacement, contents)
            else:
                contents = contents.replace(pattern, replacement)
            changed = True

        if changed:
            with open(path, "w") as file:
                file.write(contents)

    def is_debranding_enabled(self):
        if self.remove_branding:
            return True
        if self.keep_branding:
            return False

        if self.cache.get("remove_branding"):
            return True
        if self.cache.get("keep_branding"):
            return False

        return True

    def get_effective_name(self):
        if self.alternative_name is not None:
            return self.alternative_name
        cached_value = self.cache.get("alternative_name")
        if cached_value is not None:
            return cached_value
        return self.DEFAULT

    def remember_settings(self):
        if self.remove_branding:
            self.cache.set("remove_branding", True)
            self.cache.set("keep_branding", False)
        elif self.keep_branding:
            self.cache.set("keep_branding", True)
            self.cache.set("remove_branding", False)
        if self.alternative_name is not None:
            self.cache.set("alternative_name", self.alternative_name)

    def log_settings(self):
        if self.logged:
            return
        self.logged = True

        if not self.is_debranding_enabled():
            option = "option" if self.keep_branding else "cached option"
            logging.info("Using %s --keep-branding to keep VyOS branding intact" % option)
        else:
            name = self.get_effective_name()
            if name == self.DEFAULT:
                logging.info("Using %s as default debrainding name" % name)
            else:
                option = "option" if self.alternative_name is not None else "cached option"
                logging.info("Using %s --branding-name=%s as debrainding name" % (option, quote(name)))
