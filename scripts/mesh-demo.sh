#!/usr/bin/env bash
source /usr/lib/openfoam/openfoam2412/etc/bashrc
set -euo pipefail
test "$WM_PROJECT_VERSION" = v2412
run_dir=$(mktemp -d "$HOME/fan-agent-mesh-XXXXXXXX")
echo "CASE_DIRECTORY=$run_dir"
trap 'code=$?; echo "FAILED_EXIT=$code"; tail -n 25 "$run_dir"/log.* 2>/dev/null; exit "$code"' ERR
/usr/bin/python3 "$(dirname "$0")/build-mesh-demo.py" "$run_dir" "${FAN_AGENT_MESH_PROFILE:-medial}" > "$run_dir/log.geometry" 2>&1
cd "$run_dir"
find system constant/triSurface -type f -exec sha256sum {} + > source-sha256.txt
timeout 120 surfaceCheck constant/triSurface/fan.stl > log.surfaceCheck 2>&1
timeout 120 blockMesh > log.blockMesh 2>&1
timeout 120 surfaceFeatureExtract > log.surfaceFeatureExtract 2>&1
foamDictionary system/snappyHexMeshDict -entry addLayers -set false > log.configure 2>&1
timeout 600 snappyHexMesh -overwrite > log.snapping 2>&1
cp log.snapping log.snappyHexMesh
timeout 120 topoSet > log.topoSet 2>&1
timeout 120 checkMesh -constant -allTopology -allGeometry > log.checkMesh 2>&1
mkdir -p stages/snapped/constant
cp -a constant/polyMesh stages/snapped/constant/
if test -d 0/polyMesh; then mkdir -p stages/snapped/0; cp -a 0/polyMesh stages/snapped/0/; fi
cp log.checkMesh log.snappyHexMesh log.topoSet stages/snapped/
/usr/bin/python3 "$(dirname "$0")/inspect-mesh.py" "$run_dir/stages/snapped" > log.snapped-diagnostics
foamDictionary system/snappyHexMeshDict -entry castellatedMesh -set false >> log.configure 2>&1
foamDictionary system/snappyHexMeshDict -entry snap -set false >> log.configure 2>&1
foamDictionary system/snappyHexMeshDict -entry addLayers -set true >> log.configure 2>&1
timeout 600 snappyHexMesh -overwrite > log.layers 2>&1
cat log.snapping log.layers > log.snappyHexMesh
timeout 120 topoSet > log.topoSet 2>&1
touch mesh.foam
timeout 120 checkMesh -constant -allTopology -allGeometry > log.checkMesh 2>&1
/usr/bin/python3 "$(dirname "$0")/inspect-mesh.py" "$run_dir" --gate
grep -q 'Mesh OK' log.checkMesh
grep -Eq 'cellZoneSet rotor now size [1-9][0-9]*' log.topoSet
echo 'MESH_CHECK=passed'
echo 'RESULT_CLASS=experimental_mesh_only'
tail -n 22 log.checkMesh
