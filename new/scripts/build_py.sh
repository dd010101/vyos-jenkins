#!/usr/bin/env bash
set -e
package_name="$1"

my_script="/my-build-scripts/$package_name.sh"
if [ -f "$my_script" ]; then
  $my_script
else
  # It's required to call python explicitly since some scripts don't have correct shebang.
  python3 ./build.py
fi
