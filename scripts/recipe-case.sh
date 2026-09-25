#!/usr/bin/env bash
# Phase 1 recipe: one mesh level, fixed synthetic fan, bounded iteration budget. Usage: LEVEL RPM DIRECTION
source /usr/lib/openfoam/openfoam2412/etc/bashrc
set -euo pipefail
test "$WM_PROJECT_VERSION" = v2412
level=$1; rpm=$2; direction=$3
case "$level" in coarse|medium|fine) ;; *) echo 'Invalid level'; exit 2 ;; esac
[[ "$rpm" =~ ^[0-9]+(\.[0-9]+)?$ ]] || { echo 'Invalid rpm'; exit 2; }
case "$direction" in cw|ccw) ;; *) echo 'Invalid direction'; exit 2 ;; esac
procs=${FAN_AGENT_CFD_PROCS:-1}
[[ "$procs" =~ ^[1-9][0-9]*$ ]] || { echo 'Invalid FAN_AGENT_CFD_PROCS'; exit 2; }
solver_timeout=${FAN_AGENT_SOLVER_TIMEOUT:-14400}
[[ "$solver_timeout" =~ ^[1-9][0-9]*$ ]] || { echo 'Invalid FAN_AGENT_SOLVER_TIMEOUT'; exit 2; }
script_dir=$(cd "$(dirname "$0")" && pwd)
run_dir=$(mktemp -d "${FAN_AGENT_RUN_ROOT:-$HOME}/fan-agent-recipe-$level-XXXXXXXX")
echo "CASE_DIRECTORY=$run_dir"
trap 'code=$?; echo "FAILED_EXIT=$code"; tail -n 25 "$run_dir"/log.* 2>/dev/null; exit "$code"' ERR
timeout 3600 /usr/bin/python3 "$script_dir/build-recipe-case.py" "$run_dir" "$level" "$rpm" "$direction" "$procs" > "$run_dir/log.build" 2>&1
cd "$run_dir"
find system constant 0 -type f -exec sha256sum {} + > source-sha256.txt
timeout 1800 gmshToFoam volume.msh > log.gmshToFoam 2>&1
/usr/bin/python3 "$script_dir/cad-mesh-audit.py" "$run_dir" --walls
timeout 600 topoSet > log.topoSet 2>&1
timeout 1800 checkMesh -constant -allTopology -allGeometry > log.checkMesh 2>&1
/usr/bin/python3 "$script_dir/cad-mesh-audit.py" "$run_dir" > log.meshAudit
touch simulation.foam
solve() {
    if test "$procs" -gt 1; then timeout "$1" mpirun -np "$procs" simpleFoam -parallel; else timeout "$1" simpleFoam; fi
}
if test "$procs" -gt 1; then decomposePar -force > log.decomposePar 2>&1; fi
solve "$solver_timeout" > log.stage1 2>&1
grep -q '^End' log.stage1
cp system/fvSchemes.stage2 system/fvSchemes
cp system/fvSolution.stage2 system/fvSolution
max_iterations=$(/usr/bin/python3 -c "import sys; sys.path.insert(0, '$script_dir/..'); from fan_agent.recipe import CONVERGENCE; print(CONVERGENCE['max_iterations'])")
foamDictionary system/controlDict -entry endTime -set "$max_iterations" > log.stage2-config 2>&1
solve "$solver_timeout" > log.stage2 2>&1
grep -q '^End' log.stage2
if test "$procs" -gt 1; then reconstructPar -latestTime > log.reconstructPar 2>&1; fi
cat log.stage1 log.stage2 > log.simpleFoam
/usr/bin/python3 "$script_dir/assess-recipe-case.py" "$run_dir"
