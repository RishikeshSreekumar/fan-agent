"""Explicit developer runtime check; never runs a designer case."""

import json
from pathlib import Path
import subprocess
from datetime import datetime, timezone

from .runner import HostError, Runner


def mesh_diagnostics_from_output(output):
    """Failure-log tails can repeat earlier stage records; select the final mesh only."""
    for line in output.splitlines():
        if line.startswith('MESH_DIAGNOSTICS_JSON='):
            value = json.loads(line.split('=', 1)[1])
            if value.get('stage') == 'final':
                return value
    return None


def smoke(mesh=False, cad=False, host=False):
    root = Path(__file__).resolve().parent.parent
    script = "host-check.sh" if host else "cad-mesh-demo.sh" if cad else "mesh-demo.sh" if mesh else "runtime-smoke.sh"
    runner = Runner()
    purpose = ("CFD host toolchain check; no case or solver run" if host else
               "Synthetic fan mesh development, not solver qualification" if mesh or cad else
               "Vendor MRF tutorial runtime check, not fan validation")
    report = {"started_at": datetime.now(timezone.utc).isoformat(), "purpose": purpose,
              "accepted_fan_results": False, "script": script, "host": runner.describe()}
    try:
        result = runner.run_script(script, timeout=120 if host else 1200 if mesh or cad else 600)
        report.update(exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr,
                      status="passed" if result.returncode == 0 else "failed")
        diagnostics = mesh_diagnostics_from_output(result.stdout)
        if diagnostics is not None:
            report['mesh_diagnostics'] = diagnostics
    except (OSError, subprocess.TimeoutExpired, HostError) as exc:
        report.update(status="failed", error=str(exc))
    output = root / "data" / "runtime"
    output.mkdir(parents=True, exist_ok=True)
    target = output / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json")
    target.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Runtime report: {target}")
    return 0 if report["status"] == "passed" else 1


def _result_from_output(output):
    for line in output.splitlines():
        if line.startswith("RECIPE_RESULT_JSON="):
            return json.loads(line.split("=", 1)[1])
    return None


def combine_levels(results):
    """GCI for torque and jet flow from fine/medium/coarse results of one recipe and operating point."""
    from .gci import three_grid
    from .recipe import CONVERGENCE
    ordered = [results.get(level) for level in ("fine", "medium", "coarse")]
    if any(r is None for r in ordered):
        return {"status": "incomplete", "missing_levels": [l for l, r in zip(("fine", "medium", "coarse"), ordered) if r is None]}
    keys = {(r["recipe"], r["rpm"], r["direction"]) for r in ordered}
    if len(keys) != 1:
        return {"status": "inconsistent", "reason": "Levels differ in recipe, RPM or direction."}
    unstable = [r["level"] for r in ordered if r["convergence"]["status"] != "stable" or not r["mesh_check_passed"]]
    if unstable:
        return {"status": "blocked", "reason": "Every level must pass checkMesh and the convergence rule first.", "levels": unstable}
    volume = ordered[0]["fluid_volume_m3"]
    cells = [r["cells"] for r in ordered]
    quantities = {name: three_grid(cells, [r["monitors"][name] for r in ordered], volume, CONVERGENCE["gci_limit"])
                  for name in ("axis_torque_nm", "jet_flow_cmm")}
    accepted = all(q["accepted"] for q in quantities.values())
    return {"status": "mesh_study_passed" if accepted else "mesh_study_failed", "quantities": quantities,
            "recipe": ordered[0]["recipe"], "rpm": ordered[0]["rpm"], "direction": ordered[0]["direction"],
            "note": "Discretisation uncertainty on synthetic geometry only; physical accuracy needs measured fan data (Phase 2)."}


def recipe_study(levels, rpm, direction):
    """Run the listed mesh levels on the CFD host, keep each result, and combine when all three exist."""
    from .recipe import RECIPE, omega_rad_s
    omega_rad_s(rpm, direction)  # validate before touching the host
    root = Path(__file__).resolve().parent.parent
    store = root / "data" / "runtime" / "recipe"
    store.mkdir(parents=True, exist_ok=True)
    runner = Runner()
    code = 0
    for level in levels:
        started = datetime.now(timezone.utc).isoformat()
        print(f"Running {level} level at {rpm:g} RPM ({direction}) on {runner.describe()['backend']}...", flush=True)
        report = {"started_at": started, "level": level, "host": runner.describe(), "accepted_fan_results": False}
        try:
            # Host scripts enforce their own per-stage timeouts; this outer limit is a backstop.
            result = runner.run_script("recipe-case.sh", timeout=12 * 3600, args=(level, f"{rpm:g}", direction))
            report.update(exit_code=result.returncode, stdout=result.stdout[-20000:], stderr=result.stderr[-5000:],
                          result=_result_from_output(result.stdout))
            report["status"] = "completed" if result.returncode == 0 and report["result"] else "failed"
        except (OSError, subprocess.TimeoutExpired, HostError) as exc:
            report.update(status="failed", error=str(exc))
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        (store / f"{level}-{stamp}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        if report["status"] == "completed":
            (store / f"{level}.json").write_text(json.dumps(report["result"], indent=2), encoding="utf-8")
            status = report["result"]["convergence"]["status"]
            print(f"  {level}: {report['result']['cells']} cells, convergence {status}", flush=True)
        else:
            print(f"  {level}: failed; see {store / f'{level}-{stamp}.json'}", flush=True)
            code = 1
    results = {}
    for level in ("fine", "medium", "coarse"):
        path = store / f"{level}.json"
        if path.exists():
            candidate = json.loads(path.read_text(encoding="utf-8"))
            if candidate.get("recipe") == RECIPE["id"]:
                results[level] = candidate
    summary = dict(combine_levels(results), levels={k: {"cells": v["cells"], "convergence": v["convergence"]["status"],
                   "monitors": v["monitors"], "case": v["case"]} for k, v in results.items()})
    (root / "docs" / "recipe-study.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in summary if k != "levels"}, indent=2))
    return code or (0 if summary["status"] in ("mesh_study_passed", "incomplete") else 1)
