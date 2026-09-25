"""Prepare author-version ceiling-fan data; never assert Dryad equivalence."""
import csv
import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def read_matrix(path, columns):
    with path.open(newline="") as f:
        rows = list(csv.reader(f, delimiter=";"))
    if len(rows) != 16 or any(len(row) != columns for row in rows):
        raise ValueError("Unexpected source dimensions")
    matrix = [[float(v) for v in row] for row in rows[1:]]
    if any(not math.isfinite(v) or v < 0 for row in matrix for v in row):
        raise ValueError("Invalid speed")
    return rows[0], matrix

def main():
    provenance = json.loads((ROOT / "author-source-provenance.json").read_text())
    for item in provenance:
        data = (ROOT / "author-source" / item["file"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise ValueError("Author source checksum changed")
    headers, values = read_matrix(ROOT / "author-source/Single_Fan.csv", 384)
    two_headers, two = read_matrix(ROOT / "author-source/Two_Fan.csv", 1344)
    records = []
    for block in range(32):
        label = headers[12 * block].strip()
        match = re.fullmatch(r"Speed (\d) - (\d+\.\d+) m", label)
        if not match:
            raise ValueError("Unrecognized block: " + label)
        level, height = int(match[1]), float(match[2])
        if level != 7 - block // 4 or height != (1.7, 1.1, 0.6, 0.1)[block % 4]:
            raise ValueError("Unexpected block ordering")
        for row in range(15):
            for col in range(12):
                # Author server.R lines 2-3 and plot transforms reverse rows.
                records.append((level, round(.385 + .35 * col, 3),
                                round(.235 + .35 * (14-row), 3), height,
                                values[row][12 * block + col]))
    for block in range(112):
        expected = f"Case {block // 4 + 1} - {(1.7, 1.1, 0.6, 0.1)[block % 4]} m"
        if two_headers[block * 12].strip() != expected:
            raise ValueError("Unexpected two-fan case ordering")
    if len(set(r[:4] for r in records)) != 5760:
        raise ValueError("Duplicate or missing single-fan locations")
    with (ROOT / "single-fan-points.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["speed_level", "x_m", "y_m", "height_m", "mean_speed_m_s"])
        writer.writerows(records)
    summaries = []
    for level in range(8):
        for height in (.1, .6, 1.1, 1.7):
            speeds = [r[4] for r in records if r[0] == level and r[3] == height]
            summaries.append(dict(speed_level=level, height_m=height, points=len(speeds),
                                  minimum=min(speeds), maximum=max(speeds),
                                  arithmetic_sample_mean=sum(speeds)/len(speeds)))
    report = dict(source="author GitHub version, not checksum-identical to Dryad",
                  single_fan_points=len(records), two_fan_values=sum(map(len,two)),
                  geometry_available=False, blade_validation_ready=False,
                  quantity="time-averaged omnidirectional speed; not axial velocity",
                  coordinate_source="single-fan server.R lines 2-3,17; cm converted to m, rows reversed",
                  summaries=summaries)
    (ROOT / "data-checks.json").write_text(json.dumps(report, indent=2)+"\n")
    print("Verified author hashes, schemas, block labels, finite nonnegative values and unique coordinates.")
    print("Prepared 5760 single-fan points; checked 20160 two-fan values. No geometry qualification.")

if __name__ == "__main__":
    main()
