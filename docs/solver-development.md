> Latest: the bounded continuation reached 2,000 iterations. See [comparison and current status](convergence-study.md). The 1,000-iteration results below document the initial baseline; `solver-assessment.json` now contains the latest run.

# Development solver assessment

The synthetic three-blade case completed 1,000 simpleFoam iterations using OpenCFD OpenFOAM v2412, steady MRF at 280 RPM, and k-omega SST. The CAD tetrahedral mesh contains 168,591 cells and passes extended checkMesh.

## Acceptance

**Not converged; not approved for design.** Torque peak-to-peak variation over the last 50 iterations is 0.80% (target ≤2%). Downward flow changes 2.67% between iterations 900 and 1000 (target ≤2%). Velocity, pressure and k residuals exceed the provisional limits. The pressure residual is 0.009942, taking the worst initial residual across final-iteration corrections.

## Measurements

The exact horizontal cut at 1.2 m covers 16 m². Each intersected tetrahedron contributes its cut area and stationary-frame cell velocity. Downward and reverse flow are integrated separately. This is piecewise-constant velocity integration, not conservative face-flux integration or a certified air-delivery measurement.

Final provisional values: downward flow 490.65 m³/min, reverse flow 484.63 m³/min, torque 1.8142 N·m and shaft power 53.20 W. They describe synthetic geometry, not the company fan. First-order numerics, broad wall y-plus, absent mesh-sensitivity studies and absent experimental validation limit interpretation.

## Evidence and reproduction

Full fields and logs: `/home/akshay/fan-agent-solver-extended-XLn0e3bm` in WSL. Machine-readable assessment: `solver-assessment.json` alongside this document. The Engineering run page reads this saved assessment.

`scripts/solver-demo.sh` runs the fixed 300-iteration case using the retained passing mesh; `scripts/continue-solver-demo.sh` copies the retained initial case and extends it to 1000. These development scripts depend on the recorded baseline directories. `scripts/assess-solver-demo.py CASE_DIRECTORY` regenerates metrics from saved fields without another solver run.

Next engineering work is to resolve convergence and qualify near-wall resolution and mesh sensitivity before connecting uploaded company CAD to designer execution. Completing a run alone never unlocks performance acceptance.
