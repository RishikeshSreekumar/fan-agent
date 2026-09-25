# Mesh stage review — 2026-09-16

The mesh-quality problem is not resolved. No fan solver run was started and no mesh acceptance thresholds were relaxed.

## Findings

- The displacement-solver trial `qGVvCf6c` had 19 concave cells before layers and 823 afterward, with 24 small-determinant cells. The achieved mean was 2.84 layers. Replacing the shrinker did not solve the problem.
- Preserving boundary faces (`zTflybvO`) worsened pre-layer concavity to 1,503 cells and final concavity to 1,808, with 30 small-determinant cells. This is not the default.
- A separate 0.1 mm, quality-controlled edge-collapse trial (`fan-agent-repair-CBf6OXf9`) retained 808 concave cells, 20 small-determinant cells and two low-quality face-tetrahedron decompositions. It failed three checks. Repair is not part of the production path, and post-repair layer coverage and surface fidelity are unverified.

## Implemented safeguards

The meshing script now saves a complete snapped mesh under `stages/snapped`, checks it independently, and then adds layers. Final diagnostics contain both stage measurements. Flagged-cell sets must match the logged count; stale sets are rejected. Runtime parsing accepts only an explicitly final diagnostic, so a repeated earlier stage in a failure-log tail cannot overwrite the final result.

The two initial staged runtime JSON reports (`20260916T001709302087Z` and `20260916T001906723163Z`) were captured before the stage-selection bug was fixed: their nested `mesh_diagnostics` can describe the snapped stage instead of the final mesh. Their raw stdout is retained. Use the regenerated `mesh-trials.json` and original checkMesh logs for the authoritative comparison.

## Reproduction

The default remains the prior medial-axis method. For controlled comparison only, set `FAN_AGENT_MESH_PROFILE` to `motion` or `motion-unmerged` before running `python -m fan_agent mesh-demo`. These profiles are rejected experiments, not approved options for designers. Every run uses a new WSL directory.

## Engineering hold point

The next substantive work is a local mesh-topology correction or an independently qualified alternative meshing method, followed by surface-fidelity and layer-coverage assessment. Further solver/UI integration must not label these meshes ready. A CFD review of the retained mesh and flagged sets is appropriate before more parameter tuning or any change to acceptance criteria.
