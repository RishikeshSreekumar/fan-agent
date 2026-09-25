# Qualification plan

**2026-09-16 update:** The alternative CAD-derived tetrahedral mesh passes the full extended checkMesh without relaxed limits. See `cad-mesh-baseline.md`. The rejected prism-layer trials below remain useful historical evidence; the mesh baseline now allows controlled solver development to resume. Wall treatment and physical validation are still pending.

## Milestone 1 — implemented foundation

Local interface; reference dashboard; validated case inputs; STL inspection and preview; immutable saved specifications; explicit readiness gates; no unrestricted LLM generation.

## Milestone 2 — first reproducible solver case

Required inputs: real fan CAD/STL with coordinate system and units; room dimensions and boundaries; mounting height and rotation direction. The user has agreed to build the foundation before supplying geometry and to use useful, independently defined screening metrics instead of strictly reproducing company metrics. A parametric CAD family is a separate capability.

1. Runtime check completed: OpenCFD OpenFOAM v2412 under WSL Ubuntu generated and checked the bundled mixerVessel2D mesh and completed 500 simpleFoam iterations. Reproduce with `python -m fan_agent runtime-smoke`; reports are in `data/runtime/`, and full cases are retained in WSL. This 2D k-epsilon MRF tutorial is not the intended 3D fan/SST template. Adapt the unqualified Foundation 10 draft to v2412, record the binary/package identity, and qualify the fan template before enabling designer execution.
2. CFD engineer establishes one reference MRF/simpleFoam/kOmegaSST case, including air properties, boundaries, rotor zone, blade wall velocity, wall treatment and mesh controls.
3. Implement deterministic case generation from the qualified template. Hash template and geometry, store full effective settings. Reject inputs outside the approved envelope. No shell interpolation of user text.
4. Run surface/volume mesh quality checks before solver startup. Geometry closure is not a volume mesh acceptance criterion.
5. Implement process exit/timeout checks, solver completion and finite fields, mass balance, residuals and monitored torque/flow stability. Exact tolerances must be set by CFD review. A zero exit code is insufficient.
6. Extract torque about the correct axis with incompressible density handling; compute aerodynamic shaft power. Use the proposed horizontal-plane screening definition in `fan_agent/analytics.py`: area-weighted downward/reverse flow, mean speed and downward coverage, at the recorded height. Save fixed-coordinate slices and machine-readable results. These are not certified fan ratings.
7. Validate against suitable measured data and mesh/domain sensitivity. Agree acceptable error and design-ranking accuracy before enabling designer results. The company image is a visual reference; metric equivalence is not assumed or required.

## Failure policy

### Mesh development evidence (2026-09-15)

Seven retained trials are compared in `mesh-trials.md`. Interior smoothing and increased refinement reduced the original 2,292 concave cells to 18 in a no-layer trial, but boundary-layer insertion introduces additional quality defects. The current blade-only fixed-thickness trial requests three layers and achieves a mean 2.83, with 16,744 layer cells; checkMesh still flags 808 concave cells and 20 small-determinant cells. Neither trial is approved. No solver run is authorized by the application on these meshes.

OpenFOAM's mesher success message is not equivalent to passing extended checkMesh. The report parser preserves that distinction and rejects missing evidence. Counts, requested layer number, achieved mean and thickness fraction are separate quantities; none establishes area coverage or y-plus validity. The layer strategy follows the installed v2412 configuration; see the [vendor snapping documentation](https://doc.openfoam.com/2306/tools/pre-processing/mesh/generation/snappyhexmesh/snapping/) for internal smoothing and feature alignment.

Never infer a pitch/chord change solely from numerical errors. Preserve failure logs and original input. Bounded numerical retries must come from an approved policy and be recorded. No numerical retry changes designer geometry or operating point. Cases failing acceptance cannot display accepted performance cards.

## Milestone 3 — designer screening release

Qualified geometry family and RPM envelope; run queue/cancellation; selected comparisons; fixed PDF/report exports; optional natural-language-to-schema input requiring explicit resolved parameters; confidential local/team deployment with authentication if network exposed.

## Milestone 4 — separate transient workflow

Qualify a sliding-mesh AMI template, angular/time-step controls, transient averaging, mesh/time-step sensitivity and vortex-study objectives. Keep this an engineer-facing workflow until independently qualified.
