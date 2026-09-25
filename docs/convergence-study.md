# Bounded convergence study — 2,000 iterations

## Outcome

**Execution completed; residual targets remain unmet.** Airflow snapshot stability now passes. This improves confidence in the extraction pipeline but does not establish an accepted fan prediction.

| Check | At 1,000 | At 2,000 | Target |
|---|---:|---:|---:|
| Pressure initial residual, worst correction | 0.009942 | 0.004486 | ≤0.001 |
| Maximum velocity initial residual | 0.000911 | 0.000490 | ≤0.0001 |
| k initial residual | 0.000256 | 0.000137 | ≤0.0001 |
| Last-50 torque peak-to-peak / mean | 0.80% | 0.10% | ≤2% |
| Last-two saved downward-flow change | 2.67% | 0.99% | ≤2% |

The final torque is 1.60285 N·m (46.998 W shaft power), versus 1.81420 N·m at iteration 1,000. Consecutive 250-sample mean torques still differ by 2.38%; the new longer-window diagnostic exposes drift hidden by a stable short window. It is not a newly substituted acceptance threshold.

At iteration 2,000 the exact 16 m² cut at 1.2 m yields downward flow 499.14 m³/min and reverse flow 492.21 m³/min. These are full-room recirculation integrals, not certified air-delivery values. The geometry is synthetic.

## Controlled comparison

The continuation uses the same mesh, rotor zone, physics, discretization, linear solvers and relaxation factors. Byte comparisons verified six mesh/zone files and five physics/numerical dictionaries against the 1,000-iteration baseline. Only the run endpoint and restart selection changed. No acceptance target was relaxed.

Source case: `/home/akshay/fan-agent-solver-extended-XLn0e3bm`.
Study case: `/home/akshay/fan-agent-convergence-gBv6lFxm`.
Reproduction script: `scripts/convergence-study.sh`, with a 1,200-second solver timeout. All original files are retained. The script requires the recorded baseline directory.

## Wall resolution and next decision

Fan y-plus ranges from 2.83 to 604.75 (mean 146.91). Near-wall treatment remains unqualified. Residual reduction suggests additional settling, but this single continuation cannot distinguish numerical limitations from persistent flow unsteadiness. No pitch or geometry fault can be inferred from it.

The next qualification work is a controlled numerical-settings comparison and near-wall mesh review, followed by mesh sensitivity once a sufficiently settled solution is available. More iterations alone are not evidence of physical accuracy. Designer execution remains gated.

## Software verification

51 Python tests pass. Added tests reject nonfinite/negative residual corrections, verify final-iteration pressure selection and sampled diagnostic history, and detect long torque drift despite a stable tail. The Engineering run page now includes residual-to-target trends and wall y-plus evidence.
