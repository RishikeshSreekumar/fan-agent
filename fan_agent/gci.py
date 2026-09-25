"""Three-grid discretisation uncertainty (Celik et al. 2008, J. Fluids Eng. 130, 078001)."""
import math


def three_grid(cells, values, volume_m3, limit=.05):
    """cells/values ordered fine, medium, coarse. Returns order, extrapolation and GCI.

    GCI is only reported for monotonic convergence. Oscillatory results report the
    half-range of the three solutions instead; divergent results report nothing.
    """
    if len(cells) != 3 or len(values) != 3:
        raise ValueError("Provide fine, medium and coarse results.")
    if not all(isinstance(n, int) and n > 0 for n in cells) or not cells[0] > cells[1] > cells[2]:
        raise ValueError("Cell counts must be positive and decrease from fine to coarse.")
    if not all(math.isfinite(v) for v in (*values, volume_m3)) or volume_m3 <= 0:
        raise ValueError("Values and volume must be finite.")
    h1, h2, h3 = [(volume_m3 / n) ** (1 / 3) for n in cells]
    r21, r32 = h2 / h1, h3 / h2
    phi1, phi2, phi3 = values
    e21, e32 = phi2 - phi1, phi3 - phi2
    result = {"cells": list(cells), "values": list(values), "h_m": [h1, h2, h3],
              "r21": r21, "r32": r32, "limit": limit, "accepted": False}
    if r21 < 1.3 or r32 < 1.3:
        result["warning"] = "Refinement ratio below 1.3; Celik et al. recommend at least 1.3."
    if e21 == 0 and e32 == 0:
        result.update(convergence="exact", order=None, extrapolated=phi1, gci_fine=0.0, gci_medium=0.0, accepted=True)
        return result
    if e32 == 0:
        result.update(convergence="undetermined", reason="Coarse and medium results are identical.")
        return result
    ratio = e21 / e32
    if ratio < 0:
        spread = (max(values) - min(values)) / 2
        result.update(convergence="oscillatory", convergence_ratio=ratio, half_range=spread,
                      relative_half_range=spread / max(abs(phi1), 1e-12))
        return result
    if ratio >= 1:
        result.update(convergence="divergent", convergence_ratio=ratio)
        return result
    s = 1.0  # monotonic: sign(e32/e21) is positive
    p = 1.0
    for _ in range(100):
        q = math.log((r21 ** p - s) / (r32 ** p - s))
        updated = abs(math.log(abs(e32 / e21)) + q) / math.log(r21)
        if abs(updated - p) < 1e-10:
            p = updated
            break
        p = updated
    extrapolated = (r21 ** p * phi1 - phi2) / (r21 ** p - 1)
    ea21 = abs((phi1 - phi2) / phi1) if phi1 else math.inf
    ea32 = abs((phi2 - phi3) / phi2) if phi2 else math.inf
    gci_fine = 1.25 * ea21 / (r21 ** p - 1)
    gci_medium = 1.25 * ea32 / (r32 ** p - 1)
    result.update(convergence="monotonic", convergence_ratio=ratio, order=p, extrapolated=extrapolated,
                  approximate_error_fine=ea21, extrapolated_error_fine=abs((extrapolated - phi1) / extrapolated) if extrapolated else math.inf,
                  gci_fine=gci_fine, gci_medium=gci_medium, accepted=gci_fine <= limit)
    if not .5 <= p <= 4:
        result["warning"] = f"Apparent order {p:.2f} is outside 0.5-4; treat the GCI with caution."
    return result
