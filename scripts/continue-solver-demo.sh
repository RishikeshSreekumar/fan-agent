#!/usr/bin/env bash
source /usr/lib/openfoam/openfoam2412/etc/bashrc
set -euo pipefail
source_case=/home/akshay/fan-agent-solver-uZX4M3Fw
run_dir=$(mktemp -d "$HOME/fan-agent-solver-extended-XXXXXXXX")
echo "CASE_DIRECTORY=$run_dir"
cp -a "$source_case/." "$run_dir/"
cd "$run_dir"
cp system/controlDict system/controlDict.initial
foamDictionary system/controlDict -entry startFrom -set latestTime > log.extend-config 2>&1
foamDictionary system/controlDict -entry endTime -set 1000 >> log.extend-config 2>&1
cp log.simpleFoam log.initial-simpleFoam
timeout 900 simpleFoam > log.continuation 2>&1
cat log.initial-simpleFoam log.continuation > log.simpleFoam
grep -q '^End' log.continuation
test -s 1000/U
/usr/bin/python3 "$(dirname "$0")/assess-solver-demo.py" "$run_dir"
