"""Create a local evidence table from retained experimental mesh cases."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fan_agent.mesh_report import summarize

rows = []
for argument in sys.argv[1:]:
    root = Path(argument)
    quality = summarize(*[(root/name).read_text() for name in ('log.checkMesh','log.snappyHexMesh','log.topoSet')])
    rows.append(dict(case=str(root), quality=quality))
out = Path(__file__).resolve().parent.parent/'docs'
(out/'mesh-trials.json').write_text(json.dumps(rows, indent=2))
lines = ['# Experimental mesh trials', '',
 'These are synthetic geometry tests, not validated fan simulations. No solver acceptance follows from these measurements.', '',
 '| WSL case suffix | Cells | Concave cells reported | Small determinant cells reported | Added layer cells | Mean layers | Extended check |',
 '|---|---:|---:|---:|---:|---:|---|']
for row in rows:
    q = row['quality']
    mean = q['layers']['mean_layers'] if q['layers'] else None
    path = Path(row['case'])
    label = path.parent.parent.name + ' / snapped' if path.name == 'snapped' else path.name
    values = [label, q['total_cells'],q['concave_cells'],q['small_determinant_cells'],q['added_layer_cells'],mean,'Pass' if q['extended_mesh_check_passed'] else 'Fail']
    lines.append('| '+' | '.join('Not reported' if v is None else str(v) for v in values)+' |')
lines += ['', 'Missing values mean not reported, not zero. Mean layer count is not the fraction of surface area covered. Full evidence is in each retained WSL case and `mesh-trials.json`.', '',
 'The synthetic fan surface and generated layers still need geometry fidelity, boundary-layer coverage, y-plus, grid sensitivity and physical validation before design use. The extended quality gate has not been relaxed.']
(out/'mesh-trials.md').write_text('\n'.join(lines))
print('\n'.join(lines))
