# Fan-Agent

**AI study planner:** Request-to-proposal UI with OpenAI (default; Gemini optional) is implemented. Run `./start-ai.ps1` to enter your OpenAI key locally and select a model, then open **AI study planner**. [Setup, tests and limitations](docs/ai-study-planner.md). Three live Gemini 2.5 Flash smoke checks passed; solver execution stays gated.

**Project continuity:** Read [the agreed plan and current checkpoint](docs/PROJECT_PLAN.md) before starting work. It records the no-CFD-team-support constraint, public-benchmark priority, preserved simulation evidence and planned AI integration.

**Validation direction:** Public ceiling-fan evidence review is active; see [source shortlist and gaps](docs/ceiling-fan-benchmark-review.md). FAN-01 ducted-fan work is paused and preserved. No ceiling-fan performance recipe is validated yet.

**Synthetic development milestone:** The synthetic 3D MRF/SST simulation completed 2,000 iterations. Exact plane integration and torque extraction are connected to the Engineering run page. Short-window torque and airflow stability passed; residual targets remain unmet. Longer-window torque drift remains visible. See [controlled comparison](docs/convergence-study.md). See [solver assessment](docs/solver-development.md).

**Mesh milestone:** a CAD-derived tetrahedral baseline now passes OpenFOAM's complete extended mesh checks: 168,591 cells with a populated rotor zone. Run `python -m fan_agent cad-mesh-demo`. See [verified baseline](docs/cad-mesh-baseline.md). This uses near-wall refinement, not prism layers, and is not yet a validated flow simulation.

Local, constrained ceiling-fan CFD workbench. This is the first implementation milestone: a usable designer interface, saved case specifications, STL preflight, reference analytics, and explicit qualification gates. A development OpenFOAM simulation has run; physical validation and designer-launched simulations remain gated.

## Start

Python 3.10+; no third-party dependencies:

```powershell
python -m fan_agent serve
```

Run from this `fan-agent` directory, then open http://127.0.0.1:8765. Override the port with `--port 8766`. Run tests with `python -m unittest discover -s tests -v`.

On this Windows workspace you can also run `./start.ps1` in PowerShell. It checks a local virtual environment, Python on PATH, then the available Codex Python runtime. Keep the terminal open while using the application; Ctrl+C stops it.

This local, single-user server binds to loopback only. Geometry and case data stay in `data/`. Do not expose it to a network. No API keys, model downloads, or upstream Foam-Agent imports are required.

## What works

- STEP/STP import through Gmsh 4.12.1 in WSL Ubuntu (`python3-gmsh` package). STEP-declared units are normalized to metres; the STL unit selector applies only to STL. Original CAD, converted surface, source hash, conversion settings and logs are retained locally. Conversion has a 180-second timeout and requires solid CAD. Draft surface sizing is span/500 to span/60 with curvature sizing; it requires refinement checks for real blade edges. This does not generate an OpenFOAM volume mesh or repair CAD automatically.

- Company-reference dashboard: transcribed velocity samples, CMM/CFM conversion, torque, calculated shaft power, provenance and unknown measurement definitions.
- Case form with explicit dimensions, SI conversion, installation position, RPM, direction, and screening-plane height.
- ASCII/binary STL upload, file hash, bounds, degenerate triangles, exact shared-edge closure checks, and a geometry preview. Coordinates are converted from declared units to metres. Supported upload: 32 MiB / 200,000 triangles.
- Persistent case manifests and a deterministic preflight report. Download manifests or the reference data as JSON.
- Tested area-weighted screening reductions for downward/reverse flow, mean speed, coverage, torque and shaft power. OpenFOAM field extraction works for the fixed tetrahedral development case. Sampling height is recorded per case; company metric equivalence is not required.
- Separate input validity, geometry readiness, template qualification, runtime verification, and measurement readiness. No fake simulation progress or generated CFD contours.

## What remains gated

### Experimental 3D meshing workflow

**2026-09-16:** Added independent before/after-layer snapshots and tested an alternative shrinker, boundary-face preservation and isolated small-edge repair. None cleared the quality gate. See [stage review](docs/mesh-stage-review.md) for results and an identified/corrected stage-reporting issue.

`python -m fan_agent mesh-demo` builds a fixed synthetic three-blade rotor at 2.4 m in a 4 × 4 × 3 m room. It generates the surface with Gmsh, runs surface checks, blockMesh, feature extraction, snappyHexMesh, cylinder-based rotor cell-zone selection and extended checkMesh. All files and logs are retained under a unique `~/fan-agent-mesh-*` WSL directory, with a JSON execution report in `data/runtime/`. The `.foam` marker can be opened in ParaView.

This developer workflow is not connected to uploaded CAD or the designer run button. It requests three layers on the broad blade surfaces, excluding edge and hub patches. The current experimental settings use a 1 mm first layer with 1.2 expansion and a finer surface tessellation. They are not a qualified wall treatment. There are no solver fields or performance outputs. Failed extended quality checks keep its report failed; mesh creation alone does not constitute acceptance. A new development gate also rejects absent layer cells or an empty rotor zone.

The latest trial produced 180,170 cells, including 16,744 added layer cells, with a mean 2.83 layers on the selected patch. It still failed with 808 concave cells and 20 cells with small determinants. A different trial reduced concavity to 18 but suppressed all layers; it is also rejected. See [trial comparison](docs/mesh-trials.md), [machine-readable evidence](docs/mesh-trials.json) and [mesh cross-section](docs/mesh-section.svg). All original WSL trials and their logs remain intact. The UI's simulation gate remains blocked.

Diagnostics include the actual flagged cell locations when there are at most 100, a local face-intersection SVG slice, layer counts, and independent checkMesh results. Source hashes and the manifest record each trial's settings. Next work is local surface/layer-transition correction and independent CFD review before CAD placement and parameterized case generation are connected to designer execution.

### Verified solver runtime

OpenCFD OpenFOAM **v2412** is installed in WSL Ubuntu at `/usr/lib/openfoam/openfoam2412`. The isolated vendor `simpleFoam/mixerVessel2D` MRF tutorial passed mesh generation, `checkMesh`, and 500 solver iterations on this machine. This is a 2D k-epsilon tutorial, not validation of the proposed 3D ceiling-fan/SST recipe. The Foundation 10 recipe displayed in the UI remains an unqualified proposal; version-specific fan templates must be implemented for v2412 before enabling runs.

From this directory, run `python -m fan_agent runtime-smoke` to repeat the test. Each invocation creates a separate `~/fan-agent-smoke-*` directory in WSL, preserving tutorial source hashes, mesh, fields and logs. A timestamped report is saved under `data/runtime/`. Commands are fixed and have time limits; designer input is not passed to the shell. The check requires WSL Ubuntu with the above installation. It is a developer command, not a simulation launch action in the UI.

Completion and mesh checks demonstrate runtime operation only. They do not establish mesh independence, physical accuracy, or fan performance acceptance.

The MRF + simpleFoam + k-omega SST recipe is a **proposal**, not a gold-standard case. CFD review must qualify wall treatment, mesh controls, domain boundaries, operating envelope, quality thresholds, and convergence/metric stability criteria. Merely uploading a closed STL does not establish mesh quality, absence of self-intersections, correct blade orientation, or physical validity.

There is deliberately no simulation launch endpoint yet. Drafts cannot become accepted results. AMI, parametric CAD modification, natural-language interpretation, actual mesh generation, solver execution and force/flow extraction are later milestones.

The upstream source at `../Foam-Agent-main` remains separate. Its general LLM file generator and automatic rewrites are not used. Its data files are LFS pointers in this checkout, but the new application does not depend on them.

See `docs/qualification.md` for the next engineering milestone and `docs/reference.md` for transcription details.
