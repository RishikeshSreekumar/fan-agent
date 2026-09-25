#!/usr/bin/env bash
source /usr/lib/openfoam/openfoam2412/etc/bashrc
set -euo pipefail
script_dir=$(cd "$(dirname "$0")" && pwd)
source_case=/home/akshay/fan-agent-solver-extended-XLn0e3bm
run_dir=$(mktemp -d "${FAN_AGENT_RUN_ROOT:-$HOME}/fan-agent-convergence-XXXXXXXX")
echo "CASE_DIRECTORY=$run_dir"
cp -a "$source_case/." "$run_dir/"
cd "$run_dir"
cp system/controlDict system/controlDict.before-study
foamDictionary system/controlDict -entry startFrom -set latestTime > log.study-config 2>&1
foamDictionary system/controlDict -entry endTime -set 2000 >> log.study-config 2>&1
cp log.simpleFoam log.before-study
sha256sum system/fvSchemes system/fvSolution constant/MRFProperties > study-settings-sha256.txt
timeout 1200 simpleFoam > log.study 2>&1
cat log.before-study log.study > log.simpleFoam
grep -q '^End' log.study
test -s 2000/U
/usr/bin/python3 "$script_dir/assess-solver-demo.py" "$run_dir" > log.assessment
echo 'STUDY_COMPLETED=yes'
cat solver-assessment.json
