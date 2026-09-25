"""Validated designer inputs and deterministic qualification gates."""

import math

from .recipe import RECIPE  # single source for the screening recipe

INPUT_RANGES = {"rpm": (1, 3000), "diameter_mm": (100, 10000),
              "room_x_m": (0.5, 100), "room_y_m": (0.5, 100), "room_z_m": (0.5, 30),
              "rotor_height_m": (0.1, 29.9), "sampling_height_m": (0.01, 29.8)}


def validate_case(raw):
    if not isinstance(raw, dict):
        raise ValueError("Case input must be an object.")
    allowed = {"name", "rpm", "diameter_mm", "room_x_m", "room_y_m", "room_z_m", "rotor_height_m", "sampling_height_m", "direction", "geometry_id", "measurement_notes"}
    extras = set(raw) - allowed
    if extras:
        raise ValueError("Unsupported inputs: " + ", ".join(sorted(extras)))
    result = {}
    name = raw.get("name", "")
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 100:
        raise ValueError("Design name must contain 1–100 characters.")
    result["name"] = name.strip()
    # These are input sanity limits, not a validated operating envelope.
    for field, (low, high) in INPUT_RANGES.items():
        value = raw.get(field)
        if isinstance(value, bool):
            raise ValueError(f"{field} must be a number.")
        try:
            value = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Enter a value for {field}.") from exc
        if not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f"{field} must be between {low:g} and {high:g}.")
        result[field] = value
    if result["rotor_height_m"] >= result["room_z_m"]:
        raise ValueError("Rotor height must be below the ceiling and above the floor.")
    if result["sampling_height_m"] >= result["rotor_height_m"]:
        raise ValueError("Sampling plane must be below the rotor and above the floor.")
    diameter = result["diameter_mm"] / 1000
    if diameter >= min(result["room_x_m"], result["room_y_m"]):
        raise ValueError("Fan diameter must fit inside the room footprint.")
    if raw.get("direction") not in {"cw", "ccw"}:
        raise ValueError("Choose a rotation direction viewed from above, looking down the shaft.")
    result["direction"] = raw["direction"]
    for field, limit in (("geometry_id", 100), ("measurement_notes", 2000)):
        value = raw.get(field, "")
        if not isinstance(value, str) or len(value) > limit:
            raise ValueError(f"Invalid {field}.")
        result[field] = value
    result["angular_speed_rad_s"] = result["rpm"] * 2 * math.pi / 60
    result["tip_speed_ms"] = result["angular_speed_rad_s"] * diameter / 2
    result["coordinate_convention"] = "Z up; floor Z=0; room centred on X/Y; rotation axis +Z; rotor centre at (0,0,rotor_height_m). CAD alignment still requires review."
    return result


def preflight(parameters, geometry=None):
    geometry_ok = bool(geometry and geometry.get("surface_preflight_pass"))
    checks = [
        {"id": "inputs", "label": "Parameter sanity", "status": "pass", "detail": "Dimensions and units are consistent. Operating envelope is not yet qualified."},
        {"id": "geometry", "label": "STL surface inspection", "status": "pass" if geometry_ok else "blocked",
         "detail": "Basic surface checks passed; orientation and rotor suitability need CFD review." if geometry_ok else "Upload a closed, nondegenerate STL."},
        {"id": "alignment", "label": "Geometry placement", "status": "blocked", "detail": "Confirm CAD axis, blade span, clearances, orientation and rotating-zone enclosure."},
        {"id": "recipe", "label": "CFD template qualification", "status": "blocked", "detail": "Candidate recipe " + RECIPE["id"] + " awaits the three-level mesh study and comparison with measured fan data."},
        {"id": "measurement", "label": "Screening metric qualification", "status": "blocked", "detail": "Plane height is recorded. Qualify downward/reverse flow, area-weighted speed and torque extraction. Reproducing the company CMM method is not required."},
        {"id": "runtime", "label": "Solver runtime", "status": "blocked", "detail": "OpenFOAM v2412 ran only on a developer host; designer runs have no verified execution host."}
    ]
    return {"status": "blocked", "can_run": False, "checks": checks,
            "summary": "Case saved for qualification. No meshing or solver job has been launched."}


def diagnose_log(text):
    """Evidence-based failure categories; never guesses a blade design change."""
    lowered = text.lower()
    if "negative volume" in lowered or "negative cell volume" in lowered:
        return {"category": "mesh_quality", "action": "Inspect the flagged cells and geometry; do not use this mesh for solving.", "design_change": None}
    if "courant" in lowered and ("fatal" in lowered or "floating point" in lowered):
        return {"category": "numerical_instability", "action": "Review the Courant history, mesh and time-step controls. The log alone does not establish a blade-geometry cause.", "design_change": None}
    if "fatal" in lowered or "error:" in lowered:
        return {"category": "solver_failure", "action": "CFD review required; retain the original case and error evidence.", "design_change": None}
    return {"category": "unclassified", "action": "Insufficient evidence to assess execution or convergence.", "design_change": None}
