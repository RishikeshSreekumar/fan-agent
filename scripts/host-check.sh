#!/usr/bin/env bash
# Confirms the CFD host toolchain only. Creates no case and runs no solver.
set -uo pipefail
status=0
if source /usr/lib/openfoam/openfoam2412/etc/bashrc 2>/dev/null && test "${WM_PROJECT_VERSION:-}" = v2412; then
    echo "OPENFOAM_VERSION=$WM_PROJECT_VERSION"
    for tool in blockMesh snappyHexMesh gmshToFoam topoSet checkMesh simpleFoam; do
        command -v "$tool" > /dev/null || { echo "MISSING_TOOL=$tool"; status=1; }
    done
else
    echo 'OPENFOAM_VERSION=missing (expected /usr/lib/openfoam/openfoam2412)'; status=1
fi
if gmsh_version=$(/usr/bin/python3 -c 'import gmsh; print(gmsh.__version__)' 2>/dev/null); then
    echo "GMSH_PYTHON=$gmsh_version"
else
    echo 'GMSH_PYTHON=missing (install python3-gmsh)'; status=1
fi
for tool in m4 timeout sha256sum; do
    command -v "$tool" > /dev/null || { echo "MISSING_TOOL=$tool"; status=1; }
done
run_root=${FAN_AGENT_RUN_ROOT:-$HOME}
if test -d "$run_root" && test -w "$run_root"; then echo "RUN_ROOT=$run_root"; else echo "RUN_ROOT=not writable: $run_root"; status=1; fi
echo "CPU_COUNT=$(nproc 2>/dev/null || echo unknown)"
test "$status" = 0 && echo 'HOST_CHECK=passed' || echo 'HOST_CHECK=failed'
exit "$status"
