Package info for equuleus
--

List of required packages and their Jenkinsfile:

Some packages (`wide-dhcpv6`) are broken right now, that's why
fork `https://github.com/dd010101/vyos-build.git` is required. Until they are fixed.

Some packages aren't in the VyOS repositories at all (`python3-inotify`), that's why
`https://github.com/dd010101/vyos-missing.git` is required.

| Package                 | GIT repository                                      | Branch   | Location of Jenkinsfile              |
|-------------------------|-----------------------------------------------------|----------|--------------------------------------|
| dropbear                | https://github.com/vyos/vyos-build.git              | equuleus | packages/dropbear/Jenkinsfile        |
| frr                     | https://github.com/vyos/vyos-build.git              | equuleus | packages/frr/Jenkinsfile             |
| hostap                  | https://github.com/vyos/vyos-build.git              | equuleus | packages/hostap/Jenkinsfile          |
| hvinfo                  | https://github.com/vyos/hvinfo.git                  | equuleus | Jenkinsfile                          |
| ipaddrcheck             | https://github.com/vyos/ipaddrcheck.git             | equuleus | Jenkinsfile                          |
| iproute2                | https://github.com/vyos/vyos-build.git              | equuleus | packages/iproute2/Jenkinsfile        |
| keepalived              | https://github.com/vyos/vyos-build.git              | equuleus | packages/keepalived/Jenkinsfile      |
| libnss-mapuser          | https://github.com/vyos/libnss-mapuser.git          | equuleus | Jenkinsfile                          |
| libpam-radius-auth      | https://github.com/vyos/libpam-radius-auth.git      | equuleus | Jenkinsfile                          |
| libvyosconfig           | https://github.com/vyos/libvyosconfig.git           | equuleus | Jenkinsfile                          |
| linux-kernel            | https://github.com/vyos/vyos-build.git              | equuleus | packages/linux-kernel/Jenkinsfile    |
| live-boot               | https://github.com/vyos/live-boot.git               | equuleus | Jenkinsfile                          |
| mdns-repeater           | https://github.com/vyos/mdns-repeater.git           | equuleus | Jenkinsfile                          |
| minisign                | https://github.com/vyos/vyos-build.git              | equuleus | packages/minisign/Jenkinsfile        |
| netfilter               | https://github.com/vyos/vyos-build.git              | equuleus | packages/netfilter/Jenkinsfile       |
| ocserv                  | https://github.com/vyos/vyos-build.git              | equuleus | packages/ocserv/Jenkinsfile          |
| python3-inotify         | **https://github.com/dd010101/vyos-missing.git**    | equuleus | packages/python3-inotify/Jenkinsfile |
| telegraf                | https://github.com/vyos/vyos-build.git              | equuleus | packages/telegraf/Jenkinsfile        |
| udp-broadcast-relay     | https://github.com/vyos/udp-broadcast-relay.git     | equuleus | Jenkinsfile                          |
| vyatta-bash             | https://github.com/vyos/vyatta-bash.git             | equuleus | Jenkinsfile                          |
| vyatta-biosdevname      | https://github.com/vyos/vyatta-biosdevname.git      | equuleus | Jenkinsfile                          |
| vyatta-cfg              | https://github.com/vyos/vyatta-cfg.git              | equuleus | Jenkinsfile                          |
| vyatta-cfg-firewall     | https://github.com/vyos/vyatta-cfg-firewall.git     | equuleus | Jenkinsfile                          |
| vyatta-cfg-qos          | https://github.com/vyos/vyatta-cfg-qos.git          | equuleus | Jenkinsfile                          |
| vyatta-cfg-quagga       | https://github.com/vyos/vyatta-cfg-quagga.git       | equuleus | Jenkinsfile                          |
| vyatta-cfg-system       | https://github.com/vyos/vyatta-cfg-system.git       | equuleus | Jenkinsfile                          |
| vyatta-cfg-vpn          | https://github.com/vyos/vyatta-cfg-vpn.git          | equuleus | Jenkinsfile                          |
| vyatta-cluster          | https://github.com/vyos/vyatta-cluster.git          | equuleus | Jenkinsfile                          |
| vyatta-config-mgmt      | https://github.com/vyos/vyatta-config-mgmt.git      | equuleus | Jenkinsfile                          |
| vyatta-conntrack        | https://github.com/vyos/vyatta-conntrack.git        | equuleus | Jenkinsfile                          |
| vyatta-nat              | https://github.com/vyos/vyatta-nat.git              | equuleus | Jenkinsfile                          |
| vyatta-op               | https://github.com/vyos/vyatta-op.git               | equuleus | Jenkinsfile                          |
| vyatta-op-firewall      | https://github.com/vyos/vyatta-op-firewall.git      | equuleus | Jenkinsfile                          |
| vyatta-op-qos           | https://github.com/vyos/vyatta-op-qos.git           | equuleus | Jenkinsfile                          |
| vyatta-op-vpn           | https://github.com/vyos/vyatta-op-vpn.git           | equuleus | Jenkinsfile                          |
| vyatta-wanloadbalance   | https://github.com/vyos/vyatta-wanloadbalance.git   | equuleus | Jenkinsfile                          |
| vyatta-zone             | https://github.com/vyos/vyatta-zone.git             | equuleus | Jenkinsfile                          |
| vyos-1x                 | https://github.com/vyos/vyos-1x.git                 | equuleus | Jenkinsfile                          |
| vyos-cloud-init         | https://github.com/vyos/vyos-cloud-init.git         | equuleus | Jenkinsfile                          |
| vyos-http-api-tools     | https://github.com/vyos/vyos-http-api-tools.git     | equuleus | Jenkinsfile                          |
| vyos-nhrp               | https://github.com/vyos/vyos-nhrp.git               | equuleus | Jenkinsfile                          |
| vyos-opennhrp           | https://github.com/vyos/vyos-opennhrp.git           | equuleus | Jenkinsfile                          |
| vyos-strongswan         | https://github.com/vyos/vyos-strongswan.git         | equuleus | Jenkinsfile                          |
| vyos-user-utils         | https://github.com/vyos/vyos-user-utils.git         | equuleus | Jenkinsfile                          |
| vyos-utils              | https://github.com/vyos/vyos-utils.git              | equuleus | Jenkinsfile                          |
| vyos-world              | https://github.com/vyos/vyos-world.git              | equuleus | Jenkinsfile                          |
| vyos-xe-guest-utilities | https://github.com/vyos/vyos-xe-guest-utilities.git | equuleus | Jenkinsfile                          |
| wide-dhcpv6             | **https://github.com/dd010101/vyos-build.git**      | equuleus | packages/wide-dhcpv6/Jenkinsfile     |

Package info for sagitta
--

List of required packages and their Jenkinsfile:

Some packages (`pam_tacplus`, `strongswan`, `linux-kernel`) are broken right now, that's why
fork `https://github.com/dd010101/vyos-build.git` is required. Until they are fixed.

Some packages aren't in the vyos repositories at all (`libnss-tacplus`), that's why
`https://github.com/dd010101/vyos-missing.git` is required.

Another special case is `vyos-xe-guest-utilities` where `current` branch is required.

| Package                                  | GIT repository                                      | Branch      | Location of Jenkinsfile                                       |
|------------------------------------------|-----------------------------------------------------|-------------|---------------------------------------------------------------|
| aws-gateway-load-balancer-tunnel-handler | https://github.com/vyos/vyos-build.git              | sagitta     | packages/aws-gateway-load-balancer-tunnel-handler/Jenkinsfile |
| ddclient                                 | https://github.com/vyos/vyos-build.git              | sagitta     | packages/ddclient/Jenkinsfile                                 |
| dropbear                                 | https://github.com/vyos/vyos-build.git              | sagitta     | packages/dropbear/Jenkinsfile                                 |
| ethtool                                  | https://github.com/vyos/vyos-build.git              | sagitta     | packages/ethtool/Jenkinsfile                                  |
| frr                                      | https://github.com/vyos/vyos-build.git              | sagitta     | packages/frr/Jenkinsfile                                      |
| hostap                                   | https://github.com/vyos/vyos-build.git              | sagitta     | packages/hostap/Jenkinsfile                                   |
| hsflowd                                  | https://github.com/vyos/vyos-build.git              | sagitta     | packages/hsflowd/Jenkinsfile                                  |
| hvinfo                                   | https://github.com/vyos/hvinfo.git                  | sagitta     | Jenkinsfile                                                   |
| ipaddrcheck                              | https://github.com/vyos/ipaddrcheck.git             | sagitta     | Jenkinsfile                                                   |
| isc-dhcp                                 | https://github.com/vyos/vyos-build.git              | sagitta     | packages/isc-dhcp/Jenkinsfile                                 |
| keepalived                               | https://github.com/vyos/vyos-build.git              | sagitta     | packages/keepalived/Jenkinsfile                               |
| libnss-mapuser                           | https://github.com/vyos/libnss-mapuser.git          | sagitta     | Jenkinsfile                                                   |
| libnss-tacplus                           | **https://github.com/dd010101/vyos-missing.git**    | sagitta     | packages/libnss-tacplus/Jenkinsfile                           |
| libpam-radius-auth                       | https://github.com/vyos/libpam-radius-auth.git      | sagitta     | Jenkinsfile                                                   |
| libvyosconfig                            | https://github.com/vyos/libvyosconfig.git           | sagitta     | Jenkinsfile                                                   |
| linux-kernel                             | **https://github.com/dd010101/vyos-build.git**      | sagitta     | packages/linux-kernel/Jenkinsfile                             |
| live-boot                                | https://github.com/vyos/live-boot.git               | sagitta     | Jenkinsfile                                                   |
| ndppd                                    | https://github.com/vyos/vyos-build.git              | sagitta     | packages/ndppd/Jenkinsfile                                    |
| net-snmp                                 | https://github.com/vyos/vyos-build.git              | sagitta     | packages/net-snmp/Jenkinsfile                                 |
| netfilter                                | https://github.com/vyos/vyos-build.git              | sagitta     | packages/netfilter/Jenkinsfile                                |
| opennhrp                                 | https://github.com/vyos/vyos-build.git              | sagitta     | packages/opennhrp/Jenkinsfile                                 |
| openvpn-otp                              | https://github.com/vyos/vyos-build.git              | sagitta     | packages/openvpn-otp/Jenkinsfile                              |
| owamp                                    | https://github.com/vyos/vyos-build.git              | sagitta     | packages/owamp/Jenkinsfile                                    |
| pam_tacplus                              | **https://github.com/dd010101/vyos-build.git**      | sagitta     | packages/pam_tacplus/Jenkinsfile                              |
| pmacct                                   | https://github.com/vyos/vyos-build.git              | sagitta     | packages/pmacct/Jenkinsfile                                   |
| podman                                   | https://github.com/vyos/vyos-build.git              | sagitta     | packages/podman/Jenkinsfile                                   |
| pyhumps                                  | https://github.com/vyos/vyos-build.git              | sagitta     | packages/pyhumps/Jenkinsfile                                  |
| radvd                                    | https://github.com/vyos/vyos-build.git              | sagitta     | packages/radvd/Jenkinsfile                                    |
| strongswan                               | **https://github.com/dd010101/vyos-build.git**      | sagitta     | packages/strongswan/Jenkinsfile                               |
| telegraf                                 | https://github.com/vyos/vyos-build.git              | sagitta     | packages/telegraf/Jenkinsfile                                 |
| udp-broadcast-relay                      | https://github.com/vyos/udp-broadcast-relay.git     | sagitta     | Jenkinsfile                                                   |
| vyatta-bash                              | https://github.com/vyos/vyatta-bash.git             | sagitta     | Jenkinsfile                                                   |
| vyatta-biosdevname                       | https://github.com/vyos/vyatta-biosdevname.git      | sagitta     | Jenkinsfile                                                   |
| vyatta-cfg                               | https://github.com/vyos/vyatta-cfg.git              | sagitta     | Jenkinsfile                                                   |
| vyatta-cfg-system                        | https://github.com/vyos/vyatta-cfg-system.git       | sagitta     | Jenkinsfile                                                   |
| vyatta-op                                | https://github.com/vyos/vyatta-op.git               | sagitta     | Jenkinsfile                                                   |
| vyatta-wanloadbalance                    | https://github.com/vyos/vyatta-wanloadbalance.git   | sagitta     | Jenkinsfile                                                   |
| vyos-1x                                  | https://github.com/vyos/vyos-1x.git                 | sagitta     | Jenkinsfile                                                   |
| vyos-cloud-init                          | https://github.com/vyos/vyos-cloud-init.git         | sagitta     | Jenkinsfile                                                   |
| vyos-http-api-tools                      | https://github.com/vyos/vyos-http-api-tools.git     | sagitta     | Jenkinsfile                                                   |
| vyos-user-utils                          | https://github.com/vyos/vyos-user-utils.git         | sagitta     | Jenkinsfile                                                   |
| vyos-utils                               | https://github.com/vyos/vyos-utils.git              | sagitta     | Jenkinsfile                                                   |
| vyos-world                               | https://github.com/vyos/vyos-world.git              | sagitta     | Jenkinsfile                                                   |
| vyos-xe-guest-utilities                  | https://github.com/vyos/vyos-xe-guest-utilities.git | **current** | Jenkinsfile                                                   |
| wide-dhcpv6                              | https://github.com/vyos/vyos-build.git              | sagitta     | packages/wide-dhcpv6/Jenkinsfile                              |

Additional jobs
--

These jobs aren't packages, but they are made in the same spirit to make configuration simpler. Configuration on
Jenkins side is identical to configuration for packages.

| Job                  | GIT repository                                 | Branch       | Location of Jenkinsfile                   |
|----------------------|------------------------------------------------|--------------|-------------------------------------------|
| vyos-build-container | **https://github.com/dd010101/vyos-build.git** | **equuleus** | packages/vyos-build-container/Jenkinsfile |
| vyos-build-container | **https://github.com/dd010101/vyos-build.git** | **sagitta**  | packages/vyos-build-container/Jenkinsfile |
| vyos-build-container | **https://github.com/dd010101/vyos-build.git** | **current**  | packages/vyos-build-container/Jenkinsfile |

Job `vyos-build-container` builds `vyos-build` docker container image. This image is pushed to local registry specified
with environment variable `CUSTOM_DOCKER_REPO`. The `vyos-build` docker container is used to build all packages.
This job is used as automation to do the same process as described above in
[Build patched vyos-build docker images](#build-patched-vyos-build-docker-images)
to keep the docker images up to date - this replaces the need to rebuild images from time to time and thus reduces
maintenance.
