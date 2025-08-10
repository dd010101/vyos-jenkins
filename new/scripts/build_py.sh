#!/usr/bin/env bash
set -e
source /my-build-scripts/env.sh
package_name="$1"

# just to be sure
sudo apt-get update

my_script="/my-build-scripts/$package_name.sh"
if [ -f "$my_script" ]; then
  $my_script
else
  # It's required to call python explicitly since some scripts don't have correct shebang.
  python3 ./build.py
fi
