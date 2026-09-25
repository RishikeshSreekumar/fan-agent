"""Deterministic engineering reductions, ready for a future OpenFOAM adapter.

Input samples are area-weighted cells/faces on a horizontal plane, with velocity
in the stationary Cartesian frame (Z up). No point-sample-to-area assumptions.
"""

import math

from .reference import cmm_to_cfm, shaft_power

METRIC_DEFINITION = {
    "id": "horizontal-plane-screening-v1", "status": "proposed",
    "plane": "Horizontal room cross-section at a recorded height above the floor, below the rotor.",
    "coordinates": "Stationary velocity; Z up; positive downward velocity is -Uz.",
    "downward_flow": "Integral of max(-Uz,0) dA; m3/s multiplied by 60 for CMM.",
    "reverse_flow": "Integral of max(Uz,0) dA; reported separately, not discarded.",
    "net_flow": "Downward flow minus reverse flow. Can be near zero in a closed room.",
    "mean_air_speed": "Area-weighted mean of velocity magnitude on the plane.",
    "coverage": "Fraction of plane area with downward velocity at least the recorded threshold (proposed 0.5 m/s).",
    "torque": "Pressure plus viscous moment projected onto the rotor axis; sign retained.",
    "shaft_power": "Absolute aerodynamic torque times angular speed; not electrical input power.",
    "qualification": "Screening metrics only. Not a certified air-delivery rating or reproduction of the company CMM method."
}


def plane_metrics(samples, coverage_threshold_ms=0.5):
    if not isinstance(coverage_threshold_ms, (int, float)) or isinstance(coverage_threshold_ms, bool) or not math.isfinite(coverage_threshold_ms) or coverage_threshold_ms <= 0:
        raise ValueError("Coverage threshold must be positive and finite.")
    areas, downward, reverse, speeds, covered = [], [], [], [], []
    for sample in samples:
        try:
            area = float(sample["area_m2"])
            velocity = tuple(float(v) for v in sample["velocity_ms"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Each sample requires area_m2 and three velocity components.") from exc
        if len(velocity) != 3 or not math.isfinite(area) or area <= 0 or not all(math.isfinite(v) for v in velocity):
            raise ValueError("Invalid sample area or velocity; partial/invalid samples are not silently dropped.")
        down = -velocity[2]
        areas.append(area)
        downward.append(max(down, 0) * area)
        reverse.append(max(-down, 0) * area)
        speeds.append(math.hypot(*velocity) * area)
        covered.append(area if down >= coverage_threshold_ms else 0)
    if not areas:
        raise ValueError("No plane samples supplied.")
    total_area = math.fsum(areas)
    down = math.fsum(downward) * 60
    back = math.fsum(reverse) * 60
    return {"definition_id": METRIC_DEFINITION["id"], "sample_count": len(areas),
            "plane_area_m2": total_area, "downward_flow_cmm": down,
            "downward_flow_cfm": cmm_to_cfm(down), "reverse_flow_cmm": back,
            "net_downward_flow_cmm": down-back,
            "mean_air_speed_ms": math.fsum(speeds)/total_area,
            "downward_coverage_fraction": math.fsum(covered)/total_area,
            "coverage_threshold_ms": coverage_threshold_ms}


def load_metrics(moment_nm, axis, rpm):
    if len(moment_nm) != 3 or len(axis) != 3 or not all(math.isfinite(v) for v in (*moment_nm, *axis, rpm)) or rpm <= 0:
        raise ValueError("Finite 3D moment/axis and positive RPM required.")
    norm = math.hypot(*axis)
    if norm == 0:
        raise ValueError("Rotation axis cannot be zero.")
    torque = sum(m*a/norm for m,a in zip(moment_nm,axis))
    return {"axis_torque_nm": torque, "aerodynamic_shaft_power_w": shaft_power(abs(torque),rpm),
            "electrical_input_power_w": None}
