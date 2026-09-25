#!/usr/bin/env bash
# Experimental repair of a retained synthetic case; never operates in-place.
source /usr/lib/openfoam/openfoam2412/etc/bashrc
set -euo pipefail
source_case=/home/akshay/fan-agent-mesh-6xCb4e4u
run_dir=$(mktemp -d "${FAN_AGENT_RUN_ROOT:-$HOME}/fan-agent-repair-XXXXXXXX")
echo "CASE_DIRECTORY=$run_dir"
cp -a "$source_case/constant" "$source_case/system" "$run_dir/"
cd "$run_dir"
cp /usr/lib/openfoam/openfoam2412/etc/caseDicts/annotated/collapseDict system/collapseDict
foamDictionary system/collapseDict -entry collapseEdgesCoeffs/minimumEdgeLength -set 0.0001 > log.configure 2>&1
foamDictionary system/collapseDict -entry collapseEdgesCoeffs/maximumMergeAngle -set 5 >> log.configure 2>&1
find system -type f -exec sha256sum {} + > source-sha256.txt
timeout 180 collapseEdges -overwrite -constant > log.collapseEdges 2>&1
timeout 120 checkMesh -constant -allTopology -allGeometry > log.checkMesh 2>&1
touch mesh.foam
echo 'RESULT_CLASS=repair_trial_only'
echo 'Layer coverage and CAD surface fidelity must be remeasured after repair.'
tail -n 30 log.checkMesh
grep -q 'Mesh OK' log.checkMesh
