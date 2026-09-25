from pathlib import Path
import gmsh,json
ROOT=Path(__file__).resolve().parent
groups=json.loads((ROOT/'surface-components.json').read_text())
gmsh.initialize();gmsh.option.setNumber('General.Terminal',0)
try:
 gmsh.model.occ.importShapes(str(ROOT/'healed-assembly.brep'));gmsh.model.occ.synchronize()
 selected=[17,18,19];keep={t for g in groups if g['id'] in selected for t in g['faces']}
 gmsh.model.occ.remove([(d,t) for d,t in gmsh.model.getEntities(2) if t not in keep],recursive=True)
 gmsh.model.occ.synchronize();report=[]
 for gid in selected:
  group=next(g for g in groups if g['id']==gid)
  if set(group['edge_incidence_histogram'])!={'2'}:raise ValueError('Shell is not closed.')
  loop=gmsh.model.occ.addSurfaceLoop(group['faces'],sewing=True)
  volume=gmsh.model.occ.addVolume([loop]);gmsh.model.occ.synchronize()
  mass=gmsh.model.occ.getMass(3,volume)
  if mass<=0:raise ValueError('Invalid volume.')
  report.append({'source_group':gid,'volume_tag':volume,'volume_mm3':mass,'face_count':len(gmsh.model.getBoundary([(3,volume)],oriented=False))})
 gmsh.write(str(ROOT/'stationary-solids-mm.brep'))
 gmsh.model.occ.affineTransform(gmsh.model.getEntities(3),[0,.001,0,.460,0,0,.001,-1.515,.001,0,0,.400,0,0,0,1]);gmsh.model.occ.synchronize()
 gmsh.write(str(ROOT/'stationary-solids-metres.brep'))
 (ROOT/'stationary-preparation.json').write_text(json.dumps({'status':'closed_CAD_solids_not_fluid_mesh','components':report},indent=2));print(json.dumps(report,indent=2))
finally:gmsh.finalize()
