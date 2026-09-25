#!/usr/bin/env bash
# Fixed vendor tutorial only. No designer input or arbitrary commands.
source /usr/lib/openfoam/openfoam2412/etc/bashrc
set -euo pipefail
test "$WM_PROJECT_VERSION" = v2412
run_dir=$(mktemp -d "${FAN_AGENT_RUN_ROOT:-$HOME}/fan-agent-smoke-XXXXXXXX")
echo "CASE_DIRECTORY=$run_dir"
echo "OPENFOAM_VERSION=$WM_PROJECT_VERSION"
cp -a "$FOAM_TUTORIALS/incompressible/simpleFoam/mixerVessel2D/." "$run_dir/"
cd "$run_dir"
trap 'code=$?; echo "FAILED_EXIT=$code"; for logfile in log.blockMesh log.checkMesh log.simpleFoam; do if test -f "$logfile"; then echo "LOG=$logfile"; tail -n 20 "$logfile"; fi; done; exit "$code"' ERR
find constant system 0.orig -type f -exec sha256sum {} + > source-sha256.txt
cp -a 0.orig 0
m4 system/blockMeshDict.m4 > system/blockMeshDict
timeout 120 blockMesh > log.blockMesh 2>&1
timeout 120 checkMesh > log.checkMesh 2>&1
grep -q 'Mesh OK' log.checkMesh
timeout 300 simpleFoam > log.simpleFoam 2>&1
grep -q '^End' log.simpleFoam
test -s 500/U
test -s 500/p
echo 'MESH_CHECK=passed'
echo 'SOLVER_COMPLETION=passed'
echo 'RESULT_CLASS=runtime_smoke_only'
echo '--- solver summary ---'
tail -n 18 log.simpleFoam
