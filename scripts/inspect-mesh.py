"""Summarize flagged cells using vertex-average locations (not volume centroids)."""
import json
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fan_agent.mesh_report import summarize

root = Path(sys.argv[1])
mesh = root/'constant/polyMesh'
def body(path):
    text = path.read_text()
    text = re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)
    return re.search(r'\n\s*\d+\s*\((.*)\)', text, re.S).group(1)
points = [tuple(map(float, p.split())) for p in re.findall(r'\(([^()]*)\)', body(mesh/'points'))]
faces = [list(map(int, p.split())) for p in re.findall(r'\d+\(([^()]*)\)', body(mesh/'faces'))]
owner = list(map(int, body(mesh/'owner').split()))
neighbour = list(map(int, body(mesh/'neighbour').split()))
set_paths = [root/'0/polyMesh/sets/concaveCells', mesh/'sets/concaveCells']
quality = summarize((root/'log.checkMesh').read_text(), (root/'log.snappyHexMesh').read_text(), (root/'log.topoSet').read_text())
set_path = max((p for p in set_paths if p.exists()), key=lambda p:p.stat().st_mtime, default=None) if quality['concave_cells'] else None
flagged = set(map(int, body(set_path).split())) if set_path else set()
if quality['concave_cells'] and len(flagged) != quality['concave_cells']:
    raise ValueError('Flagged-cell set does not match the current quality log; refusing stale geometry diagnostics.')
vertices = {cell:set() for cell in flagged}
boundary = set()
for i, face in enumerate(faces):
    for cell in (owner[i], neighbour[i] if i < len(neighbour) else -1):
        if cell in vertices:
            vertices[cell].update(face)
            if i >= len(neighbour): boundary.add(cell)
centres = [tuple(sum(points[v][j] for v in vv)/len(vv) for j in range(3)) for vv in vertices.values()]
summary = {'stage':'snapped' if root.name == 'snapped' else 'final', 'flagged_cells_read':len(flagged) if set_path else None, 'set_file':str(set_path), 'touch_boundary':len(boundary),
 'near_rotor':sum(x*x+y*y < .75**2 and 2.1 < z < 2.7 for x,y,z in centres),
 'location_method':'mean of cell vertices, diagnostic only'}
summary['flagged_locations_m'] = centres if len(centres) <= 100 else []
summary['quality'] = quality
before_path = root/'stages/snapped/diagnostics.json'
if before_path.exists():
    summary['before_layers'] = json.loads(before_path.read_text())['quality']
print(json.dumps(summary, indent=2))
print('MESH_DIAGNOSTICS_JSON=' + json.dumps(summary, separators=(',', ':')))
(root/'diagnostics.json').write_text(json.dumps(summary, indent=2))
# A geometrical face-intersection slice, not a velocity contour.
lines = []
for i, face in enumerate(faces):
    coords = [points[v] for v in face]
    if min(p[1] for p in coords) > 0 or max(p[1] for p in coords) < 0:
        continue
    hits = []
    for a,b in zip(coords, coords[1:]+coords[:1]):
        if (a[1] <= 0 < b[1]) or (b[1] <= 0 < a[1]):
            t = -a[1]/(b[1]-a[1])
            hits.append((a[0]+t*(b[0]-a[0]), a[2]+t*(b[2]-a[2])))
    if len(hits) != 2 or not all(-.8 <= x <= .8 and 2.1 <= z <= 2.7 for x,z in hits):
        continue
    (x,z),(xx,zz) = hits
    red = owner[i] in flagged or (i < len(neighbour) and neighbour[i] in flagged)
    color = '#ce332b' if red else '#597b72'
    lines.append(f'<path d="M {50+(x+.8)*687.5:.2f} {65+(2.7-z)*687.5:.2f} L {50+(xx+.8)*687.5:.2f} {65+(2.7-zz)*687.5:.2f}" stroke="{color}" stroke-width="{1.8 if red else .5}"/>')
svg = '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="540" viewBox="0 0 1200 540"><rect width="1200" height="540" fill="white"/><g font-family="Arial" fill="#203c34"><text x="50" y="30" font-size="20">Synthetic fan mesh — X–Z section at Y = 0 m</text><text x="50" y="52" font-size="12">X: −0.8 to 0.8 m; Z: 2.1 to 2.7 m. Red: slice edges adjoining flagged concave cells.</text>'+''.join(lines)+'<text x="50" y="515" font-size="13">Geometry diagnostic only. This slice may not intersect every flagged cell. No flow solution.</text></g></svg>'
(root/'mesh-section.svg').write_text(svg)
if '--gate' in sys.argv and not summary['quality']['development_gate_passed']:
    raise SystemExit(1)
