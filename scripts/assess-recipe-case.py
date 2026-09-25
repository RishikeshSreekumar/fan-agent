"""Assess one Phase 1 recipe run from saved monitors and fields. Prints RECIPE_RESULT_JSON=..."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fan_agent.analytics import load_metrics
from fan_agent.cell_slice import slice_case
from fan_agent.convergence import assess, moment_series, residual_series, surface_series
from fan_agent.mesh_report import summarize
from fan_agent.recipe import RECIPE
from fan_agent.solver_results import iteration_diagnostics

root = Path(sys.argv[1]).resolve()
manifest = json.loads((root / 'manifest.json').read_text())
def texts(pattern):
    files = sorted(root.glob(pattern), key=lambda p: float(p.parent.name))
    if not files:
        raise ValueError('Missing monitor output: ' + pattern)
    return [p.read_text() for p in files]
torque = moment_series(texts('postProcessing/fanLoads/*/moment.dat'))
jet = [(i, -v * 60) for i, v in surface_series(texts('postProcessing/jetFlow/*/surfaceFieldValue.dat'))]  # CMM, downward positive
log = (root / 'log.simpleFoam').read_text()
convergence = assess(torque, jet, residual_series(log))
latest = max(int(p.name) for p in root.iterdir() if p.is_dir() and p.name.isdigit() and (p / 'U').exists())
plane, _ = slice_case(root, latest, manifest['fan']['plane_height_m'])
mesh = summarize((root / 'log.checkMesh').read_text(), '', (root / 'log.topoSet').read_text())
wall = iteration_diagnostics(log)['latest_y_plus']
torque_mean = convergence['torque'].get('mean')
result = {
    'recipe': RECIPE['id'], 'level': manifest['level'], 'rpm': manifest['rpm'], 'direction': manifest['direction'],
    'case': str(root), 'cells': mesh['total_cells'], 'fluid_volume_m3': manifest['fluid_volume_m3'],
    'mesh_check_passed': mesh['extended_mesh_check_passed'], 'rotor_cells': mesh['rotor_cells'],
    'last_iteration': convergence['last_iteration'], 'convergence': convergence,
    'monitors': {'axis_torque_nm': torque_mean, 'jet_flow_cmm': convergence['jet_flow'].get('mean'),
                 'shaft_power_w': load_metrics((0, 0, torque_mean), (0, 0, 1), manifest['rpm'])['aerodynamic_shaft_power_w'] if torque_mean is not None else None},
    'plane_at_latest_write': dict(plane, iteration=latest), 'y_plus': wall,
    'accepted_performance': False,
    'limitations': ['Synthetic geometry.', 'Jet flow is the net downward flow (integral of -Uz) through the fan-footprint square at the sampling height.',
                    'Mesh sensitivity needs all three levels; accuracy needs measured data.'],
}
(root / 'recipe-assessment.json').write_text(json.dumps(result, indent=2))
print('RECIPE_RESULT_JSON=' + json.dumps(result))
