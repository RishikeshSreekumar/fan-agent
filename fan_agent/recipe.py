"""Phase 1 screening recipe: one deterministic source for physics, numerics, mesh levels and
convergence rules. Candidate only until the mesh study and experimental comparison pass.

Key choice: y+-insensitive wall treatment (Spalding nut + blended omega wall functions) on the
CAD-subtracted tetrahedral mesh, instead of resolved prism layers that failed quality checks.
"""
import math
from pathlib import Path

RECIPE = {
    "id": "mrf-sst-v2412-screening-1", "status": "candidate",
    "platform": "OpenCFD OpenFOAM v2412", "solver": "simpleFoam",
    "rotation": "MRF (steady frozen rotor)", "turbulence": "kOmegaSST",
    "wall_treatment": "nutUSpaldingWallFunction + omegaWallFunction (tanh blending); y+-insensitive, no prism layers",
    "mesh": "Gmsh CAD-subtracted tetrahedra, distance-graded near the fan; three systematically scaled levels",
    "numerics": "Stage 1: bounded first-order upwind; stage 2: bounded linearUpwind for U, upwind for k/omega",
    "description": "Candidate screening recipe. Not approved for design decisions until the mesh study "
                   "and comparison with measured fan data pass.",
}

# Every mesh length is scaled by one factor per level, so refinement is systematic (Celik et al. 2008).
# Medium reproduces the 168,591-cell baseline sizes. Ratio 1.4 per level gives about 2.7x cells.
REFINEMENT_RATIO = 1.4
BASE_SIZES_M = {"near_fan": .012, "bulk": .20, "minimum": .006, "grade_start": .025, "grade_end": .45}
MESH_LEVELS = {"coarse": REFINEMENT_RATIO, "medium": 1.0, "fine": 1 / REFINEMENT_RATIO}

CONVERGENCE = {
    "stage1_iterations": 250,        # first-order start-up, never assessed
    "max_iterations": 3000,          # hard budget; no automatic extension
    "window": 250,                   # iterations per averaging window
    "mean_change_limit": .01,        # consecutive window means of torque and jet flow
    "residual_growth_limit": 1.10,   # last/previous window mean residual; above this is diverging
    "write_interval": 250,
    "gci_limit": .05,                # fine-grid GCI for torque and jet flow
}

# Synthetic development fan (same as the retained baseline): three flat pitched blades and hub.
SYNTHETIC_FAN = {"center_m": (0.0, 0.0, 2.4), "blade_inner_m": .07, "blade_length_m": .5,
                 "blade_chord_m": .13, "blade_thickness_m": .04, "pitch_deg": 12, "blades": 3,
                 "hub_radius_m": .11, "hub_height_m": .08, "room_m": (4.0, 4.0, 3.0), "plane_height_m": 1.2}


def mesh_sizes(level):
    if level not in MESH_LEVELS:
        raise ValueError("Mesh level must be coarse, medium or fine.")
    return {k: v * MESH_LEVELS[level] for k, v in BASE_SIZES_M.items()}


def omega_rad_s(rpm, direction):
    """Angular speed about +Z. Clockwise viewed from above is negative."""
    if not isinstance(rpm, (int, float)) or isinstance(rpm, bool) or not math.isfinite(rpm) or not 1 <= rpm <= 3000:
        raise ValueError("RPM must be between 1 and 3000.")
    if direction not in ("cw", "ccw"):
        raise ValueError("Direction must be cw or ccw viewed from above.")
    return (-1 if direction == "cw" else 1) * rpm * 2 * math.pi / 60


def rotor_zone(fan=SYNTHETIC_FAN):
    """MRF cylinder: 1.2x tip radius, 0.2 m above and below the rotor centre."""
    tip = fan["blade_inner_m"] + fan["blade_length_m"]
    cx, cy, cz = fan["center_m"]
    return {"p1": (cx, cy, cz - .2), "p2": (cx, cy, cz + .2), "radius": round(1.2 * tip, 4), "tip_radius": tip}


def _vec(v):
    return "(" + " ".join(f"{x:.10g}" for x in v) + ")"


def _header(name, kind="dictionary"):
    return f"FoamFile {{ version 2.0; format ascii; class {kind}; object {name}; }}\n"


WALLS = ("fan", "floor", "ceiling", "roomWalls")
FIELDS = (  # name, dimensions, internal value, wall condition
    ("U", "0 1 -1 0 0 0 0", "(0 0 0)", "noSlip;"),
    ("p", "0 2 -2 0 0 0 0", "0", "zeroGradient;"),
    ("k", "0 2 -2 0 0 0 0", "0.01", "kqRWallFunction; value uniform 0.01;"),
    ("omega", "0 0 -1 0 0 0 0", "10", "omegaWallFunction; blending tanh; value uniform 10;"),
    ("nut", "0 2 -1 0 0 0 0", "0", "nutUSpaldingWallFunction; value uniform 0;"),
)

SCHEMES = {
    1: "div(phi,U) bounded Gauss upwind;",
    2: "div(phi,U) bounded Gauss linearUpwind grad(U);",
}
RELAXATION = {1: "fields {p 0.2;} equations {U 0.4; k 0.4; omega 0.4;}",
              2: "fields {p 0.2;} equations {U 0.5; k 0.5; omega 0.5;}"}


def case_files(rpm, direction, fan=SYNTHETIC_FAN, procs=1):
    """All solver dictionaries as {relative path: text}. Mesh files come from the host builder."""
    omega = omega_rad_s(rpm, direction)
    zone = rotor_zone(fan)
    cx, cy, cz = fan["center_m"]
    height = fan["plane_height_m"]
    if not 0 < height < cz:
        raise ValueError("Sampling plane must lie between the floor and the rotor.")
    tip = zone["tip_radius"]
    c = CONVERGENCE
    files = {
        "constant/transportProperties": _header("transportProperties") + "transportModel Newtonian; nu [0 2 -1 0 0 0 0] 1.5e-5;\n",
        "constant/turbulenceProperties": _header("turbulenceProperties") + "simulationType RAS; RAS { RASModel kOmegaSST; turbulence on; printCoeffs on; }\n",
        "constant/MRFProperties": _header("MRFProperties") + (
            f"rotorMRF {{ cellZone rotor; active yes; nonRotatingPatches (floor ceiling roomWalls); "
            f"origin {_vec(fan['center_m'])}; axis (0 0 1); omega {omega:.10g}; }}\n"),
        "system/topoSetDict": _header("topoSetDict") + (
            "actions (\n{name rotorCells; type cellSet; action new; source cylinderToCell;\n"
            f" sourceInfo {{p1 {_vec(zone['p1'])}; p2 {_vec(zone['p2'])}; radius {zone['radius']:.10g};}}}}\n"
            "{name rotor; type cellZoneSet; action new; source setToCellZone; sourceInfo {set rotorCells;}}\n);\n"),
        "system/decomposeParDict": _header("decomposeParDict") + f"numberOfSubdomains {int(procs)}; method scotch;\n",
        "system/controlDict": _header("controlDict") + f"""
application simpleFoam; startFrom latestTime; startTime 0; stopAt endTime;
endTime {c['stage1_iterations']}; deltaT 1; writeControl timeStep; writeInterval {c['write_interval']};
purgeWrite 2; writeFormat ascii; writePrecision 10; runTimeModifiable false;
functions {{
 fanLoads {{ type forces; libs (forces); patches (fan); rho rhoInf; rhoInf 1.2;
  CofR {_vec(fan['center_m'])}; log true; writeControl timeStep; writeInterval 1; }}
 jetFlow {{ type surfaceFieldValue; libs (fieldFunctionObjects); regionType sampledSurface; name jetPlane;
  sampledSurfaceDict {{ type plane; planeType pointAndNormal;
   pointAndNormalDict {{ point {_vec((cx, cy, height))}; normal (0 0 1); }}
   bounds ({_vec((cx - tip, cy - tip, height - .01))} {_vec((cx + tip, cy + tip, height + .01))});
   interpolate false; }}
  operation areaNormalIntegrate; fields (U); writeFields false; log true;
  writeControl timeStep; writeInterval 1; }}
 wallYPlus {{ type yPlus; libs (fieldFunctionObjects); writeControl writeTime; }}
}}
""",
    }
    for name, dims, value, wall in FIELDS:
        boundary = " ".join(f"{w} {{ type {wall} }}" for w in WALLS)
        kind = "volVectorField" if name == "U" else "volScalarField"
        files[f"0/{name}"] = _header(name, kind) + f"dimensions [{dims}]; internalField uniform {value}; boundaryField {{ {boundary} }}\n"
    for stage in (1, 2):
        suffix = "" if stage == 1 else ".stage2"
        files["system/fvSchemes" + suffix] = _header("fvSchemes") + f"""
ddtSchemes {{ default steadyState; }}
gradSchemes {{ default cellLimited Gauss linear 1; }}
divSchemes {{ default none; {SCHEMES[stage]} div(phi,k) bounded Gauss upwind; div(phi,omega) bounded Gauss upwind;
 div((nuEff*dev2(T(grad(U))))) Gauss linear; }}
laplacianSchemes {{ default Gauss linear limited 0.5; }}
interpolationSchemes {{ default linear; }}
snGradSchemes {{ default limited 0.5; }}
wallDist {{ method meshWave; }}
"""
        files["system/fvSolution" + suffix] = _header("fvSolution") + f"""
solvers {{
 p {{solver GAMG; tolerance 1e-8; relTol 0.05; smoother GaussSeidel;}}
 "(U|k|omega)" {{solver smoothSolver; smoother symGaussSeidel; tolerance 1e-8; relTol 0.1;}}
}}
SIMPLE {{ nNonOrthogonalCorrectors 1; consistent no; pRefCell 0; pRefValue 0; }}
relaxationFactors {{ {RELAXATION[stage]} }}
"""
    return files


def write_case(root, rpm, direction, fan=SYNTHETIC_FAN, procs=1):
    root = Path(root)
    for relative, text in case_files(rpm, direction, fan, procs).items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
