"""Conservative STL inspection. Does not claim CAD/mesh certification."""

import hashlib
import math
import re
import struct
from collections import Counter

MAX_BYTES = 32 * 1024 * 1024
MAX_TRIANGLES = 200_000


def inspect_stl(data: bytes, units: str):
    if units not in {"mm", "m"}:
        raise ValueError("Select STL coordinates in millimetres or metres.")
    if not data or len(data) > MAX_BYTES:
        raise ValueError("STL must be nonempty and at most 32 MiB.")
    count = struct.unpack_from("<I", data, 80)[0] if len(data) >= 84 else 0
    binary = len(data) >= 84 and len(data) == 84 + count * 50
    triangles = []
    scale = 0.001 if units == "mm" else 1.0
    if binary:
        if count > MAX_TRIANGLES:
            raise ValueError("STL exceeds the 200,000-triangle preview limit.")
        for i in range(count):
            numbers = struct.unpack_from("<12fH", data, 84 + 50 * i)
            triangles.append([tuple(v * scale for v in numbers[j:j + 3]) for j in (3, 6, 9)])
    else:
        try:
            content = data.decode("ascii")
        except UnicodeDecodeError as exc:
            raise ValueError("Invalid STL: binary size/header mismatch or non-ASCII text.") from exc
        # Require the facet structure, not merely arbitrary lines containing vertices.
        facets = re.findall(r"\bfacet\s+normal\s+.*?\bendfacet\b", content, re.S | re.I)
        if not content.lstrip().lower().startswith("solid") or not facets or len(facets) > MAX_TRIANGLES:
            raise ValueError("Invalid ASCII STL or too many triangles.")
        for facet in facets:
            vertices = re.findall(r"\bvertex\s+([^\r\n]+)", facet, re.I)
            if len(vertices) != 3:
                raise ValueError("Each STL facet must have exactly three vertices.")
            try:
                triangle = [tuple(float(v) * scale for v in line.split()) for line in vertices]
            except ValueError as exc:
                raise ValueError("Invalid STL coordinate.") from exc
            if any(len(v) != 3 for v in triangle):
                raise ValueError("Each vertex must have three coordinates.")
            triangles.append(triangle)
    if not triangles:
        raise ValueError("STL has no triangles.")
    if any(not math.isfinite(x) or abs(x) > 10000 for tri in triangles for v in tri for x in v):
        raise ValueError("STL coordinates are non-finite or exceed the supported coordinate range.")
    edges = Counter()
    degenerate = 0
    for a, b, c in triangles:
        ab = tuple(b[i] - a[i] for i in range(3))
        ac = tuple(c[i] - a[i] for i in range(3))
        cross = (ab[1]*ac[2]-ab[2]*ac[1], ab[2]*ac[0]-ab[0]*ac[2], ab[0]*ac[1]-ab[1]*ac[0])
        if sum(x*x for x in cross) <= 1e-24:
            degenerate += 1
        for p, q in ((a, b), (b, c), (c, a)):
            edges[tuple(sorted((p, q)))] += 1
    lower = [min(v[i] for t in triangles for v in t) for i in range(3)]
    upper = [max(v[i] for t in triangles for v in t) for i in range(3)]
    open_edges = sum(n == 1 for n in edges.values())
    nonmanifold = sum(n > 2 for n in edges.values())
    stride = max(1, math.ceil(len(triangles) / 1800))
    return {
        "sha256": hashlib.sha256(data).hexdigest(), "units": units,
        "format": "binary STL" if binary else "ASCII STL",
        "triangle_count": len(triangles), "bounds_m": [lower, upper],
        "extent_m": [upper[i]-lower[i] for i in range(3)],
        "boundary_edges": open_edges, "nonmanifold_edges": nonmanifold,
        "degenerate_triangles": degenerate,
        "surface_preflight_pass": not (open_edges or nonmanifold or degenerate),
        "preview_triangles_m": triangles[::stride],
        "limitations": "Exact-edge closure check only. Self-intersections, winding, disconnected solids, blade count and rotor suitability are not certified."
    }
