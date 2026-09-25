"""Validate named walls and save the independent CAD-mesh baseline assessment."""
import json
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from fan_agent.mesh_report import summarize
root = Path(sys.argv[1])
boundary = root/'constant/polyMesh/boundary'
text = boundary.read_text()
patches = re.findall(r'(\w+)\s*\{[^{}]*?nFaces\s+(\d+);[^{}]*\}',text)
if {name for name,count in patches} != {'fan','floor','ceiling','roomWalls'} or any(int(count)<=0 for name,count in patches):
    raise ValueError('Incomplete or unexpected boundary patches.')
if '--walls' in sys.argv:
    text,count = re.subn(r'\btype\s+patch;', 'type wall;',text)
    if count != 4: raise ValueError('Expected four imported wall patches.')
    boundary.write_text(re.sub(r'\bphysicalType\s+patch;', 'physicalType wall;',text))
else:
    quality = summarize((root/'log.checkMesh').read_text(), '', (root/'log.topoSet').read_text())
    result = {'stage':'final','method':'CAD-derived tetrahedral baseline', 'quality':quality,
              'mesh_baseline_passed':bool(quality['extended_mesh_check_passed'] and quality['rotor_cells']),
              'prism_layers':False, 'performance_validated':False,
              'boundary_faces':{name:int(count) for name,count in patches}}
    (root/'cad-mesh-assessment.json').write_text(json.dumps(result,indent=2))
    print('MESH_DIAGNOSTICS_JSON='+json.dumps(result))
    if not result['mesh_baseline_passed']: raise SystemExit(1)
