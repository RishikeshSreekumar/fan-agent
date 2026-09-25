> **PAUSED — 2026-09-17:** Preserved ducted-fan research, not the active ceiling-fan validation reference. Historical next steps below are inactive. Do not resume by default; read ../../docs/PROJECT_PLAN.md.

# FAN-01 aerodynamic benchmark specification

Status: **rotor recovered and surface-checked; inner passage reconstructed; full validation domain still incomplete**. No FAN-01 solver run has been launched. Existing synthetic-run results stay separate.

## Selection decision

Choose FAN-01 rather than starting with a pump/mixer: it directly provides axial-fan CAD and experimental pressure/velocity evidence. Its source files are downloadable without contacting authors or a company CFD team. A ducted fan will test relevant methods, not establish ceiling-fan room-performance accuracy by itself.

The initial objective is mean aerodynamic performance near design flow. Acoustic spectra and high-fidelity DES reproduction are excluded from this first pilot. A steady MRF/SST approximation is an engineering proposal to evaluate, not the published method or an assumption of sufficient accuracy.

## Source facts

[Dataset paper](https://arxiv.org/abs/2211.12014), Table 2: nine blades, 495 mm rotor, 248 mm hub, 2.5 mm radial clearance, nominal 1486 RPM and 1.4 m³/s. The 150 Pa value is a design target; measured pressure is about 126.5 Pa. The local measurement document describes a nozzle, diffuser and external motor/torque measurement.

[Published numerical study](https://doi.org/10.1051/aacus/2020021), sections 3–3.2: the authors retained blades and downstream struts, simplified other details and used inlet/outlet chambers with prescribed volume flow, zero outlet pressure and no-slip remaining boundaries. Their subsequent transient DES study is not equivalent to our proposed steady screening model.

## Imported experimental reference

From `characteristic_n1ug.h5`, nearest raw point to nominal design flow (zero-based index 12):

| Original channel | Stored value |
|---|---:|
| volumetric_flow_in_m3_per_s | 1.40324 |
| p_chamber_static_in_Pa | 126.45657916912445 |
| P_shaft_in_Nm | 333.30089514952226 |

**Unit discrepancy:** `P_shaft_in_Nm` appears to contain power in W, despite the suffix. That interpretation yields efficiency 0.5323986, consistent with the published approximately 53%, and torque 2.14185 N·m at 1486 RPM. This is an explicitly recorded inference, not corrected source metadata or a direct torque measurement. Strict torque-validation acceptance stays disabled until resolved from public evidence; preserve raw labels and values. The MAT file uses the same ambiguous name.

Time-averaged LDA data contain normalized radius, axial positions in mm and component means/RMS. Use their recorded coordinate definitions after mapping CAD orientation; do not reuse the synthetic case's Z-axis/1.2 m plane convention. Ensemble-averaged data are archived for later use, not a steady-phase validation target.

## Geometry audit and preparation gate

The IGES header declares MM. Gmsh 4.12.1 imports an extensive assembly (3,864 faces, no solid volumes), with native bounds approximately (-1600,-815,-25) to (980,630.3,2715). These bounds describe the assembly, not rotor dimensions. Do not blindly scale/center the entire assembly as a fan.

Update: the rotor is now a closed solid with a verified STL; the axis/frame and internal passage are documented in [GEOMETRY.md](GEOMETRY.md). Full chamber/obstruction assembly and experimental-coordinate mapping remain pending. The original IGES is unchanged.

## Case and measurement decisions before execution

1. Set the first pressure-comparison point to the actual raw flow 1.40324 m³/s at nominal 1486 RPM. LDA is documented at nominal 1.4 m³/s: record this small mismatch and use a separate nominal-flow profile run if needed.
2. Prescribe flow and predict pressure/load. Prescribed flow is not an independently validated flow prediction. Never impose measured pressure as a boundary condition while claiming to predict it.
3. Map the chamber pressure-ring location and ambient reference from `pressure_sensors.pdf` and `annotations.txt`; establish sign convention. Raw channel values are positive, but suction-side physical gauge pressure may be negative. Do not substitute an arbitrary rotor-plane total-pressure difference.
4. Resolve air density, viscosity, inlet turbulence, rotation sense viewed along a defined axis, CAD-to-LDA origin and experimental uncertainties from public sources. These remain open; any necessary assumption must be labeled and sensitivity-tested, not reported as measured.
5. Define full rotating-load patch set and moment reference. Convert OpenFOAM kinematic pressure to Pa consistently with the declared density. Separate blade/hub aerodynamic loads from shaft/bearing losses if comparison data require it.

The synthetic case's fixed 16 m² plane extraction and force-patch names cannot be reused unchanged here.

## Proposed bounded validation workflow

- Geometry preparation: one audited assembly/transform, no solver launch until the above measurement/domain mapping is reviewable.
- Pilot mesh: extended topology/geometry checks and explicit tip-gap/wall-resolution inspection. Meshing timeout 20 minutes; stop and assess if a pilot exceeds 2 million cells. These are initial resource limits, not resolution requirements or proof of sufficient accuracy.
- One initial design-point solver trial: maximum 30 minutes; capture iteration count, hardware/process count, residual and pressure/torque histories. End with an assessment, not an automatic unbounded continuation. Revisit budget only with measured cost and a documented reason.
- Start-up numerics may be robust first-order; assess the final mean-flow result with a separately documented higher-order discretization. Do not confuse agreement caused by numerical diffusion with mesh independence.
- Three related mesh levels, refining blade/tip-gap/wake regions and reporting actual cell sizes and wall treatment. Compare pressure, torque and velocity profiles after comparable convergence or statistical stationarity. Do not compare an unconverged coarse run against a settled fine run as a grid study.
- Initial internal screening targets: pressure error ≤10%, profile normalized RMS error ≤10%, and medium-to-fine pressure/load changes ≤3%. These are proposed engineering targets, not published experimental uncertainty or a claim of certification. Torque accuracy target remains unset while the source units/loss definitions are unresolved.
- Retain residual checks and require stable engineering histories over both short and longer windows, plus mass conservation. For a transient follow-up, use averages across enough revolutions, confidence/stationarity evidence and time-step sensitivity; do not reuse steady residual acceptance alone.

The initial budget is a feasibility probe. If steady MRF cannot satisfy the agreed checks, diagnose settings/mesh/model adequacy from a controlled comparison. Do not adjust the physical geometry to fit reference data. Validate a transient approach separately if justified.

## Current outcome and next action

Acquisition, reference import, rotor recovery/surface verification and inner-passage reconstruction are complete; no CFD comparison exists. The immediate next action is **complete chamber/obstruction layout and measurement mapping**, then a reviewed fluid-domain/mesh specification. No internal team assistance is required or expected.
