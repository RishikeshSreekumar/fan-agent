# Fan-Agent — agreed plan and project memory

Last updated: 2026-09-25
Status: deterministic development pipeline and proposal-only Gemini/OpenAI integration implemented; live Gemini smoke verification passed; engineering validation pending.

This document preserves decisions from the user conversation. New explicit user instructions supersede it. Keep it current after substantive work rather than repeatedly restarting planning.

## Current brief — read first

- **Product:** AI-assisted ceiling-fan design screening for Havells industrial designers.
- **Constraint:** no company CFD-team support or internal worked example; source public evidence ourselves.
- **Preserve:** approved Havells UI, STEP/STL pipeline, existing code and simulation evidence. This is not a restart.
- **Actual status:** deterministic foundation exists; synthetic run finished but is not accepted; proposal-only LLM integration passed three live Gemini 2.5 Flash smoke checks; physical validation remains pending.
- **Scope correction:** FAN-01 is a ducted axial-fan reference. Its artifacts are retained, but further preparation and simulation are paused. It does not qualify ceiling-fan performance.
- **Current deliverable completed:** [AI study planner](ai-study-planner.md): Gemini (default) / OpenAI structured extraction, deterministic checks, UI, proposal export and design-form transfer; 65 tests and mocked browser smoke test pass. Live Gemini verification passed for the three recorded generic scenarios.
- **Provider decision (2026-09-25, supersedes Gemini default):** OpenAI is the default provider. Gemini transport remains as an optional fallback only.
- **Execution host (2026-09-25):** CFD (OpenFOAM, Gmsh, meshing, solver) must not run on the user's Mac development machine. Target host still to be chosen; the old WSL host is the only verified runtime.
- **Separation (2026-09-25):** fan-agent stays a separate product from Thermal Design Agent; no shared platform.
- **Validation data (2026-09-25):** user will later supply Havells CAD and IS 374 / BEE air-delivery test data for 2–3 existing fans. This replaces the public-benchmark search as the validation route.
- **Next bounded action:** add persistent study proposals and multi-case saving so a reviewed RPM comparison can be retained as one study. Preserve per-case validation and solver gates. Physical validation remains a separate unresolved engineering task.
- **Stop rule:** no new solver runs, blind iteration increases, unrelated UI work or switch to another fan class during this evidence review. An unresolved source gap must be reported, not filled with invented dimensions.

## 1. Product objective

Build a lightweight, constrained AI-guided OpenFOAM application for industrial ceiling-fan designers at Havells India Ltd who are not CFD specialists. Designers should be able to provide CAD and plain-language requests or parameters, run supported screening studies, and understand airflow, torque, shaft power and velocity distributions through a professional Havells-branded UI.

The business objective is fast, repeatable design screening. Simulation controls must be deterministic and qualified; AI makes the workflow accessible and coordinates approved tools. Neither arbitrary CFD generation nor an indefinitely deterministic-only application fulfills the intended product.

## 2. User constraints — do not lose these

- **No CFD-team support is available.** Do not depend on, request or wait for internal CFD setup files, a complete company worked example, validation help or company-team participation.
- **Find standard public problems ourselves.** The user explicitly authorized independently fetching a documented benchmark with reproducible geometry, operating conditions and reference results.
- Company CAD can come later. It is not a prerequisite for the current public-benchmark milestone.
- The supplied company report is a visual/product reference. Exact reproduction of its metrics is not required. “STL Location,” sampling definitions and its air-delivery calculation are not established.
- Useful, explicitly defined screening metrics are acceptable. Do not equate full-room downward-flow integrals with certified air delivery or company CMM values.
- Preserve the approved UI and Havells branding. Support STEP as a designer-facing CAD format as well as STL; STEP conversion and meshing remain separate operations.
- The user is frustrated by endless “next milestone” loops. Work toward concrete outcomes with bounded experiments and explicit decisions, not repeated blind iteration increases or unrelated feature expansion.
- A 100% successful/accurate simulation guarantee for arbitrary CAD is not credible. The intended reliability is a qualified operating range, bounded recovery and clear unsupported/failed outcomes.

## 3. What is actually implemented

Application: `fan-agent/`, a local Python HTTP server with HTML/CSS/JavaScript UI. It is not Streamlit. The localhost link opens the application while its server is running; it is not a hosted public service.

Implemented development assets:

- Havells-branded reference dashboard, design input form and saved case records.
- STEP/STP conversion through Gmsh in WSL; STL inspection, unit handling and geometry preview.
- OpenCFD OpenFOAM v2412 runtime in WSL Ubuntu, plus fixed development execution scripts.
- CAD-subtracted tetrahedral synthetic-fan mesh with extended checkMesh verification.
- Fixed simpleFoam / MRF / k-omega SST development case, with bounded execution.
- Exact horizontal tetrahedron-plane intersection and area-weighted cell-velocity integration; downward/reverse flow, torque and shaft-power extraction.
- Engineering run page with convergence checks, residual trends, y-plus evidence and longer-window torque drift.
- Last verified software checkpoint: 51 Python tests passed, JavaScript/data-rendering checks passed and the live API returned the 2,000-iteration assessment.

Not implemented or established:

- A validated fan-performance recipe or qualified design envelope.
- Designer-launched simulation execution from uploaded CAD.
- Live verification of the implemented OpenAI proposal client; multi-turn conversation and the upstream multi-agent workflow remain unimplemented.
- A qualified transient/AMI workflow, mesh independence or experimental accuracy.
- Any equivalence between synthetic-case outputs and the supplied company report.

The older Foundation 10 recipe displayed in parts of the app is an unqualified proposal, not the actual v2412 development runtime. Resolve that distinction when implementing the qualified recipe.

## 4. Simulation checkpoint — retain this work

The synthetic three-blade case is a development/regression asset, not a validation benchmark. It contains 168,591 cells in a 4 × 4 × 3 m room, runs at 280 RPM, and uses steady MRF with SST and first-order bounded upwind schemes. It has near-wall refinement but no qualified prism-layer treatment.

The completed continuation ended normally at **2,000 iterations**. That run is finished, not still running in the background. This records the simulation's status, not the lifetime of the local UI server.

- Short-window torque variation: 0.10%, passed its provisional 2% check.
- Last-two-snapshot airflow change: 0.99%, passed its provisional 2% check.
- Pressure initial residual: 0.004486, above the 0.001 target. Velocity and k targets also remain unmet.
- Consecutive 250-sample torque means differ by 2.38%; a stable short tail does not erase longer drift.
- Fan y-plus: approximately 2.83–604.75; wall treatment remains unqualified.
- Overall result: **not converged; performance not accepted**.

Full fields/logs are retained in WSL:

- Initial 300 iterations: `/home/akshay/fan-agent-solver-uZX4M3Fw`
- 1,000-iteration baseline: `/home/akshay/fan-agent-solver-extended-XLn0e3bm`
- 2,000-iteration continuation: `/home/akshay/fan-agent-convergence-gBv6lFxm`
- Passing source mesh: `/home/akshay/fan-agent-cadmesh-6zIy8SyE`

Evidence: [latest assessment](solver-assessment.json), [controlled comparison](convergence-study.md), [comparison data](convergence-study.json), [mesh baseline](cad-mesh-baseline.md). Keep archived trials and their limitations. Do not delete or relabel them as validated when moving to public benchmarks.

## 5. Immediate priority: public ceiling-fan validation evidence

The current shortlist and source limitations are in [the benchmark review](ceiling-fan-benchmark-review.md). No fully reproducible ceiling-fan benchmark has yet been qualified. FAN-01 is paused, not the selected product-validation case.

Selection requires a ceiling fan with matched blade geometry, operating conditions, room/test boundaries and measured reference quantities. Confirm geometry access or sufficient reconstruction dimensions, measurement definitions and uncertainty, licensing, and tractable computational cost. A public velocity dataset without the matching blades is not sufficient for blade-design validation.

Before simulation, record a reproducible specification, source provenance, unresolved assumptions, comparison metrics, mesh-sensitivity approach and finite run budget. Solver completion alone is not success. Require numerical checks, convergence or statistical stability, mesh sensitivity and quantitative experimental comparison. Qualify only the quantities and conditions actually tested; room-speed agreement does not establish torque accuracy.

## 6. Foam-Agent and AI integration plan

### Honest current status

Foam-Agent has informed the architecture and the upstream code/paper were reviewed. Its agents have **not** been integrated into the application. Existing case preparation, execution and analytics are deterministic scripts. A separate OpenAI study-proposal client and UI are now implemented, with mocked API tests and browser verification; a real model call is pending local credentials.

### Planned responsibility split

| Function | LLM/AI responsibility | Deterministic responsibility |
|---|---|---|
| Understand a request | Interpret intent and ask for genuinely missing inputs | Validate required fields, units and supported ranges |
| Prepare a study | Produce a structured study specification | Generate cases from qualified templates |
| Coordinate work | Invoke approved tools and explain progress | Execute CAD, mesh, solver and assessment steps with limits |
| Explain problems | Summarize evidence, distinguish hypotheses and uncertainty | Recognize known failures and enforce approved recovery policies |
| Compare studies | Explain trade-offs and answer questions grounded in results | Calculate metrics, comparisons and acceptance status |

Example intended request: “Compare this fan at 250 and 300 RPM and explain whether the airflow gain justifies the extra shaft power.” The AI should convert it into a validated study, coordinate supported runs and explain computed results. The CFD solver supplies physics; the AI must not invent outputs. This milestone currently proposes cases only, without coordinating runs.

Selectively adapt useful Foam-Agent orchestration, tool interfaces and review patterns after inspecting their implementation. Replace open-ended case writing and autonomous code repair with the fixed generator and approved recovery choices. Reuse upstream code where it helps; do not force a wholesale integration merely to claim reuse.

### First AI milestone

Plain-language request → structured study specification → deterministic validation → proposed cases and a clear explanation of missing/unsupported inputs.

This can be implemented alongside benchmark work once that work is underway, but must not displace the immediate benchmark priority. Actual run execution remains gated by engineering qualification. Model/provider selection and credential configuration have not been decided; do not assume credentials exist or send company CAD to an external model without an appropriate explicit scope.

AI failure explanations must cite available case/log evidence. Never infer a specific geometry fix such as “reduce pitch by 5 degrees” solely from a solver crash. AI cannot override acceptance checks, silently edit physics or convert provisional results into approved predictions.

## 7. Eventual designer workflow

- Accept a screening result only when the study is within a tested range and all qualified checks pass.
- Attempt only bounded, preapproved recovery actions with recorded changes and runtime limits.
- Report unsupported inputs or unresolved failure clearly and retain diagnostic artifacts. Human specialist review may be an eventual operational option, but **our present development and validation must not depend on unavailable company CFD support**.
- Qualify representative parameter variations before broadening the supported envelope.

## 8. Checkpoint and next-session checklist

Checkpoint, 2026-09-17: corrected ceiling-fan scope, paused FAN-01 and completed an initial three-source review. No application code or simulation results changed; no new simulation was launched. The Chen study explicitly uses different digital fans from its measured Haiku fan. The completed Adeeb audit records a no-go: baseline geometry/test boundaries remain unverified and maximum-based measurements are not clearly compatible with mean-flow predictions. Figure inspection was blocked by screenshot failures and PDF download HTTP 403; do not claim the figure was checked. Update 2026-09-18: Dryad metadata and manifest acquired; exactly two CSV files, no CAD/README, CC0 metadata. CSV download routes failed (401/403); data were not acquired or imported. Test conditions and speed averaging verified against the institutional paper. See benchmarks/ceiling-fan-dryad/README.md. No matched blade-validation benchmark is selected.

Next session:

1. Read AGENTS.md and this current brief; state objective, bounded deliverable and relevance.
2. Read ai-study-planner.md. The first AI milestone is implemented; verify it with real local API configuration rather than rebuilding it. Geometry qualification remains unresolved. Do not repeat closed searches or resume FAN-01.
3. Record a go/no-go decision with remaining evidence gaps. Do not request company CFD support.
4. Update this checkpoint and the review with what actually changed and one concrete next action.

Latest checkpoint, 2026-09-18: recovered both author CSVs, retained licenses and commit/hash provenance, implemented and ran the reference importer successfully. Original and newline-normalized hashes differ from Dryad; no equivalence claimed. Manufacturer/BIM checks did not establish matching 60-inch H-Series blade geometry. Close this search route as room-speed evidence; advance the independently authorized AI study-proposal milestone. No solver run or engineering qualification claim.

### Preserved historical work — superseded direction

On 2026-09-16 FAN-01 sources were acquired and checksum-verified, characteristic/LDA data imported, a closed rotor recovered and its surface checked, and an inner passage reconstructed. Chambers, stationary obstructions, measurement coordinates and shaft-channel units remained unresolved. No FAN-01 solver run was performed. These artifacts remain under benchmarks/fan01/ for reference; their historical next steps are inactive following the user's ceiling-fan scope correction.

Checkpoint 2026-09-21: implemented fan_agent/study.py, local AI routes, planner UI and start-ai.ps1. Shared input sanity bounds with existing validation. 62 Python tests and JavaScript syntax pass; headless Edge validates the UI using a mocked proposal. User approved OpenAI API with locally configured credentials. No key/model is configured in the development process and no live API call was made. See ai-study-planner.md for exact activation steps and limitations.

Provider correction: Gemini native generateContent transport, Gemini-default startup helper and provider-aware disclosure added. 65 tests pass. Live Gemini request remains pending local GEMINI_API_KEY and model configuration; no credentials were requested in chat.

Startup correction: user selected gemini-2.5-flash, but launch failed with empty PSScriptRoot before the server started. start-ai.ps1 now resolves/validates its launcher before requesting credentials and supports AppDirectory or the current project folder for pasted execution. Use the saved script by absolute path; do not paste its contents. Live Gemini verification remains pending.

Live Gemini checkpoint: three generic requests reached gemini-2.5-flash through the configured app. Missing-input and unsupported-work checks passed; complete comparison failed because the model labeled Compare unsupported despite extracting values correctly. Evidence: ai-live-checks/20260921T184435239329Z.json. Prompt corrected to explicitly permit RPM comparisons; server restart and live recheck pending. No solver or CAD submission occurred. New scripts/check-live-ai.py performs bounded checks and records evidence without accessing credentials.

Completed live AI milestone: after restarting with the corrected comparison instructions, all three live Gemini 2.5 Flash checks passed. Evidence: [ai-live-checks/20260921T184638173355Z.json](ai-live-checks/20260921T184638173355Z.json). Six model calls total across initial and corrected checks, no solver calls. 65 local tests still pass. This is smoke-test evidence for three scenarios, not a broad language evaluation or physics validation. Initial failure is retained.

Checkpoint 2026-09-25: code review on a new Mac workstation (65 tests pass; no OpenFOAM/Gmsh/WSL present, and CFD must not run there). Decisions above recorded. Changes: OpenAI made default provider; displayed recipe relabelled from Foundation 10 to the v2412 runtime actually used; git repository initialised with binaries in Git LFS; vendored numpy under benchmarks/fan01/.reader-deps ignored, not deleted. Revised direction: wall-function mesh (y+ 30–150) instead of resolved prism layers; convergence judged on time-averaged airflow/torque; validation against Havells fans in the IS 374 test room once data arrive. Execution host: old Windows/WSL machine now; user evaluating a remote Linux server or Docker host. Next: build a host-agnostic runner replacing the hard-coded wsl calls in cad.py and runtime.py.
