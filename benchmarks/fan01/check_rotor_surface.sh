#!/usr/bin/env bash
source /usr/lib/openfoam/openfoam2412/etc/bashrc >/dev/null 2>&1
set -euo pipefail
script_dir=$(cd "$(dirname "$0")" && pwd)
audit_dir=$(mktemp -d /tmp/fan01-surface-XXXXXXXX)
cp "$script_dir/rotor-metres.stl" "$audit_dir/rotor.stl"
cd "$audit_dir"
echo "AUDIT_DIRECTORY=$audit_dir" > "$script_dir/log.surfaceCheck"
timeout 120 surfaceCheck -checkSelfIntersection rotor.stl >> "$script_dir/log.surfaceCheck" 2>&1
cat "$script_dir/log.surfaceCheck"
