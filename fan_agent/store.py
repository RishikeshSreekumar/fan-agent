"""Immutable local case records. Client paths are never used as storage paths."""

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .domain import RECIPE, preflight, validate_case
from .geometry import inspect_stl
from .analytics import METRIC_DEFINITION


class Store:
    def __init__(self, root):
        self.root = Path(root)
        for part in ("cases", "geometry"):
            (self.root / part).mkdir(parents=True, exist_ok=True)

    def read(self, part, identifier):
        if part not in {"cases", "geometry"} or not re.fullmatch(r"[a-f0-9]{32}", identifier):
            raise ValueError("Invalid record identifier.")
        path = self.root / part / (identifier + ".json")
        if not path.is_file():
            raise ValueError("Record not found.")
        return json.loads(path.read_text(encoding="utf-8"))

    def _save(self, part, record):
        path = self.root / part / (record["id"] + ".json")
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(record, indent=2, allow_nan=False), encoding="utf-8")
        temporary.replace(path)

    def upload(self, data, units, source_format="stl"):
        if source_format == "step":
            from .cad import convert_step
            report = convert_step(data, self.root / "geometry")
            self._save("geometry", report)
            return report
        if source_format != "stl":
            raise ValueError("Unsupported geometry format.")
        report = inspect_stl(data, units)
        report["id"] = uuid.uuid4().hex
        (self.root / "geometry" / (report["id"] + ".stl")).write_bytes(data)
        self._save("geometry", report)
        return report

    def create(self, raw):
        parameters = validate_case(raw)
        geometry = self.read("geometry", parameters["geometry_id"]) if parameters["geometry_id"] else None
        record = {
            "schema_version": 1, "id": uuid.uuid4().hex,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "parameters": parameters, "recipe": dict(RECIPE),
            "metric_definition": dict(METRIC_DEFINITION),
            "geometry": {k: v for k, v in geometry.items() if k != "preview_triangles_m"} if geometry else None,
            "preflight": preflight(parameters, geometry),
            "execution": {"status": "not_started", "results": None},
            "reference_id": "company-inveno-ul-itr4"
        }
        self._save("cases", record)
        return record

    def list_cases(self):
        records = [json.loads(p.read_text(encoding="utf-8")) for p in (self.root / "cases").glob("*.json")]
        return sorted(records, key=lambda r: r["created_at"], reverse=True)
