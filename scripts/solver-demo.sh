#!/usr/bin/env bash
source /usr/lib/openfoam/openfoam2412/etc/bashrc
set -euo pipefail
script_dir=$(cd "$(dirname "$0")" && pwd)
source_case=/home/akshay/fan-agent-cadmesh-6zIy8SyE
run_dir=$(mktemp -d "${FAN_AGENT_RUN_ROOT:-$HOME}/fan-agent-solver-XXXXXXXX")
echo "CASE_DIRECTORY=$run_dir"
trap 'code=$?; tail -n 35 "$run_dir"/log.* 2>/dev/null; exit "$code"' ERR
cp -a "$source_case/constant" "$source_case/system" "$run_dir/"
/usr/bin/python3 "$(dirname "$0")/build-solver-demo.py" "$run_dir"
cd "$run_dir"
timeout 120 checkMesh -constant -allTopology -allGeometry > log.checkMesh 2>&1
grep -q 'Mesh OK' log.checkMesh
find system constant 0 -type f -exec sha256sum {} + > source-sha256.txt
timeout 900 simpleFoam > log.simpleFoam 2>&1
grep -q '^End' log.simpleFoam
test -s 300/U
/usr/bin/python3 "$script_dir/assess-solver-demo.py" "$run_dir" > log.assessment
touch simulation.foam
echo 'EXECUTION_COMPLETED=yes'
echo 'PERFORMANCE_ACCEPTED=no'
tail -n 24 log.simpleFoam
