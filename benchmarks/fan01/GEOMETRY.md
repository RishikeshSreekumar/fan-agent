> **PAUSED — 2026-09-17:** Preserved ducted-fan research, not the active ceiling-fan validation reference. Historical next steps below are inactive. Do not resume by default; read ../../docs/PROJECT_PLAN.md.

# FAN-01 geometry preparation checkpoint

## Completed and checked

- Identified 36 connected surface groups in the source assembly. Group 35 is the nine-blade rotor; groups 17/18 contain the nozzle/straight duct and diffuser, and group 19 contains connecting hardware. Group IDs are tied to the saved Gmsh 4.12.1 import and `surface-components.json`, not universal CAD identifiers.
- Recovered one closed rotor solid by local sewing at 0.001 mm. All 100 faces remain; blades were not parametrically redesigned. Originals are untouched.
- Established a right-handed, metre-based case frame from the CAD axis and coaxial duct sections.
- Generated a 112,728-triangle rotor STL. Its positive signed volume differs from the CAD volume by 0.1891%. This is a tessellation check, not a mesh-sensitivity result.
- OpenFOAM v2412 independently reports closed surface, one connected part, one consistent-normal region and no self-intersection. Minimum surface triangle quality is 0.00117793; do not interpret closure as volume-mesh quality approval.
- Reconstructed the inner passage from CAD-verified profiles and subtracted the actual rotor, giving one connected fluid volume with 105 faces.

## Files

- `rotor-metres.brep`: recovered CAD rotor in the documented case frame.
- `rotor-metres.stl`: verified surface triangulation, coordinates in metres.
- `passage-metres.brep`: clean inner passage without rotor subtraction.
- `rotor-passage-fluid-metres.brep`: partial fluid-domain CAD, **not a complete validation case**.
- `geometry-audit.png`: front and side native-CAD wireframe views for component identification.
- `geometry-checkpoint.json`: provenance, transforms, checks, hashes and failed-attempt record.
- `log.surfaceCheck`, `rotor-preparation.json`, `passage-preparation.json`: detailed verification evidence.

## Coordinate mapping

Let (X,Y,Z) be original CAD coordinates in mm. The fan shaft lies at X = -400 mm, Z = 1515 mm and points downstream along +Y. Define:

```
x = (Y + 460) / 1000
y = (Z - 1515) / 1000
z = (X + 400) / 1000
```

Case x is downstream, y is upward, z completes the right-handed frame. The chosen x=0 is the nozzle-to-straight-duct transition. **This is our engineering datum; it is not yet established as the experimental LDA origin.** Torque-axis location may lie anywhere along this shaft line, with moments projected onto x.

The sampled rotor radius is 0.2474978 m, consistent with the nominal 0.2475 m. The straight passage radius is 0.25 m. The nominal tip gap remains 0.0025 m; finite surface sampling is not a rigorous minimum-distance clearance calculation.

## Passage reconstruction and simplifications

CAD face 1283 samples match a quarter-circle bellmouth profile of radius 50 mm to approximately 1.3e-12 mm numerical error. CAD face 1428 matches a conical diffuser to approximately 1.5e-12 mm at the sampled points. These identify simple analytic shapes; the residuals are numerical checks, not manufacturing tolerances.

The metre profile uses bellmouth inlet x=-0.05/r=0.30, straight start x=0/r=0.25, straight end x=0.196, and diffuser outlet x=0.324/r=0.275. Small assembly gaps/manufacturing openings are closed along the nominal passage, consistent with the simplification intent in the numerical study; this is still an explicit model adaptation.

Passage CAD volume is 0.0769121658407 m³, matching an independent analytic volume calculation. Rotor volume is 0.00117297900687 m³. The Boolean result has volume 0.0757393183385 m³ and passes the configured subtraction tolerance (relative 1e-5).

The source has additional support structures, shaft, motor and external frame. These have not all been included in the fluid CAD. The inlet and outlet chambers are also absent. The passage cannot be used alone while claiming reproduction of the published experimental setup.

## Measurement mapping: established versus unresolved

The supplied pressure diagram and annotations establish chamber wall taps connected to a ring and a differential transducer referenced to outside ambient. They do not give exact tap coordinates. The static pressure on the suction side and the reported positive pressure-rise convention must be mapped explicitly.

HDF5 LDA arrays specify 20 mm (suction) and 90 mm (pressure), with 26 radial samples per plane. The current public diagrams do not unambiguously locate that axial origin relative to the native CAD. Do not silently place them at case x=0.02 and x=0.09, or claim profile validation until resolved. The clockwise rotation description is from the supplied suction-side illustration; confirm its mapping into the case frame before writing MRF omega.

The numerical study's diagrams were inspected locally (`study-page-2.png`, `study-page-3.png`). A thesis link from the university led to a login page and its indexed OAPEN mirror returned HTTP 403. No thesis content was recovered; the failed HTML response is not treated as a PDF or source evidence. Continue with accessible public references without requiring company support.

## Reproduction and next action

Gmsh scripts run with WSL `/usr/bin/python3` and Gmsh 4.12.1. Geometry stages: `audit_components.py`, `map_components.py`, `recover_solids.py 35 0.001`, `prepare_rotor.py --constant-size`, `check_rotor_surface.sh`, `inspect_duct_faces.py`, `build_passage.py`. Auxiliary wireframe scripts produce the component illustration. See script outputs/checkpoint for intermediate files.

Next: complete the validation-domain layout and stationary obstructions using the recovered rotor and audited passage; resolve measurement datum/pressure extraction and fluid properties from public sources; then produce a bounded pilot fluid mesh. No FAN-01 solver run has occurred. The former synthetic-fan results remain separate.

Sources: [FAN-01 data](https://zenodo.org/records/10787093), [numerical study DOI](https://doi.org/10.1051/aacus/2020021). CAD-derived measurements above are our local checks, not new experimental results.
