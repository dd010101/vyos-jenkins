sagitta
==

iproute2 (unknown)
--

The `iproute2` package is present in `https://github.com/vyos/vyos-build.git` for equuleus but missing for both
sagitta and current branch, yet it was present in sagitta `dev.packages.vyos.net` repository as 
`iproute2_6.6.0-1~bpo12+1_amd64.deb`. The name suggests this is Debian backported package, not sure what to think 
about this, but I don't see that this would be vyos-specific version and then why it's in the repository?

libnss-tacplus + libtacplus-map (unknown)
--

The `pam_tacplus` packages was successfully built, did produce .deb packages but not all of them
where packages like `libnss-tacplus_1.0.4-cl5.1.0u11_amd64.deb` and `libtacplus-map1_1.0.1-cl5.1.0u9_amd64.deb`
come from?

python3-vici (unknown)
--

This package is missing yet the `strongswan` was built successfully. For equuleus `python3-vici` was produced by
`vyos-strongswan` but sagitta has its own `strongswan` packages. Where the `python3-vici_5.9.8-1_all.deb` came from?

vpp (unknown)
--
Bunch of packages related to `vpp` are missing. Like `libvppinfra_23.06.0-2~gd34ae5c11~b27_amd64.deb`,
`vpp_23.06.0-2~gd34ae5c11~b27_amd64.deb`, `python3-vpp-api_23.06.0-2~gd34ae5c11~b27_amd64.deb` and others.
Where these did come from?

amazon-cloudwatch-agent (believed to be used only for AWS images)
--
See equuleus note.

-------

equuleus
==

xe-guest-utilities (believed to be unsused)
--

This package is missing but was present on `dev.packages.vyos.net`. I didn't find way to build this
package, there is `vyos-xe-guest-utilities.deb` form `https://github.com/vyos/vyos-xe-guest-utilities.git`
with references to `xe-guest-utilities.deb` but successful build produces only `vyos-xe-guest-utilities.deb`
and not `xe-guest-utilities.deb`. I far as I can see there isn't dependency on `xe-guest-utilities`, the only 
reference related to usage or dependency I found was for `vyos-xe-guest-utilities` thus I concluded this packages
isn't used and thus in the original mirror it was some legacy leftover? ISO builder did produce ISO even if this
packages was missing. If someone knows more about this please share what you know. 

amazon-cloudwatch-agent (believed to be used only for AWS images)
--

This package is missing but was present on `dev.packages.vyos.net`. I believe this isn't vyos-specific
version but just copy of amazon's package. This package should be used only for AWS images thus not used in
regular ISO image. If someone wants to build AWS images then you need to hunt down this .deb from amazon
I didn't find the right version, but I didn't look too hard either. If someone finds copy of
`amazon-cloudwatch-agent_1.247358.0b252413-1_amd64.deb` please share it (via GitHub Issues for example).
