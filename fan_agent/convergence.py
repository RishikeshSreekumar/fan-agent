"""Steady-MRF convergence from monitored quantities, not residual magnitudes.

A steady room-fan run keeps a residual floor because the jet below the fan is unsteady.
Acceptance therefore uses consecutive window means of torque and jet flow, plus a check
that residuals are not growing. Values are reported as the last-window mean with its
half peak-to-peak range, so remaining oscillation is visible.
"""
import math
import re

from .recipe import CONVERGENCE


def _rows(texts):
    """Merge restart files: {iteration: numeric row}; later files replace repeated iterations."""
    merged = {}
    for text in texts:
        for line in text.splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            values = [float(v) for v in line.replace("(", " ").replace(")", " ").split()]
            if not values or not all(math.isfinite(v) for v in values):
                raise ValueError("Nonfinite or empty monitor record.")
            merged[int(round(values[0]))] = values[1:]
    return merged


def moment_series(texts, axis_index=2):
    """forces moment.dat: time, total (x y z), pressure (x y z), viscous (x y z)."""
    rows = _rows(texts)
    if any(len(v) != 9 for v in rows.values()):
        raise ValueError("Unexpected moment.dat layout; expected total, pressure and viscous vectors.")
    return [(i, rows[i][axis_index]) for i in sorted(rows)]


def surface_series(texts):
    """surfaceFieldValue.dat with one scalar result (areaNormalIntegrate)."""
    rows = _rows(texts)
    if any(len(v) != 1 for v in rows.values()):
        raise ValueError("Unexpected surfaceFieldValue layout; expected one scalar column.")
    return [(i, rows[i][0]) for i in sorted(rows)]


def residual_series(log):
    """Worst initial residual per field per iteration from a simpleFoam log."""
    history = []
    parts = re.split(r"^Time = ([0-9]+)\s*$", log, flags=re.MULTILINE)
    for step, block in zip(parts[1::2], parts[2::2]):
        found = {}
        for field, value in re.findall(r"Solving for (\w+), Initial residual = ([^,\s]+)", block):
            value = float(value)
            if not math.isfinite(value) or value < 0:
                raise ValueError("Nonfinite or negative residual.")
            found[field] = max(found.get(field, 0.0), value)
        if found:
            history.append((int(step), found))
    return history


def window_stability(series, start, window, limit):
    """Compare means of the last two full windows after `start` (exclusive)."""
    values = [v for i, v in series if i > start]
    result = {"samples": len(values), "window": window, "limit": limit, "stable": False}
    if len(values) < 2 * window:
        result["reason"] = f"Needs {2 * window} samples after iteration {start}; has {len(values)}."
        return result
    last, previous = values[-window:], values[-2 * window:-window]
    mean, before = math.fsum(last) / window, math.fsum(previous) / window
    change = abs(mean - before) / max(abs(mean), 1e-12)
    result.update(mean=mean, previous_mean=before, relative_change=change,
                  half_range=(max(last) - min(last)) / 2,
                  relative_half_range=(max(last) - min(last)) / 2 / max(abs(mean), 1e-12),
                  stable=change <= limit)
    return result


def residual_trend(history, start, window, growth_limit):
    """Diverging if any field's last-window mean residual exceeds growth_limit x the previous window."""
    rows = [r for i, r in history if i > start]
    if len(rows) < 2 * window:
        return {"diverging": None, "reason": "Too few iterations for a residual trend."}
    ratios = {}
    for field in rows[-1]:
        last = [r[field] for r in rows[-window:] if field in r]
        previous = [r[field] for r in rows[-2 * window:-window] if field in r]
        if last and previous:
            ratios[field] = (math.fsum(last) / len(last)) / max(math.fsum(previous) / len(previous), 1e-30)
    return {"diverging": any(v > growth_limit for v in ratios.values()), "growth_ratios": ratios,
            "growth_limit": growth_limit, "final_initial_residuals": rows[-1]}


def assess(torque, jet_flow, history, settings=CONVERGENCE):
    """torque: [(iteration, N m)]; jet_flow: [(iteration, m3/s, signed, downward negative)]."""
    start, window = settings["stage1_iterations"], settings["window"]
    torque_check = window_stability(torque, start, window, settings["mean_change_limit"])
    flow_check = window_stability(jet_flow, start, window, settings["mean_change_limit"])
    trend = residual_trend(history, start, window, settings["residual_growth_limit"])
    if trend["diverging"]:
        status = "diverging"
    elif torque_check["stable"] and flow_check["stable"] and trend["diverging"] is False:
        status = "stable"
    else:
        status = "not_converged"
    return {"status": status, "torque": torque_check, "jet_flow": flow_check, "residuals": trend,
            "last_iteration": max((i for i, _ in torque), default=None), "settings": dict(settings),
            "note": "Stability of monitored means within a fixed iteration budget; not mesh independence or accuracy."}
