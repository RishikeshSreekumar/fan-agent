# Passing CAD-derived mesh baseline

## Result — 2026-09-16

The synthetic three-blade fan in the 4 × 4 × 3 m room now has a reproducible mesh that passes OpenFOAM v2412 `checkMesh -constant -allTopology -allGeometry`. The original prism-layer trials remain rejected and archived.

| Measurement | Verified result |
|---|---:|
| Total cells | 168,591 |
| Rotor-zone cells | 111,065 |
| Maximum non-orthogonality | 67.214604° |
| Maximum skewness | 1.0338469 |
| Minimum cell volume | 1.8525067e-8 m³ |
| Minimum cell determinant | 0.0018868265 |
| Concavity / determinant / face-tet checks | Passed |
| Extended checkMesh result | Mesh OK |

The successful retained case is `/home/akshay/fan-agent-cadmesh-6zIy8SyE` in WSL Ubuntu. Open `mesh.foam` in ParaView to inspect it. The local runtime report is `data/runtime/20260916T003459786324Z.json`; full logs, physical patches, CAD BREP, mesh and manifest are retained in the WSL directory.

## What changed

Gmsh subtracts the same synthetic fan CAD from the room and creates a tetrahedral fluid mesh with near-wall refinement. This avoids the failed snapping and prism-layer extrusion path. The initial tetrahedral mesh passed the shape checks but failed the finite-volume determinant check at 306 boundary tetrahedra. Subdividing tetrahedra that touch multiple boundary faces adds internal neighbours while preserving every exterior triangle. No CAD boundary vertex is moved. Volume conservation and boundary preservation have automated tests.

The imported `fan`, `floor`, `ceiling` and `roomWalls` patches are checked and set to wall type. The rotor zone is populated. The same extended checkMesh limits are used; none was weakened.

## Reproduce

From the `fan-agent` directory:

```powershell
python -m fan_agent cad-mesh-demo
```

Requires the installed WSL Ubuntu / OpenFOAM v2412 / Gmsh 4.12.1 environment. Every invocation uses a new directory and preserves evidence. `mesh-demo` remains the separate, failed prism-layer experimental workflow.

## Scope of the pass

This is a **mesh baseline**, not a validated ceiling-fan simulation or a general STEP-to-solver service. It uses tetrahedral near-wall refinement with **no prism layers**. The previous layer-dependent development gate is not marked passed. Physical performance remains unvalidated, and the designer simulation button remains disabled.

The next step is a controlled MRF/SST solver case with explicit wall treatment, measured y-plus, convergence and torque/flow monitoring. Grid sensitivity and comparison to trusted results are required before design decisions. This baseline removes the immediate volume-mesh blocker; it does not establish aerodynamic accuracy.
