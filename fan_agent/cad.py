"""STEP conversion adapter. Only generated paths reach the fixed worker."""
import hashlib
import json
from pathlib import Path
import subprocess
import uuid
from .geometry import MAX_BYTES, inspect_stl


def linux_path(path):
    path = Path(path).resolve()
    return "/mnt/" + path.drive[0].lower() + path.as_posix()[2:] if path.drive else str(path)


def convert_step(data, folder):
    if not data or len(data) > MAX_BYTES or not data.lstrip().startswith(b"ISO-10303-21;"):
        raise ValueError("Expected a STEP Part 21 file, at most 32 MiB.")
    identifier = uuid.uuid4().hex
    folder = Path(folder)
    source, target, meta = [folder / (identifier + suffix) for suffix in (".step", ".stl", ".conversion.json")]
    source.write_bytes(data)
    worker = Path(__file__).resolve().parent.parent / "scripts" / "convert-step.py"
    command = ["wsl", "-d", "Ubuntu", "--", "/usr/bin/python3"] if worker.drive else ["/usr/bin/python3"]
    try:
        result = subprocess.run(command + [linux_path(p) for p in (worker, source, target, meta)],
                                capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError("STEP conversion unavailable or timed out. Original CAD retained for review.") from exc
    (folder / (identifier + ".conversion.log")).write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise ValueError("STEP conversion failed. Original CAD and conversion log retained for review.")
    if target.stat().st_size > MAX_BYTES:
        raise ValueError("Converted surface exceeds 32 MiB. Tessellation needs engineering review.")
    report = inspect_stl(target.read_bytes(), "m")
    report.update(id=identifier, source_format="STEP", source_sha256=hashlib.sha256(data).hexdigest(),
                  conversion=json.loads(meta.read_text()))
    return report
