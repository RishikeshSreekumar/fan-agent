#!/usr/bin/env bash
source /usr/lib/openfoam/openfoam2412/etc/bashrc
set -euo pipefail
run_dir=$(mktemp -d "${FAN_AGENT_RUN_ROOT:-$HOME}/fan-agent-cadmesh-XXXXXXXX")
echo "CASE_DIRECTORY=$run_dir"
trap 'code=$?; echo "FAILED_EXIT=$code"; tail -n 25 "$run_dir"/log.* 2>/dev/null; exit "$code"' ERR
/usr/bin/python3 "$(dirname "$0")/build-mesh-demo.py" "$run_dir" > "$run_dir/log.geometry" 2>&1
timeout 600 /usr/bin/python3 "$(dirname "$0")/build-cad-volume.py" "$run_dir" > "$run_dir/log.gmsh" 2>&1
cd "$run_dir"
find system -type f -exec sha256sum {} + > source-sha256.txt
timeout 120 gmshToFoam volume.msh > log.gmshToFoam 2>&1
/usr/bin/python3 "$(dirname "$0")/cad-mesh-audit.py" "$run_dir" --walls
timeout 120 topoSet > log.topoSet 2>&1
timeout 120 checkMesh -constant -allTopology -allGeometry > log.checkMesh 2>&1
touch mesh.foam
/usr/bin/python3 "$(dirname "$0")/cad-mesh-audit.py" "$run_dir"
echo 'RESULT_CLASS=cad_volume_mesh_baseline_no_prism_layers'
tail -n 28 log.checkMesh
grep -q 'Mesh OK' log.checkMesh
grep -Eq 'cellZoneSet rotor now size [1-9][0-9]*' log.topoSet
echo 'MESH_CHECK=passed'
