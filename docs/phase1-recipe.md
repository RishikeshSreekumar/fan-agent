# Phase 1: screening recipe and mesh study

Status: **implemented, not yet run.** Recipe `mrf-sst-v2412-screening-1` is a candidate. It becomes
qualified only after (1) the three-level mesh study below passes and (2) Phase 2 comparison with
measured Havells fan data (IS 374 / BEE air delivery) passes.

## What changed from the development run

| Issue in the 2,000-iteration run | Phase 1 decision |
|---|---|
| Prism layers failed quality checks; y+ 2.8–605 on tetrahedra | Keep the passing Gmsh tetrahedral mesh. Use `nutUSpaldingWallFunction` + `omegaWallFunction` with `blending tanh`, which is valid across viscous, buffer and log regions. No layer targets. |
| Pressure residual floor (4.5e-3) never met 1e-3 | Residual magnitude is not an acceptance test for a steady room-fan jet. Residuals must only not grow (last/previous window mean ≤ 1.10). |
| Short-window torque stable, 250-iteration means drifted 2.4% | Accept only when consecutive 250-iteration means of torque **and** jet flow change ≤ 1%. Report last-window mean ± half range. |
| First-order numerics throughout | 250 first-order iterations, then bounded `linearUpwind` for U (k, ω stay upwind). |
| Whole-room downward flow ≈ reverse flow (closed room) | New per-iteration monitor: net downward flow through the fan-footprint square at 1.2 m (`surfaceFieldValue`, `areaNormalIntegrate`). The whole-plane metrics are still reported at the last write. |
| No mesh sensitivity | Three levels, every mesh length scaled by 1.4 (≈2.7× cells per level). GCI after Celik et al. (2008); pass when fine-grid GCI ≤ 5% for torque and jet flow. |

Fixed budget: 3,000 iterations per level. No automatic extension; a level that is not stable
by then is reported as `not_converged` and blocks the GCI.

## Running it (on the CFD host only)

On the Windows/WSL machine, from `fan-agent/`:

```
$env:FAN_AGENT_CFD_PROCS = "8"          # MPI ranks; default 1
python -m fan_agent host-check
python -m fan_agent recipe-study --levels coarse          # ~60k cells; run first as a smoke test
python -m fan_agent recipe-study --levels medium fine     # can be run later/overnight
```

Each level prints its cell count and convergence status. Results:

- `data/runtime/recipe/<level>.json` — latest successful result per level; `<level>-<timestamp>.json` — full run record.
- `docs/recipe-study.json` — combined status and GCI once fine, medium and coarse all exist.
- Case folders (fields, logs, `recipe-assessment.json`) stay on the host under `FAN_AGENT_RUN_ROOT` or `$HOME` as `fan-agent-recipe-<level>-*`.

`FAN_AGENT_SOLVER_TIMEOUT` (seconds, default 14400) limits each solver stage.

Outcomes of `docs/recipe-study.json`:

| status | meaning / next action |
|---|---|
| `mesh_study_passed` | Medium or fine level usable for screening; see `gci_medium` to choose. Proceed to Phase 2. |
| `mesh_study_failed` | GCI > 5% or oscillatory/divergent. Review; one bounded change (e.g. finer near-fan size) and rerun. |
| `blocked` | A level failed checkMesh or did not stabilise within 3,000 iterations. Inspect that level's logs. |
| `incomplete` | Some levels not yet run. |

## Not established by Phase 1

Physical accuracy, suitability of the synthetic fan for any real product, and the operating envelope.
The study quantifies discretisation uncertainty only.

## Unverified on a real host

Written without access to OpenFOAM. First run may need small syntax fixes in: `omegaWallFunction`
`blending` keyword, the `sampledSurface` plane `bounds` entry, and the `surfaceFieldValue.dat` column
layout expected by `fan_agent/convergence.py`. Run the coarse level first.
