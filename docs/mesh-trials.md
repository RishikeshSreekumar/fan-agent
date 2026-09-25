# Experimental mesh trials

These are synthetic geometry tests, not validated fan simulations. No solver acceptance follows from these measurements.

| WSL case suffix | Cells | Concave cells reported | Small determinant cells reported | Added layer cells | Mean layers | Extended check |
|---|---:|---:|---:|---:|---:|---|
| fan-agent-mesh-AAS5lrVd | 60170 | 2292 | Not reported | Not reported | Not reported | Fail |
| fan-agent-mesh-RTnnHBDn | 82275 | 732 | 14 | 3261 | 1.34 | Fail |
| fan-agent-mesh-EeqhvBDG | 163426 | 18 | Not reported | 0 | Not reported | Fail |
| fan-agent-mesh-gkjzPkUQ | 179380 | 1519 | 18 | 15954 | 1.66 | Fail |
| fan-agent-mesh-BGaGpYp8 | 171200 | 18 | 64 | 7774 | 0.804 | Fail |
| fan-agent-mesh-YnXuQdas | 179419 | 863 | 22 | 15993 | 2.71 | Fail |
| fan-agent-mesh-6xCb4e4u | 180170 | 808 | 20 | 16744 | 2.83 | Fail |
| fan-agent-mesh-qGVvCf6c / snapped | 163426 | 19 | Not reported | Not reported | Not reported | Fail |
| fan-agent-mesh-qGVvCf6c | 180201 | 823 | 24 | 16775 | 2.84 | Fail |
| fan-agent-mesh-zTflybvO / snapped | 163426 | 1503 | Not reported | Not reported | Not reported | Fail |
| fan-agent-mesh-zTflybvO | 174589 | 1808 | 30 | 11163 | 1.54 | Fail |

Missing values mean not reported, not zero. Mean layer count is not the fraction of surface area covered. Full evidence is in each retained WSL case and `mesh-trials.json`.

The synthetic fan surface and generated layers still need geometry fidelity, boundary-layer coverage, y-plus, grid sensitivity and physical validation before design use. The extended quality gate has not been relaxed.