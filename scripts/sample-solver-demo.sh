#!/usr/bin/env bash
source /usr/lib/openfoam/openfoam2412/etc/bashrc
set -euo pipefail
case_dir=/home/akshay/fan-agent-solver-uZX4M3Fw
cp "$(dirname "$0")/airflowPlane" "$case_dir/system/airflowPlane"
cd "$case_dir"
timeout 120 simpleFoam -postProcess -func airflowPlane -time '100,200,300' > log.sampling 2>&1
find postProcessing/airflowPlane -type f
