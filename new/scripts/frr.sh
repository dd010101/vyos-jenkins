#!/usr/bin/env bash
set -e

sudo apt-get update
sudo apt-get install -y bison flex libelf-dev:native libreadline-dev liblua5.3-dev

# temporary workaround, official build script doesn't work lib libyang3 currently
# so we need to patch it back to libyang2 to make the official build script work
awk '
BEGIN { pkg = "" }
/^\[\[packages\]\]/ { pkg = "" }
/^name *= *"libyang"/ { pkg = "libyang" }
/^commit_id *= *"v3/ && pkg == "libyang" {
    sub(/v3[^"]*/, "v2.1.148")
}
{ print }
' package.toml > package.toml.tmp
mv package.toml.tmp package.toml

python3 ./build.py
