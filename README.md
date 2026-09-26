# Fan-Agent

AI-assisted ceiling-fan design screening for Havells industrial designers. A local web workbench:
designers supply CAD and a plain-language request; deterministic OpenFOAM workflows compute airflow,
torque and shaft power; AI turns requests into structured studies and explains results. The CFD
solver owns the numbers — AI never invents results or overrides acceptance checks.

## Status

| Area | State |
|---|---|
| Designer UI, case records, STL/STEP preflight | Working (Havells-branded, local server) |
| AI study planner (request → validated study proposal) | Working; OpenAI default, Gemini optional. Proposes cases only |
| CFD host runner (WSL / local Linux / SSH / Docker) | Implemented; verified by mocked tests only |
| Phase 1 screening recipe + three-level mesh study | Implemented; **not yet run on OpenFOAM** |
| Validation against measured fan data (Phase 2) | Waiting for Havells CAD and IS 374 / BEE test data |
| Designer-launched simulations from uploaded CAD | Not implemented (Phase 3) |

No result from this tool is an approved design prediction yet. See the
[project plan and checkpoints](docs/PROJECT_PLAN.md) before starting work.

## Quick start (UI)

Python 3.10+, no third-party packages. From this folder:

```
python -m fan_agent serve          # http://127.0.0.1:8765  (--port to change)
```

On Windows, `./start.ps1` finds a Python runtime; `./start-ai.ps1` also asks for an OpenAI key
(kept in the process only) and model for the AI study planner. The server binds to loopback only —
do not expose it to a network. Case data and uploaded geometry stay in `data/`.

## CFD host

OpenFOAM and Gmsh never run on an unconfigured machine. The UI can run anywhere; fixed worker scripts
run on the CFD host chosen by environment variables:

| Backend | Use |
|---|---|
| `wsl` (default on Windows) | Windows machine with OpenFOAM v2412 + `python3-gmsh` in WSL Ubuntu |
| `ssh` | Remote Linux server (`FAN_AGENT_CFD_HOST`, `FAN_AGENT_CFD_REMOTE_DIR`) |
| `local` | The app runs on the Linux CFD host itself |
| + Docker | `FAN_AGENT_CFD_DOCKER_IMAGE` with `docker/Dockerfile` (local or ssh) |

```
python -m fan_agent host-check     # verifies the toolchain; creates no case
```

Details: [CFD host configuration](docs/cfd-host.md).

## Phase 1: screening recipe and mesh study

Recipe `mrf-sst-v2412-screening-1`: steady MRF, k-ω SST, y+-insensitive wall functions on a
CAD-subtracted tetrahedral mesh, two-stage numerics, monitor-based convergence and a three-level GCI
mesh study on a synthetic fan. On the CFD host:

```
python -m fan_agent recipe-study --levels coarse           # smoke test (~60k cells)
python -m fan_agent recipe-study --levels medium fine      # then the rest
```

Results go to `data/runtime/recipe/` and `docs/recipe-study.json`. Rationale, acceptance rules and
outcomes: [Phase 1 recipe](docs/phase1-recipe.md).

## Tests

```
python -m unittest discover -s tests -v
```

All tests are offline: solver hosts and AI providers are mocked. `tests/browser-study.cjs` is a
Windows-only Playwright UI smoke test.

## Repository layout

| Path | Contents |
|---|---|
| `fan_agent/` | Server, validation, geometry, analytics, AI planner, runner, recipe, convergence, GCI |
| `web/` | HTML/CSS/JS user interface |
| `scripts/` | Fixed host-side workers (Gmsh builders, OpenFOAM run scripts, assessors) |
| `docker/` | CFD worker image (OpenFOAM v2412 + Gmsh) |
| `docs/` | Plan, decisions, evidence and reports |
| `benchmarks/` | Public benchmark audits (FAN-01 ducted fan paused; Dryad room-speed data) |
| `presentations/` | Project update decks |
| `tests/` | Unit and integration tests |

Large binaries (CAD, meshes, PDFs, images, decks) are stored with **Git LFS** — install it
(`git lfs install`) before cloning. The FAN-01 importer's vendored numpy
(`benchmarks/fan01/.reader-deps`) is not committed.

## Documentation

- [Project plan, decisions and checkpoints](docs/PROJECT_PLAN.md)
- [CFD host configuration](docs/cfd-host.md) · [Phase 1 recipe](docs/phase1-recipe.md)
- [AI study planner](docs/ai-study-planner.md)
- Development history: [solver assessment](docs/solver-development.md), [convergence study](docs/convergence-study.md),
  [CAD mesh baseline](docs/cad-mesh-baseline.md), [mesh trials](docs/mesh-trials.md), [qualification](docs/qualification.md)
- Validation sources: [ceiling-fan benchmark review](docs/ceiling-fan-benchmark-review.md), [company reference transcription](docs/reference.md)

## Limits

- The synthetic-fan runs are development assets, not validation. Discretisation checks (Phase 1)
  do not establish physical accuracy; that needs measured fan data (Phase 2).
- Screening metrics (plane flows, coverage, aerodynamic shaft power) are defined in
  `fan_agent/analytics.py`; they are not certified air-delivery ratings or electrical input power.
- Uploading a closed STL does not establish mesh quality, blade orientation or physical validity.
