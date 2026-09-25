"""Explicit developer runtime check; never runs a designer case."""

import json
from pathlib import Path
import subprocess
from datetime import datetime, timezone


def mesh_diagnostics_from_output(output):
    """Failure-log tails can repeat earlier stage records; select the final mesh only."""
    for line in output.splitlines():
        if line.startswith('MESH_DIAGNOSTICS_JSON='):
            value = json.loads(line.split('=', 1)[1])
            if value.get('stage') == 'final':
                return value
    return None


def smoke(mesh=False, cad=False):
    root = Path(__file__).resolve().parent.parent
    script = root / "scripts" / ("cad-mesh-demo.sh" if cad else "mesh-demo.sh" if mesh else "runtime-smoke.sh")
    if script.drive:
        linux_script = "/mnt/" + script.drive[0].lower() + script.as_posix()[2:]
        command = ["wsl", "-d", "Ubuntu", "--", "bash", linux_script]
    else:
        command = ["bash", str(script)]
    report = {"started_at": datetime.now(timezone.utc).isoformat(),
              "purpose": "Synthetic fan mesh development, not solver qualification" if mesh or cad else "Vendor MRF tutorial runtime check, not fan validation",
              "accepted_fan_results": False, "command": command}
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=1200 if mesh or cad else 600)
        report.update(exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr,
                      status="passed" if result.returncode == 0 else "failed")
        diagnostics = mesh_diagnostics_from_output(result.stdout)
        if diagnostics is not None:
            report['mesh_diagnostics'] = diagnostics
    except (OSError, subprocess.TimeoutExpired) as exc:
        report.update(status="failed", error=str(exc))
    output = root / "data" / "runtime"
    output.mkdir(parents=True, exist_ok=True)
    target = output / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json")
    target.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Runtime report: {target}")
    return 0 if report["status"] == "passed" else 1
