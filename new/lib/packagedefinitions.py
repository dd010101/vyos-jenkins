import logging

from lib.github import GitHub


class PackageDefinitions:
    def __init__(self, vyos_stream_mode=False):
        self.vyos_stream_mode = vyos_stream_mode
        self.static_definitions = {
            "circinus-stream": circinus_stream,
            "circinus": circinus_frozen,
        }

    def get_definitions(self, github_org, branch):
        virtual_branch = self.get_virtual_branch(branch)
        if virtual_branch in self.static_definitions:
            return self.static_definitions[virtual_branch]
        else:
            github = GitHub(self.vyos_stream_mode)
            logging.info("Fetching vyos repository list")
            repositories = github.find_repositories("org", github_org)
            logging.info("Analyzing package metadata")
            packages = github.analyze_repositories_workflow(github_org, repositories, branch)
            return packages

    def is_static(self, branch):
        virtual_branch = self.get_virtual_branch(branch)
        return virtual_branch in self.static_definitions

    def get_virtual_branch(self, branch):
        virtual_branch = branch
        if self.vyos_stream_mode:
            virtual_branch += "-stream"
        return virtual_branch


circinus_stream = {
    "aws-gwlbtun": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "aws-gwlbtun",
        "build_type": "build.py",
        "path": "scripts/package-build/aws-gwlbtun",
        "change_patterns": [
            "scripts/package-build/aws-gwlbtun/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "ddclient": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "ddclient",
        "build_type": "build.py",
        "path": "scripts/package-build/ddclient",
        "change_patterns": [
            "scripts/package-build/ddclient/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "dropbear": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "dropbear",
        "build_type": "build.py",
        "path": "scripts/package-build/dropbear",
        "change_patterns": [
            "scripts/package-build/dropbear/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "ethtool": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "ethtool",
        "build_type": "build.py",
        "path": "scripts/package-build/ethtool",
        "change_patterns": [
            "scripts/package-build/ethtool/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "frr": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "frr",
        "build_type": "build.py",
        "path": "scripts/package-build/frr",
        "change_patterns": [
            "scripts/package-build/frr/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "hostap": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "hostap",
        "build_type": "build.py",
        "path": "scripts/package-build/hostap",
        "change_patterns": [
            "scripts/package-build/hostap/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "hsflowd": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "hsflowd",
        "build_type": "build.py",
        "path": "scripts/package-build/hsflowd",
        "change_patterns": [
            "scripts/package-build/hsflowd/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "hvinfo": {
        "repo_name": "hvinfo",
        "branch": "circinus",
        "package_name": "hvinfo",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/hvinfo.git",
    },
    "ipaddrcheck": {
        "repo_name": "ipaddrcheck",
        "branch": "circinus",
        "package_name": "ipaddrcheck",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/ipaddrcheck.git",
    },
    "isc-dhcp": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "isc-dhcp",
        "build_type": "build.py",
        "path": "scripts/package-build/isc-dhcp",
        "change_patterns": [
            "scripts/package-build/isc-dhcp/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "kea": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "kea",
        "build_type": "build.py",
        "path": "scripts/package-build/kea",
        "change_patterns": [
            "scripts/package-build/kea/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "keepalived": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "keepalived",
        "build_type": "build.py",
        "path": "scripts/package-build/keepalived",
        "change_patterns": [
            "scripts/package-build/keepalived/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "libnss-mapuser": {
        "repo_name": "libnss-mapuser",
        "branch": "circinus",
        "package_name": "libnss-mapuser",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/libnss-mapuser.git",
    },
    "libpam-radius-auth": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "libpam-radius-auth",
        "build_type": "build.py",
        "path": "scripts/package-build/libpam-radius-auth",
        "change_patterns": [
            "scripts/package-build/libpam-radius-auth/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "tacacs": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "tacacs",
        "build_type": "build.py",
        "path": "scripts/package-build/tacacs",
        "change_patterns": [
            "scripts/package-build/tacacs/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "libvyosconfig": {
        "repo_name": "libvyosconfig",
        "branch": "circinus",
        "package_name": "libvyosconfig",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/libvyosconfig.git",
    },
    "linux-kernel": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "linux-kernel",
        "build_type": "build.py",
        "path": "scripts/package-build/linux-kernel",
        "change_patterns": [
            "data/defaults.toml",
            "scripts/package-build/linux-kernel/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "live-boot": {
        "repo_name": "live-boot",
        "branch": "circinus",
        "package_name": "live-boot",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/live-boot.git",
    },
    "ndppd": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "ndppd",
        "build_type": "build.py",
        "path": "scripts/package-build/ndppd",
        "change_patterns": [
            "scripts/package-build/ndppd/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "net-snmp": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "net-snmp",
        "build_type": "build.py",
        "path": "scripts/package-build/net-snmp",
        "change_patterns": [
            "scripts/package-build/net-snmp/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "netfilter": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "netfilter",
        "build_type": "build.py",
        "path": "scripts/package-build/netfilter",
        "change_patterns": [
            "scripts/package-build/netfilter/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "opennhrp": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "opennhrp",
        "build_type": "build.py",
        "path": "scripts/package-build/opennhrp",
        "change_patterns": [
            "scripts/package-build/opennhrp/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "openvpn-otp": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "openvpn-otp",
        "build_type": "build.py",
        "path": "scripts/package-build/openvpn-otp",
        "change_patterns": [
            "scripts/package-build/openvpn-otp/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "owamp": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "owamp",
        "build_type": "build.py",
        "path": "scripts/package-build/owamp",
        "change_patterns": [
            "scripts/package-build/owamp/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "pmacct": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "pmacct",
        "build_type": "build.py",
        "path": "scripts/package-build/pmacct",
        "change_patterns": [
            "scripts/package-build/pmacct/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "podman": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "podman",
        "build_type": "build.py",
        "path": "scripts/package-build/podman",
        "change_patterns": [
            "scripts/package-build/podman/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "pyhumps": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "pyhumps",
        "build_type": "build.py",
        "path": "scripts/package-build/pyhumps",
        "change_patterns": [
            "scripts/package-build/pyhumps/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "radvd": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "radvd",
        "build_type": "build.py",
        "path": "scripts/package-build/radvd",
        "change_patterns": [
            "scripts/package-build/radvd/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "strongswan": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "strongswan",
        "build_type": "build.py",
        "path": "scripts/package-build/strongswan",
        "change_patterns": [
            "scripts/package-build/strongswan/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "telegraf": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "telegraf",
        "build_type": "build.py",
        "path": "scripts/package-build/telegraf",
        "change_patterns": [
            "scripts/package-build/telegraf/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "udp-broadcast-relay": {
        "repo_name": "udp-broadcast-relay",
        "branch": "circinus",
        "package_name": "udp-broadcast-relay",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/udp-broadcast-relay.git",
    },
    "vyatta-bash": {
        "repo_name": "vyatta-bash",
        "branch": "circinus",
        "package_name": "vyatta-bash",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/vyatta-bash.git",
    },
    "vyatta-biosdevname": {
        "repo_name": "vyatta-biosdevname",
        "branch": "circinus",
        "package_name": "vyatta-biosdevname",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/vyatta-biosdevname.git",
    },
    "vyatta-cfg": {
        "repo_name": "vyatta-cfg",
        "branch": "circinus",
        "package_name": "vyatta-cfg",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/vyatta-cfg.git",
    },
    "vyatta-wanloadbalance": {
        "repo_name": "vyatta-wanloadbalance",
        "branch": "circinus",
        "package_name": "vyatta-wanloadbalance",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/vyatta-wanloadbalance.git",
    },
    "vyos-1x": {
        "repo_name": "vyos-1x",
        "branch": "circinus",
        "package_name": "vyos-1x",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/vyos-1x.git",
    },
    "vyos-cloud-init": {
        "repo_name": "vyos-cloud-init",
        "branch": "circinus",
        "package_name": "vyos-cloud-init",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/vyos-cloud-init.git",
    },
    "vyos-http-api-tools": {
        "repo_name": "vyos-http-api-tools",
        "branch": "circinus",
        "package_name": "vyos-http-api-tools",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/vyos-http-api-tools.git",
    },
    "vyos-user-utils": {
        "repo_name": "vyos-user-utils",
        "branch": "circinus",
        "package_name": "vyos-user-utils",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/vyos-user-utils.git",
    },
    "vyos-utils": {
        "repo_name": "vyos-utils",
        "branch": "circinus",
        "package_name": "vyos-utils",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/vyos-utils.git",
    },
    "waagent": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "waagent",
        "build_type": "build.py",
        "path": "scripts/package-build/waagent",
        "change_patterns": [
            "scripts/package-build/waagent/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "wide-dhcpv6": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "wide-dhcpv6",
        "build_type": "build.py",
        "path": "scripts/package-build/wide-dhcpv6",
        "change_patterns": [
            "scripts/package-build/wide-dhcpv6/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "xen-guest-agent": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "xen-guest-agent",
        "build_type": "build.py",
        "path": "scripts/package-build/xen-guest-agent",
        "change_patterns": [
            "scripts/package-build/xen-guest-agent/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    }
}

########################################## frozen ##########################################

circinus_frozen = {
    "aws-gwlbtun": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "aws-gwlbtun",
        "build_type": "build.py",
        "path": "scripts/package-build/aws-gwlbtun",
        "change_patterns": [
            "scripts/package-build/aws-gwlbtun/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "ddclient": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "ddclient",
        "build_type": "build.py",
        "path": "scripts/package-build/ddclient",
        "change_patterns": [
            "scripts/package-build/ddclient/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "dropbear": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "dropbear",
        "build_type": "build.py",
        "path": "scripts/package-build/dropbear",
        "change_patterns": [
            "scripts/package-build/dropbear/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "ethtool": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "ethtool",
        "build_type": "build.py",
        "path": "scripts/package-build/ethtool",
        "change_patterns": [
            "scripts/package-build/ethtool/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "frr": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "frr",
        "build_type": "build.py",
        "path": "scripts/package-build/frr",
        "change_patterns": [
            "scripts/package-build/frr/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "hostap": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "hostap",
        "build_type": "build.py",
        "path": "scripts/package-build/hostap",
        "change_patterns": [
            "scripts/package-build/hostap/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "hsflowd": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "hsflowd",
        "build_type": "build.py",
        "path": "scripts/package-build/hsflowd",
        "change_patterns": [
            "scripts/package-build/hsflowd/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "hvinfo": {
        "repo_name": "hvinfo",
        "branch": "circinus",
        "package_name": "hvinfo",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/hvinfo.git",
    },
    "ipaddrcheck": {
        "repo_name": "ipaddrcheck",
        "branch": "circinus",
        "package_name": "ipaddrcheck",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/ipaddrcheck.git",
    },
    "isc-dhcp": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "isc-dhcp",
        "build_type": "build.py",
        "path": "scripts/package-build/isc-dhcp",
        "change_patterns": [
            "scripts/package-build/isc-dhcp/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "kea": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "kea",
        "build_type": "build.py",
        "path": "scripts/package-build/kea",
        "change_patterns": [
            "scripts/package-build/kea/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "keepalived": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "keepalived",
        "build_type": "build.py",
        "path": "scripts/package-build/keepalived",
        "change_patterns": [
            "scripts/package-build/keepalived/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "libnss-mapuser": {
        "repo_name": "libnss-mapuser",
        "branch": "circinus",
        "package_name": "libnss-mapuser",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/libnss-mapuser.git",
    },
    "libpam-tacplus": {
        "repo_name": "libpam-tacplus",
        "branch": "circinus",
        "package_name": "libpam-tacplus",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/libpam-tacplus.git",
    },
    "libvyosconfig": {
        "repo_name": "libvyosconfig",
        "branch": "circinus",
        "package_name": "libvyosconfig",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/libvyosconfig.git",
    },
    "linux-kernel": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "linux-kernel",
        "build_type": "build.py",
        "path": "scripts/package-build/linux-kernel",
        "change_patterns": [
            "data/defaults.toml",
            "scripts/package-build/linux-kernel/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "live-boot": {
        "repo_name": "live-boot",
        "branch": "circinus",
        "package_name": "live-boot",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/live-boot.git",
    },
    "ndppd": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "ndppd",
        "build_type": "build.py",
        "path": "scripts/package-build/ndppd",
        "change_patterns": [
            "scripts/package-build/ndppd/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "net-snmp": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "net-snmp",
        "build_type": "build.py",
        "path": "scripts/package-build/net-snmp",
        "change_patterns": [
            "scripts/package-build/net-snmp/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "netfilter": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "netfilter",
        "build_type": "build.py",
        "path": "scripts/package-build/netfilter",
        "change_patterns": [
            "scripts/package-build/netfilter/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "opennhrp": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "opennhrp",
        "build_type": "build.py",
        "path": "scripts/package-build/opennhrp",
        "change_patterns": [
            "scripts/package-build/opennhrp/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "openvpn-otp": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "openvpn-otp",
        "build_type": "build.py",
        "path": "scripts/package-build/openvpn-otp",
        "change_patterns": [
            "scripts/package-build/openvpn-otp/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "owamp": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "owamp",
        "build_type": "build.py",
        "path": "scripts/package-build/owamp",
        "change_patterns": [
            "scripts/package-build/owamp/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "pmacct": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "pmacct",
        "build_type": "build.py",
        "path": "scripts/package-build/pmacct",
        "change_patterns": [
            "scripts/package-build/pmacct/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "podman": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "podman",
        "build_type": "build.py",
        "path": "scripts/package-build/podman",
        "change_patterns": [
            "scripts/package-build/podman/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "pyhumps": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "pyhumps",
        "build_type": "build.py",
        "path": "scripts/package-build/pyhumps",
        "change_patterns": [
            "scripts/package-build/pyhumps/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "radvd": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "radvd",
        "build_type": "build.py",
        "path": "scripts/package-build/radvd",
        "change_patterns": [
            "scripts/package-build/radvd/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "strongswan": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "strongswan",
        "build_type": "build.py",
        "path": "scripts/package-build/strongswan",
        "change_patterns": [
            "scripts/package-build/strongswan/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "telegraf": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "telegraf",
        "build_type": "build.py",
        "path": "scripts/package-build/telegraf",
        "change_patterns": [
            "scripts/package-build/telegraf/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "udp-broadcast-relay": {
        "repo_name": "udp-broadcast-relay",
        "branch": "circinus",
        "package_name": "udp-broadcast-relay",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/udp-broadcast-relay.git",
    },
    "vyatta-bash": {
        "repo_name": "vyatta-bash",
        "branch": "circinus",
        "package_name": "vyatta-bash",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/vyatta-bash.git",
    },
    "vyatta-biosdevname": {
        "repo_name": "vyatta-biosdevname",
        "branch": "circinus",
        "package_name": "vyatta-biosdevname",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/vyatta-biosdevname.git",
    },
    "vyatta-cfg": {
        "repo_name": "vyatta-cfg",
        "branch": "circinus",
        "package_name": "vyatta-cfg",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/vyatta-cfg.git",
    },
    "vyatta-wanloadbalance": {
        "repo_name": "vyatta-wanloadbalance",
        "branch": "circinus",
        "package_name": "vyatta-wanloadbalance",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/vyatta-wanloadbalance.git",
    },
    "vyos-1x": {
        "repo_name": "vyos-1x",
        "branch": "circinus",
        "package_name": "vyos-1x",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/vyos-1x.git",
    },
    "vyos-cloud-init": {
        "repo_name": "vyos-cloud-init",
        "branch": "circinus",
        "package_name": "vyos-cloud-init",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/vyos-cloud-init.git",
    },
    "vyos-http-api-tools": {
        "repo_name": "vyos-http-api-tools",
        "branch": "circinus",
        "package_name": "vyos-http-api-tools",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/vyos-http-api-tools.git",
    },
    "vyos-user-utils": {
        "repo_name": "vyos-user-utils",
        "branch": "circinus",
        "package_name": "vyos-user-utils",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/vyos-user-utils.git",
    },
    "vyos-utils": {
        "repo_name": "vyos-utils",
        "branch": "circinus",
        "package_name": "vyos-utils",
        "build_type": "dpkg-buildpackage",
        "path": "",
        "change_patterns": [
            "*"
        ],
        "git_url": "https://github.com/vyos/vyos-utils.git",
    },
    "waagent": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "waagent",
        "build_type": "build.py",
        "path": "scripts/package-build/waagent",
        "change_patterns": [
            "scripts/package-build/waagent/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "wide-dhcpv6": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "wide-dhcpv6",
        "build_type": "build.py",
        "path": "scripts/package-build/wide-dhcpv6",
        "change_patterns": [
            "scripts/package-build/wide-dhcpv6/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    },
    "xen-guest-agent": {
        "repo_name": "vyos-build",
        "branch": "circinus",
        "package_name": "xen-guest-agent",
        "build_type": "build.py",
        "path": "scripts/package-build/xen-guest-agent",
        "change_patterns": [
            "scripts/package-build/xen-guest-agent/**"
        ],
        "git_url": "https://github.com/vyos/vyos-build.git",
    }
}
